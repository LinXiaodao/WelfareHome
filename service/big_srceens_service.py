from pao_python.pao.data import DataProcess,process_db_mysql,dataframe_to_list,get_mysql_data,get_mysql_con,get_table_data,get_engine
import pandas as pd
from sqlalchemy import create_engine


class BigScreens(DataProcess):

    def get_organization_distributed(self):
        '''获取机构分布'''
        res = {}
        def process_func(db):
            nonlocal res
            parameter = ('cm_organization','Happiness','WelfareCentre','Provider')
            sql = "select name,type,latitude,longitude,pkOrganization from (%s) where type in ('%s','%s','%s')" % parameter
            data=pd.read_sql(sql=sql,con=db)
            statistics = data.groupby(['type']).size().to_frame(name='sum').reset_index()
            apa.data = dataframe_to_list(data)
            res = {'data':dataframe_to_list(data),'statistics':dataframe_to_list(statistics)}
        process_db_mysql(self.db_addr, self.db_port, self.db_name,self.db_pwd,self.user,process_func)
        return res
    
    def get_senior_citizens(self):
        '''获取长者分布情况'''
        res = []
        def process_func(db):
            nonlocal res
            parameter = ('Happiness','WelfareCentre')
            parameter_type = ((23,24,25,26,27,28,29,30,31,32,33,34,35,36,38,39,40,44,45,46),)
            sql_home = 'select pkMember from mem_member_type where pkMemberType in %s' % parameter_type
            sql = "select a.name,a.type,a.latitude,a.longitude from cm_organization as a,mem_member as b where a.pkOrganization = b.pkOrganization and a.type in ('%s','%s')" % parameter
            data=pd.read_sql(sql=sql,con=db)
            data_home = len(pd.read_sql(sql=sql_home,con=db))
            statistics = data.groupby(['type']).size().to_frame(name='sum').reset_index()
            organization = data.groupby(['name','latitude','longitude']).size().to_frame(name='sum').reset_index()
            res = {'statistics':dataframe_to_list(statistics),'data':dataframe_to_list(organization)}
            res['statistics'].append({'sum':data_home,'type':'Provider'})
        process_db_mysql(self.db_addr, self.db_port, self.db_name,self.db_pwd,self.user,process_func)
        return res

    def get_all_table(self, north_sql):
        # self.format_data(north_sql)
        # 养老类型字典表
        self.insert_member_type_dict()
        # engine = create_engine("mysql+pymysql://home_nh:!QAZ2wsx@14.215.45.162:3306/home_nh?charset=utf8")
        # db = north_sql.get_db()
        # df = pd.read_excel("宝山区办老年人和即将步入老年人员信息.xlsx", index_col=0)
        # pf_new = pd.read_csv(io.StringIO(df.to_csv(index=False)))
        # pf_new.to_sql('bd_personalinfo', engine, if_exists='append', index=False, index_label=False)
      
    def format_data(self,north_sql):
        engine = create_engine("mysql+pymysql://home_nh:!QAZ2wsx@14.215.45.162:3306/home_nh?charset=utf8")

        # 个人信息表
        sex_list = ['Male','Female']
        row_name = ['id','name', 'borthday', 'sex', 'identity_card', 'mobile_phone', 'address', 'telephone','extra']
        modify_row_name = {
            'idNumber':'identity_card',
            'mobilePhone':'mobile_phone',
            'phone':'telephone',
            'pkAreaAddress':'county' ,
            'birthday':'borthday' ,
            # 'id': 'pkPersonalInfo',
            # 'extra':'type'
        }

        # 会员表
        data = get_table_data(self, 'elder', 'Tables_in_elder', 'hfmember_info').drop_duplicates(subset='identity_card', keep='first', inplace=False)
        pd_data = data[row_name]
        pd_data.rename(columns=modify_row_name, inplace=True)
        pd_data['idType'] = 'IdentityCard'
        # # 替换性别值
        pd_data['sex'].replace({1.0: 'Male', 2.0: 'Female'}, inplace=True)

        # 地址替换
        # address = {
        #     445272947762950528: 773,
        #     445272883988558208: 771,
        #     442361400319934464: 776,
        #     445273019179364736: 774,
        #     445272984299532672: 772,
        #     446705050601029632: 2315,
        #     445273198871736704:777,
        #     449280548787093504: None,
        #     443724500404564352: None,
        #     277759085547987648:None
            
        # }
        # pd_data['pkAreaAddress'].replace(address, inplace=True)
        # pd_data.to_sql('bd_personalinfo', engine, if_exists='append', index=False, index_label=False,chunksize=10)

        #会员表
        # mem_pd = pd_data[['pkPersonalInfo']]
        # mem_pd.to_sql('mem_member', engine, if_exists='append', index=False, index_label=False,chunksize=10)

        #养老类型
        # self.get_member_type(pd_data, north_sql)
        
    
    def get_member_type(self, data, north_sql):
        engine = get_engine('home_nh:!QAZ2wsx', '14.215.45.162:3306', 'home_nh')        
        pd_data = data[['pkPersonalInfo', 'type']]
        sql = 'select pkMember,pkPersonalInfo from mem_member'
        person_pd = pd.read_sql(sql=sql, con=engine)
        pd_data['pkPersonalInfo'] = pd_data['pkPersonalInfo'].astype('int64')
        mem_type_sql = 'select name,pkMemberType from mem_membertype'
        mem_type = pd.read_sql(sql=mem_type_sql, con=engine)
        res = pd.merge(person_pd, pd_data, how='left', on='pkPersonalInfo')
        res = pd.merge(res,mem_type,how='left',left_on='type',right_on='name')
        res = res[['pkMember', 'pkMemberType']].fillna(axis=0,method='ffill')
        res.to_sql('mem_member_type', engine, if_exists='append', index=False, index_label=False, chunksize=10)

    def insert_member_type_dict(self):
        '''养老类型字典表录入'''
        engine = get_engine('home_nh:!QAZ2wsx', '14.215.45.162:3306', 'home_nh')
        data = get_table_data(self, 'elder', 'Tables_in_elder', 'hfbase_membertype')
        data.to_sql('mem_membertype', engine, if_exists='append', index=False, index_label=False, chunksize=10)
