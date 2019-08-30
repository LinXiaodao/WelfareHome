'''
版权: Copyright (c) 2019 red

文件: proxy_app.py
创建日期: Sunday February 24th 2019
作者: pao
说明:
1、反向代理App
'''
from .app import BaseApp
from .server.reverse_proxy import DistributeListenServer, OriginServer, ProxyClient


class ProxyServerApp(BaseApp):
    '''代理服务App
    '''

    def __init__(self, host, port, server_ports, origin_servers):
        self.host = host
        self.port = port
        self.server_ports = server_ports
        self.origin_servers = origin_servers

    def origin_finder(self, origin_server_id, origin_server_pass):
        origin_server_config = self.origin_servers[origin_server_id]
        if not origin_server_config or origin_server_config["password"] != origin_server_pass:
            return None

        origin_server = OriginServer()
        origin_server.id = origin_server_config["id"]
        origin_server.name = origin_server_config["name"]
        origin_server.server_port = origin_server_config["server_port"]
        return origin_server

    def run(self):
        listen_server = DistributeListenServer(
            listen_host=self.host,
            listen_port=self.port,
            server_port_defs=self.server_ports,
            origin_server_finder=self.origin_finder)

        listen_server.start()


class ProxyClientApp(BaseApp):
    def __init__(self, server_host, server_port, origin_servers):
        self.server_host = server_host
        self.server_port = server_port
        self.origin_servers = origin_servers

    def run(self):
        for origin_server in self.origin_servers:
            proxy_client = ProxyClient(
                proxy_server_host=self.server_host,
                proxy_server_port=self.server_port,
                origin_server_id=origin_server["id"],
                origin_server_pass=origin_server["password"],
                origin_server_host=origin_server["host"],
                origin_server_port=origin_server["port"])
            proxy_client.start()
