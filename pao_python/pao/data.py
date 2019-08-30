# -*- coding: utf-8 -*-
import pymongo
import datetime
import time
import json
import pandas as df
from flask import current_app
from flask_jsonrpc import Error
from flask_jsonrpc._compat import text_type
import calendar
import pymysql
from sqlalchemy import create_engine


class JsonRpc2Error(Error):
    ''' JsonRpc 2.0 异常

    Attribute:
        code    {number}    错误码
        message {string}    错误信息
        data    {any}       附加数据
    '''

    def __init__(self, code, message, data=None):
        '''构造函数'''
        Error.__init__(self, message, code)

    @property
    def json_rpc_format(self):
        """Return the Exception data in a format for JSON-RPC
        """

        error = {
            'name': text_type(self.__class__.__name__),
            'code': self.code,
            'message': self.message,
            'data': self.data
        }

        if current_app.config['DEBUG']:
            import sys
            import traceback
            error['stack'] = traceback.format_exc()
            error['executable'] = sys.executable

        return error


class UnauthorizedError(JsonRpc2Error):
    '''未授权异常'''
    code = -35005
    message = '未授权'

    def __init__(self, data=None):
        '''构造函数'''
        if data is not None:
            self.data = data

class PermisssionFrobitError(JsonRpc2Error):
    '''权限禁止异常'''
    code = -35006
    message = '权限禁止异常'

    def __init__(self, data=None):
        '''构造函数'''
        if data is not None:
            self.data = data

class DataProcess:
    '''数据处理'''

    def __init__(self, db_addr, db_port, db_name,db_pwd=None,user=None):
        self.db_addr = db_addr
        self.db_port = db_port
        self.db_name = db_name
        self.db_pwd = db_pwd
        self.user = user
class ErrorCode:
    '''平台错误码   
        
    '''

def string_to_date(date):
    '''将日期字符串转换为日期
    '''
    return datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")


def string_to_date_only(date):
    return datetime.datetime.strptime(date, "%Y-%m-%d")
# 创建时间


def get_date(format="%Y-%m-%d"):
    return time.strftime(format, time.localtime())

# 把时间戳转成字符串形式
# def timestamp_toString(stamp):
#     return time.strftime("%Y-%m-%d", time.localtime(stamp))


def date_to_string(date):
    # 将日期转换成字符串
    return date.strftime("%Y-%m-%d %H:%M:%S")


def data_to_string_date(date):
    return date.strftime("%Y-%m-%d")
# 获取当前时间


def get_cur_time():
    return datetime.datetime.now()


def process_db(db_addr, db_port, db_name, process_func):
    '''打开Collection并处理
    '''
    client = pymongo.MongoClient(db_addr, db_port)
    db = client[db_name]
    process_func(db)
    client.close()


def dataframe_to_list(data_df):
    '''
    dataframe转list
    '''
    per_json = data_df.to_json(orient='index', force_ascii=False)
    per_dict = json.loads(per_json)
    per_list = list(per_dict.values())
    return per_list

def getMonthFirstDayAndLastDay(year=None, month=None):
    """
    :param year: 年份，默认是本年，可传int或str类型
    :param month: 月份，默认是本月，可传int或str类型
    :return: firstDay: 当月的第一天，datetime.date类型
            lastDay: 当月的最后一天，datetime.date类型
    """
    if year:
        year = int(year)
    else:
        year = datetime.date.today().year

    if month:
        month = int(month)
    else:
        month = datetime.date.today().month

    # 获取当月第一天的星期和当月的总天数
    firstDayWeekDay, monthRange = calendar.monthrange(year, month)

    # 获取当月的第一天
    firstDay = datetime.date(year=year, month=month, day=1).strftime('%Y-%m-%d')
    lastDay = datetime.date(year=year, month=month, day=monthRange).strftime('%Y-%m-%d')

    return {'first':firstDay, 'last':lastDay}

def process_db_mysql(db_addr, db_port, db_name,db_pwd,user,process_func):
    ''' 连接mysql数据库
        db_addr 数据库ip
        db_port 数据库端口
        db_name 数据库名称
        user    用户名
        db_pwd  密码
        process_func 回调方法
    '''
    conn = pymysql.connect(host=db_addr,port=db_port,database=db_name, password=db_pwd,user=user)
    try:
        print(conn,'数据库')
        process_func(conn)
        conn.commit()
    except:
        conn.rollback()
    conn.close()

def get_mysql_data(db,sql):
    ''' 查询mysql
        db  数据库对象
        sql 查询语句
    '''
    data=df.read_sql(sql=sql,con=db)
    res = dataframe_to_list(data)
    return res

def get_mysql_con(db_addr, db_port, db_name, db_pwd, user):
    return pymysql.connect(host=db_addr, port=db_port, database=db_name, password=db_pwd, user=user)
    

def get_table_data(self,db_name,filder,table_name=None):
    res = []
    other = ''
    sql = 'show tables from %s' % db_name
    sql_all = 'select * from %s' 
    db = get_mysql_con(self.db_addr, self.db_port, db_name, self.db_pwd, self.user)
    table_names = dataframe_to_list(df.read_sql(sql=sql, con=db)[filder])
    for x in table_names:
        if not x in ['东明', '幸福院房间', '房间信息', '楼宇信息']:
            sql_new = sql_all % x
            data = df.read_sql(sql=sql_new, con=db)
            if table_name and x == table_name:
                other = data
            elif len(data):
                res.append({x: dataframe_to_list(data)})
    return other if table_name else res

def get_engine(user_pwd,ip_port,db_name):
    return create_engine("mysql+pymysql://"+user_pwd+"@"+ip_port+"/"+db_name+"?charset=utf8")