# -*- coding: utf-8 -*-

'''
版权: Copyright (c) 2019 red

文件: server.py
创建日期: Thursday January 17th 2019
作者: pao
说明:
1、服务相关程序
'''
from .. import BaseObject


class BaseServer(BaseObject):
    '''服务器基类
    '''

    def start(self):
        '''服务启动
        '''

        pass

    def stop(self):
        '''服务停止
        '''

        pass


class BaseService(BaseObject):
    '''服务基类
    '''
