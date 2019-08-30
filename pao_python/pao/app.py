'''
版权: Copyright (c) 2018 red

文件: base_app.py
创建日期: Friday December 14th 2018
作者: pao
说明:
1、基础应用
'''
from flask import Flask, session
from flask_cors import CORS
from pao_python.pao import log
from flask_jsonrpc import JSONRPC
from pao_python.pao.server.reverse_proxy import ProxyClient
import os
from datetime import timedelta


class BaseApp:
    '''应用基类
    '''

    def __init__(self, app_name):
        # 构造函数
        self.app_name = app_name

    def run(self):
        pass


# Flash应用服务


class FlaskApp(BaseApp):
    proxy_server_config = '代理服务配置'

    # 构造函数
    def __init__(self, app_name, address, port, web_origins):
        BaseApp.__init__(self, app_name)
        self.address = address
        self.port = port
        self.web_origins = web_origins

    def run(self):
        # 启动
        BaseApp.run(self)

        # 定义flask框架
        self.app = Flask(self.app_name)

        # 解决跨域
        CORS(self.app, supports_credentials=True, origins=self.web_origins)

        # 设置一个随机24位字符串为加密盐。每次重启服务器所有的session都会失效
        self.app.config['SECRET_KEY'] = os.urandom(24)
        self.app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(
            days=7)  # 设置session 7天有效
        self.on_app_start(self.app)

        # 连接代理服务器
        if type(self.proxy_server_config).__name__ == 'tuple':
            (proxy_server_host,
             proxy_server_port,
             origin_server_id,
             origin_server_pass, ) = self.proxy_server_config
            log('Flask', '连接代理服务器(Host=%s, Port=%d, OriginServerID=%s)' % (proxy_server_host,
                                                                           proxy_server_port,
                                                                           origin_server_id))
            proxy_client = ProxyClient(
                proxy_server_host, proxy_server_port, origin_server_id, origin_server_pass, self.address, self.port)
            proxy_client.start()

        # 启动Flash框架
        log('Flask', 'Flash服务启动: %s:%d' % (self.address, self.port))
        self.app.run(host=self.address, port=self.port,
                     debug=True)

    def on_app_start(self, app):
        # 启动事件
        pass


# json rpc服务


class JsonRpcApp(FlaskApp):
    # Json RPC服务器

    def on_app_start(self, app):

        # 定义jsonRpc框架
        self.jsonrpc = JSONRPC(
            app, '/remoteCall', enable_web_browsable_api=True)
        self.on_regsiter_services(self.jsonrpc, session)
        self.on_regsiter_upload(self.app,self.jsonrpc)

    def on_regsiter_upload(self, app,jsonrpc):
        # 注册文件上传
        pass

    def on_regsiter_services(self, jsonrpc, session):
        # 注册服务
        pass
