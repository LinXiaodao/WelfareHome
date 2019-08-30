# @Author: linjinkun
# @Date: 2019-05-29 15:34:09
# @Last Modified by:   linjinkun
# @Last Modified time: 2019-05-29 15:34:09
# @description   常用的公共方法
import json
import uuid
import re
import pandas as pd
from pao_python.pao.data import dataframe_to_list, process_db, get_cur_time, get_date, DataProcess
from sqlalchemy import create_engine



def inset_collection(db, data, key):
    ''' 插入数据
        args:
            db  集合
            data    数据
        return:
            是否成功    True/False
    '''
    # for x in data:
    #     x[key] = str(uuid.uuid1())
    res = db.insert_many(data)
    return len(res.inserted_ids) == len(data)


def update_collection(db, data, key):
    ''' 编辑数据
        args:
            db  集合
            data    数据
        return:
            是否成功    True/False
    '''
    res = db.update_one({key: data[key]}, {'$set': data})
    return res.modified_count == 1


def delete_collection(db, IDS, key='id'):
    ''' 删除数据
        db  集合
        IDS 要删除的id集合
    '''
    res = db.delete_many({key: {'$in': IDS}})
    return res.deleted_count == len(IDS)


def paramter_none(condition, blurry=None):
    ''' 删除空值字段
        Args:
            conditon    查询条件
            blurry      需要处理成模糊搜索的key
        return:
            conditon    处理完毕的查询条件
    '''
    for key in list(condition.keys()):
        if not condition.get(key):
            del condition[key]
        else:
            if blurry and key in blurry:
                re_data = re.compile(condition[key])
                condition[key] = re_data
            if isinstance(condition[key], list):
                condition[key] = {'$in': condition[key]}

    return condition


def find_collection(db, condition, isList=True, pageNo=1, pageSize=10):
    ''' 查询数据
        Args:
            db  查询表对象
            condition   查询条件
            isList      是否转化成list-True  False-DataFrame
        return:
            res     list/DataFrame数据对象
    '''
    res = []
    data_list = list(db.find(condition).skip((pageNo-1)*pageSize+1).limit(pageSize)[:])
    if len(data_list):
        pd_data = pd.DataFrame(data_list).drop(['_id'], axis=1)
        res = dataframe_to_list(pd_data) if isList else pd_data
    return res


def insert_data(self, col_name, condition, key='id', hasTime=None):
    ''' 新建/编辑数据
        Args:
            self    当前对象，提供数据库地址，端口，数据库名称
            col_name    集合名称
            condition   新建/编辑信息
            key     用于判断是否新建的key
        return:
            { 'msg': '新建成功/失败' }
    '''
    msg = ''

    def process_func(db):
        nonlocal msg
        new_condition = paramter_none(condition)
        if key not in new_condition.keys():
            if hasTime:
                new_condition['create_time'] = get_cur_time()
                new_condition['date'] = get_date(hasTime)
            insert_res = inset_collection(db[col_name], [new_condition], key)
            msg = '新增成功' if insert_res else '新增失败'
        else:
            update_res = update_collection(db[col_name], new_condition, key)
            msg = '编辑成功' if update_res else '编辑失败'
    process_db(self.db_addr, self.db_port, self.db_name, process_func)
    return {'msg': msg}

def insert_many_data(self, col_name, condition, key='id', hasTime=None):
    ''' 新建/编辑数据
        Args:
            self    当前对象，提供数据库地址，端口，数据库名称
            col_name    集合名称
            condition   新建/编辑信息
            key     用于判断是否新建的key
        return:
            { 'msg': '新建成功/失败' }
    '''
    msg = ''

    def process_func(db):
        nonlocal msg
        insert_res = inset_collection(db[col_name], condition, key)
        # new_condition = paramter_none(condition)
        # if key not in new_condition.keys():
        #     if hasTime:
        #         new_condition['create_time'] = get_cur_time()
        #         new_condition['date'] = get_date(hasTime)
        #     insert_res = inset_collection(db[col_name], [new_condition], key)
        #     msg = '新增成功' if insert_res else '新增失败'
        # else:
        #     update_res = update_collection(db[col_name], new_condition, key)
        #     msg = '编辑成功' if update_res else '编辑失败'
    process_db(self.db_addr, self.db_port, self.db_name, process_func)
    return {'msg': msg}

