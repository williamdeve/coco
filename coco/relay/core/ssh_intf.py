# -*- coding:utf-8 -*-
#
# Copyright @ 2017 OPS Inc.
#
# Author: Jinlong Yang
#

import os
import threading
from io import StringIO

from coco.util.service import CocoService

import paramiko


class SSHServer(paramiko.ServerInterface):

    def __init__(self, context):
        self.context = context
        self.shell_request_event = threading.Event()
        context.change_win_size_event = threading.Event()

    def check_auth_password(self, username, password):
        ts = CocoService()
        if ts.validate(username, password):
            self.context.username = username
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, public_key):
        # NOTE(Because use password + otp authentication, so don't need to
        #      use the public key certificate)
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_pty_request(self, channel, term, width, height,
                                  pixelwidth, pixelheight, modes):
        self.context.win_width = self.context.channel.win_width = width
        self.context.win_height = self.context.channel.win_height = height
        return True

    def check_channel_shell_request(self, channel):
        self.shell_request_event.set()
        return True

    def check_channel_window_change_request(self, channel, width, height,
                                            pixelwidth, pixelheight):
        self.context.win_width = self.context.channel.win_width = width
        self.context.win_height = self.context.channel.win_height = height
        self.context.change_win_size_event.set()
        return True


class SSHKeyGen(object):

    @classmethod
    def rsa_key(cls):
        proj_path = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))))
        rsa_key_path = os.path.join(proj_path, '.keys', 'rsa_key')
        if not os.path.isfile(rsa_key_path):
            cls.create_rsa_key(rsa_key_path)
        return paramiko.RSAKey(filename=rsa_key_path)

    @classmethod
    def create_rsa_key(cls, filename, length=2048, password=None):
        """ Generating private key
        """
        f = StringIO()
        prv = paramiko.RSAKey.generate(length)
        prv.write_private_key(f, password=password)
        private_key = f.getvalue()
        with open(filename, 'w') as f:
            f.write(private_key)
