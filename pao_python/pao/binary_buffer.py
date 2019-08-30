'''
版权: Copyright (c) 2019 red

文件: binary_buffer.py
创建日期: Tuesday January 22nd 2019
作者: pao
说明:
1、字节数组缓冲
'''

DEFAULT_BITEORDER = 'big'


class BinaryBuffer:
    '''二进制缓冲'''
    data = bytearray()
    pos = 0

    def __init__(self, data=None):
        if data:
            self.data = data
        self.pos = 0

    def __move_down(self, pos):
        self.pos = self.pos + pos

    def read_data(self, size):
        data = self.data[self.pos: self.pos+size]
        self.__move_down(size)
        return data

    def write_data(self, size, data):
        self.data[self.pos: self.pos+size] = data
        self.__move_down(size)

    def __read_int(self, int_size, signed=True):
        val = int.from_bytes(
            self.read_data(int_size), byteorder=DEFAULT_BITEORDER, signed=signed)
        return val

    def __write_int(self, int_size, val, signed=True):
        data = val.to_bytes(
            int_size, byteorder=DEFAULT_BITEORDER, signed=signed)
        self.write_data(int_size, data)

    def set_pos(self, pos):
        self.pos = pos

    def read_int8(self):
        return self.__read_int(1)

    def write_int8(self, val):
        self.__write_int(1, val)

    def read_int16(self):
        return self.__read_int(2)

    def write_int16(self, val):
        self.__write_int(2, val)

    def read_int32(self):
        return self.__read_int(4)

    def write_int32(self, val):
        self.__write_int(4, val)

    def read_int64(self):
        return self.__read_int(8)

    def write_int64(self, val):
        self.__write_int(8, val)

    def read_uint8(self):
        return self.__read_int(1, False)

    def write_uint8(self, val):
        self.__write_int(1, val, False)

    def read_uint16(self):
        return self.__read_int(2, False)

    def write_uint16(self, val):
        self.__write_int(2, val, False)

    def read_uint32(self):
        return self.__read_int(4, False)

    def write_uint32(self, val):
        self.__write_int(4, val, False)

    def read_uint64(self):
        return self.__read_int(8, False)

    def write_uint64(self, val):
        self.__write_int(8, val, False)

    def read_bytes(self):
        length = self.read_uint16()
        data = self.read_data(length)
        return data

    def write_bytes(self, val):
        length = len(val)
        self.write_uint16(length)
        self.write_data(length, val)

    def read_string(self, encoding='utf-8'):
        str_bytes = self.read_bytes()
        return str_bytes.decode(encoding)

    def write_string(self, val, encoding='utf-8'):
        str_bytes = bytearray(val.encode(encoding))
        self.write_bytes(str_bytes)
