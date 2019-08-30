'''
版权: Copyright (c) 2019 red

文件: netthing.py
创建日期: Friday January 25th 2019
作者: pao
说明:
1、物联网设备
2、物联网数据协议
    字段        类型                说明
    header      UINT8               协议头，固定为0xFF
    command     UINT8               命令
    crc         UINT32              data的crc32校验值
    data_length UINT16              数据长度，data的长度
    data        UINT8[data_length]  数据，其长度是data_length
'''
from ..socket import SocketServer
from ... import log
from . import BaseDeviceService
from ...binary_buffer import BinaryBuffer
import binascii

COMMAND_CHECK_ONLINE = 0x01  # 检查是否在线
COMMAND_GET_IMEI = 0x02     # 获取IMEI
COMMAND_DATA = 0x03  # 数据
COMMAND_RESET = 0x04  # 重新启动
COMMAND_SET_CLOUD_IP = 0x05  # 设置云端地址
COMMAND_SET_SERIAL_PORT = 0x06  # 设置串口参数
COMMAND_GET_LBS = 0x07  # 获取基站信息
COMMAND_FOTA = 0x08  # 更新固件

HEADER = 0xFF

OK = 'OK'

DEFAULT_ENCODING = 'utf-8'

# 全局命令索引
global_command_index = 0


def get_command_seq():
    global global_command_index
    global_command_index = global_command_index + 1
    return global_command_index


