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
from fish_util.fish_benefit_fun import can_take_benefit,check_sign_valid,get_user_sign_info
import time

@fish_app.post('/takeBenefit')
@web_util.allow_cross_request
def do_take_benefit(redis,session):
    """ 救济金补领接口 """

    fields = ('sid','token')
    for field in fields:
        exec(consts.FORMAT_PARAMS_POST_STR%(field,field))

    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    check_code,check_msg,user_table,osid = check_session_verfiy(redis,'/fish/getRewardInfo/',SessionTable,account,sid,verfiySid)
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

    try:
        #领取救济金
        pipe = redis.pipeline()
        pipe.hincrby(FISH_BENEFIT_COIN_TABLE,uid,1)
        pipe.hincrby(user_table,'coin',benefit_info['benefit_coin'])
    except Exception,e:
        log_util.error('[do_take_benefit] take benefit error[%s]'%(e))
        return {'code':-9000,'msg':'领取救济金失败!'}

    pipe.delete(USER_BENEFIT_TOKEN%(uid))
    pipe.execute()
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

    return {'code':0,'signInfo':sign_info,'nowDay':now_day_index}

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

    pipe = redis.pipeline()
    message = ''
    sign_type = convert_util.to_int(sign_day_info['give_type'])
    if sign_type == consts.GIVE_COIN:
        #领取的是金币的话
        message = "金币{}".format(sign_day_info['coin'])
        pipe.hincrby(user_table,'coin',convert_util.to_int(sign_day_info['coin']))
        sign_day_info['taked'].append(uid)
        pipe.hset(FISH_SIGN_TABLE%(sign_id),signDay,sign_day_info)
        log_util.info('[do_take_sign_reward] uid[%s] do sign success.signDay[%s] coin[%s]'%(uid,signDay,sign_day_info['coin']))

    pipe.execute()
    return {'code':0,'msg':'签到成功,获取{}'.format(message)}
