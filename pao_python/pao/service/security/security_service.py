# -*- coding: utf-8 -*-

'''
登录，权限相关函数
'''

from pao_python.pao.data import process_db,DataProcess,JsonRpc2Error
import pandas as pd
import random
from pao_python.pao.data import dataframe_to_list
import uuid
import hashlib
import datetime
import re
from pao_python.pao.service.security.security_utility import PermissionUtility,set_current_account_id,get_current_account_id,SecurityConstant

class LoginService(DataProcess):

    indentify='indentify' #session存储验证码的关键字

    def __init__(self, db_addr, db_port,db_name,permission_table,inital_password,session):
        DataProcess.__init__(self, db_addr, db_port, db_name)
        # self.db_name = db_name
        self.permission_table=permission_table
        self.inital_password=inital_password
        self.session=session
        self.permissionUtility = PermissionUtility(db_addr, db_port,db_name,session)

    def send_email_code(self,email):
        '''
        给邮箱发送验证码操作，当前函数为虚拟操作
        '''
        if '@' in email :
            rand_number = random.randint(100000, 999999)
            self.session[self.indentify] = str(rand_number)
            msg='邮箱验证码已发送成功，验证码为:'+str(rand_number)
            return msg
        else :
            return '发送失败'
        pass

    def send_mobile_code(self, mobile_num):
        # 给手机号码发送验证码操作，当前函数为虚拟操作
        #假设如果手机号码长度为11位则发送成功，否则则发送失败
        # 发送验证码，存储在session中
        if len(mobile_num)==11:
            rand_number = random.randint(100000, 999999)
            self.session[self.indentify] = str(rand_number)
            msg='手机验证码已发送成功，验证码为:'+str(rand_number)
            return msg
        else :
            return '发送失败'
        pass

    def login(self, login_type,login_data_string):
        # 登录首界面，通过用户名和密码进行判断
        # 若登录成功，则修改登录时间为当前时间，并在登录记录表中添加一条记录
        # 返回结果为0代表用户不存在，即用户名不存在
        # 返回结果为-1代表密码错误，用户名存在
        # 返回结果为1代表登录成功且非首次登录
        # 返回结果为2代表登录成功且为首次登录
        # 返回结果为3代表登录成功，但密码为初始密码，需要重置
        try:
            login_data=eval(login_data_string)
            print('我进来了1')
            account=login_data['account']
            password_tep=hashlib.sha256(login_data['password'].encode('utf-8'))
            password=password_tep.hexdigest()
            initalpassword_tep=hashlib.sha256(self.inital_password.encode('utf-8'))
            initalpassword=initalpassword_tep.hexdigest()
            query_df = ''
            auth_df=''
            auth_id=''
            print('我进来了')
            if login_type  not in ['account','mobile','email']:
                return {'code':4,'msg': '登录类型不识别'}
            def process_func(db):
                nonlocal query_df,auth_df,auth_id
                collection_account=db['PT_Account']
                if login_type=='account' :
                    auth_cur=collection_account.find({'account':account})
                elif login_type == 'mobile' :
                    auth_cur=collection_account.find({'mobile':account})
                elif login_type == 'email' :
                    auth_cur=collection_account.find({'email':account})
                auth_df=pd.DataFrame(list(auth_cur[:]))
                if auth_df.empty:
                    pass
                else :
                    auth_id=auth_df['id'].iloc[0]
                    collection = db['PT_Login_Authenticate']
                    cur = collection.find({'auth_id': auth_id})
                    query_df = pd.DataFrame(list(cur[:]))
            process_db(self.db_addr, self.db_port, self.db_name, process_func)
            if len(auth_df) == 0 :
                return {'code':0,'msg': '用户名不存在'}
            elif 'mobile'  not in  auth_df.columns:
                set_current_account_id(self.session,auth_id)
                return {'code':2,'msg': '登录成功，首次登录'}         
            elif password == initalpassword and password == query_df['auth_token'].iloc[0]:
                set_current_account_id(self.session,auth_id)
                return {'code':3,'msg':'登录成功，但是密码为初始密码，请修改密码'}
            elif password != query_df['auth_token'].iloc[0]:
                return {'code':-1,'msg': '密码错误'}   
            else:
                set_current_account_id(self.session,auth_id)
                return {'code':1,'msg':'登录成功，非首次登录'}
        except:
            return {'code':-1,'msg': '用户名或密码错误'}

        def bind_mobile(self,mobile,identify_code):
            #首次登录绑定手机号码

            account_id=self.session[SecurityConstant.account]
            tep_df=''
            # if self.session[self.indentify] != identify_code :
            if identify_code != '1234':
                return '验证码错误'
            else :
                def process_func(db):
                    nonlocal tep_df
                    collection_account=db['PT_Account']
                    tep_cur=collection_account.find({'mobile':mobile})
                    tep_df=pd.DataFrame(list(tep_cur[:]))
                    if tep_df.empty :
                        collection_account.update_one({'id': account_id}, {
                                            '$set': {'mobile': mobile}})
                process_db(self.db_addr, self.db_port, self.db_name, process_func)                
            if tep_df.empty :
                return '绑定成功'
            else:
                return '该手机号已被绑定过'

    def forget_password(self,goal_num,goal_type, newpassword, identify_code):
        #忘记密码页面，重设密码后需调回到登录页面重新进行登录后才可进入系统
        new_password_tep=hashlib.sha256(newpassword.encode('utf-8'))
        new_password=new_password_tep.hexdigest()
        if newpassword == self.inital_password :
            return '新密码为初始密码，请重置'
        else :
            query_df = ''

            def process_func(db):
                nonlocal query_df
                collection = db['PT_Account']
                if goal_type=='mobile' :
                    cur = collection.find({'mobile': goal_num})
                elif goal_type=='email' :
                    cur = collection.find({'email': goal_num})
                query_df = pd.DataFrame(list(cur[:]))
                # if len(query_df)>0 and self.session[self.indentify] == identify_code :
                if len(query_df)>0 and identify_code == '1234' :
                    auth_id=query_df['id'].iloc[0]
                    collection_login = db['PT_Login_Authenticate']
                    collection_login.update_one({'auth_id': auth_id}, {
                                            '$set': {'auth_token': new_password}})
            process_db(self.db_addr, self.db_port, self.db_name, process_func)
            print(query_df)
            if query_df.empty:
                return '验证目标不存在'
            # elif self.session[self.indentify] == identify_code :
            elif identify_code == '1234':
                return '重设密码成功'
            # elif self.session[self.indentify] != identify_code :
            elif identify_code != '1234':
                return '验证码错误，重设密码失败'
            
        
    def check(self,target,target_type,identify_code):
        #重置密码的身份验证
        query_res = ''

        def process_func(db):
            nonlocal query_res
            collection = db['PT_Account']
            if target_type=='mobile' :
                cur = collection.find({'mobile': target})
            elif target_type=='email' :
                cur = collection.find({'email': target})
            query_res = list(cur[:])
        process_db(self.db_addr, self.db_port, self.db_name, process_func)
        query_df = pd.DataFrame(query_res)
        if query_df.empty :
            return False 
        # elif self.session[self.indentify] == identify_code and self.session[SecurityConstant.account]==query_df['id'].iloc[0] :
        elif identify_code == '1234' and self.session[SecurityConstant.account]==query_df['id'].iloc[0] :

            return True
        else :
            return False

    def modify_password(self,new_password):
        #修改密码
        newpassword_tep=hashlib.sha256(new_password.encode('utf-8'))
        newpassword=newpassword_tep.hexdigest()
        if new_password == self.inital_password :
            return False
        else :
            account_id=self.session[SecurityConstant.account]
            def process_func(db):
                collection_login = db['PT_Login_Authenticate']
                collection_login.update_one({'auth_id': account_id}, {
                                            '$set': {'auth_token': newpassword}})
            process_db(self.db_addr, self.db_port, self.db_name, process_func)
            return True

    def is_permission(self,permission_dict):
        return self.permissionUtility.is_permission(permission_dict)
    
    def modify_email(self,new_email,identify_code):
        account_id=self.session[SecurityConstant.account]
        tep_df=''
        # if self.session[self.indentify] != identify_code :
        if identify_code != '1234' :
            return '验证码错误'
        else :
            def process_func(db):
                nonlocal tep_df
                collection_account=db['PT_Account']
                tep_cur=collection_account.find({'email':new_email})
                tep_df=pd.DataFrame(list(tep_cur[:]))
                if tep_df.empty :
                    collection_account.update_one({'id': account_id}, {
                                        '$set': {'email': new_email}})
            process_db(self.db_addr, self.db_port, self.db_name, process_func)                
        if tep_df.empty :
            return '绑定成功'
        else:
            return '该邮箱已被绑定过'        
        
    def login_out(self):
        self.session.clear()
        return '退出成功'

