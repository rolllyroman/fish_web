# coding=utf-8

import copy
import numpy as np
import random

from xiaoxiaole_db_define import WIDTH, HEIGHT, TYPECount

X = 1
Y = 2

W = 'W'
S = 'S'
A = 'A'
D = 'D'

ASPECTA = [W, S, A, D]
TYPE_BB = range(1, TYPECount + 1)

TYPE_FIVE_I = 0
TYPE_FIVE_L = 1


def Rprint(str):
    pass
    # print str


def getZeros(height=HEIGHT, width=WIDTH):
    return np.zeros((width, height))


# 排序
def Sort_point(PointList):
    '''
    排序,X轴坐标优先,Y
    :param PointList:
    :return:
    '''
    return sorted(PointList, cmp=lambda x, y: cmp(x[1], y[1]) if x[0] == y[0] else cmp(x[0], y[0]))


def get_Type_L(XRange, YRange, len_count):
    result_list = []

    if len_count < 5 or len_count > 15:
        return []

    if len_count%2==0:  #偶数
        lenList = [(len_count/2, len_count/2+1),(len_count/2+1, len_count/2)]
    else:
        lenList = [((len_count+1) / 2, (len_count+1) / 2)]

    for _lens in lenList:

        count = 0
        lenX,lenY = _lens
        endX = XRange - lenX + 1
        endY = YRange - lenY + 1

        if endX < 0 or endY < 0:
            return []

        for _axisX in xrange(0, endX):
            for _axisY in xrange(0, endY):
                for _x in xrange(0, lenX):
                    for _y in xrange(0, lenY):
                        count += 1
                        Tmp = Sort_point(list(set([(_axisX + _x, _axisY + y) for y in xrange(0, lenY)] + [(_axisX + x, _axisY + _y) for x in xrange(0, lenX)])))
                        if Tmp not in result_list:
                            result_list.append(Tmp)
    return result_list

Type_Five_L_ALL = get_Type_L(8,8,5)
Type_Six_L_ALL = get_Type_L(8,8,6)
# 超出所有符合长度的线段
class CheckBeeLine(object):
    def __init__(self, table, axis, minLen):
        '''
        :param table:待处理的table
        :param axis: 递归方向 X,Y
        :param minLen: 最小长度
        '''
        self.table = copy.deepcopy(table)
        self.axis = axis
        self.minLen = minLen
        self.dictTiles = {}
        self.run()

    def run(self):
        for x in xrange(HEIGHT):
            for y in xrange(WIDTH):
                if self.table[x][y] == 0:
                    self.getNear(x, y, isfirst=True, axis=self.axis)
                    self.table[x][y] = 1
                    Rprint('666 %s' % self.dictTiles)

    def getNear(self, x, y, isfirst=False, msg='', axis=None, Points=None, masterPoint=None):
        Rprint('*' * 100)
        Rprint('开始(%s,%s)' % (x, y))
        Rprint('当前(%s,%s isfirst[%s] msg[%s] axis[%s] masterPoint[%s])' % (x, y, isfirst, msg, axis, masterPoint))
        Rprint('当前(Points %s)' % (Points))
        if not Points:
            Points = [(x, y)]

        isHas = False
        self.table[x][y] = 1

        if axis == Y:
            if y + 1 < WIDTH:
                _x = x
                _y = y + 1
                if self.table[_x][_y] == 0 and (_x, _y) not in Points:
                    Rprint('当前(%s,%s) 111 新坐标(%s,%s)' % (x, y, _x, _y))
                    Points.append((_x, _y))
                    isHas = True
                    self.getNear(_x, _y, msg='(%s, %s)' % (x, y), Points=Points, axis=axis, masterPoint=masterPoint)
            if y - 1 >= 0:
                _x = x
                _y = y - 1
                if self.table[_x][_y] == 0 and (_x, _y) not in Points:
                    Rprint(('当前(%s,%s) 222 新坐标(%s,%s)' % (x, y, _x, _y)))
                    Points.append((_x, _y))
                    isHas = True
                    self.getNear(_x, _y, msg='(%s, %s)' % (x, y), Points=Points, axis=axis, masterPoint=masterPoint)
        if axis == X:
            if x + 1 < HEIGHT:
                _x = x + 1
                _y = y
                if self.table[_x][_y] == 0 and (_x, _y) not in Points:
                    Rprint('当前(%s,%s) 333 新坐标(%s,%s)' % (x, y, _x, _y))
                    Points.append((_x, _y))
                    isHas = True
                    self.getNear(_x, _y, msg='(%s, %s)' % (x, y), Points=Points, axis=axis, masterPoint=masterPoint)
            if x - 1 >= 0:
                _x = x - 1
                _y = y
                if self.table[_x][_y] == 0 and (_x, _y) not in Points:
                    Rprint('当前(%s,%s) 444 新坐标(%s,%s)' % (x, y, _x, _y))
                    Points.append((_x, _y))
                    isHas = True
                    self.getNear(_x, _y, msg='(%s, %s)' % (x, y), Points=Points, axis=axis, masterPoint=masterPoint)

        if isfirst:
            Rprint('%' * 100)
            Rprint('结束(%s,%s) isHas[%s]' % (x, y, isHas))
            Rprint('结束(%s,%s isfirst[%s] msg[%s] axis[%s] masterPoint[%s])' % (x, y, isfirst, msg, axis, masterPoint))
            Rprint('结束(Points[%s] )' % (Points))
            lenPoints = len(Points)
            if lenPoints >= self.minLen:
                for _point in Points:
                    self.table[_point[0]][_point[1]] = 1
                self.dictTiles.setdefault(lenPoints, [])
                self.dictTiles[lenPoints].append(Points)


