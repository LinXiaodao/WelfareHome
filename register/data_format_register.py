from service.data_format import FormatData
def register(jsonrpc, db_addr, db_port, db_name, db_pwd, db_user):
    frmat_data = FormatData(db_addr, db_port, db_name, db_pwd, db_user)

    @jsonrpc.method('IFormatDataService.add_person_data')
    def get_organization_distributed_service():
        res = frmat_data.add_person()
        return res

    @jsonrpc.method('IFormatDataService.add_organization')
    def get_organization_distributed_service():
        res = frmat_data.add_organization()
        return res
    @jsonrpc.method('IFormatDataService.add_service_item')
    def get_add_service_item():
        res = frmat_data.add_service_item()
        return res
    
    @jsonrpc.method('IFormatDataService.add_order')
    def get_order():
        res = frmat_data.add_order()
        return res
    