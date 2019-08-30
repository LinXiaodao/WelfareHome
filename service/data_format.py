from pao_python.pao.data import DataProcess, get_engine,dataframe_to_list
from .common import insert_data,inset_collection,insert_many_data
import pandas as pd
import time

class FormatData(DataProcess):
    def __init__(self, db_addr, db_port, db_name, db_pwd=None, user=None):
        DataProcess.__init__(self,db_addr, db_port, db_name, db_pwd=db_pwd, user=user)
        self.engine = get_engine('nanhai_ybj:nanhai_ybj', '112.93.116.212:50177', 'nh')

    def add_person(self):
        '''新增长者'''
        sql = '''select a.name,concat(ifnull('user-',"defaultvalue"),b.pkMember) as id,b.pkMember as code,a.idNumber as id_card,                  a.mobilePhone as telephone,a.birthday as birth_date,(case a.sex WHEN 'Male' THEN '男' WHEN 'Female' THEN '女' END)           as sex 
                 from bd_personalinfo a,mem_member b
                 where a.pkPersonalInfo = b.pkPersonalInfo'''
        data = self.__get_table_data(sql=sql)
        map_user = dataframe_to_list(data[['id','code']])
        res = dataframe_to_list(data)
        add_field = {
            'personnel_category': '4',
            'id_card_type': '身份证',
            'personnel_type':'1'
        }
        for index, val in enumerate(res):
            res[index] = dict(val, **add_field)
            res[index]['personnel_info'] = val
        
        self.__inser_table_data('PT_User', res)
        # 影射表
        self.__inser_table_data('Mapping_User',map_user)

    def add_organization(self):
        '''新增组织'''
        sql = '''
        select name,(case type WHEN 'WelfareCentre' THEN '养老院' WHEN 'Government' THEN '民政部门' WHEN 'Happiness' THEN '社区机构' END) as organization_type,contact1Name as contacts,phone as telephone,concat(ifnull('organization-',"defaultvalue"),pkOrganization) as id,pkOrganization as code from cm_organization'''
        data = self.__get_table_data(sql=sql)
        map_organization = dataframe_to_list(data[['id','code']])
        add_field = {
            'id_card_type': '身份证',
            'personnel_type':'2'
        }
        res = dataframe_to_list(data)
        for index, val in enumerate(res):
            res[index] = dict(val, **add_field)
            res[index]['organizational_info'] = val
        self.__inser_table_data('PT_User', res)
        self.__inser_table_data('Mapping_Organization',map_organization)
        
    def add_service_item(self):
        '''新增服务项目'''
        sql = '''select name,price,pkOperator,pkServiceType from om_servicetype'''
        data = dataframe_to_list(self.__get_table_data(sql=sql))
        self.__inser_table_data('serviceItem',data)

    def add_order(self):
        sql = '''select pkOrder as OrderId,pkMember as userId,pkOrganization as organizationId,pkServicePackage as servicePackageId,pkServiceType as itemId from om_order'''
        data = dataframe_to_list(self.__get_table_data(sql=sql))
        self.__inser_table_data('serviceOrder', data)
        
    def __get_table_data(self, tableName=None, sql=None):
        sql_condition = sql if sql else ('select * from %s' % tableName)
        person_pd = pd.read_sql(sql=sql_condition, con=self.engine)
        return person_pd

    def __inser_table_data(self, tableName, condition):
        insert_many_data(self,tableName,condition)

    def __get_date(self, date):
        if date > 0:
            timeArray = time.localtime(date)
            return time.strftime("%Y--%m--%d %H:%M:%S", timeArray)