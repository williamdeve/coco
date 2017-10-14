# -*- coding:utf-8 -*-
#
# Copyright @ 2017 OPS Inc.
#
# Author: Jinlong Yang
#

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
