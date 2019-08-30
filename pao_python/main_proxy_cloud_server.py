'''
版权: Copyright (c) 2019 red

文件: main_proxy_server.py
创建日期: Sunday February 24th 2019
作者: pao
说明:
1、云端代理服务主程序
'''
from pao.proxy_app import ProxyServerApp
######################### 以下为配置 #########################
origin_servers = {
    'http_server': {
        'id': 'http_server',
        'password': '123456',
        'name': 'HTTP代理服务器',
        'server_port': 3001
    },
    'device_server': {
        'id': 'device_server',
        'password': '123456',
        'name': '设备服务器',
        'server_port': 3000
    }
}

server_ports = [
    ('HTTP服务器', 3001),
    ('设备服务器', 3000),
]

host = '10.10.0.135'
port = 4000

######################### 以下为服务启动 #########################

serverApp = ProxyServerApp(host, port, server_ports, origin_servers)
serverApp.run()
