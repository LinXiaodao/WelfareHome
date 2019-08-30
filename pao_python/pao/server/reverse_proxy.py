'''
版权: Copyright (c) 2019 red

文件: distribute_proxy.py
创建日期: Tuesday January 22nd 2019
作者: pao
说明:
1、反向代理
'''
from .socket import SocketServer
from ..binary_buffer import BinaryBuffer
from . import BaseServer
import socket
import threading
from pao_python.pao import log

COMMAND_CONNECT = 0
COMMAND_CHANNEL_2to3 = 1
COMMAND_CHANNEL_3to2 = 2

class DistributeListenServer(SocketServer):
    '''分布式监听服务器
    '''
    # 代理服务器列表
    proxy_servers = {}
    # 代理命令通道主线程
    proxy_command_channel_threads = {}

    def __init__(self, listen_host, listen_port, server_port_defs, origin_server_finder):
        '''构造函数

        Arguments:
            listen_host {string} -- 监听服务器地址
            listen_port {int} -- 监听服务器端口 
            server_port_defs {[(name, port)]} -- 代理服务器端口定义
            origin_server_finder {func(server_id, server_pass): OriginServer} -- 源服务器检索器
        '''
        SocketServer.__init__(self, listen_host, listen_port)

        self.__server_port_defs = server_port_defs
        self.__origin_server_finder = origin_server_finder

    def __log(self, message):
        log('DistributeListenServer', message)

    def start(self):
        '''启动
        '''
        for (name, port) in self.__server_port_defs:
            # 创建代理服务器并启动
            proxy_server = ReverseProxyServer(
                self.host, port, name)
            self.proxy_servers[port] = proxy_server
            proxy_server.start()
        SocketServer.start(self)

    def on_accepted(self, connect, address):
        '''事件: 接收到连接

        Arguments:
            connect {socket} -- 客户端Socket
            address {string} -- 客户端地址

        Raises:
            RuntimeError -- 1.检索到不到指定服务器或密码错误
                            2.指定的服务端口未定义
        '''
        self.__log('ACPT(3->2, Address=%s) 接受到来自源服务器的连接' % address)
        proxy_command_channel_thread = threading.Thread(
            target=self.__receive_command, args=(connect,))
        proxy_command_channel_thread.start()
        self.proxy_command_channel_threads[address] = proxy_command_channel_thread

    def __receive_command(self, connect):
        data = connect.recvall()
        buffer = BinaryBuffer(data)

        # 读取命令类型
        command = buffer.read_uint8()
        if command == COMMAND_CONNECT:
            # 收到来自源服务器的连接请求
            # 读取代理服务器ID
            origin_server_id = buffer.read_string()
            # 读取代理服务器密码
            origin_server_pass = buffer.read_string()

            self.__log(
                'RCV(3->2) CONNECT(OriginServerID=%s) 收到来自源服务器的连接请求' % origin_server_id)

            # 从服务器检索器检索代理服务器定义
            origin_server = self.__origin_server_finder(
                origin_server_id, origin_server_pass)
            if not origin_server.server_port:
                raise RuntimeError('检索不到指定源服务器定义:%s，或者密码错误' %
                                    (origin_server_id))

            # 连接指定代理服务器
            proxy_server = self.proxy_servers[origin_server.server_port]
            if not proxy_server:
                raise RuntimeError('指定的服务端口未定义:%s' %
                                    origin_server.server_port)

            origin_server.command_socket = connect
            proxy_server.add_origin_server(origin_server)
        elif command == COMMAND_CHANNEL_3to2:
            # 来自源服务器的建立连接通道的请求
            server_port = buffer.read_uint32()
            # 读取代理服务器ID
            origin_server_id = buffer.read_string()
            # 读取外部地址
            outer_address = buffer.read_string()

            self.__log(
                'RCV(3->2) CHANNEL(OriginServerID=%s, ServerPort=%d, OuterAddress=%s) 收到来自源服务器的建立连接通道的请求' % (origin_server_id, server_port, outer_address))

            # 在代理服务器建立新的代理通道
            proxy_server = self.proxy_servers[server_port]
            if not proxy_server:
                raise RuntimeError('指定的服务端口未定义:%s' %
                                    server_port)

            proxy_server.create_proxy_channel(
                connect, origin_server_id, outer_address)
        else:
            raise RuntimeError('收到了来自代理服务器的未知命令: %s' % command)

