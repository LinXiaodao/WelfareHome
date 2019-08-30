import jsonrpcclient
#获取机构分布图
# result = jsonrpcclient.request(
#     'http://localhost:3003/remoteCall', 'IBigScreenService.getOrganizationDistributed') 
# print(result.data.result)

#长者分布图&机构长者数量统计
# result = jsonrpcclient.request(
#     'http://localhost:3003/remoteCall', 'IBigScreenService.getSeniorCitizens')  
# print(result.data.result)

# result = jsonrpcclient.request(
#     'http://localhost:3003/remoteCall', 'IFormatDataService.add_person_data')  
# print(result.data.result)

result = jsonrpcclient.request(
    'http://localhost:3003/remoteCall', 'IFormatDataService.add_organization')  
print(result.data.result)

# result = jsonrpcclient.request(
#     'http://localhost:3003/remoteCall', 'IFormatDataService.add_service_item')  
# print(result.data.result)

# result = jsonrpcclient.request(
#     'http://localhost:3003/remoteCall', 'IFormatDataService.add_order')  
# print(result.data.result)