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
from web_db_define import *


def can_take_benefit(redis,uid,user_table):
    """ 判断是否能领取救济金 """
    min_coin,take_count,benefit_coin = redis.hmget(FISH_CONSTS_CONFIG,('save_min_money','save_times','save_money'))
    user_coin = redis.hget(user_table,'coin')
    user_take_count = convert_util.to_int(redis.hget(FISH_BENEFIT_COIN_TABLE,uid))
    benefit_info = {
                    'user_take_count':  user_take_count,
                    'min_coin': convert_util.to_int(min_coin),
                    'take_count': convert_util.to_int(take_count),
                    'benefit_coin': convert_util.to_int(benefit_coin)
    }
    if convert_util.to_int(min_coin) <= convert_util.to_int(user_coin):
        #金币不符合
        log_util.debug('[can_take_benefit]user_table[%s] min_coin[%s] take_count[%s] benefit_coin[%s] user_coin[%s] user_take_count[%s]'\
                                            %(user_table,min_coin,take_count,benefit_coin,user_coin,user_take_count))
        return -9001,'持有金币不满足领取救济金.',benefit_info

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

    if int(signDay) > now_day:
        return -1003,'还没到该日签到日期',''

    if uid in sign_day_info['taked']:
        return -10002,'你今天已经签到过.',''

    log_util.info('[get_user_sign_table] return signInfo[%s]'%(sign_day_info))
    return 0,'',sign_day_info


def get_user_sign_info(redis,uid,signId):
    """ 获取用户的签到视图 """

    sign_table = FISH_SIGN_TABLE%(signId)
    if not redis.exists(sign_table):
        return -10001,'签到表已失效',''

    sign_day_info = redis.hgetall(sign_table)
    user_sign_info = {1:{},2:{},3:{},4:{},5:{},6:{},7:{}}

    for day,val in sign_day_info.items():
        log_util.debug('day[%s] val[%s]'%(day,val))
        if day == 'title':
            continue
        val = eval(val)
        day = int(day)
        user_sign_info[day]['status'] = 1 if uid in val['taked'] else 0
        user_sign_info[day]['image'] = val['image']
        user_sign_info[day]['num'] = val['coin']

    log_util.debug('[get_user_sign_info] signId[%s] userSignInfo[%s]'%(signId,user_sign_info))

    return 0,'',user_sign_info
