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
        url = CONF.INTF.user_valid_intf
        payload = {
            'username': username,
            'password': password
        }
        user_info = self.http_handler(url, payload, 'POST')
        if user_info is None:
            return False
        return True

    def get_user_asset(self, username):
        url = CONF.INTF.user_asset_intf
        payload = {
            'username': username
        }
        sign = self.data_sign(payload)
        payload['sign'] = sign
        assets = self.http_handler(url, payload, 'POST')
        asset_list = [DotMap(item) for item in assets if item]
        return asset_list

    def get_ldap_pass(self, username):
        url = CONF.INTF.user_ldap_pass_intf
        payload = {
            'ldap_user': username
        }
        sign = self.data_sign(payload)
        payload['sign'] = sign
        ret = self.http_handler(url, payload, 'POST')
        return ret

    def data_sign(self, data):
        """ 接口传输参数进行签名计算, 分如下三步:
        第一, 首先根据key进行排序.
        第二, 之后将key和value拼接一起成为一个字符串, 并计算出一个md5.
        第三, 将第二步的md5再加盐算出新的md5值.
        For example:

        原始数据:
        >>> data = {'name': 'yy', 'age': 18}

        计算签名:
        >>> new_data = {'age': 18, 'name': 'yy'}
        >>> origin_data = 'age18nameyy'
        >>> encrypt_data = hashlib.md5(origin_data.encode()).hexdigest()
        >>> sign = hashlib.md5(encrypt_data+CONF.INTF.sal).encode().hexdigest()
        >>> return sign
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
