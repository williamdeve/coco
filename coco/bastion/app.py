# -*- coding:utf-8 -*-
#
# Copyright @ 2017 OPS Inc.
#
# Author: Jinlong Yang
#

import io
import os
import sys
import time
import fcntl
import signal
import struct
import termios
import getpass
from datetime import datetime

import pexpect
from oslo_config import cfg
from osmo.basic import Basic
from oslo_log import log as logging

import coco.util.common as cm
from coco.util.service import CocoService

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

LOG = logging.getLogger(__name__)

record_opts = [
    cfg.StrOpt('record_path',
                help='Coco server record operation log info.')
]

CONF = cfg.CONF
CONF.register_opts(record_opts, 'RECORD')


class Bastion(Basic):
    name = 'bastion'
    version = '0.1'

    def __init__(self):
        super(Bastion, self).__init__()
        self.username = getpass.getuser()
        self.user_info = UserHostInfo(self.username)
        self.terminal = SSHTerminal()

    def run(self):
        self.display_banner()

    def screen_clear(self):
        os.system('clear')

    def show_art(self):
        print (cm.terminal_art())

    def show_nav(self):
        print (cm.terminal_nav(self.username))

    def exit_tty(self):
        proxy_path = os.path.dirname(os.path.abspath(__file__))
        exit_cmd = '/bin/bash %s/exit.sh' % proxy_path
        os.system(exit_cmd)

    def display_banner(self):
        self.screen_clear()
        self.show_art()
        self.show_nav()

        while True:
            try:
                option = input(cm.PROMPT)
            except EOFError:
                self.screen_clear()
                self.show_nav()
                continue
            except KeyboardInterrupt:
                self.screen_clear()
                self.show_nav()
                continue
            try:
                self.interactive_handle(option)
            except Exception as _ex:
                LOG.error('*** interactive handle error: %s' % str(_ex))
                self.screen_clear()
                self.show_nav()
                continue

    def interactive_handle(self, option):
        if option in ['p', 'P']:
            self.user_info.show_hostlist()
        elif option.startswith('/'):
            self.user_info.show_searchinfo(option)
        elif option in ['h', 'H']:
            self.screen_clear()
            self.show_nav()
        elif option in ['q', 'Q']:
            self.exit_tty()
            sys.exit()
        else:
            search_result = self.user_info.search_host(option)
            if len(search_result) == 1:
                self.terminal.redirect_ssh_proxy(self.username,
                                                 search_result[0].ip,
                                                 search_result[0].port)
            elif len(search_result) == 0:
                print (cm.ws('No host match, please input again.',
                             level='warn'))
            else:
                print (cm.ws('Search result not unique, select below '
                             'or search again.', after=2, level='warn'))


class UserHostInfo(object):

    def __init__(self, username):
        self.assets = CocoService().get_user_asset(username)

    def show_hostlist(self):
        self.show_host_table(self.assets)

    def show_host_table(self, asset_list):
        line = '[%-4s] %-16s %-5s %-30s'
        print (cm.ws(cm.wc(line % ('ID', 'IP', 'Port', 'Hostname'))))
        end = len(asset_list) - 1
        for index, item in enumerate(asset_list):
            info = cm.ws(cm.wc(
                line % (index, item.ip, '22', item.hostname), False))
            if index == end:
                info += '\n'
            print (info)

    def show_searchinfo(self, option):
        option = option.lstrip('/').strip().lower()
        search_result = self.search_host(option)
        self.show_host_table(search_result)

    def search_host(self, option):
        if option:
            search_result = [
                asset for asset in self.assets if option in asset.ip] or [
                    asset for asset in self.assets
                    if option in asset.hostname.lower()
                ]
            return search_result
        return self.assets


class SSHTerminal(object):

    def __init__(self):
        self.cs = CocoService()

    def window_change(self, sig, data):
        """This function use to set the window size of the terminal!
        """
        winsize = self.get_window_size()
        self.ssh.setwinsize(winsize[0], winsize[1])

    def get_window_size(self):
        """This function use to get the size of the windows!
        """
        if 'TIOCGWINSZ' in dir(termios):
            TIOCGWINSZ = termios.TIOCGWINSZ
        else:
            TIOCGWINSZ = 1074295912  # Assume
        s = struct.pack('HHHH', 0, 0, 0, 0)
        x = fcntl.ioctl(sys.stdout.fileno(), TIOCGWINSZ, s)
        return struct.unpack('HHHH', x)[0:2]

    def get_log_file(self, username, ip):
        today = datetime.now().strftime('%Y%m%d')
        log_dir = '%s/%s' % (CONF.RECORD.record_path, today)
        if not os.path.isdir(log_dir):
            os.mkdir(log_dir)
        record_log = '%s/%s_%s_%s.log' % (log_dir, ip, today, username)
        logfile = open(record_log, 'a')
        logfile.write('\nuser: %s on time: %s login host: %s\n'
                      % (username, time.strftime('%Y-%m-%d %H:%M:%S'), ip))
        return logfile

    def redirect_ssh_proxy(self, username, ip, port=22):
        """ Use pexpect connect to server
        """
        logfile = self.get_log_file(username, ip)
        password = self.cs.get_ldap_pass(username)
        command = 'ssh -p %s %s@%s' % (port, username, ip)
        self.ssh = pexpect.spawn('/bin/bash', ['-c', command])
        self.ssh.logfile = logfile.buffer
        while True:
            index = self.ssh.expect(
                ['continue', 'assword', pexpect.EOF, pexpect.TIMEOUT],
                timeout=120
            )
            if index == 0:
                self.ssh.sendline('yes')
                continue
            elif index == 1:
                self.ssh.sendline(password)
            elif index == 2:
                print ('Connect exception, please check the server '
                       'whether is started')
                break
            elif index == 3:
                print ('Connect timeout, please check the server '
                       'whether is started.')
                break

            index = self.ssh.expect(
                ['assword', '.*', pexpect.EOF, pexpect.TIMEOUT], timeout=120)
            if index == 1:
                signal.signal(signal.SIGWINCH, self.window_change)
                size = self.get_window_size()
                self.ssh.setwinsize(size[0], size[1])
                print ('\033[32;1mLogin host %s success!\033[0m' % ip)
                self.ssh.interact()
                break
            elif index == 0:
                print ('Password error, please contact system administrator!')
                break
            else:
                print ('Login failed, please contact system administrator!')
                break
        self.ssh.terminate(force=True)
