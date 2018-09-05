#-*- coding:utf-8 -*-
#!/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    捕鱼福利系统接口
"""

from bottle import request,response,default_app
from fish import fish_app
from common import web_util,log_util,convert_util,encrypt_util
from datetime import datetime
from fish_config import consts
from common.utilt import getInfoBySid
from model.hallModel import check_session_verfiy
from model.protoclModel import *
from web_db_define import *
from fish_util.fish_benefit_fun import can_take_benefit,check_sign_valid,get_user_sign_info,get_should_sign_warheads
import time
import json

@fish_app.post('/takeBenefit')
@web_util.allow_cross_request
def do_take_benefit(redis,session):
    """ 救济金补领接口 """

    fields = ('sid','token')
    for field in fields:
        exec(consts.FORMAT_PARAMS_POST_STR%(field,field))

    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    check_code,check_msg,user_table,osid = check_session_verfiy(redis,'/fish/getRewardInfo/',SessionTable,account,sid,verfiySid)

    # ----------暂时可无限领取弹头救济金-----------------
    '''
    warhead = redis.hget('users:%s'%uid,'warhead') 
    warhead = int(warhead or 0)
    if warhead < 1000:
        redis.hincrby('users:%s'%uid,20000)
        sendProtocol2AllGameService(redis, HEAD_SERVICE_PROTOCOL_MEMBER_REFRESH%(account),game="FISH")
        return {'code':0,'msg':'领取救济金成功'}
    '''
    # ----------暂时可无限领取弹头救济金-----------------

    log_util.debug('[try do_refresh] check_code[%s] check_msg[%s]'%(check_code,check_msg))
    if int(check_code)<0:
        if check_code == -4:
            return {'code':check_code,'msg':check_msg,'osid':osid}
        return {'code':check_code,'msg':check_msg}

    server_token = redis.get(USER_BENEFIT_TOKEN%(uid))
    if token != server_token:
        log_util.info('[do_take_benefit] client_token[%s] server_token[%s]'%(token,server_token))
        return {'code':-9003,'msg':'不能重复领取!'}

    code,msg,benefit_info = can_take_benefit(redis,uid,user_table)
    if code < 0:
        log_util.debug('[do_take_benefit] can\'t take benefit code[%s] msg[%s]'%(code,msg))
        return {'code':code,'msg':msg}


    _datetime = time.strftime("%Y-%m-%d", time.localtime())
    try:
        #领取救济金
        pipe = redis.pipeline()
        pipe.hincrby(FISH_BENEFIT_COIN_TABLE % _datetime ,uid,1)
        pipe.hincrby(user_table,'coin',benefit_info['benefit_coin'])

    except Exception,e:
        log_util.error('[do_take_benefit] take benefit error[%s]'%(e))
        return {'code':-9000,'msg':'领取救济金失败!'}

    pipe.delete(USER_BENEFIT_TOKEN%(uid))
    pipe.execute()
    redis.expire(FISH_BENEFIT_COIN_TABLE % _datetime, 86400)
    #发送协议通知游戏服务端
    sendProtocol2AllGameService(redis, HEAD_SERVICE_PROTOCOL_MEMBER_REFRESH%(account),game="FISH")
    return {'code':0,'msg':'领取救济金成功'}

@fish_app.post('/getBenefitInfo')
@web_util.allow_cross_request
def get_benefit_info(redis,session):
    fields = ('sid',)
    for field in fields:
        exec(consts.FORMAT_PARAMS_POST_STR%(field,field))

    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    check_code,check_msg,user_table,osid = check_session_verfiy(redis,'/fish/getRewardInfo/',SessionTable,account,sid,verfiySid)
    log_util.debug('[try do_refresh] check_code[%s] check_msg[%s]'%(check_code,check_msg))
    if int(check_code)<0:
        if check_code == -4:
            return {'code':check_code,'msg':check_msg,'osid':osid}
        return {'code':check_code,'msg':check_msg}

    #判断是否能领取救济金
    code, _,benefit= can_take_benefit(redis,uid,user_table)
    if code < 0:
        canTakeBenefit = 0
    else:
        canTakeBenefit = 1

    benefitInfo = {
            'minCoin': benefit['min_coin'],
            'benefitCoin': benefit['benefit_coin'],
            'benefitCount': benefit['take_count'],
            'userCount':  benefit['user_take_count'],
            'canTakeBenefit': canTakeBenefit
    }

    token = encrypt_util.to_md5(str(time.time())+sid)
    redis.set(USER_BENEFIT_TOKEN%(uid),token)
    log_util.info('[getBenefitInfo] uid[%s] token[%s]'%(uid,token))
    return {'code':0,'benefitInfo':benefitInfo,'token':token}

@fish_app.post('/getSignInfo')
@web_util.allow_cross_request
def get_sign_info(redis,session):
    """ 获取签到信息接口 """
    fields = ('sid',)
    for field in fields:
        exec(consts.FORMAT_PARAMS_POST_STR%(field,field))

    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    check_code,check_msg,user_table,osid = check_session_verfiy(redis,'/fish/getSignInfo/',SessionTable,account,sid,verfiySid)
    log_util.debug('[try do_refresh] check_code[%s] check_msg[%s]'%(check_code,check_msg))
    if int(check_code)<0:
        if check_code == -4:
            return {'code':check_code,'msg':check_msg,'osid':osid}
        return {'code':check_code,'msg':check_msg}

    sign_id = redis.get(FISH_TABLE_NOW_RUN)
    if not sign_id:
        sign_id = 1
    code,msg,sign_info = get_user_sign_info(redis,uid,sign_id)
    if code<0:
        return {'code':code,'msg':msg}

    now_day_index = convert_util.to_week_day(datetime.now())
    #signInfo = get_user_sign_table(redis,uid,user_table)
    log_util.info('[get_sign_info] sign table info[%s] now_day[%s]'%(sign_info,now_day_index))
    month = time.strftime("%Y-%m")
    number = redis.hget(FISH_SIGN_TABLE_USER_NUMBER % month, account)
    number = int(number) if number else 0
    receiveMoney = json.loads(json.dumps({
        5:1000000,
        10:1000000,
        15:1000000,
        20:1000000
    }))
    receive = redis.hget(FISH_SIGN_TABLE_USER_RECEIVE % month, account)
    if not receive:
        receive = json.loads(json.dumps({5: 0, 10:0, 15:0, 20:0}))
    else:
        receive = json.loads(receive)

    return {'code':0,'signInfo':sign_info,'nowDay':now_day_index, "number": number, "receiveMoney": receiveMoney, "receive": receive}

@fish_app.post("/doSignMonth")
@web_util.allow_cross_request
def doSignMonth(redis, session):
    "领取"
    fields = ('sid', 'day')
    for field in fields:
        exec (consts.FORMAT_PARAMS_POST_STR % (field, field))

    SessionTable, account, uid, verfiySid = getInfoBySid(redis, sid)
    check_code,check_msg,user_table,osid = check_session_verfiy(redis,'/fish/getRewardInfo/',SessionTable,account,sid,verfiySid)
    log_util.debug('[try do_refresh] check_code[%s] check_msg[%s]'%(check_code,check_msg))
    if int(check_code)<0:
        if check_code == -4:
            return {'code':check_code,'msg':check_msg,'osid':osid}
        return {'code':check_code,'msg':check_msg}
    account2user_table = FORMAT_ACCOUNT2USER_TABLE % (account)
    userTable = redis.get(account2user_table)
    receiveMoney = json.loads(json.dumps({
        5: 100000,
        10: 250000,
        15: 500000,
        20: 1000000
    }))

    month = time.strftime("%Y-%m")
    # 获取领取表格
    receive = redis.hget(FISH_SIGN_TABLE_USER_RECEIVE % month, account)
    number = redis.hget(FISH_SIGN_TABLE_USER_NUMBER % month, account)
    number = int(number) if number else 0
    if not receive:
        receive = json.loads(json.dumps({5: 0, 10:0, 15:0, 20:0}))
    else:
        receive = json.loads(receive)

    if int(day) <= number:
        print(u"传进来的天数:%s" % day)
        if day not in receive.keys():
            return {"code": 1, "msg": "不存在这一天"}
        money = receiveMoney[day]
        print(u"天数：%s 金钱：%s " % (day, money))
        if receive[day] == 0:
            redis.hincrby(userTable, 'coin', money)
            receive[day] = 1
            redis.hset(FISH_SIGN_TABLE_USER_RECEIVE % month, account, json.dumps(receive))
        else:
            return {"code": 1, "msg": "你已经领取过了"}
        #return {"code": 0, "msg": "成功", 'receive': receive, "money": money}
        return {"code": 0, "msg": "成功", 'receive': '1000000', "money": 1000000}
    else:
        return {"code": 1, "msg": "暂时还不能领取"}

@fish_app.post('/doSign')
@web_util.allow_cross_request
def do_take_sign_reward(redis,session):
    """ 领取签到奖励接口 """
    fields = ('sid','signDay','isRetake')
    for field in fields:
        exec(consts.FORMAT_PARAMS_POST_STR%(field,field))

    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    check_code,check_msg,user_table,osid = check_session_verfiy(redis,'/fish/doSign/',SessionTable,account,sid,verfiySid)
    log_util.debug('[try do_refresh] check_code[%s] check_msg[%s]'%(check_code,check_msg))
    if int(check_code)<0:
        if check_code == -4:
            return {'code':check_code,'msg':check_msg,'osid':osid}
        return {'code':check_code,'msg':check_msg}

    sign_id = redis.get(FISH_TABLE_NOW_RUN)
    if not sign_id:
        sign_id = 1

    #检查领取是否有效
    code,msg,sign_day_info= check_sign_valid(redis,uid,signDay,sign_id)
    if code<0:
        return {'code':code,'msg':msg}
    weekTime = time.strftime("%Y-%m-%d:%W")
    pipe = redis.pipeline()
    message = ''
    sign_type = convert_util.to_int(sign_day_info['give_type'])
    if sign_type == consts.GIVE_COIN:
        #领取的是金币的话
        message = "金币{}".format(sign_day_info['coin'])
        #pipe.hincrby(user_table,'coin',convert_util.to_int(sign_day_info['coin']))

        # 改成领取1000000弹头
        sign_warheads = get_should_sign_warheads(redis,uid)
        pipe.hincrby(user_table,'warhead',sign_warheads)
        # sign_day_info['taked'].append(uid)
        pipe.hset(FISH_SIGN_TABLE%(sign_id), signDay, sign_day_info)

        users = redis.hget(FISH_SIGN_TABLE_WEEK % (sign_id, weekTime), signDay)
        if users:
            users = eval(users)
        else:
            users = []
        users.append(uid)
        pipe.hset(FISH_SIGN_TABLE_WEEK % (sign_id, weekTime), signDay, users)
        log_util.info('[do_take_sign_reward] uid[%s] do sign success.signDay[%s] coin[%s]'%(uid,signDay,sign_day_info['coin']))

    month = time.strftime("%Y-%m")
    number = redis.hget(FISH_SIGN_TABLE_USER_NUMBER % month, account)
    if number:
        number = int(number)
        redis.hincrby(FISH_SIGN_TABLE_USER_NUMBER % month, account, 1)
        number += 1
    else:
        redis.hset(FISH_SIGN_TABLE_USER_NUMBER % month, account, 1)
        number = 1
    pipe.hset("users:%s"%uid,"last_sign_date",str(datetime.now())[:10])
    pipe.execute()
    #return {'code':0,'msg':'签到成功,获取{}'.format(message), "number": number}
    return {'code':0,'msg':'签到成功,获取{}'.format(sign_warheads), "number": number}