class Maths_Mgr(object):
    def __init__(self,mathsList_type_len):
        self.table = getZeros(HEIGHT, WIDTH)
        self.mathsList_type_len = mathsList_type_len

    def do_job(self):
        mathsDict_len_type = {}

        for type_len in self.mathsList_type_len:
            _type, _len = type_len
            mathsDict_len_type.setdefault(_len, [])
            mathsDict_len_type[_len].append(_type)

        Rprint(mathsDict_len_type)

        for _len in sorted(mathsDict_len_type.keys(), reverse=True):
            _type_list = mathsDict_len_type[_len]
            for _type in _type_list:
                if _len == 5:
                    type_five = [TYPE_FIVE_L,TYPE_FIVE_I]
                    random.shuffle(type_five)
                    for _type_five in type_five:
                        if _type_five == TYPE_FIVE_L:
                            resultPoint = self.Math_T(_len)
                            if resultPoint:
                                self.Set_type(type=_type, Points=resultPoint)
                                break
                        else:
                            resultPoint = self.Math_I(_len)
                            self.Set_type(type=_type, Points=resultPoint)
                            break
                elif _len in [3, 4, 5, 6, 7, 8]:
                    resultPoint = self.Math_I(_len)
                    self.Set_type(type=_type, Points=resultPoint)
        self.full_table()
        return self.table

    def checkAllIn(self,Points):
        for point in Points:
            if self.table[point[0]][point[1]] != 0:
                return False
        return True

    def Math_T(self,_len):
        tmp_five = copy.deepcopy(Type_Five_L_ALL)
        random.shuffle(tmp_five)
        for _tmp_five in tmp_five:
            if self.checkAllIn(_tmp_five):
                return _tmp_five
        return []

    def Math_I(self, _len):
        Tmp_beeLine = []
        BeeLineX = CheckBeeLine(self.table, axis=X, minLen=_len)
        BeeLineY = CheckBeeLine(self.table, axis=Y, minLen=_len)

        for _beeline in BeeLineX.dictTiles.values():
            Rprint('_beeline')
            Rprint(_beeline)
            Tmp_beeLine.extend(_beeline)

        for _beeline in BeeLineY.dictTiles.values():
            Rprint('_beeline')
            Rprint(_beeline)
            Tmp_beeLine.extend(_beeline)

        if Tmp_beeLine:
            Rprint('Tmp_beeLine')
            Rprint(Tmp_beeLine)
            Sort_points = Sort_point(random.choice(Tmp_beeLine))
            Rprint(Sort_points)

            sIndex = random.choice(xrange(0, len(Sort_points) - _len + 1))

            resultPoint = Sort_points[sIndex:sIndex + _len]
        else:
            resultPoint = []
        return resultPoint

    def full_table(self):
        for x in xrange(HEIGHT):
            for y in xrange(WIDTH):
                if self.table[x][y] == 0:
                    Rprint('#' * 50)
                    Rprint('(x,y) (%s,%s)' % (x, y))
                    ignores = []
                    for _aspect in ASPECTA:
                        Rprint('_aspect %s' % _aspect)
                        if _aspect == W:
                            _x = x - 1
                            _y = y
                            if _x >= 0:
                                _type = int(self.table[_x][_y])
                                if _type:
                                    ignores.append(int(_type))
                        elif _aspect == S:
                            _x = x + 1
                            _y = y
                            if _x <= 7:
                                _type = int(self.table[_x][_y])
                                if _type:
                                    ignores.append(int(_type))
                        elif _aspect == A:
                            _x = x
                            _y = y - 1
                            if _y >= 0:
                                _type = int(self.table[_x][_y])
                                if _type:
                                    ignores.append(int(_type))
                        elif _aspect == D:
                            _x = x
                            _y = y + 1
                            if _y <= 7:
                                _type = int(self.table[_x][_y])
                                if _type:
                                    ignores.append(int(_type))
                        else:
                            pass
                    if ignores:
                        Rprint('#' * 50)
                        Rprint('(x,y) (%s,%s)' % (x, y))
                        Rprint('ignores %s' % ignores)
                    Rprint('%s' % (set(TYPE_BB) - set(ignores)))
                    _type = random.choice(list(set(TYPE_BB) - set(ignores)))
                    self.table[x][y] = _type

    def Set_type(self, type, Points):
        Rprint(self.table)
        for _Point in Points:
            self.table[_Point[0]][_Point[1]] = type
        Rprint(self.table)


if __name__ == '__main__':
    pass
    # tmp_table = createCanvas()
    #
    # aaa = CheckBeeLine(tmp_table,Y,minLen=3)
    # print tmp_table
    # print ''
    # print ''
    # print ''
    # print ''
    # bbb = CheckBeeLine(tmp_table,X,minLen=3)
    # print tmp_table
