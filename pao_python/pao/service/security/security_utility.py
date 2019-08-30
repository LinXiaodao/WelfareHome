from pao_python.pao.data import process_db,DataProcess
import pandas as pd
import json
# class DataProcess:
#     def __init__(self, db_addr, db_port):
#         self.db_addr = db_addr
#         self.db_port = db_port
        
class SecurityConstant:
    '''安全常量
    Attribute:
    account     ---     Session关键字：当前账户ID
    indentify   ---     Session关键字：存储验证码
    '''

    account='account_id'
    indentify='indentify'

def set_current_account_id(session,account_id):
    '''设置当前账户ID'''
    session[SecurityConstant.account] = account_id
    

def get_current_account_id(session):
    '''获取当前账户ID'''
    return session[SecurityConstant.account]

class PermissionUtility(DataProcess):
    '''权限工具类'''

    def __init__(self,db_addr, db_port,db_name,session):
        '''构造函数'''
        DataProcess.__init__(self, db_addr, db_port,db_name)
        # self.db_name = db_name
        self.session = session
        self.PERMISSIOM = '有此权限'

    def is_permission(self,permission_dict):
        #传入参数为权限名称和模块名称
        account_id=self.session[SecurityConstant.account]
        permission=permission_dict['permission']
        module=permission_dict['module']
        print(self.session[SecurityConstant.account],'account_id')
        per_df=''
        def process_func(db):
            nonlocal per_df
            collection=db['PT_Account_Role']
            tep_cur=collection.find({'account_id':account_id})
            tep_df=pd.DataFrame(list(tep_cur[:]))
            role_ids=tep_df['role_id'].tolist()
            collection_role=db['PT_Role']
            per_cur=collection_role.find({'id':{'$in':role_ids}})
            per_df=pd.DataFrame(list(per_cur[:]))
        process_db(self.db_addr, self.db_port, self.db_name, process_func)      
        per_state_list=[]
        for i in range(len(per_df)):
            permission_list=per_df['permission'].iloc[i]
            permission_df=pd.DataFrame(permission_list)
            tep=permission_df['permission_state'][(permission_df['permission']==permission) & (permission_df['module']==module)].iloc[0]
            per_state_list.append(tep)
        if 'forbid' in  per_state_list:
            return '无此权限'
        elif 'grant' in per_state_list:
            return '有此权限'
        else :
            return '未授权'

    '''判断是否拥有该权限'''
    def is_peimission_pass(self,func,permission_dict):
        permission_result = self.is_permission(permission_dict)
        if permission_result == self.PERMISSIOM:
            return func()
        else:
            return permission_result
    
    