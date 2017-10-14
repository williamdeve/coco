# -*- coding:utf-8 -*-
#
# Copyright @ 2017 OPS Inc.
#
# Author: Jinlong Yang
#

from dotmap import DotMap


class CocoService(object):

    def validate(self, username, password):
        return True

    def get_user_asset(self, username):
        assets = [
            DotMap({'ip': '10.0.2.189', 'hostname': 'l-jinlong1.op.dev'}),
            DotMap({'ip': '10.0.2.41', 'hostname': 'l-jinlong2.op.dev'}),
        ]
        return assets

    def get_ldap_pass(self, username):
        return 'yangjinlong'
