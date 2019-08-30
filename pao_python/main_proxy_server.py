'''
版权: Copyright (c) 2019 red

文件: main_proxy_server.py
创建日期: Sunday February 24th 2019
作者: pao
说明:
1、代理服务主程序
'''
from pao.proxy_app import ProxyServerApp
######################### 以下为配置 #########################
origin_servers = {
    'http_server': {
        'id': 'http_server',
        'password': '123456',
        'name': 'HTTP代理服务器',
        'server_port': 8080
    },
    'http_server1': {
        'id': 'http_server1',
        'password': '123456',
        'name': 'HTTP代理服务器',
        'server_port': 8081
    }
}

server_ports = [
    ('外网网站', 8080),
    ('外网网站', 8081)
]

host = 'localhost'
port = 7990

######################### 以下为服务启动 #########################
server_app = ProxyServerApp(host, port, server_ports, origin_servers)
server_app.run()
