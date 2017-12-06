# -*- coding:utf-8 -*-
#
# Copyright @ 2017 OPS Inc.
#
# Author: Jinlong Yang
#

import sys
import time
import selectors
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

ssh_opts = [
    cfg.StrOpt(
        'local_ssh_ip',
        help='local host ssh server ip.'
    ),
    cfg.IntOpt(
        'local_ssh_port',
        help='local host ssh server port.'
    )
]

CONF = cfg.CONF
CONF.register_opts(idle_opts, 'IDLE')
CONF.register_opts(record_opts, 'RECORD')
CONF.register_opts(ssh_opts, 'SSH')


class SSHProxy(threading.Thread):

    def __init__(self, context, client_channel):
        super(SSHProxy, self).__init__()
        self.context = context
        self.ip = CONF.SSH.local_ssh_ip
        self.port = CONF.SSH.local_ssh_port
        self.username = context.username
        self.client_channel = client_channel
        self.password = CocoService().get_ldap_pass(self.username)

    def run(self):
        self.login()

    def login(self, term='linux', width=80, height=24):
        """ Login to relay proxy server.
        """
        width = self.context.win_width
        height = self.context.win_height
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client_channel.sendall(
            cm.ws('......Connecting to relay %s, please wait.\r\n' % self.ip))
        try:
            ssh_client.connect(self.ip, port=self.port, username=self.username,
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

        sel = selectors.DefaultSelector()
        sel.register(client, selectors.EVENT_READ)
        sel.register(client_channel, selectors.EVENT_READ)
        sel.register(backend_channel, selectors.EVENT_READ)

        while True:
            events = sel.select(CONF.IDLE.timeout)
            fd_sets = [key.fileobj for key, mask in events if key]
            # NOTE(SecureCrt events return [])
            if not fd_sets:
                self.timeout_handle(client_channel)
                self.exception_handle(backend_channel)
                sys.exit(1)

            # NOTE(Iterm2 events return [client事件])
            if client_channel in fd_sets or backend_channel in fd_sets:
                begin_time = int(time.time())
            cur_time = int(time.time())
            if (cur_time - begin_time) > CONF.IDLE.timeout:
                self.timeout_handle(client_channel)
                self.exception_handle(backend_channel)
                sys.exit(1)

            if self.context.change_win_size_event.is_set():
                self.context.change_win_size_event.clear()
                width = self.context.win_width
                height = self.context.win_height
                LOG.debug('*** Proxy fetch change window size (%s, %s).'
                          % (width, height))
                backend_channel.resize_pty(width=width, height=height)

            if client_channel in fd_sets:
                client_data = client_channel.recv(1024)
                if len(client_data) == 0:
                    LOG.warn('*** Proxy receive client from user: %s data '
                             'length is 0, so exit.' % self.username)
                    self.exception_handle(backend_channel)
                    sys.exit(1)
                backend_channel.sendall(client_data)

            if backend_channel in fd_sets:
                backend_data = backend_channel.recv(1024)
                if len(backend_data) == 0:
                    client_channel.sendall(cm.ws(
                        'Disconnect from %s' % self.ip))
                    LOG.info('Logout from user: %s host: %s.'
                             % (self.username, self.ip))
                    self.exception_handle(backend_channel)
                    sys.exit(1)
                client_channel.sendall(backend_data)
                time.sleep(paramiko.common.io_sleep)

    def timeout_handle(self, client_channel):
        tips = '\033[1;31mLogout\r\n'
        tips += ('Noting to do, timeout %s seconds, so disconnect.\033[0m'
                 % CONF.IDLE.timeout)
        client_channel.sendall('\r\n' + tips + '\r\n')
        LOG.warn('*** User %s on host %s %s' % (self.username, self.ip, tips))

    def exception_handle(self, backend_channel):
        if self.client_channel == self.context.channel_list[0]:
            for chan in self.context.channel_list:
                chan.close()
            self.context.transport.atfork()
        else:
            if self.client_channel in self.context.channel_list:
                self.context.channel_list.remove(self.client_channel)
            self.client_channel.close()
        if backend_channel:
            try:
                backend_channel.close()
            except:
                pass
