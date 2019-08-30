'''
版权: Copyright (c) 2019 red

文件: idmis_app.py
创建日期: Mondy March 18th 2019
作者: linjinkun
说明:
1、工业互联网标识管理系统
'''
from pao_python.pao.app import JsonRpcApp
from pao_python.pao import log
import register.big_screens_register as big_screens
import register.data_format_register as data_format_register

# 工业互联网标识管理系统APP类


class WelfareHome(JsonRpcApp):

    def __init__(self, app_name, address, port, web_origins, db_addr, db_port, db_name, db_pwd,user):
        JsonRpcApp.__init__(self, app_name, address, port, web_origins)
        self.db_addr = db_addr
        self.db_port = db_port
        self.db_name = db_name
        self.db_pwd = db_pwd
        self.db_user = user

    def on_regsiter_services(self, jsonrpc, session):
        # 标识管理系统服务注册
        log('', '标识管理系统运行成功')
        #大屏服务注册
        # big_screens.register(jsonrpc, self.db_addr, self.db_port, self.db_name, self.db_pwd, self.db_user)
        data_format_register.register(jsonrpc, self.db_addr, self.db_port, self.db_name, self.db_pwd, self.db_user)

       