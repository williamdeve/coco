# -*- coding:utf-8 -*-
#
# Copyright @ 2017 OPS Inc.
#
# Author: Jinlong Yang
#

import hashlib
from operator import itemgetter

import requests
from oslo_config import cfg
from oslo_log import log as logging

LOG = logging.getLogger(__name__)

intf_opts = [
    cfg.StrOpt('salt',
               help='coco service interface md5 salt value.'),
]

CONF = cfg.CONF
CONF.register_opts(intf_opts, 'INTF')

PROMPT = 'Opt> '

SESSION_LIMIT = 10


def terminal_art():
    art = "\033[1;36m"
    art += " " * 3 + "                                           \r\n"
    art += " " * 3 + "                  _oo8oo_                  \r\n"
    art += " " * 3 + "                 o8888888o                 \r\n"
    art += " " * 3 + '                 88" . "88                 \r\n'
    art += " " * 3 + "                 (| -_- |)                 \r\n"
    art += " " * 3 + "                 0\  =  /0                 \r\n"
    art += " " * 3 + "               ___/'==='\___               \r\n"
    art += " " * 3 + "             .' \\|     |// '.             \r\n"
    art += " " * 3 + "            / \\|||  :  |||// \            \r\n"
    art += " " * 3 + "           / _||||| -:- |||||_ \           \r\n"
    art += " " * 3 + "          |   | \\\  -  /// |   |          \r\n"
    art += " " * 3 + "          | \_|  ''\---/''  |_/ |          \r\n"
    art += " " * 3 + "          \  .-\__  '-'  __/-.  /          \r\n"
    art += " " * 3 + "        ___'. .'  /--.--\  '. .'___        \r\n"
    art += " " * 3 + "     ."" '<  '.___\_<|>_/___.'  >' "".     \r\n"
    art += " " * 3 + "    | | :  `- \`.:`\ _ /`:.`/ -`  : | |    \r\n"
    art += " " * 3 + "    \  \ `-.   \_ __\ /__ _/   .-` /  /    \r\n"
    art += " " * 3 + "=====`-.____`.___ \_____/ ___.`____.-`=====\r\n"
    art += " " * 3 + "                  `=---=`                  \r\n"
    art += "\033[0m"
    art += " " * 3 + "                                           \r\n"
    art += "\033[1;31m"
    art += " " * 3 + "        佛祖保佑           永无bug             "
    art += "\033[0m"
    return art


def terminal_nav(username):
    tip = '\r\n\033[1;31m'
    tip += ' ' * 3 + '%s \033[0m你好, 跳板机使用方法如下: \r\n\r\n' % username
    tip += ' ' * 5 + '➜  输入\033[1;31mID\033[0m 直接登录'
    tip += '或\033[1;31m部分IP,主机名\033[0m进行搜索登录(如果唯一).\r\n'
    tip += ' ' * 5 + '➜  输入\033[1;31m/\033[0m + \033[1;31mIP, '
    tip += '主机名\033[0m 搜索, 如: /ip.\r\n'
    tip += ' ' * 5 + '➜  输入\033[1;31mP/p\033[0m 显示您有权限的主机.\r\n'
    tip += ' ' * 5 + '➜  输入\033[1;31mH/h\033[0m 帮助.\r\n'
    tip += ' ' * 5 + '➜  输入\033[1;31mQ/q\033[0m 退出.\r\n'
    return tip


def ws(s, before=0, after=0, level='info'):
    """ Wrap string info with line feed.
    """
    tip = ''
    if level == 'info':
        tip = '\r\n' * before + s + '\r\n' * after
    elif level == 'warn':
        tip = '\r\n' * before + '\033[1;33m' + s + '\033[0m' + '\r\n' * after
    return tip


def wc(s, has_bg=True):
    """ Wrap string with color.
    """
    if has_bg:
        return '\033[1;30;41m' + s + '\033[0m'
    else:
        return '\033[1;31m' + s + '\033[0m'


def parameter_sign(data):
    """ Interface request parameters sign calculate method.

    Signature calculation process is as follows:
    1. according the "key" to sorted
    2. stitching "key" and "value" to a string, and calculate the md5
    3. use the second step of "md5" add "salt" work out new md5.

    origin data:
    >>> data = {'name': 'yy', 'age': 18}

    calculate origin data's signature:
    >>> new_data = {'age': 18, 'name': 'yy'}
    >>> origin_data = 'age18nameyy'
    >>> encrypt_data = hashlib.md5(origin_data.encode()).hexdigest()
    >>> new_data = (encrypt_data+CONF.INTF.salt).encode()
    >>> sign = hashlib.md5(new_data).hexdigest().upper()
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


def http_handler(url, payload, http_type='GET'):
    """ Use ``requests`` library handle http get or post request.

    URL interface return value is json object. such as:
    {'errcode': 0/1, 'errmsg': 'xxxx', data: []/{}/value}


    :returns: data list or dict or concrete value if request is success.
              or ``None``
    """
    try:
        if http_type == 'POST':
            resp = requests.post(url, data=payload)
        else:
            resp = requests.get(url, params=payload)
    except Exception as _ex:
        LOG.error('*** Request %s eception: %s' % (http_type, str(_ex)))
        return None
    status_code = resp.status_code
    if status_code != 200:
        LOG.error('*** Request %s http code: %s' % (http_type, status_code))
        return None
    ret_info = resp.json()
    errcode = ret_info.get('errcode')
    if errcode != 0:
        errmsg = ret_info.get('errmsg')
        LOG.warn('*** Request intf: %s data failed: %s' % (url, errmsg))
        return None
    return ret_info.get('data')
