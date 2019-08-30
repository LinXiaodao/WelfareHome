# -*- coding: utf-8 -*-

'''
登录,权限接口注册
'''
from pao_python.pao import log
from pao_python.pao.service.security.security_service import LoginService,RoleService
from pao_python.pao.service.security.security_utility import PermissionUtility

def register(jsonrpc, db_addr, db_port,db_name,permission_list,inital_password,session):
    security_service = LoginService(db_addr, db_port,db_name,permission_list,inital_password,session)
    Role_func=RoleService(db_addr, db_port,db_name,inital_password,session)
    permissionUtility_func = PermissionUtility(db_addr, db_port,db_name,session)

    @jsonrpc.method('ISecurityService.preprosess')
    def __preprosess(loginType,target):
        if loginType == 'mobile':
            res=security_service.send_mobile_code(target)
            return res
        elif loginType=='email':
            res=security_service.send_email_code(target)
            return res
    
    @jsonrpc.method('ISecurityService.login')
    def __login(loginType,logindData):
        res=security_service.login(loginType,logindData)
        return res
    
    @jsonrpc.method('ISecurityService.logout')
    def __logout():
        res=security_service.login_out()
        return res

    @jsonrpc.method('ISecurityService.retrieve_password')
    def __retrieve_password(verify_type,target,password,verify_code):
        res=security_service.forget_password(target,verify_type, password, verify_code)
        return res

    @jsonrpc.method('ISecurityService.bind_mobile')
    def __bind_mobile(mobile,identify_code):
        res=security_service.bind_mobile(mobile,identify_code)
        return res
    
    @jsonrpc.method('ISecurityService.check')
    def __check(target,target_type,identify_code):
        #修改密码前验证身份
        res=security_service.check(target,target_type,identify_code)
        return res

    @jsonrpc.method('ISecurityService.modify_password')
    def __modify_password(new_password):
        #验证身份通过后修改密码
        res=security_service.modify_password(new_password)
        return res     
            
    @jsonrpc.method('IPermissionService.get_permission_list')
    def __get_permission_list():
        res=permission_list
        return res
    
    @jsonrpc.method('IPermissionService.get_role_list')
    def __get_role_list(condition,page,count):
        res=Role_func.get_role_list(condition,page,count)
        return res
    
    @jsonrpc.method('IPermissionService.update_role')
    def __update_role(role):
        res=Role_func.update_role(role)
        return res
    
    @jsonrpc.method('IPermissionService.get_role')
    def __get_role(select_id):
        res=Role_func.get_role(select_id)
        return res
    
    @jsonrpc.method('IPermissionService.is_permission')
    def __is_permisssion(permission_dict):
        res=permissionUtility_func.is_permission(permission_dict)
        return res

    @jsonrpc.method('ISecurityService.modify_email')
    def __modify_email(new_email,identify_code):
        res=security_service.modify_email(new_email,identify_code)
        return res
    
    @jsonrpc.method('IPermissionService.delete_role')
    def __delete_role(role_id):
        res = Role_func.del_role(role_id)
        return res

    @jsonrpc.method('IAccountService.get_account_lis')
    def __get_account_lis(condition,page,count):
        res=Role_func.get_account_role_list(condition,page,count)
        return res
    
    @jsonrpc.method('IAccountService.update_account')
    def __update_account(Data):
        res=Role_func.update_account_role(Data)
        return res

    @jsonrpc.method('IAccountService.delete_account')
    def __delete_account(account_id_list):
        res=Role_func.del_account(account_id_list)
        return res

    @jsonrpc.method('IAccountService.get_account')
    def __get_account(account_id):
        res=Role_func.get_account_by_id(account_id)
        return res