class ReverseProxyServer(SocketServer):
    '''反向代理服务器
    '''
    # 源服务器列表 {server_port: OriginServer}
    origin_servers = {}
    # 代理连接列表
    proxy_connections = {}

    def __init__(self, host, port, name):
        '''构造函数

        Arguments:
            host {string} -- 代理服务器地址
            port {int} -- 代理服务器端口
            name {string} -- 代理服务器名称
        '''

        SocketServer.__init__(self, host, port)
        self.__name = name

    def __log(self, message):
        log('ReverseProxyServer(PORT=%d)' % self.port, message)

    def add_origin_server(self, origin_server):
        '''添加源服务器

        Arguments:
            origin_server {OriginServer} -- 源服务器
        '''

        self.origin_servers[origin_server.id] = origin_server

    def create_proxy_channel(self, connect, origin_server_id, outer_address):
        '''建立代理连接

        Arguments:
            connect {socket} -- 来自内网的通道连接
            origin_server_id {string} -- 源服务ID
            outer_address {string} -- 外部地址
        '''
        origin_server = self.origin_servers[origin_server_id]
        if not origin_server:
            raise RuntimeError('指定服务器:%s已经不存在了' % origin_server_id)

        proxy_connection = self.proxy_connections[outer_address]
        if not proxy_connection:
            raise RuntimeError('来自外网:%s的连接已经不存在了' % outer_address)
        proxy_connection.inner_connect = connect

        # 将内外网连接打通
        proxy_connection.outer_to_inner_thread = threading.Thread(target=self.__outer_to_inner, args=(
            outer_address, proxy_connection.outer_connect, proxy_connection.inner_connect,))
        proxy_connection.outer_to_inner_thread.start()
        proxy_connection.inner_to_outer_thread = threading.Thread(target=self.__inner_to_outer, args=(
            outer_address, proxy_connection.outer_connect, proxy_connection.inner_connect,))
        proxy_connection.inner_to_outer_thread.start()

    def __outer_to_inner(self, outer_address, outer_connect, inner_connect):
        '''将数据从外网转发到内网

        Arguments:
            outer_address {string} -- 外网地址
            outer_connect {socket} -- 外网连接
            inner_connect {socket} -- 内网连接
        '''
        while True:
            try:
                data = outer_connect.recvall()
                if data:
                    self.__log('RCV(0->1) DATA(OuterAddress=%s, Size=%d)' %
                               (outer_address, len(data)))
                    inner_connect.sendall(data)
                    self.__log('SND(2->3) DATA(OuterAddress=%s, Size=%d)' %
                               (outer_address, len(data)))
            except ConnectionError as err:
                self.__log('ERR(0->3) (OuterAddress=%s, Error=%s)' % (outer_address, err))
                # 如果数据中断应当关闭连接
                if self.proxy_connections.get(outer_address):
                    del self.proxy_connections[outer_address]
                break

    def __inner_to_outer(self, outer_address, outer_connect, inner_connect):
        '''将数据从内网转发到外网

        Arguments:
            outer_address {string} -- 外网地址
            outer_connect {socket} -- 外网连接
            inner_connect {socket} -- 内网连接
        '''
        while True:
            try:
                data = inner_connect.recvall()
                if data:
                    self.__log('RCV(3->2) DATA(OuterAddress=%s, Size=%d)' %
                               (outer_address, len(data)))
                    outer_connect.sendall(data)
                    self.__log('SND(1->0) DATA(OuterAddress=%s, Size=%d)' %
                               (outer_address, len(data)))
            except ConnectionError as err:
                self.__log('ERR(3->0) (OuterAddress=%s, Error=%s)' % (outer_address, err))
                # 如果数据中断应当关闭连接
                if self.proxy_connections.get(outer_address):
                    del self.proxy_connections[outer_address]
                break

    def on_accepted(self, connect, address):
        '''事件: 接收到连接

        Arguments:
            connect {socket} -- 客户端Socket
            address {string} -- 客户端地址

        Raises:
            RuntimeError -- 
        '''
        proxy_connect = ProxyConnection(address)
        proxy_connect.outer_connect = connect
        self.proxy_connections[address] = proxy_connect

        self.__log('ACPT(0->1, Address=%s) 接受到来自外网的连接' % address)
        # 连接源服务器
        for origin_server_id in self.origin_servers.keys():
            origin_server = self.origin_servers[origin_server_id]
            # 匹配服务端口然后匹配分发规则，连接源服务器
            if self.port == origin_server.server_port and origin_server.distribute_rule (address, connect):
                buffer = BinaryBuffer()
                # 建立通道的命令
                buffer.write_uint8(COMMAND_CHANNEL_2to3)
                # 服务端口
                buffer.write_uint32(self.port)
                # 外部地址
                buffer.write_string(address)
                origin_server.command_socket.sendall(buffer.data)
                self.__log(
                    'SND(2->3) CHANNEL(OuterAddress=%s, ServerPort=%d)' % (address, self.port))


