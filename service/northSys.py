from pao_python.pao.data import DataProcess, get_table_data,get_mysql_con,get_engine

class NorthSql(DataProcess):

    def get_all_data(self,tabel_name=None):
        return get_table_data(self, 'home_nh', 'Tables_in_home_nh',tabel_name)
        
    def get_db(self):
        return get_mysql_con(self.db_addr, self.db_port, self.db_name, self.db_pwd, self.user)