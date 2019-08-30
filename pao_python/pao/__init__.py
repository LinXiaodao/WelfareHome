"""
pao工具包
"""
import uuid
import time


class BaseObject():
    """
    基础对象

    功能：
            1. 定义了唯一的ID，每个对象皆有一个
            1. 比较： 重载了__eq__, __gt__等方法，可以用于比较大小，
                    如果派生类只有单一值，可以直接重载get_key，否则需要重载__eq__和__gt__两个函数
    """
    uid = uuid.uuid1()

    def get_key(self):
        return self.uid

    def __eq__(self, target):
        """ == """
        if not target.get_key:
            return False

        if self.get_key() == target.get_key():
            return True
        return False

    def __gt__(self, target):
        """ > """
        if not target.get_key:
            return False

        if self.get_key() > target.get_key():
            return True
        return False

    def __ne__(self, target):
        """ != """
        return not self.__eq__(target)

    def __ge__(self, target):
        """ >= """
        return self.__gt__(target) and self.__eq__(target)

    def __le__(self, target):
        """ <= """
        return not self.__gt__(target)

    def __lt__(self, target):
        """ < """
        return not self.__ge__(target)


def log(src, information):
    """日志记录"""
    print('[%s] %s\t%s' % (time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime()), src, information))