class ProxyConnection:
    '''代理连接
    '''
    # 外部地址
    outer_address = None
    # 外部连接
    outer_connect = None
    # 内部连接
    inner_connect = None
    # 外网到内网的代理线程
    outer_to_inner_thread = None
    # 内网到外网的代理线程
    inner_to_outer_thread = None

    def __init__(self, outer_address):
        self.outer_address = outer_address


def default_distribute_rule(self, address, conn):
    '''默认分发规则

    Arguments:
        address {string} -- 地址
        conn {socket} -- 连接

    Returns:
        bool -- 是否负责分发规则
    '''

    return True


class OriginServer:
    '''源服务器
    '''
    # {func(address, conn): bool} 分发规则函数
    distribute_rule = default_distribute_rule
    # 命令Socket
    command_socket = None
    # {string} 源服务器ID
    id = ''
    # {string} 源服务器名称
    name = ''
    # 服务端口
    server_port = 0


class OriginConnection:
    '''源服务器连接
    '''
    # 外部地址
    outer_address = None
    # 代理了连接
    proxy_connect = None
    # 源服务器连接
    origin_connect = None
    # 代理到源的代理线程
    proxy_to_origin_thread = None
    # 源到代理的的代理线程
    origin_to_proxy_thread = None

    def __init__(self, outer_address, server_port):
        self.outer_address = outer_address
        self.server_port = server_port


