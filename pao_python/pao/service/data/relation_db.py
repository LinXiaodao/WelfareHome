from pao_python.pao.service.data import IRelationDataFilter
from pao_python.pao.service.data.error import ErrorCode,ErrorMes

class BaseRelationDataFilter(IRelationDataFilter):
    ''' 数据过滤器'''
    def getFilterSql(self,paramValues):
        ''' 获取过滤语句
            Args:
                paramValues     参数
            Return:
                where       sql语句
        '''
        self.parameters = []
        where = ''
        if len(self.childFilters)>0:
            composite = False
            for filters in self.childFilters:
                filterSql = filters.getFilterSql(paramValues)
                param = filters.getParameters(paramValues)
            if not filterSql is None:
                if where != "":
                    where = where + self.getLogicSign + filterSql
                    composite = True
                else:
                    where = filterSql
                    self.parameters = []
                self.parameters.extend(param)
        return where

    def getParameters(self):
        '''获取参数'''
        return self.parameters

    def getChildFilter(self):
        '''获取过滤器'''
        return self.childFilters
    
    def and_data_Filter(self,filters):
        ''' AND逻辑运算
            Args:
                filters     表达式
            Return:
                self    实例本身
        '''
        if self.childFilters is None:
            self.childFilters = []
        andFilter = AndRelationDataFilter([],[])
        for f in filters:
            andFilter.getChildFilter.append(f)
        self.childFilters.append(andFilter)
        return self

    def or_data_filter(self,filters):
        ''' OR逻辑运算
            Args:
                filters     表达式
            Return:
                self    实例本身
        '''
        if self.childFilters is None:
            self.childFilters = []
        orFilter = OrRelationDataFilter([],[])
        for f in filters:
            andFilter.getChildFilter.append(f)
        self.childFilters.append(orFilter)
        return self
    
    def and_data_Filter(self,filters):
        ''' 添加筛选类型的过滤条件
            Args:
                filters     筛选类型的过滤条件
        '''
        if self.childFilters is None:
            self.childFilters = []
        orFilter = OrRelationDataFilter([],[])
        for f in filters:
            self.childFilters.append(f)
        return self

class AndRelationDataFilter(BaseRelationDataFilter):
    '''AND逻辑运算过滤器'''

    def getLogicSign(self):
        return 'AND'
    
class OrRelationDataFilter(BaseRelationDataFilter):

    '''OR逻辑运算过滤器'''
    def getLogicSign(self):
        return 'OR'

class SqlRelationDataFilter:
    ''' SQL语句过滤器
        Args:
            fieldKey    字段关键字
            sql     SQL过滤语句
            caption     标题
    '''

    def __init__(self,fieldKey,sql,caption):
        self.fieldKey = fieldKey
        self.sql = sql
        self.caption = caption

    def getFilterSql(self,paramValues):
        try:
            if self.fieldKey in paramValues:
                return self.sql
        except:
            raise JsonRpc2Error(ErrorCode.SQL_GET_ABNORMAL,ErrorMes.SQL_GET_ABNORMAL)
        return None

    def getParameters(self,paramValues):
        ''' 获取参数列表
            Args:
                paramValues     参数-dict
            Return:     
                params      参数列表
        '''     
        try:
            if self.fieldKey in paramValues:
                params = []
                params.append(paramValues[self.fieldKey])
            return params
        except:
            raise JsonRpc2Error(ErrorCode.SQL_GET_PARAM,ErrorMes.SQL_GET_PARAM)
        return None

class DatabaseConnection:
    ''' 数据库连接对象
        Args：
            dbConnection    数据库连接配置
            _currentConnection  当前TypeORM的连接对象
            databaseManager     数据连接对象管理器
    '''

    def __init__(self,dbConnection,_currentConnection,databaseManager):
        self.dbConnection = dbConnection
        self._currentConnection = _currentConnection
        self.databaseManager = databaseManager

    def connect(self):
        '''数据库连接'''

        if self.dbConnection:
            databaseName = self.dbConnection.name if self.dbConnection.name else self.dbConnection.name
            if self.databaseManager.has(databaseName):
                self._currentConnection = self.databaseManager.get(databaseName)
            else:
                self._currentConnection = self.databaseManager.create(self.dbConnection)

        if self._currentConnection.isConnected:
            self._currentConnection.close()
        return self._currentConnection.connect()

class RelationDataService:
    ''' 关系型数据服务
        描述：操作关系型数据库,实现数据操作的服务
        Args:
            connection   数据库连接信息
            commandList     命令列表
    '''

    def __init__(self,connection,commandList):
        self.connection = connection
        self.commandList = commandList

    def getCommandByID(self,commandID):
        if self.commandList:
            for cmd in self.commandList:
                if cmd['id'] == commandID:
                    return cmd
        else:
            return None
    
    def query(self,command,params):
       conn = DatabaseConnection(self.connection,{},{})
       let cmd = self.getCommandByID(command);
       if not cmd:
            raise JsonRpc2Error(ErrorCode.FIND_NOT_EXIT,ErrorMes.FIND_NOT_EXIT.format(name=command))

       # 待执行的SQL语句
       executeSql = cmd.getCommandText(params)
       param = cmd.getParameters()
       connection = conn.connect
       result = connection.query(executeSql, param)
       return result