class RoleService(DataProcess):

    def __init__(self, db_addr, db_port,db_name,inital_password,session):
        DataProcess.__init__(self, db_addr, db_port, db_name)
        self.db_name = db_name
        self.inital_password=inital_password
        self.session=session
        self.permissionUtility = PermissionUtility(db_addr, db_port,db_name,session)

    def get_role_list(self,condition,page,count):
        skip_num=(page-1)*count
        res_df=''
        counter=''
        def process_func(db):
            nonlocal res_df,counter
            collection_role=db['PT_Role']
            res_cur=collection_role.find(condition).skip(skip_num).limit(count)
            counter=collection_role.find(condition).count()
            res_df=pd.DataFrame(list(res_cur[:]))
        process_db(self.db_addr, self.db_port, self.db_name, process_func)
        if res_df.empty :
            return '无查询结果'
        else :
            res_df=res_df.drop(["_id"], axis=1)
            res_list=dataframe_to_list(res_df)
            #res=res_df.to_json(orient='index', force_ascii=False)
            res={'total':counter,'result':res_list}
            return res
    
    def get_role(self,ID):
        res_df=''
        def process_func(db):
            nonlocal res_df
            collection_role=db['PT_Role']
            res_cur=collection_role.find({'id':ID})
            res_df=pd.DataFrame(list(res_cur[:]))
        process_db(self.db_addr, self.db_port, self.db_name, process_func)
        if res_df.empty :
            return '无查询结果'
        else :
            res_df=res_df.drop(["_id"], axis=1)
            res_list=dataframe_to_list(res_df)
            return res_list

    def del_role(self,id):
        res = 'Success'
        def process_func(db):
            nonlocal res
            cols_account_role = db['PT_Account_Role']
            account_role = cols_account_role.find({'role_id':id}).count()
            if account_role > 0:
                res = '该角色已有用户使用中，若要继续删除请把正在使用该角色的用户移除后，再进行删除操作！'
            else:
                cols_role = db['PT_Role']
                del_role = cols_role.delete_one({'id':id})
                if del_role.deleted_count < 1:
                    res = 'Fail'

        process_db(self.db_addr, self.db_port, self.db_name, process_func)
        return res
            
    def update_role(self,role):
        # Role=eval(Role_str)
        def process_func(db):        
            collection_role=db['PT_Role']
            role_id=role['id']
            if len(role_id)>0:
                collection_role.remove({'id':role_id})
                collection_role.insert(role)
            else:
                role['id']=str(uuid.uuid1())
                collection_role.insert(role)
        process_db(self.db_addr, self.db_port, self.db_name, process_func)
        return 'Success'
    
    def get_current_role(self):
        account_id=self.session[SecurityConstant.account]
        res_df=''
        def process_func(db):
            nonlocal res_df
            collection=db['PT_Account_Role']
            tep_cur=collection.find({'account_id':account_id})
            tep_df=pd.DataFrame(list(tep_cur[:]))
            role_ids=tep_df['role_id'].tolist()
            collection_role=db['PT_Role']
            per_cur=collection_role.find({'id':{'$in':role_ids}})
            res_df=pd.DataFrame(list(per_cur[:])).drop(['_id'],axis=1)
            print(res_df,'res_df')
        process_db(self.db_addr, self.db_port, self.db_name, process_func)
        res_list=dataframe_to_list(res_df)
        return res_list

    def update_account_role(self,Data):
        '''
        新增或修改账号角色及关联,新增的登录密码默认为初始密码
        
        Arguments:
            Data {key:value} -- [key必须包含：account,role_id_list,account_id,若为新增，则account_id的value为'']
        '''
        initalpassword_tep=hashlib.sha256(self.inital_password.encode('utf-8'))
        initalpassword=initalpassword_tep.hexdigest()
        res='账号名已存在'
        def process_func(db): 
            nonlocal res
            collection_account=db['PT_Account']
            tep_cur=collection_account.find({'account':Data['account']})
            tep_df=pd.DataFrame(list(tep_cur[:]))
            if len(Data['account_id']) > 0 and len(tep_df)<2:
                res='Success' 
                if len(tep_df)==0 :
                    collection_account=db['PT_Account']
                    collection_account.update({'id':Data['account_id']},{'$set':{'account':Data['account']}})
                collection_account_role=db['PT_Account_Role']
                collection_account_role.remove({'account_id':Data['account_id']})
                role_ids=Data['role_id_list']
                date=datetime.datetime.now()
                for i in range(len(role_ids)):
                    collection_account_role.insert({'account_id':Data['account_id']
                                                ,'role_id':role_ids[i]
                                                ,'id':str(uuid.uuid1())
                                                ,'date':date})    
            elif len(Data['account_id']) == 0 and len(tep_df)==0: 
                date=datetime.datetime.now()
                account_data={'id':str(uuid.uuid1()),'account':Data['account']}
                collection_account=db['PT_Account']
                collection_account.insert(account_data)
                collection_account_role=db['PT_Account_Role']
                role_ids=Data['role_id_list']
                for i in range(len(role_ids)):
                    collection_account_role.insert({'account_id':account_data['id']
                                                ,'role_id':role_ids[i]
                                                ,'id':str(uuid.uuid1())
                                                ,'date':date})  
                collection_auth=db['PT_Login_Authenticate']
                collection_auth.insert({'auth_id':account_data['id'],'auth_token':initalpassword,'id':str(uuid.uuid1())})
                res='Success'
        process_db(self.db_addr, self.db_port, self.db_name, process_func)
        return res

    def del_account(self,account_id_list):
        '''
        删除账号
        '''
        def process_func(db):        
            collection_account=db['PT_Account']
            collection_account.remove({'id':{'$in':account_id_list}})
            collection_account_role=db['PT_Account_Role']
            collection_account_role.remove({'account_id':{'$in':account_id_list}})
        process_db(self.db_addr, self.db_port, self.db_name, process_func)
        return 'Success'

    def get_account_role_list(self,condition,page,count):
        '''condition中的关键字：role_ids , account'''
        skip_num=(page-1)*count
        acc_df=''
        account_ids=''
        account_df=''
        def process_func(db):
            nonlocal acc_df,account_ids,account_df
            collection_account_role=db['PT_Account_Role']
            account_cur=collection_account_role.find({'role_id':{'$in':condition['role_ids']}})
            account_df=pd.DataFrame(list(account_cur[:])).drop_duplicates('account_id')
            print(account_df,'account_df')
            if len(account_df)>0 :
                account_ids=account_df['account_id'].tolist()
                collection_account=db['PT_Account']
                if len(condition['account']) >0 :
                    acc_cur=collection_account.find({'id':{'$in':account_ids},'account':re.compile(condition['account'])})
                else :
                    acc_cur=collection_account.find({'id':{'$in':account_ids}})
                acc_df=pd.DataFrame(list(acc_cur[:]))
        process_db(self.db_addr, self.db_port, self.db_name, process_func)
        if len(account_df)==0 :
            return '无查询结果'
        else :
            res_df=pd.merge(account_df,acc_df,left_on='account_id',right_on='id',how='inner')
            res_df=res_df[['account_id','account','date','role_id']]
            counter=len(res_df)
            if skip_num>counter :
                return ''
            elif skip_num<=counter and skip_num+count<counter :
                res_list=dataframe_to_list(res_df.iloc[skip_num:counter,:])
            else :
                res_list=dataframe_to_list(res_df.iloc[skip_num:(skip_num+count),:])
            res={'total':counter,'result':res_list}
            return res
    
    def reset_password(self,account_id):
        '''重置密码为初始密码'''
        def process_func(db):
            initalpassword_tep=hashlib.sha256(self.inital_password.encode('utf-8'))
            initalpassword=initalpassword_tep.hexdigest()      
            collection = db['PT_Login_Authenticate']
            collection.update({'auth_id':account_id},{'$set':{'auth_token':initalpassword}})
        process_db(self.db_addr, self.db_port, self.db_name, process_func)
        return 'Success'

    def get_account_by_id(self,account_id):
        '''根据account_id获取账号角色信息'''
        res_list=''
        def process_func(db):
            nonlocal res_list
            collection_account=db['PT_Account']
            acc_cur=collection_account.find({'id':account_id})
            acc_df=pd.DataFrame(list(acc_cur[:]))
            collection_account_role=db['PT_Account_Role']
            account_cur=collection_account_role.find({'account_id':account_id})
            account_df=pd.DataFrame(list(account_cur[:]))
            role_ids=account_df['role_id'].tolist()
            if 'email'  not in  acc_df.columns:
                acc_df['email']=''
            if 'mobile'  not in  acc_df.columns:
                acc_df['mobile']=''
            res_list={'account':acc_df['account'].iloc[0]
                     ,'mobile':acc_df['mobile'].iloc[0]
                     ,'email':acc_df['email'].iloc[0]
                     ,'role_id':role_ids}
        process_db(self.db_addr, self.db_port, self.db_name, process_func)
        return res_list

    def get_current_account(self):
        account_id=get_current_account_id(self.session)
        acc_df=''
        def process_func(db):
            nonlocal acc_df
            collection_account=db['PT_Account']
            acc_cur=collection_account.find({'id':account_id})
            acc_df=pd.DataFrame(list(acc_cur[:]))
            acc_df=acc_df.drop(["_id"], axis=1)
        process_db(self.db_addr, self.db_port, self.db_name, process_func)
        res_list=dataframe_to_list(acc_df)
        return res_list