def get_data(self, col_name, condition, isList=True, pageNo=1, pageSize=10):
    ''' 查询数据库
        Args:
            self    当前对象，提供数据库地址，端口，数据库名称
            col_name    集合名称
            condition   查询条件
            isList      是否转化成list
        return:
            res     list/dataFrame数据对象
    '''
    res = {}

    def process_func(db):
        nonlocal res
        res['result'] = find_collection(db[col_name], condition, isList, pageNo, pageSize)
        res['total'] = get_data_count(self, col_name, condition)
    process_db(self.db_addr, self.db_port, self.db_name, process_func)
    return res


def delete_data(self, col_name, ids, key='id'):
    ''' 删除数据
        Args:
            self    当前对象，提供数据库地址，端口，数据库名称
            col_name    集合名称
            ids   删除的数据ID
        return:
            { 'msg': '删除成功/失败' }
    '''
    msg = ''

    def process_func(db):
        nonlocal msg
        delete_res = delete_collection(db[col_name], ids, key)
        msg = '删除成功' if delete_res else '删除失败'
    process_db(self.db_addr, self.db_port, self.db_name, process_func)
    return {'msg': msg}


def get_data_count(self, col_name, condition):
    ''' 统计数据库记录'''
    count = 0

    def process_func(db):
        nonlocal count
        count = db[col_name].find(condition).count()
    process_db(self.db_addr, self.db_port, self.db_name, process_func)
    return count


class ServiceProcess(DataProcess):
    ''' 服务实现基类，用于快速构建简单的增删查改'''

    def query(self, col_name, condition, isList=True, pageNo=1, pageSize=10):
        ''' 查询
            Args:
                self    当前对象，提供数据库地址，端口，数据库名称
                col_name    集合名称
                condition   查询条件
                isList      是否转化成list
            return:
                res     list/dataFrame数据对象
        '''
        return get_data(self, col_name, condition, isList=True, pageNo=1, pageSize=10)

    def delete(self, col_name, ids):

        return delete_data(self, col_name, ids)

    def insert(self, col_name, condition, key='id', hasTime=None):

        return insert_data(self, col_name, condition, key='id', hasTime=None)


class ServiceProcessMySql(DataProcess):

    ''' 服务实现基类-mysql，用于快速构建简单的增删查改'''

    def __init__(self, db_addr, db_port, db_name, db_pwd=None, db_user=None):
        DataProcess.__init__(self, db_addr, db_port, db_name, db_pwd, db_user)
        self.data = None
        self.sql = None
        self.count = None

    def get_engine(self):
        '''获取数据库对象'''
        return create_engine("mysql+pymysql://" + self.db_user + ":" + self.db_pwd + "@" + self.db_addr + ":" + self.db_port + "/" + self.db_name + "?charset=utf8")

    def query_data(self, func=None, x_field=None, y_field=None, isList=True):
        self.data = pd.read_sql(sql=self.sql, con=self.get_engine())
        if x_field:
            self.data.rename(columns={x_field: 'name'}, inplace=True)
        if y_field:
            self.data.rename(columns={y_field: 'value'}, inplace=True)
        self.data = func() if func else self.data
        self.count = len(self.data)
        return dataframe_to_list(self.data) if isList else self.data

    def query_data_by_sum(self, key):
        data = pd.read_sql(sql=self.sql, con=self.get_engine())
        statistics = data.groupby([key]).size().to_frame(name='value').reset_index()
        return dataframe_to_list(statistics)

    def _statics_data(self, isList=False):
        self.data = self.data.groupby(['name']).size().to_frame(name='value').reset_index()
        self.data = dataframe_to_list(self.data) if isList else self.data
        # return self.data

    def query_data_by_groupby(self, type, pd_data=None):
        '''二层分组
            Args:
                self    当前对象，提供数据库地址，端口，数据库名称
                type    最外层的分组字段
            return:
                res     dict字典
        '''
        data = pd_data if not pd_data is None else pd.read_sql(sql=self.sql, con=self.get_engine())
        print(data)
        per_json = data.to_json(orient='index', force_ascii=False)
        per_dict = json.loads(per_json)
        re_dict = {}
        for i, val in per_dict.items():
            n_list = []
            key = val.pop(type)
            if re_dict.get(key):
                re_dict.get(key).append(val)
            else:
                n_list.append(val)
                re_dict[key] = n_list
        return re_dict

    def get_line_chart_format(self, data):
        res = []
        for key_name in data.keys():
            dict_data = {'x_label': key_name}
            for x in data[key_name]:
                dict_data[x['name']] = x['value']
            res.append(dict_data)
        self.data = res


