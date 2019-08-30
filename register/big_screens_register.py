from service.big_srceens_service import BigScreens
from service.northSys import NorthSql

def register(jsonrpc,db_addr,db_port,db_name,db_pwd,db_user):
    big_screen = BigScreens(db_addr, db_port, db_name, db_pwd, db_user)
    north_sql = NorthSql('14.215.45.162',3306,'home_nh','!QAZ2wsx','home_nh')

    @jsonrpc.method('IBigScreenService.getOrganizationDistributed')
    def get_organization_distributed_service():
        res = big_screen.get_organization_distributed()
        return res

        
    @jsonrpc.method('IBigScreenService.getSeniorCitizens')
    def get_senior_citizens_service():
        res = big_screen.get_senior_citizens()
        return res

    @jsonrpc.method('IBigScreenService.getAllTable')
    def get_all_table_service():
        res = big_screen.get_all_table(north_sql)
        return res