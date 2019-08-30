'''
版权: Copyright (c) 2019 red

文件: socket.py
创建日期: Tuesday January 22nd 2019
作者: pao
说明:
1、Socket服务器
'''

import socket
import threading
from .. import log
from . import BaseServer

BUFFER_SIZE = 1024


def recv_data(self):
    return self.recv(BUFFER_SIZE)


# 为socket增加recvall方法
socket.socket.recvall = recv_data


class SocketServer(BaseServer):
    '''Socket服务器，实现了TCP服务器功能
    '''
    connections = []
    conn_threads = []

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))

    def __log(self, message):
        log('SocketServer(PORT=%d)' % (self.port), message)

    def start(self):
        self.stopped = False
        self.__log('开始监听, 地址:%s, 端口:%d' %
                   (self.host, self.port))
        self.socket.listen(20)
        self.accept_thread = threading.Thread(target=self.__accept_socket)
        self.accept_thread.start()

    def stop(self):
        self.stopped = True
        for (connect, address) in self.connections:
            self.__log('连接关闭(Address=%s)' % (address))
            connect.close()

        self.__log('监听端口关闭(Host=%s, Port=%d)' %
                   (self.host, self.port))
        self.socket.close()

        # 停止所有的连接线程
        for conn_thread in self.conn_threads:
            del conn_thread
        self.conn_threads.clear()

        del self.socket

    def __accept_socket(self):
        while not self.stopped:
            connect, address = self.socket.accept()
            address = '%s:%d' % address
            self.__log('连接建立(From=%s, To=%s)' %
                       (connect.getpeername(), connect.getsockname()))
            self.connections.append((connect, address))
            conn_thread = threading.Thread(
                target=self.on_accepted, args=(connect, address))
            conn_thread.start()
            self.conn_threads.append(conn_thread)

    def on_accepted(self, connect, address):
        self.__log('on_accepted')
