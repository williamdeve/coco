# -*- coding:utf-8 -*-
#
# Copyright @ 2017 OPS Inc.
#
# Author: Jinlong Yang
#

from dotmap import DotMap

from oslo_config import cfg
from oslo_log import log as logging

import coco.util.common as cm

LOG = logging.getLogger(__name__)

intf_opts = [
    cfg.StrOpt('salt',
               help='coco service interface md5 salt value.'),
    cfg.StrOpt('user_valid_intf',
               help='coco service user login validate interface.'),
    cfg.StrOpt('user_asset_intf',
               help='coco service fetch user asset info interface.'),
    cfg.StrOpt('user_ldap_pass_intf',
               help='coco service fetch user ldap password interface.')
]

CONF = cfg.CONF
CONF.register_opts(intf_opts, 'INTF')


class CocoService(object):

    def validate(self, username, password):
        url = CONF.INTF.user_valid_intf
        payload = {
            'username': username,
            'password': password
        }
        user_info = cm.http_handler(url, payload, 'POST')
        if user_info is None:
            return False
        return True

    def get_user_asset(self, username):
        url = CONF.INTF.user_asset_intf
        payload = {
            'username': username
        }
        sign = cm.parameter_sign(payload)
        payload['sign'] = sign
        assets = cm.http_handler(url, payload, 'POST')
        asset_list = [DotMap(item) for item in assets if item]
        return asset_list

    def get_ldap_pass(self, username):
        url = CONF.INTF.user_ldap_pass_intf
        payload = {
            'ldap_user': username
        }
        sign = cm.parameter_sign(payload)
        payload['sign'] = sign
        ret = cm.http_handler(url, payload, 'POST')
        return ret