class NetThingDeviceSocketServer(SocketServer):
    device_connects = {}

    def __log(self, message):
        log('NetThingDeviceSocketServer(PORT=%d)' % (self.port), message)

    def __init__(self, deviceServices):
        self.deviceServices = deviceServices

    def on_accepted(self, connect, address):
        pass

    def receive_command(self, device_id):
        '''接受命令

        Arguments:
            device_id {string} -- 设备ID

        Raises:
            RuntimeError -- 设备未连接
            RuntimeError -- 错误的协议头
            RuntimeError -- CRC校验错误

        Returns:
            (string, bytes) -- (命令, 数据)
        '''

        connect = self.device_connects[device_id]
        if not connect:
            raise RuntimeError('设备未连接(DeviceID=%s)' % device_id)

        data = connect.recvall()
        buffer = BinaryBuffer(data)

        header = buffer.read_uint8()
        if header != HEADER:
            raise RuntimeError('错误的协议头(DeviceID=%s, Header=%d)' %
                               (device_id, header))

        command = buffer.read_uint8()

        # crc = buffer.read_uint32()

        data_length = buffer.read_uint16()
        if data_length > 0:
            data = buffer.read_data(data_length)

        # 不做校验
        # crc_calc = binascii.crc32(data)
        # if crc != crc_calc:
            # raise RuntimeError('CRC校验错误(DeviceID=%s)' % device_id)
        return (command, data)

    def send_command(self, device_id, command, data_bytes=None):
        '''发送命令

        Arguments:
            device_id {string} -- 设备ID
            command {byte} -- 命令
            data_bytes {bytes} -- 数据长度
        '''

        connect = self.device_connects[device_id]
        if not connect:
            raise RuntimeError('设备未连接(DeviceID=%s)' % device_id)

        buffer = BinaryBuffer()
        # 计算CRC
        if data_bytes and len(data_bytes) > 0:
            crc = binascii.crc32(data_bytes)
            data_length = len(data_bytes)
        else:
            crc = 0
            data_length = 0

        buffer.write_uint8(HEADER)
        buffer.write_uint8(command)
        buffer.write_uint32(crc)
        buffer.write_uint16(data_length)
        if data_bytes and len(data_bytes) > 0:
            buffer.write_data(data_length, data_bytes)

        # 发送命令
        connect.sendall(buffer.data)

    def request_response(self, device_id, command, func_name, seq_func=None, res_func=None):
        '''请求并响应

        Arguments:
            device_id {string} -- 设备ID
            command {uint8} -- 命令
            seq_func {请求函数} -- 生成请求数据的函数
            res_func {响应函数} -- 处理响应数据的函数，可以为空，如果为空则不响应

        Raises:
            RuntimeError -- 收到错误的返回命令
        '''

        buffer_req = BinaryBuffer()
        seq_req = get_command_seq()  # 请求序号
        buffer_req.write_uint16(get_command_seq())
        if seq_func != None:
            seq_func(buffer_req)
        self.send_command(device_id, COMMAND_CHECK_ONLINE, buffer_req.data)

        if res_func != None:
            (command, data) = self.receive_command(device_id)
            buffer_res = BinaryBuffer(data)
            seq_res = buffer_res.read_uint16()  # 响应序号

            if command != COMMAND_CHECK_ONLINE or seq_req != seq_res:
                raise RuntimeError('设备%s在执行%s时收到了错误的返回命令(CmdReq=%d, SeqReq=%d, CmdReq=%d, SeqRes=%d)' %
                                   (device_id, func_name, COMMAND_CHECK_ONLINE, seq_req, command, seq_res))

            return res_func(buffer_res, (device_id, func_name, command, seq_res))

    def result_func(self, buffer_res, req_data):
        result = buffer_res.read_uint8()
        (device_id, func_name, command, seq) = req_data
        if result == 0:
            message = buffer_res.read_string()
            raise RuntimeError('设备%s执行%s(Command=%d, Seq=%d)时返回了错误消息:%s' % (
                device_id, func_name, command, seq, message))

    def check_online(self, device_id):
        self.request_response(device_id,
                              COMMAND_CHECK_ONLINE,
                              '检查设备在线',
                              None,
                              self.result_func)

    def get_imei(self, device_id):
        '''获取IMEI

        Arguments:
            device_id {string} -- 设备ID

        Returns:
            uint8[16] -- IMEI数据
        '''

        def res_func(buffer_res, seq_data):
            return buffer_res.read_data(16)

        return self.request_response(device_id,
                                     COMMAND_GET_IMEI,
                                     '获取IMEI',
                                     None,
                                     res_func)

    def process_data(self, device_id, data):
        '''数据透传

        Arguments:
            device_id {string} -- 设备ID
            data {uint8*} -- 要透传的数据
        '''
        self.send_command(device_id, COMMAND_DATA, data)

    def reset(self, device_id):
        '''重启设备

        Arguments:
            device_id {string} -- 设备ID
        '''
        self.request_response(device_id,
                              COMMAND_RESET,
                              '重启设备',
                              None,
                              None)

    def set_cloud_ip(self, device_id, ip, port):
        '''设置云端服务地址

        Arguments:
            device_id {string} -- 设备ID
            ip {uint8[16]} -- IP地址
            port {uint16} -- 端口
        '''

        def req_func(buffer_req):
            ip_data = ip.encode(DEFAULT_ENCODING)
            buffer_req.write_data(16, ip_data)
            buffer_req.write_uint16(port)
        self.request_response(device_id,
                              COMMAND_SET_CLOUD_IP,
                              '设置云端服务地址',
                              req_func,
                              self.result_func)

    def set_serial_port(self, device_id, baudrate):
        '''设置串口波特率

        Arguments:
            device_id {string} -- 设备ID
            baudrate {uint16} -- 波特率
        '''
        def req_func(buffer_req):
            buffer_req.write_uint16(baudrate)

        self.request_response(device_id,
                              COMMAND_SET_SERIAL_PORT,
                              '设置串口波特率',
                              req_func,
                              self.result_func)

    def get_lbs(self, device_id):
        '''获取基站定位信息

        Arguments:
            device_id {string} -- 设备ID

        Returns:
            LBS 的定义
            UINT16 s_lac;
            UINT16 s_cell_id;
        '''
        def res_func(buffer_res, seq_data):
            return {
                's_lac': buffer_res.read_uint16(),
                's_cell_id': buffer_res.read_uint16()
            }
        return self.request_response(device_id,
                                     COMMAND_GET_LBS,
                                     '获取基站信息',
                                     None,
                                     res_func)

    def fota(self, device_id):
        '''自动更新固件

        Arguments:
            device_id {string} -- 设备ID
        '''

        self.request_response(device_id,
                              COMMAND_FOTA,
                              '自动更新固件',
                              None,
                              None)
