#-*- coding:utf-8 -*-
#!/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    生成日均活跃和日均充值脚本
"""

import sys
sys.path.insert(0, '../mahjong')
sys.path.insert(0, '../server_common')
from web_db_define import *
from datetime import datetime,timedelta,time,date
from common import convert_util
import redis

timeDelt = timedelta(days=1)


def getInst(dbNum):
    global redisdb
    redisdb = redis.ConnectionPool(host="192.168.0.99", port=6379, db=dbNum, password='Fkkg65NbRwQOnq01OGMPy5ZREsNUeURm')
    #redisdb.connection_read_pool = redis.ConnectionPool(host="192.168.0.99", port=6000, db=dbNum, password='Fkkg65NbRwQOnq01OGMPy5ZREsNUeURm')
    return redis.Redis(connection_pool=redisdb)

def do_create_total(redis):
    count = 0
    for key in redis.keys(FORMAT_LOGIN_DATE_TABLE4FISH%('*')):
        count+=convert_util.to_int(redis.scard(key))

    print 'do_create_total  total[%s]'%(count)
    redis.set("fish:login:per:day:total",count)

def do_add_yesterday_data(redis,yesterday):
    print yesterday
    yesterday = convert_util.to_int(redis.scard(FORMAT_LOGIN_DATE_TABLE4FISH%(yesterday)))

    total = redis.incr("fish:login:per:day:total",yesterday)
    print 'do_add_yesterday_data[%s]'%(total)

def calc_per_login():
    if not redis.exists("fish:login:per:day:total"):
        do_create_total(redis)
    else:
        today = date.today()

        do_add_yesterday_data(redis,today-timeDelt)

    already_create_day = len(redis.keys(FORMAT_LOGIN_DATE_TABLE4FISH%('*')))
    already_login_total = convert_util.to_int(redis.get("fish:login:per:day:total"))
    result = already_login_total/already_create_day
    print 'already_create_day[%s] already_login_total[%s] result[%s]'%(already_create_day,already_login_total,result)
    redis.set("fish:per:login:rate",result)

def do_create_recharge_total(redis):
    """ 统计所有的充值总数 """
    count = 0
    for key in redis.keys(FISH_SYSTEM_DATE_RECHARGE_TOTAL%('*')):
        print key
        count+=convert_util.to_int(redis.hget(key,'recharge_coin_total'))

    print 'do_create_recharge_total  total[%s]'%(count)
    redis.set(FISH_SYSTEM_RECHARGE_TOTAL,count)

def calc_per_recharge():
    if not redis.exists(FISH_SYSTEM_RECHARGE_TOTAL):
        do_create_recharge_total(redis)
    else:

        already_create_day = len(redis.keys(FISH_SYSTEM_DATE_RECHARGE_TOTAL%('*')))
        already_recharge_total = convert_util.to_int(redis.get(FISH_SYSTEM_RECHARGE_TOTAL))
        result = already_recharge_total/already_create_day
        print 'already_create_day[%s] already_recharge[%s] result[%s]'%(already_create_day,already_recharge_total,result)
        redis.set("fish:per:recharge:rate",result)
    #删除当天充值人数统计
    redis.delete(FISH_RECHARGE_USER_DAY_IDS)

def clear_take_benefit(redis):
    """ 清除每日领取救济金 """
    _datetime = time.strftime("%Y-%m-%d", time.localtime())
    print redis.delete(FISH_BENEFIT_COIN_TABLE % _datetime)
    print 'already delete take benefit'

def clear_sign(redis):
    """ 清除每日领取救济金 """

    now_day = convert_util.to_week_day(datetime.now())
    print now_day
    if now_day == 1: #周一重置签到
        now_sign_id = redis.get(FISH_TABLE_NOW_RUN)
        sign_table = redis.hgetall(FISH_SIGN_TABLE%(now_sign_id))
        for day,val in sign_table.items():
            print day,val
            if day == 'title':
                continue
            val = eval(val)
            val['taked'] = []
            sign_table[day] = val
        #重置签到
        redis.hmset(FISH_SIGN_TABLE%(now_sign_id),sign_table)

redis = getInst(1)

if __name__ == '__main__':

    #1) 统计日均活跃
    calc_per_login()
    #2) 统计日均充值
    calc_per_recharge()
    #2) 统计日均充值
    clear_take_benefit(redis)
    #3) 签到刷新
    clear_sign(redis)
    #do_create_recharge_total(redis)
