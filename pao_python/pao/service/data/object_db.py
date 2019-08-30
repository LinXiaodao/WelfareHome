from pao_python.pao.service.data import BaseDataService,IMongoDataFilter,LogicKeys,ParamDataType
from pao_python.pao.data import JsonRpc2Error,DataProcess,string_to_date,process_db,dataframe_to_list
from pao_python.pao.service.data.error import ErrorCode,ErrorMes
import json
import pandas as pd

class MongoDataService(BaseDataService):
    ''' 查询服务 
        描述：解析数据命令，获取数据库操作语句
    '''

    def __init__(self,db_addr, db_port, db_name,collectionList,storage):
        BaseDataService.__init__(self,db_addr, db_port, db_name)
        self.collectionList = collectionList
        self.storage = storage
    def query(self,commandID,paramValues,startIndex,maxCount):
        '''查询服务 
            Args:
                commandID    数据命令
                paramValues  参数
                startIndex   开始索引
                maxCount    最大行数,默认0为查询全部数据
            Return:

            Raise:
        '''
        #检查有效性并获取命令
        command_dict = self.__getCommandAndFilterName(commandID)
        where = command_dict['command'].getCondition(command_dict['filterName'], paramValues)
        return self.storage.query(command_dict['command'].get_collection_name(),where,{ 'skip': startIndex, 'limit': maxCount })        
        

    def __getCommandAndFilterName(self,commandID):
        '''获取命令和过滤器名称     
           Args:
                commandID   命令ID
        '''
        commands = commandID.split(".")
        cmd = self.__checkValidity(commands[0])
        return { 'command': cmd, 'filterName': commands[1], 'primaryKeys': cmd.get_primary_keys() }

    def __checkValidity(self,commandString):
        ''' 检查合法性   
            Args:
                commandString   命令ID
        '''
        #查询的命令不能为空
        if commandString in ['',None]:
            raise JsonRpc2Error(ErrorCode.NOT_NONE,ErrorMes.NOT_NONE)
        cmd = self.collectionList[commandString]
        return cmd


class BaseMongoCollection:
    ''' 用于描述Mongo数据集合的对象 
        Args:
            name    集合名称
            collection  集合
            primarykes  集合
            filters  过滤器
    '''

    def __init__(self,name,collection,primarykeys,filters):
        self.name = name
        self.collection = collection
        self.primarykeys = primarykeys
        self.filters = filters

    def getCondition(self,filterName,paramValues):
        '''获取组合之后的过滤器'''

        if paramValues in [{},None]:
            return {}
        print(paramValues,'查询')
        return self.filters[filterName]['filter'].getCondition(paramValues)

    def get_primary_keys(self):
        '''获取参数'''
        return self.primarykeys

    def get_collection_name(self):
        '''获取数据库名称'''
        return self.collection

class BaseMongoDataFilter(IMongoDataFilter):
    ''' 获取组合过滤器
        描述：组合查询条件，包含与和或逻辑    
    '''
    
    def getCondition(self,paramValues):
        ''' 组合过滤器
            paramValues     查询参数
        '''
        filterAnd = {"$and":[]}
        filterOr = {'$or':[]}
        for filterOne in self.childrenFilters:
            filterDict =  filterOne.value.getCondition(paramValues)
            if len(filterDict) == 0:
                continue
            
            # 获取当前运算 ---与/或
            logicKey = self.getLogicKey()

            # # AND 逻辑
            if logicKey == LogicKeys.AND:
                filterAnd['$and'].append(filterDict)
            #或运算符
            if logicKey == LogicKeys.OR:
                filterOr['$or'].append(filterDict)

        if len(filterOr["$or"]) > 0:
            filterAnd.update(filterOr)
        print('获取条件',filterAnd)
        return filterAnd
        
    def getLogicKey(self):
        '''获取运算符'''
        return LogicKeys.AND


class AndMongoDataFilter(BaseMongoDataFilter):
    '''与运算过滤器'''

    def getLogicKey(self):
        '''获取and运算符'''
        return LogicKeys.AND

class OrMongoDataFilter(BaseMongoDataFilter):
    '''或运算过滤器 '''

    def getLogicKey(self):
        '''获取or运算符'''
        return LogicKeys.OR

class StringMongoDataFilter(BaseMongoDataFilter):
    ''' 参数格式化处理   
        name    名称
        key     需要处理的字段名
        condition   条件-all
        dataType    数据类型
    '''
    def __init__(self,name,key,condition,dataType=ParamDataType.String):
        self.name = name 
        self.key = key
        self.condition = condition
        self.dataType = dataType

    def getCondition(self,paramValues):
        '''获取过滤器的查询条件'''
        print(self.key,paramValues,'条件')
        if self.key not in paramValues.keys():
            raise JsonRpc2Error(ErrorCode.FIELD_NOT_EXIST,self.key+ErrorMes.FIELD_NOT_EXIST)
        return self.format(paramValues[self.key])

    def format(self,value):
        '''格式化'''
        date_value = json.dumps(self.condition)
        new_condition = json.loads(date_value)
        if self.key in new_condition:
            new_condition[self.key] = value
        if self.dataType == ParamDataType.Date.value:
            new_condition = self.get_date_format(self.condition,value)
        return new_condition

    def get_date_format(self,data,value):
        ''' 替换字符 '''
        new_data = {**data}
        print(new_data,'new_data')
        for key,val in new_data.items():
            if isinstance(val,dict):
                new_data[key] = self.get_date_format(val,value)
            elif val == '%s':
                new_data[key] = string_to_date(value)
        return new_data
class MongoStorage(DataProcess):
    
    ''' 数据操作执行
        collection  集合名称
        where   条件
        option  统计配置-结果过滤
    '''
            
    def query(self,collection,where,option):
        res = []
        def process_func(db):
            nonlocal res
            col = db[collection]
            col_list = list(col.find(where)[:])
            if len(col_list) > 0:
                res = dataframe_to_list(pd.DataFrame(col_list).drop(['_id'],axis=1))
        process_db(self.db_addr,self.db_port,self.db_name,process_func)
        return res


class IDataService(DataProcess):
    '''服务解析 
       db_addr      数据库地址
       db_port      数据库端口
       db_name      数据库名称


    '''
    # def __init__(self, db_addr, db_port,db_name):
    #   DataProcess.__init__(self, db_addr, db_port, db_name)

    def query(self,commandID,analysis_command, paramValues,startIndex,maxCount):
        ''' 查询

        Args:
            commandID    数据命令
            paramValues  参数
            analysis_command   解析列表，数据命令对应的方法
        Return:

        Raise:

        '''
        command_func = analysis_command.get_commands_list()
        #执行相应函数
        commandID_func = self.checkValidity(command_func,commandID)
        param_list = []
        #获取参数
        for val in [paramValues,startIndex,maxCount]:
            if not val is None:
                param_list.append(val)
        if param_list == []:
            res = commandID_func()
        else:
            res = commandID_func(*param_list)
        return res

    def checkValidity(self,command_func,commandID):
        if commandID == '' or commandID is None:
            raise JsonRpc2Error(ErrorCode.NOT_NONE,ErrorMes.NOT_NONE)
        if commandID not in command_func.keys():
            raise JsonRpc2Error(ErrorCode.NOT_EXIT,ErrorMes.NOT_EXIT)
        
        return command_func[commandID]