from pao_python.pao.data import DataProcess
from enum import Enum
class BaseDataService(DataProcess):
    ''' 查询服务 
        描述：解析数据命令，获取数据库操作语句
    '''

    def query(self,command,params,startIndex,maxCount):
        pass

class IMongoDataFilter:

    '''过滤器   将自过滤器拼成mongodb的查询语句
       Args:
            name    名称
            childrenFilters 子过滤器
    '''
    def __init__(self,name,childrenFilters):
        self.name = name
        self.childrenFilters = childrenFilters

    def getCondition(self,paramValues):
        pass


class LogicKeys(Enum):
    '''逻辑运算符'''
    AND = '$and'
    OR = '$or'

class ParamDataType(Enum):
    '''数据类型'''

    Date = 'date'
    String = 'str'
    Number = 'number'

class IRelationDataFilter:
    ''' 数据过滤器
        Args:
            parameters      过滤参数
            childFilters    子过滤器列表
    '''

    def __init__(self,parameters,childFilters):
        self.parameters = parameters
        self.childFilters = childFilters

    def getLogicSign(self):
        pass
    
    def getFilterSql(self,paramValues):
        pass
    
    def getParameters(self,paramValues):
        pass