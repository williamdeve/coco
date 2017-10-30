# -*- coding:utf-8 -*-
#
# Copyright @ 2017 OPS Inc.
#
# Author: Jinlong Yang
#

import os
import re
import subprocess
from datetime import date, timedelta

import pyte
from osmo.basic import Basic


class SSHIOParser(object):

    def __init__(self, width=175, height=40):
        self.screen = pyte.Screen(width, height)
        self.stream = pyte.ByteStream()
        self.stream.attach(self.screen)
        self.ps1_pattern = re.compile(r'^\[?.*@.*\]?[\$#]\s|mysql>\s')

    def tty_parser(self, data):
        display_list = []
        try:
            if not isinstance(data, bytes):
                data = data.encode('utf-8', errors='ignore')
            self.stream.feed(data)
            display_list = [line for line in self.screen.display if line.strip()]
            self.screen.reset()
        except Exception as _ex:
            print ('tty parser error: %s' % str(_ex))
        return display_list

    def tty_input_parser(self, data):
        display_list = self.tty_parser(data)
        if display_list:
            screen_info = display_list[-1]
        else:
            screen_info = ''
        return self.ps1_pattern.sub('', screen_info)

    def tty_output_parser(self, data):
        display_list = self.tty_parser(data)
        return '\n'.join(display_list)


class TTYParser(Basic):
    name = 'tty parser'
    version = '0.1'

    def __init__(self):
        super(TTYParser, self).__init__()
        self.io_parser = SSHIOParser()

    def run(self):
        pre_day = (date.today() + timedelta(days=-1)).strftime('%Y%m%d')
        log_path = '/tmp/relay/%s' % pre_day
        out = subprocess.check_output(['ls', log_path])
        log_file_list = out.decode('utf-8', errors='ignore').split('\n')
        for log_file in log_file_list:
            if log_file == '':
                continue
            self.parser(log_path, log_file)
        print ('** log directory: %s all log file handle finshed.' % pre_day)

    def parser(self, log_path, log_file):
        log_info = []
        log_file_path = '%s/%s' % (log_path, log_file)
        with open(log_file_path) as fp:
            for line in fp:
                if line.find('-sh-4.1$') != -1:
                    result = self.io_parser.tty_input_parser(line)
                else:
                    result = self.io_parser.tty_output_parser(line)
                log_info.append(result)
        self.write_back(log_path, log_file, log_info)
        try:
            os.remove(log_file_path)
        except:
            pass

    def write_back(self, log_path, log_file, log_info):
        new_log_file = '%s/new_%s' % (log_path, log_file)
        with open(new_log_file, 'a') as fp:
            for data in log_info:
                fp.write(data)
                fp.write('\n')
                fp.flush()
        print ('** log file: %s handle finished.' % log_file)
