'''
版权: Copyright (c) 2019 red

文件: main_proxy_client.py
创建日期: Sunday February 24th 2019
作者: pao
说明:
1、代理客户端主程序
'''
from pao.proxy_app import ProxyClientApp
######################### 以下为配置 #########################
server_host = '14.215.45.162'
server_port = 4000

origin_servers = [
    {
        'id': 'http_server',
        'password': '123456',
        'host': 'localhost',
        'port': 3001
    },
    {
        'id': 'device_server',
        'password': '123456',
        'host': 'localhost',
        'port': 3000
    }
]
######################### 以下为程序启动 #########################
client_app = ProxyClientApp(server_host, server_port, origin_servers)
client_app.run()