class ProxyClient(BaseServer):
    '''代理客户端
    '''

    # 源连接列表
    origin_connections = {}
    # 代理主连接
    proxy_main_connect = None
    # 代理线程
    proxy_main_thread = None
    # 源线程
    origin_thread = None

    def __init__(self, proxy_server_host, proxy_server_port, origin_server_id, origin_server_pass, origin_server_host, origin_server_port):
        self.proxy_server_host = proxy_server_host
        self.proxy_server_port = proxy_server_port
        self.origin_server_id = origin_server_id
        self.origin_server_pass = origin_server_pass
        self.origin_server_host = origin_server_host
        self.origin_server_port = origin_server_port

    def __log(self, message):
        log('ProxyClient', message)

    def start(self):
        '''启动
        '''

        # 首先连接代理服务器
        self.proxy_main_connect = socket.socket()
        self.proxy_main_connect.connect(
            (self.proxy_server_host, self.proxy_server_port))
        self.__log('CNNCT(3->2, ProxyServerHost=%s, ProxyServerPort=%d)'%(self.proxy_server_host, self.proxy_server_port))
        buffer = BinaryBuffer()
        buffer.write_uint8(COMMAND_CONNECT)
        buffer.write_string(self.origin_server_id)
        buffer.write_string(self.origin_server_pass)
        self.proxy_main_connect.sendall(buffer.data)
        self.__log('SND(3->2) CONNECT(OriginServerID=%s)'%(self.origin_server_id))

        self.proxy_main_thread = threading.Thread(target=self.__proxy_main)
        self.proxy_main_thread.start()

    def __proxy_main(self):
        while True:
            # 等待代理服务器返回服务端口和外部地址
            data = self.proxy_main_connect.recvall()
            buffer = BinaryBuffer(data)
            command = buffer.read_uint8()
            if command != COMMAND_CHANNEL_2to3:
                raise RuntimeError('收到来自代理服务器的错误命令:%s' % command)
            server_port = buffer.read_uint32()
            outer_address = buffer.read_string()
            self.__log('RCV(2->3) CHANNEL(OuterAddress=%s, ServerPort=%s)' %
                       (outer_address, server_port))

            origin_connection = OriginConnection(outer_address, server_port)
            # 连接源服务器
            origin_connection.origin_connect = socket.create_connection((self.origin_server_host, self.origin_server_port))
            self.__log('CNNCT(5, OutAddress=%s, From=%s, To=%s) 连接源服务器' % (outer_address, origin_connection.origin_connect.getsockname(), origin_connection.origin_connect.getpeername()))
            origin_connection.origin_connect.setblocking(True)
            # 连接代理服务器并发出反向通道请求
            origin_connection.proxy_connect = socket.create_connection((self.proxy_server_host, self.proxy_server_port))
            self.__log('CNNCT(2, OutAddress=%s, From=%s, To=%s) 连接代理服务器' % (outer_address, origin_connection.proxy_connect.getsockname(), origin_connection.proxy_connect.getpeername()))

            buffer = BinaryBuffer()
            buffer.write_uint8(COMMAND_CHANNEL_3to2)
            buffer.write_uint32(server_port)
            buffer.write_string(self.origin_server_id)
            buffer.write_string(outer_address)
            origin_connection.proxy_connect.sendall(buffer.data)

            self.__log('SND(3->2) CHANNEL(OuterAddress=%s, ProxyPort=%s, OriginServerID=%s) 向代理服务器发送代理连接请求' %
                       (outer_address, origin_connection.proxy_connect.getsockname(), self.origin_server_id))

            origin_connection.origin_to_proxy_thread = threading.Thread(
                target=self.__origin_to_proxy, args=(outer_address, origin_connection.origin_connect, origin_connection.proxy_connect,))
            origin_connection.origin_to_proxy_thread.start()

            origin_connection.proxy_to_origin_thread = threading.Thread(
                target=self.__proxy_to_origin, args=(outer_address, origin_connection.origin_connect, origin_connection.proxy_connect,))
            origin_connection.proxy_to_origin_thread.start()

            self.origin_connections[outer_address] = origin_connection

    def __origin_to_proxy(self, outer_address, origin_connect, proxy_connect):
        '''将数据从源服务器转发到代理服务器

        Arguments:
            outer_address {string} -- 外网地址
            origin_connect {socket} -- 源连接
            proxy_connect {socket} -- 代理连接
        '''
        while True:
            try:
                data = origin_connect.recvall()
                if data:
                    self.__log('RCV(5->4) DATA(OuterAddress=%s, OriginPort=%s, Size=%d)' %
                               (outer_address, origin_connect.getsockname(), len(data)))
                    proxy_connect.sendall(data)
                    self.__log('SND(3->2) DATA(OuterAddress=%s, ProxyPort=%s, Size=%d)' %
                               (outer_address, proxy_connect.getsockname(), len(data)))
            except ConnectionError as err:
                self.__log('ERR(5->2) (OuterAddress=%s, Error=%s)' % (outer_address, err))
                # 如果数据中断应当关闭连接
                if self.origin_connections.get(outer_address):
                    del self.origin_connections[outer_address]
                break

    def __proxy_to_origin(self, outer_address, origin_connect, proxy_connect):
        '''将数据从代理服务器转发到源服务器

        Arguments:
            outer_address {string} -- 外网地址
            origin_connect {socket} -- 源连接
            proxy_connect {socket} -- 代理连接
        '''
        while True:
            try:
                data = proxy_connect.recvall()
                if data:
                    self.__log('RCV(2->3) DATA(OuterAddress=%s, ProxyPort=%s, Size=%d)' %
                               (outer_address, proxy_connect.getsockname(), len(data)))
                    origin_connect.sendall(data)
                    self.__log('SND(4->5) DATA(OuterAddress=%s, OriginPort=%s Size=%d)' %
                               (outer_address, origin_connect.getsockname(), len(data)))
            except ConnectionError as err:
                self.__log('ERR(2->5) (OuterAddress=%s, Error=%s)' % (outer_address, err))
                # 如果数据中断应当关闭连接
                if self.origin_connections.get(outer_address):
                    del self.origin_connections[outer_address]
                break
