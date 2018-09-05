#-*- coding:utf-8 -*-
# !/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    消消乐游戏逻辑类
"""

import numpy as np
import copy
import traceback
import random
import math
from xiaoxiaole_db_define import *
from xiaoxiaole_arith import *
from bottle_mysql import get_mysql


def Rprint(str):
    # print(str)
    pass


# 获取消消乐公仔盘的生成模式
# 完全随机
KIND_RANDOM = 1
# 概率随机
KIND_CHANCE = 2
# 数学随机
KIND_MATHS = 3


def getOdds(oddTable, type, count):
    '''
    获取某个公仔对应赔率
    :param oddTable: 赔率表
    :param type: 公仔类型
    :param count: n连
    :return: 对应赔率
    '''
    type = int(type)
    count = int(count)
    if count not in oddTable[type]:
        return oddTable[type].get(0, 0)
    else:
        return oddTable[type][count]


def getMoneyType(redis, account, uid, totalPayGold):
    '''
    返回结算货币类型
    :param redis:redis
    :param account:账号
    :param uid: uid
    :param totalPayGold: 总下注
    :return: 结算的货币类型
    '''
    sHonor_Surplus = redis.hget(XXL_SHONOR_PLAYER_INFO % uid, 'sHonor_Surplus')
    try:
        sHonor_Surplus = int(sHonor_Surplus)
    except:
        sHonor_Surplus = 0
    if sHonor_Surplus and sHonor_Surplus >= totalPayGold/100:
        return HONOR
    return GOLD


def getXxlOdds(redis):
    '''获取赔率表'''
    odds_default = redis.hgetall(XXL_OODS_DEFAULT)
    new_odds_table = {}
    for _type, _odds in odds_default.iteritems():
        result, new_dict = dict_to_int_float(eval(_odds))
        if not result:
            return {}
        try:
            new_odds_table[int(_type)] = new_dict
        except:
            return {}
    return new_odds_table


def getXxlChangeTableType(redis):
    '''
    返回当前概率随机所用的概率表名
    :param redis:
    :return:
    '''
    TYPE = [DEFAULT, RELEASE, RECOVERY]
    table_type = DEFAULT

    date, week, day, week_startDay = getNowTimeInfo()

    xxl_record_day_key = XXL_MONEY_RECORD_DAY % (date)
    xxl_record_week_key = XXL_MONEY_RECORD_WEEK % (week)

    xxl_record_day = redis.hgetall(xxl_record_day_key)
    xxl_record_week = redis.hgetall(xxl_record_week_key)

    redis_table_type = int(xxl_record_day.get('now_type', 0))

    if not redis_table_type:
        print '查看'
        # get_gold_day = int(xxl_record_day.get('get_gold',0))
        # put_gold_day = int(xxl_record_day.get('put_gold',0))
        # print get_gold_day
        # print put_gold_day
        get_gold_week = int(xxl_record_week.get('get_gold', 0))
        put_gold_week = int(xxl_record_week.get('put_gold', 0))
        print get_gold_week
        print put_gold_week

        XXL_Chance_Table_Pct = redis.hgetall(XXL_CHANCE_TALBE_PCT)

        try:
            release = float(XXL_Chance_Table_Pct.get('release', 0))
            recovery = float(XXL_Chance_Table_Pct.get('recovery', 1))
        except:
            release = 0
            recovery = 0

        try:
            if get_gold_week and put_gold_week:
                pct = put_gold_week * 1.0 / get_gold_week
                print pct
                if release and recovery:
                    if pct <= XXL_Chance_Table_Pct.get('release', 0.97):
                        table_type = RELEASE
                    elif pct >= XXL_Chance_Table_Pct.get('recovery', 1.03):
                        table_type =  RECOVERY
                    else:
                        table_type = DEFAULT
                else:
                    table_type = DEFAULT
            redis.hset(xxl_record_day_key, 'now_type', table_type)
        except:
            traceback.print_exc()
            table_type = DEFAULT
        return table_type
    else:
        return redis_table_type


def saveXxlRecord(redis, get_gold, put_gold, money, uid):
    '''
    保存消消乐数据
    :param redis:
    :param get_gold:
    :param put_gold:
    :param money:
    :param uid:
    :return:
    '''
    date, week, day, week_startDay = getNowTimeInfo()
    xxl_record_day_key = XXL_MONEY_RECORD_DAY % (date)
    xxl_record_week_key = XXL_MONEY_RECORD_WEEK % (week)
    xxl_record_player_key = XXL_MONEY_RECORD_PLAYER % (uid)

    if not redis.hgetall(xxl_record_week_key):
        redis.hset(xxl_record_week_key, 'start_day', week_startDay)

    pipe = redis.pipeline()
    if get_gold:
        if money == GOLD:
            pipe.hincrby(xxl_record_day_key, 'get_gold', get_gold)
            pipe.hincrby(xxl_record_week_key, 'get_gold', get_gold)
            pipe.hincrby(xxl_record_player_key, 'get_gold', get_gold)
        elif money == HONOR:
            pipe.hincrby(xxl_record_day_key, 'get_gold_byHonor', get_gold)
            pipe.hincrby(xxl_record_week_key, 'get_gold_byHonor', get_gold)
            pipe.hincrby(xxl_record_player_key, 'get_gold_byHonor', get_gold)
    if put_gold:
        pipe.hincrby(xxl_record_day_key, 'put_%s' % (money), put_gold)
        pipe.hincrby(xxl_record_week_key, 'put_%s' % (money), put_gold)
        pipe.hincrby(xxl_record_player_key, 'put_%s' % (money), put_gold)
    pipe.execute()


def saveXxlHonorTrade(redis, uid, winHonor):
    XXL_SHONOR_PLAYER_INFO_key = XXL_SHONOR_PLAYER_INFO % uid

    nowTime = datetime.now()

    pipe = redis.pipeline()
    pipe.hincrby(XXL_SHONOR_PLAYER_INFO_key, 'sHonor_Surplus', -winHonor)
    pipe.hincrby(XXL_SHONOR_PLAYER_INFO_key, 'sHonor_Converted', winHonor)

    pipe.hincrby(XXL_SHONOR_TOTAL_INFO, 'sHonor_Surplus', -winHonor)
    pipe.hincrby(XXL_SHONOR_TOTAL_INFO, 'sHonor_Converted', winHonor)

    date = datetime.now().strftime('%Y-%m-%d')
    pipe.hincrby(XXL_SHONOR_TOTAL_DATE % (date), 'sHonor_Surplus', -winHonor)
    pipe.hincrby(XXL_SHONOR_TOTAL_DATE % (date), 'sHonor_Converted', winHonor)

    pipe.execute()

    nickname, gold, honor = redis.hmget('users:%s' % uid, ('nickname', 'gold', 'honor'))
    sHonor_Total, sHonor_Surplus, sHonor_Converted = redis.hmget(XXL_SHONOR_PLAYER_INFO_key, 'sHonor_Total', 'sHonor_Surplus', 'sHonor_Converted')

    if not gold:
        gold = 0
    if not honor:
        honor = 0
    else:
        honor = int(honor)
    if not sHonor_Total:
        sHonor_Total = 0
    if not sHonor_Surplus:
        sHonor_Surplus = 0
    if not sHonor_Converted:
        sHonor_Converted = 0

    try:
        sql = get_mysql(db="honor_db")
        sql.insert_data('xxlHonorBill',
                        {
                            'date': nowTime,
                            'uid': uid,
                            'nickname': u'%s' % nickname,
                            'gold': gold,
                            'honor': honor,
                            'bhonor': honor - winHonor,
                            'winHonor': winHonor,
                            'sHonor_Total': sHonor_Total,
                            'sHonor_Surplus': sHonor_Surplus,
                            'sHonor_Converted': sHonor_Converted,
                        })
    except:
        traceback.print_exc()

def saveXxlPlayRecord(redis, uid, moneyType):
    pipe = redis.pipeline()

    date = datetime.now().strftime('%Y-%m-%d')

    pipe.hincrby(XXL_PLAYNUM_RECORD_DATE%date, 'PlayNumTotal', 1)
    if moneyType == HONOR:
        pipe.hincrby(XXL_PLAYNUM_RECORD_DATE%date, 'PlayNum_Honor', 1)
    else:
        pipe.hincrby(XXL_PLAYNUM_RECORD_DATE%date, 'PlayNum_Gold', 1)

    pipe.hincrby(XXL_PLAYERNUM_RECORD_DATE%(date,'total'),uid,1)
    pipe.hincrby(XXL_PLAYERNUM_RECORD_DATE % (date, moneyType), uid, 1)
    pipe.execute()

def getXxlChanceTable(redis, type):
    '''
    返回概率随机所用的概率表的信息
    :param redis:
    :param type:
    :return:
    '''
    if type == RELEASE:
        chance_table = redis.hgetall(XXL_CHANCE_TALBE_RELEASE)
        if not chance_table:
            chance_table = redis.hgetall(XXL_CHANCE_TALBE_DEFAULT)
        return chance_table
    elif type == RECOVERY:
        chance_table = redis.hgetall(XXL_CHANCE_TALBE_RECOVERY)
        if not chance_table:
            chance_table = redis.hgetall(XXL_CHANCE_TALBE_DEFAULT)
        return chance_table
    else:
        chance_table = redis.hgetall(XXL_CHANCE_TALBE_DEFAULT)
        return chance_table


####################消消乐算法##########################################
def getZeros(width=WIDTH, height=HEIGHT):
    return np.zeros((height, width))


###完全随机
class getCanvas_by_random(object):
    @staticmethod
    def createCanvas():
        return np.random.random_integers(low=1, high=TYPECount, size=HEIGHT * WIDTH).reshape((HEIGHT, WIDTH))


###概率随机
class getCanvas_by_chance(object):
    def __init__(self):
        pass

    def createCanvas(self, chance_table):
        nums_list = self.getRandomType(copy.deepcopy(chance_table))
        return np.array(nums_list).reshape((HEIGHT, WIDTH))

    def getRandomType(self, chance_table):
        nums_list = []
        for _c in xrange(HEIGHT * WIDTH):
            nums_list.append(self.random_type(chance_table))
        return nums_list

    def random_type(self, chance_table):
        num = random.randrange(1, sum(chance_table.values()) + 1)
        tmp_num = 0
        for _kind in sorted(chance_table.keys()):
            tmp_num += chance_table[_kind]
            if num <= tmp_num:
                return _kind


class getCanvas_by_maths(object):
    @staticmethod
    def createCanvas(mathsList_type_len):
        mgr = Maths_Mgr(mathsList_type_len)
        return mgr.do_job()
        # return mgr.do_job1()


###消消乐控制器
class xiaoxiaoleMgr(object):
    def __init__(self, kind, chance_table=None, mathsList_type_len=None):
        self.canvas = []
        self.table = getZeros()
        self.numObjs = [None] * TYPECount

        self.kind = kind
        self.chance_table = chance_table
        self.mathsList_type_len = mathsList_type_len

    def run(self):
        self.canvas = self.setCanvas()
        self.numObjs = [xiaoxiaoleNumObj(self, num=n) for n in xrange(1, TYPECount + 1)]
        Rprint(self.canvas)
        results = self.getResults()
        return results

    def getCanvas(self):
        return self.canvas

    def getResults(self):
        results = []
        for _numobj in self.numObjs:
            _results = _numobj.getResult()
            if _results:
                results.extend(_results)
        return results

    def setCanvas(self):
        if self.kind == KIND_RANDOM:
            return getCanvas_by_random.createCanvas()
        elif self.kind == KIND_CHANCE:
            if not isinstance(self.chance_table, dict):
                assert False
            mgr = getCanvas_by_chance()
            return mgr.createCanvas(self.chance_table)
        elif self.kind == KIND_MATHS:
            if not isinstance(self.mathsList_type_len, list):
                assert False
            return getCanvas_by_maths.createCanvas(self.mathsList_type_len)
        else:
            assert False


###消消乐每个公仔的处理类
class xiaoxiaoleNumObj(object):
    def __init__(self, xiaoxiaoleMgr, num):
        self.mgr = xiaoxiaoleMgr
        self.canvas = self.mgr.canvas
        self.num = num
        self.table = getZeros()
        self.pointList = []
        self.copyPointList = []
        self.resultLists = []
        self.filter()
        Rprint(self.table)
        self.relevance(datas_points=self.copyPointList, isfirst=True)
        Rprint('结果为%s' % (self.resultLists))

    def getResult(self):
        result = []
        for _result in self.resultLists:
            rep = {
                'len': len(_result),
                'coordinates': _result,
                'type': self.num,
            }
            result.append(rep)
        return result

    def relevance(self, sample_points=None, datas_points=None, tmp_point_lists=None, isfirst=False):
        '''
        查找重合点
        :param sample_points:  样本
        :param datas_points:    数据集
        :param isfirst: 是否主函数,False为递归函数
        :param tmp_point_lists:
        :return:无
        '''
        if not datas_points:
            return
        if not tmp_point_lists:
            tmp_point_lists = []
        if not sample_points and datas_points:
            sample_points = datas_points[0]
        for _sample_point in sample_points:
            if _sample_point not in tmp_point_lists:
                tmp_point_lists.append(_sample_point)
        Rprint('查看%s是否与%s有重合 isfirst[%s]' % (sample_points, datas_points, isfirst))
        if sample_points not in datas_points:
            return
        datas_points.remove(sample_points)

        if datas_points:
            relevance_list = []
            for _point in sample_points:
                for _pointlist in datas_points:
                    if _point in _pointlist and _pointlist not in relevance_list:
                        relevance_list.append(_pointlist)
            Rprint('重合点为%s' % (relevance_list))
            for _relevance in relevance_list:
                Rprint('_relevance = %s' % _relevance)
                self.relevance(sample_points=_relevance, datas_points=datas_points, tmp_point_lists=tmp_point_lists)
        if isfirst:
            self.resultLists.append(tmp_point_lists)
            if datas_points:
                Rprint('tmp_point_lists = %s' % tmp_point_lists)
                return self.relevance(datas_points=datas_points, isfirst=True)
            else:
                Rprint('tmp_point_lists = %s' % tmp_point_lists)
                Rprint('结束')

    def filter(self):
        ''''找到该号码所有连续的点'''
        Rprint('准备查找%s的点' % (self.num))
        for row in xrange(0, HEIGHT):
            row_indexs = np.reshape(np.argwhere(self.canvas[row] == self.num), (-1))
            row_indexs = [int(_row_index) for _row_index in row_indexs]
            results = self.checkIncrease(row_indexs)
            # print '第%s行,结果为%s'%(row,results)
            for _result in results:
                Rprint(zip([row] * len(_result), _result))
                self.pointList.append(zip([row] * len(_result), _result))
                for _y in _result:
                    self.table[row, _y] = 1
                    self.mgr.table[row, _y] = 1
        for col in xrange(0, WIDTH):
            col_indexs = np.reshape(np.argwhere(self.canvas[:, col] == self.num), (-1))
            col_indexs = [int(_row_index) for _row_index in col_indexs]
            results = self.checkIncrease(col_indexs)
            # print '第%s列,结果为%s'%(col,results)
            for _result in results:
                Rprint(zip([col] * len(_result), _result))
                self.pointList.append(zip(_result, [col] * len(_result)))
                for _x in _result:
                    self.table[_x, col] = 1
                    self.mgr.table[_x, col] = 1
        Rprint('pointList = %s' % self.pointList)
        self.copyPointList = copy.deepcopy(self.pointList)

    def checkIncrease(self, index_list):
        ''''找多连续的列表'''
        results = []
        tmp_list = []
        len_array = len(index_list)
        for index, value in enumerate(index_list):
            if not tmp_list:
                tmp_list = [value]
            if index + 1 < len_array and value + 1 != index_list[index + 1]:
                if len(tmp_list) >= 3 and tmp_list not in results:
                    results.append(tmp_list)
                tmp_list = []
                continue
            else:
                if index + 1 < len_array:
                    tmp_list.append(value + 1)
        if len(tmp_list) >= 3 and tmp_list not in results:
            results.append(tmp_list)
        return results

import json
from datetime import datetime
import calendar

def get_xiaoxiaole_log(redis,startDate,endDate,uid):
    sql = get_mysql(db='honor_db')
    if startDate and endDate:
        print 'startDate',startDate
        print 'endDate',endDate

        startDate = datetime.strptime(startDate, "%Y-%m-%d")
        year,mon,day = [int(s) for s in endDate.split('-')]
        if int(day) != calendar.monthrange(year,mon)[1]:
            day += 1
        else:
            mon += 1
            day = 1
        endDate = '%s-%s-%s'%(year,mon,day)
        endDate = datetime.strptime(endDate, "%Y-%m-%d")
        sql_str = 'select * from xxlHonorBill where date >= "%s" and date <= "%s"' % (startDate, endDate)
        if uid:
            sql_str += ' and uid = "%s"'%(uid)
        result, answers = sql.select_data_bywhere(sql_str)
    else:
        if uid:
            pass
            result, answers = sql.select_data('xxlHonorBill', '*', {'uid':uid})
        else:
            pass
            result, answers = sql.select_data('xxlHonorBill', '*')
    sql.close_connect()
    if result and answers:
        answers.reverse()
        return answers
    return []

def get_xiaoxiaole_DateLog(redis,startDate,endDate):
    from mahjong.common import convert_util
    date_lists = convert_util.to_week_list(startDate,endDate)

    results_list = []

    for _date in date_lists:
        result = {}
        if redis.exists(XXL_SHONOR_TOTAL_DATE%_date) or redis.exists(XXL_MONEY_RECORD_DAY%_date):

            result.update(redis.hgetall(XXL_SHONOR_TOTAL_DATE%_date))
            result['sHonor_Surplus'] = result.get('sHonor_Surplus',0)
            result['sHonor_Converted'] = result.get('sHonor_Converted',0)
            result['sHonor_Total'] = result.get('sHonor_Total',0)

            result.update(redis.hgetall(XXL_MONEY_RECORD_DAY%_date))
            result['get_gold'] = result.get('get_gold',0)
            result['get_gold_byHonor'] = result.get('get_gold_byHonor',0)
            result['put_gold'] = result.get('put_gold',0)
            result['put_honor'] = result.get('put_honor',0)
            result['now_type'] = result.get('now_type',0)

        if result:
            result['date'] = _date
            results_list.append(result)
    print results_list

    if results_list:
        results_list.reverse()
        return results_list
    return []

def get_xiaoxiaole_DatePlayNumLog(redis,startDate,endDate):
    from mahjong.common import convert_util
    date_lists = convert_util.to_week_list(startDate,endDate)

    results_list = []

    for _date in date_lists:
        result = {}
        playNumDatas = redis.hgetall(XXL_PLAYNUM_RECORD_DATE%_date)
        PlayerNumTotal = redis.hlen(XXL_PLAYERNUM_RECORD_DATE%(_date,'total'))
        PlayerNumGold = redis.hlen(XXL_PLAYERNUM_RECORD_DATE%(_date,'gold'))
        PlayerNumHonor = redis.hlen(XXL_PLAYERNUM_RECORD_DATE%(_date,'honor'))

        if playNumDatas or PlayerNumTotal or PlayerNumGold or PlayerNumHonor:

            result['PlayNumTotal'] = playNumDatas.get('PlayNumTotal',0)
            result['PlayNum_Gold'] = playNumDatas.get('PlayNum_Gold',0)
            result['PlayNum_Honor'] = playNumDatas.get('PlayNum_Honor',0)

            result['PlayerNum_Total'] = PlayerNumTotal
            result['PlayerNum_Gold'] = PlayerNumGold
            result['PlayerNum_Honor'] = PlayerNumHonor


        if result:
            result['date'] = _date
            results_list.append(result)
    print results_list

    if results_list:
        results_list.reverse()
        return results_list
    return []

if __name__ == '__main__':
    pass
