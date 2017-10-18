# -*- coding:utf-8 -*-
#
# Copyright @ 2017 OPS Inc.
#
# Author: Jinlong Yang
#

import hashlib
from dotmap import DotMap
from operator import itemgetter

import requests
from oslo_config import cfg
from oslo_log import log as logging

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
        return True

    def get_user_asset(self, username):
        assets = [
            DotMap({'ip': '10.0.2.189', 'hostname': 'l-jinlong1.op.dev'}),
            DotMap({'ip': '10.0.2.41', 'hostname': 'l-jinlong2.op.dev'}),
        ]
        return assets

    def get_ldap_pass(self, username):
        return 'yangjinlong'

    def sign(self, data):
        """ Http interface get or post param sign encrypt mode.
        First, according to key sorted.
        Second, join key value to a string.
        Third, calculate md5 and then put salt calculate md5 again.
        For example:
            data = {'name': 'yy', 'age': 18}
            First: new_data = {'age': 18, 'name': 'yy'}
            Second: origin_data = 'age18nameyy'
            Third: calculate md5 and put salt md5 value again.
        """
        new_data = sorted(data.items(), key=itemgetter(0))
        origin_data = ''
        for item in new_data:
            origin_data += str(item[0])
            origin_data += str(item[1])
        encrypt_data = hashlib.md5(origin_data.encode()).hexdigest()
        return hashlib.md5(
            (encrypt_data+CONF.INTF.salt).encode()).hexdigest().upper()

    def http_handler(self, url, payload, http_type='GET'):
        """ Http interface return params and values's json object.
        {
            "errcode": 0 success 1 failure,
            "errmsg": error message, if success then "",
            "data":  result value, is string or list or dict and so on
        }
        """
        try:
            if http_type == 'POST':
                resp = requests.post(url, data=payload)
            else:
                resp = requests.get(url, params=payload)
        except Exception as _ex:
            LOG.error('fetch coco service http data eception: %s' % str(_ex))
            return None
        if resp.status_code != 200:
            LOG.error('fetch coco service http code: %s' % resp.status_code)
            return None
        ret_info = resp.json()
        errcode = ret_info.get('errcode')
        if errcode != 0:
            LOG.warn('fetch coco service http data error: %s'
                     % ret_info.get('errmsg'))
            return None
        return ret_info.get('data')
