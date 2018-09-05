#-*- coding:utf-8 -*-
#!/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    this is Description
"""
from common import web_util,log_util,convert_util
from datetime import datetime
from fish.fish_config import consts
from common.utilt import getInfoBySid
from model.fishModel import check_spring_time
from web_db_define import *
import time

def get_should_sign_warheads(redis,uid):
    vip_multi = int(redis.hget("users:%s"%uid,"vip_level") or 0) + 1
    return 1000000 * vip_multi

def can_take_benefit(redis,uid,user_table):
    """ 判断是否能领取救济金 """

    _datetime = time.strftime("%Y-%m-%d", time.localtime())
    min_coin,take_count,benefit_coin = redis.hmget(FISH_CONSTS_CONFIG,('save_min_money','save_times','save_money'))
    user_coin = redis.hget(user_table,'coin')
    user_take_count = convert_util.to_int(redis.hget(FISH_BENEFIT_COIN_TABLE % _datetime,uid))

    #春节活动
    isSpring, springInfo = check_spring_time(redis, 2)
    isIntime = time.strftime('%H') == '19'
    multiple = 3 if isSpring and isIntime else 1

    benefit_info = {
                    'user_take_count':  user_take_count,
                    'min_coin': convert_util.to_int(min_coin),
                    'take_count': convert_util.to_int(take_count),
                    'benefit_coin': convert_util.to_int(benefit_coin) * multiple
    }
    '''
    if convert_util.to_int(min_coin) <= convert_util.to_int(user_coin):
        #金币不符合
        log_util.debug('[can_take_benefit]user_table[%s] min_coin[%s] take_count[%s] benefit_coin[%s] user_coin[%s] user_take_count[%s]'\
                                            %(user_table,min_coin,take_count,benefit_coin,user_coin,user_take_count))
        return -9001,'持有金币不满足领取救济金.',benefit_info
    '''

    if convert_util.to_int(take_count) <= user_take_count:
        #不符合金币领取条件或者已经超过两次
        return -9002,'今日领取救济金次数已用完.',benefit_info

    return 0,True,benefit_info


def check_sign_valid(redis,uid,signDay,signType):
    """ 获取用户的签到信息 """

    sign_table = FISH_SIGN_TABLE%(signType)
    if not redis.exists(sign_table):
        return -10001,'签到表已失效',''

    sign_day_info = redis.hget(sign_table,signDay)
    sign_day_info = eval(sign_day_info)
    now_day = convert_util.to_week_day(datetime.now())
    log_util.debug('[get_user_sign_table] signDay[%s] nowDay[%s] signInfo[%s]'%(signDay,now_day,sign_day_info))

    WeekTo = {
        7: "SUN",
        1: "MON",
        2: "TUE",
        3: "WED",
        4: "THU",
        5: "FRI",
        6: "SAT",
    }
    weekTime = time.strftime("%Y-%m-%d:%W")
    year = datetime.now().year
    week = weekTime.split(":")[-1]

    timeString = "%s, %s, %s" % (year, week, WeekTo[int(signDay)])
    curDatetime = datetime.strptime(timeString, '%Y, %W, %a')
    curDatetime = "%s:%s" % (str(curDatetime.date()), week)
    print(curDatetime)
    if int(signDay) > now_day:
        return -1003,'还没到该日签到日期',''

    users = redis.hget(FISH_SIGN_TABLE_WEEK % (signType, curDatetime), signDay)
    print(users)
    print(FISH_SIGN_TABLE_WEEK % (signType, curDatetime))
    if users:
        users = eval(users)
    else:
        users = []

    if uid in users:
        return -10002,'你今天已经签到过.',''
    users.append(uid)
    redis.hset(FISH_SIGN_TABLE_WEEK % (signType, curDatetime), signDay, users)
    log_util.info('[get_user_sign_table] return signInfo[%s]'%(sign_day_info))
    return 0,'',sign_day_info


def get_user_sign_info(redis,uid,signId):
    """ 获取用户的签到视图 """

    sign_table = FISH_SIGN_TABLE%(signId)
    if not redis.exists(sign_table):
        return -10001,'签到表已失效',''

    sign_day_info = redis.hgetall(sign_table)
    user_sign_info = {1:{},2:{},3:{},4:{},5:{},6:{},7:{}}

    WeekTo = {
        7: "SUN",
        1: "MON",
        2: "TUE",
        3: "WED",
        4: "THU",
        5: "FRI",
        6: "SAT",
    }

    weekTime = time.strftime("%Y-%m-%d:%W")
    year = datetime.now().year
    week = weekTime.split(":")[-1]

    print(sign_day_info)
    for day,val in sign_day_info.items():

        log_util.debug('day[%s] val[%s]'%(day,val))
        if day == 'title':
            continue
        val = eval(val)
        day = int(day)
        timeString = "%s, %s, %s" % (year, week, WeekTo[int(day)])
        curDatetime = datetime.strptime(timeString, '%Y, %W, %a')
        curDatetime ="%s:%s" % (str(curDatetime.date()), week)

        # user_sign_info[day]['status'] = 1 if uid in val['taked'] else 0
        # pipe.hget(FISH_SIGN_TABLE % (sign_id), signDay)
        users = redis.hget(FISH_SIGN_TABLE_WEEK % (signId, curDatetime), day)
        #if day != 1 or day != 7:
        #    for
        #    upUser = redis.hget(FISH_SIGN_TABLE_WEEK % (signId, weekTime), day-1)
        print(FISH_SIGN_TABLE_WEEK % (signId, curDatetime), day)

        if users:
            users = eval(users)
        else:
            users = []
        user_sign_info[day]['status'] = 0
        print uid, users
        if str(uid) in users:
            user_sign_info[day]['status'] = 1
        user_sign_info[day]['image'] = val['image']
        user_sign_info[day]['num'] = 1000000#val['coin']

    log_util.debug('[get_user_sign_info] signId[%s] userSignInfo[%s]'%(signId,user_sign_info))

    return 0,'',user_sign_info
