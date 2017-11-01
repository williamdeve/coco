# -*- coding:utf-8 -*-
#
# Copyright @ 2017 OPS Inc.
#
# Author: Jinlong Yang
#

import sys
import time
import select
import threading

import paramiko
from oslo_config import cfg
from oslo_log import log as logging

import coco.util.common as cm
from coco.util.service import CocoService

LOG = logging.getLogger(__name__)

idle_opts = [
    cfg.IntOpt(
        'timeout',
        help='Noting to do timeout.'
    )
]

record_opts = [
    cfg.StrOpt(
        'record_path',
        help='record operation log path.'
    )
]

CONF = cfg.CONF
CONF.register_opts(idle_opts, 'IDLE')
CONF.register_opts(record_opts, 'RECORD')


class SSHProxy(threading.Thread):

    def __init__(self, context):
        super(SSHProxy, self).__init__()
        self.context = context
        self.ip = context.ip
        self.username = context.username
        self.client_channel = context.channel
        self.password = CocoService().get_ldap_pass(self.username)

    def run(self):
        self.login()

    def login(self, term='xterm', width=80, height=24):
        """ Login to relay proxy server.
        """
        width = self.context.win_width
        height = self.context.win_height
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client_channel.sendall(
            cm.ws('......Connecting to relay %s, please wait.\r\n' % self.ip))
        try:
            ssh_client.connect(self.ip, username=self.username,
                               password=self.password, allow_agent=True,
                               look_for_keys=False, compress=True, timeout=120)
        except Exception as _ex:
            msg = 'Connect to relay server %s failed: %s' % (self.ip, str(_ex))
            LOG.error(msg)
            self.client_channel.sendall(cm.ws(msg, level='warn'))
            if self.client_channel == self.context.channel_list[0]:
                try:
                    self.client_channel.close()
                except:
                    pass
            else:
                try:
                    self.context.channel_list.remove(self.client_channel)
                    self.client_channel.close()
                except:
                    pass
            sys.exit(1)
        else:
            LOG.info('Connect to relay server : %s success.' % self.ip)
            backend_channel = ssh_client.invoke_shell(
                term=term, width=width, height=height)
            backend_channel.settimeout(100)
            self.interactive_shell(backend_channel)

    def interactive_shell(self, backend_channel):
        begin_time = None
        client = self.context.client
        client_channel = self.client_channel
        rlist = [client_channel, backend_channel, client]
        while True:
            try:
                rs, ws, es = select.select(rlist, [], [], CONF.IDLE.timeout)
            except:
                self.data_except_handle(backend_channel)
                sys.exit(1)

            if rs and (client_channel in rs or backend_channel in rs):
                begin_time = int(time.time())
            cur_time = int(time.time())
            if not (rs or ws or es) or rs and begin_time is not None and \
               client_channel not in rs and backend_channel not in rs and \
               (cur_time - begin_time) > CONF.IDLE.timeout:
                tips = '\033[1;31mLogout\r\n'
                tips += 'Noting to do, timeout 1 hours, so disconnect.\033[0m'
                client_channel.sendall('\r\n' + tips + '\r\n')
                LOG.warn('User: %s asset: %s tips: %s'
                         % (self.username, self.ip, tips))
                self.data_except_handle(backend_channel)
                sys.exit(1)

            if client in rs and self.context.change_win_size_event.is_set():
                self.context.change_win_size_event.clear()
                width = self.client_channel.win_width
                height = self.client_channel.win_height
                backend_channel.resize_pty(width=width, height=height)

            if client_channel in rs:
                client_data = client_channel.recv(1024)
                if len(client_data) == 0:
                    LOG.warn('*** Proxy receive client from user: %s data '
                             'length is 0, so exit.' % self.username)
                    self.data_except_handle(backend_channel)
                    sys.exit(1)
                backend_channel.sendall(client_data)

            if backend_channel in rs:
                backend_data = backend_channel.recv(1024)
                if len(backend_data) == 0:
                    client_channel.sendall(cm.ws(
                        'Disconnect from %s' % self.ip))
                    LOG.info('Logout from user: %s host: %s.'
                             % (self.username, self.ip))
                    self.data_except_handle(backend_channel)
                    sys.exit(1)
                client_channel.sendall(backend_data)
                time.sleep(paramiko.common.io_sleep)

    def data_except_handle(self, backend_channel):
        if self.client_channel == self.context.channel_list[0]:
            for chan in self.context.channel_list:
                chan.close()
            self.context.transport.atfork()
        else:
            self.context.channel_list.remove(self.client_channel)
            self.client_channel.close()
        try:
            backend_channel.close()
        except:
            pass
