# -*- coding:utf-8 -*-
#
# Copyright @ 2017 OPS Inc.
#
# Author: Jinlong Yang
#

import sys
import socket
import signal
import traceback
import multiprocessing

import paramiko
from dotmap import DotMap
from oslo_config import cfg
from osmo.basic import Basic
from oslo_log import log as logging

from coco.relay.core.ssh_intf import SSHKeyGen
from coco.relay.core.ssh_intf import SSHServer
from coco.relay.core.ssh_proxy import SSHProxy

LOG = logging.getLogger(__name__)

server_opts = [
    cfg.StrOpt('host', default='0.0.0.0',
                help='Coco server listen address.'),
    cfg.IntOpt('port', default=None,
                help='Coco server listen port.'),
    cfg.IntOpt('pool_limit', default=None,
                help='Coco server process pool size.')
]

ssh_opts = [
    cfg.IntOpt('timeout', default=None,
               help='Transport accept next channel timeout.')
]

CONF = cfg.CONF
CONF.register_opts(server_opts, 'SERVER')
CONF.register_opts(ssh_opts, 'SSH')


def SignalHandler():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def SSHBootstrap(client, rhost, ip):
    context = DotMap()
    context.ip = ip
    context.client = client
    context.channel_list = []
    context.remote_host = rhost

    trans = paramiko.Transport(client, gss_kex=False)
    try:
        trans.load_server_moduli()
    except:
        LOG.error('(Failed to load moduli -- gex will be unsupported.)')
        client.close()
        sys.exit(1)

    context.trans = trans
    trans.add_server_key(SSHKeyGen.rsa_key())

    ssh_server = SSHServer(context)
    try:
        trans.start_server(server=ssh_server)
    except paramiko.SSHException as _ex:
        LOG.error('SSH negotiation failed: %s' % str(_ex))
        client.close()
        sys.exit(1)

    while trans.is_active():
        channel = trans.accept(timeout=CONF.SSH.timeout)
        if channel is None:
            if not context.channel_list:
                LOG.error('*** Channel timeout from remote host: %s.' % rhost)
                LOG.error('*** First login timeout > %s, so close client.'
                          % CONF.SSH.timeout)
                try:
                    client.send(b'Connect from %s timeout.' % rhost)
                    client.close()
                    trans.atfork()
                except:
                    pass
                sys.exit(1)
            continue

        ssh_server.shell_request_event.wait(10)
        if not ssh_server.shell_request_event.is_set():
            LOG.error('*** Client never asked for a shell.')
            try:
                client.send(b'Must be shell request.')
                client.close()
                trans.atfork()
            except:
                pass
            sys.exit(1)
        LOG.info('Client asking for a shell.')
        context.channel = channel
        context.channel_list.append(channel)

        proxyer = SSHProxy(context)
        proxyer.start()

    try:
        client.close()
    except:
        pass
    sys.exit(1)
    LOG.info('*** Client from %s trans.is_active() is false.' % rhost)


class Relay(Basic):
    name = 'relay'
    version = '0.1'

    def __init__(self):
        super(Relay, self).__init__()
        self.ip = self.local_ip()
        self.host = CONF.SERVER.host
        self.port = CONF.SERVER.port
        self.pool = multiprocessing.Pool(CONF.SERVER.pool_limit, SignalHandler)

    def run(self):
        self.build_lisen()
        LOG.info('Starting ssh server at %s:%s' % (self.host, self.port))
        LOG.info('Quit the server with CONTROL-C.')

        while True:
            cs, (rhost, rport) = self.fd.accept()
            LOG.info('Receive client addr: %s:%s' % (rhost, rport))
            cs.setblocking(0)
            try:
                self.pool.apply_async(SSHBootstrap, (cs, rhost, self.ip))
            except KeyboardInterrupt:
                self.pool.terminate()
                self.pool.close()
            except Exception as _ex:
                LOG.error('SSH bootstrap exception: %s' % str(_ex))
                traceback.print_exc()

    def build_lisen(self):
        self.fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.fd.bind((self.host, self.port))
        self.fd.listen(500)

    def close(self):
        try:
            self.fd.close()
        except:
            pass

    def local_ip(self):
        hostname = socket.gethostname()
        fqdn = socket.getfqdn(hostname)
        ip = socket.gethostbyname(fqdn)
        return ip
