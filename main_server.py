from app.welfare_home_app import WelfareHome

#允许所有跨域请求
web_origins = '*'
# 启动标识管理系统
app = WelfareHome(
    __name__,
    address='0.0.0.0',
    port=3003,
    web_origins=web_origins,
    db_addr="localhost",
    db_port=27017,
    db_name='nanhai',
    db_pwd='123456',
    user='root')

app.run()
