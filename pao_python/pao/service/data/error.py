class ErrorCode:
    '''信息错误码   
       
       NOT_NONE     查询的命令不能为空
       FIELD_NOT_EXIST      字段不存在
       SQL_GET_ABNORMAL     SQL数据过滤器,获取过滤语句异常
       FIND_NOT_EXIT    找不到该命令
    '''
    NOT_NONE = '-36001'
    FIELD_NOT_EXIST = '-36002'
    SQL_GET_ABNORMAL = '-36003'
    SQL_GET_PARAM = '-36004'
    FIND_NOT_EXIT = '-36005'

class ErrorMes:
    NOT_NONE = '查询的命令不能为空'
    FIELD_NOT_EXIST = '字段不存在'
    SQL_GET_ABNORMAL='SQL数据过滤器,获取过滤语句异常'
    SQL_GET_PARAM = 'SQL数据过滤器,获取参数异常'
    FIND_NOT_EXIT = '找不到{name}的命令'