#-*- coding:utf-8 -*-
#!/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    this is Description
"""
from bottle import response,request,template
from admin import admin_app
from config.config import STATIC_LAYUI_PATH,STATIC_ADMIN_PATH,BACK_PRE,PARTY_PLAYER_COUNT
from common.utilt import *
from common.log import *
from common import log_util,convert_util,web_util,json_util
from datetime import datetime
from model.protoclModel import *
from model import userModel
from model.fishModel import *
import json

def get_sign_data(redis,sign_id):
    """ 获取签到配置数据 """

    sign_table = FISH_SIGN_TABLE%(sign_id)
    datas  = redis.hgetall(sign_table)
    sign_datas = {}
    for day,value in datas.items():
        if day == 'title':
            sign_datas[day] = value
        else:
            sign_datas['day'+day] = eval(value)

    return sign_datas

def get_sign_list_data(redis):
    """ 获取签到规则列表 """

    sign_rule_list = redis.lrange(FISH_SIGN_TABLE_LIST,0,-1)
    run_rules = redis.get(FISH_TABLE_NOW_RUN)
    sign_rules = []
    for sign_rule in sign_rule_list:
        data = get_sign_data(redis,sign_rule)
        data['id'] = sign_rule
        data['status'] = True if sign_rule == run_rules else False
        data['op'] = [
                {'txt':'编辑','url':BACK_PRE+'/benefit/sign/edit','method':'GET'},
                {'txt':'删除','url':BACK_PRE+'/benefit/sign/remove','method':'POST'}
        ]
        if not data['status']:
            data['op'].append({'txt':'开启','url':BACK_PRE+'/benefit/sign/open','method':'POST'})
        sign_rules.append(data)

    return sign_rules

def get_sign_taked(redis,sign_id):
    """ 获取每天的签到人数 """
    takeds = {
            1: [],
            2: [],
            3: [],
            4: [],
            5: [],
            6: [],
            7: [],
    }
    if not sign_id:
        return takeds

    sign_table = FISH_SIGN_TABLE%(sign_id)
    datas  = redis.hgetall(sign_table)
    for day,value in datas.items():
        if day == 'title':
            continue
        else:
            value = eval(value)
            takeds[int(day)] = value['taked']

    return takeds

@admin_app.get('/benefit/sign/list')
@checkAccess
def get_sign_list(redis,session):
    """ 获取签到列表视图 """

    lang = getLang()
    fields = ('isList',)
    for field in fields:
        exec("%s=request.GET.get('%s','').strip()"%(field,field))

    if isList:
        """ 列表数据接口 """
        sign_datas = get_sign_list_data(redis)
        result = {'data':sign_datas,'count':len(sign_datas)}
        return json.dumps(result,cls=json_util.CJsonEncoder)
    else:
        """ 视图数据 """
        info = {
                    'title'         :     lang.BENEFIT_SIGN_LIST_TXT,
                    'addTitle'      :     lang.BENEFIT_SIGN_ADD_TXT,
                    'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
                    'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH,
                    'listUrl'                :       BACK_PRE+'/benefit/sign/list?isList=1',
                    'createUrl'              :       BACK_PRE+'/benefit/sign/create'
        }
        return template('admin_benefit_sign_list',info=info,lang=lang,RES_VERSION=RES_VERSION)


@admin_app.get('/benefit/sign/<action>')
def get_sign_op(redis,session,action="create"):
    """ 获取签到操作视图 """
    lang = getLang()
    sign_data = {
                'title'      :  '',
                'day1'     :  {'taked': '[]','image': '','name': '','give_type': '','coin': ''},
                'day2'      :  {"taked": '[]','image': '','name': '','give_type': '','coin': ''},
                'day3'      :  {'taked': '[]','image': '','name': '','give_type': '','coin': ''},
                'day4'      :  {'taked': '[]','image': '','name': '','give_type': '','coin': ''},
                'day5'      :  {'taked': '[]','image': '','name': '','give_type': '','coin': ''},
                'day6'      :  {'taked': '[]','image': '','name': '','give_type': '','coin': ''},
                'day7'     :  {'taked': '[]','image': '','name': '','give_type': '','coin': ''}
    }

    info = {
                'title'         :     lang.BENEFIT_SIGN_SETTING_TXT,
                'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH,
                'backUrl'               :       BACK_PRE+'/benefit/sign/list'
    }
    sign_id = ''
    if action == 'create':
        #创建视图
        info['submitUrl'] = BACK_PRE+'/benefit/sign/create'

    elif action == 'edit':
        #编辑视图
        info['submitUrl'] = BACK_PRE+'/benefit/sign/edit'
        fields = ('sign_id',)
        for field in fields:
            exec('%s=request.GET.get("%s",'').strip()'%(field,field))

        sign_data = get_sign_data(redis,sign_id)
        log_util.debug('[get_sign_op] action[%s] sign_id[%s] datas[%s]'%(action,sign_id,sign_data))

    return template('admin_benefit_op',info=info,sign_data=json.dumps(sign_data),sign_id=sign_id,RES_VERSION=RES_VERSION,lang=lang)

def do_sign_delete(redis,sign_id):
    """ 删除签到规则 """
    sign_table = FISH_SIGN_TABLE%(sign_id)
    sign_ids = redis.lrange(FISH_SIGN_TABLE_LIST,0,-1)
    now_id = redis.get(FISH_TABLE_NOW_RUN)
    pipe = redis.pipeline()
    if now_id == sign_id:
        #如果当前删除规则是正在运行的规则，自动切换到下一个
        sign_pos = sign_ids.index(sign_id)
        try:
            now_run_id = sign_ids[int(sign_pos)+1]
        except:
            now_run_id = sign_ids[0]

        pipe.set(FISH_TABLE_NOW_RUN,now_run_id)
    #删除之前的ID
    pipe.lrem(FISH_SIGN_TABLE_LIST,sign_id)
    pipe.delete(sign_table)

    return pipe.execute()

@admin_app.post('/benefit/sign/<action>')
def do_sign_op(redis,session,action="create"):
    """ 操作签到规则接口 """
    lang = getLang()
    fields = ('title','day1','day1_type','day2','day2_type','day3','day3_type','day4','day4_type','day5','day5_type','day6','day6_type','day7','day7_type','sign_id')
    for field in fields:
        exec('%s= request.forms.get("%s","").strip()'%(field,field))

    takeds = get_sign_taked(redis,sign_id)

    sign_data = {
            'title': title,
            1: {'taked':takeds[1],'give_type':day1_type,'coin':day1,'image':'/assest/default/image/welfare_img_relief.png'},
            2: {'taked':takeds[2],'give_type':day2_type,'coin':day2,'image':'/assest/default/image/welfare_img_relief.png'},
            3: {'taked':takeds[3],'give_type':day3_type,'coin':day3,'image':'/assest/default/image/welfare_img_relief.png'},
            4: {'taked':takeds[4],'give_type':day4_type,'coin':day4,'image':'/assest/default/image/welfare_img_relief.png'},
            5: {'taked':takeds[5],'give_type':day5_type,'coin':day5,'image':'/assest/default/image/welfare_img_relief.png'},
            6: {'taked':takeds[6],'give_type':day6_type,'coin':day6,'image':'/assest/default/image/welfare_img_relief.png'},
            7: {'taked':takeds[7],'give_type':day7_type,'coin':day7,'image':'/assest/default/image/welfare_img_relief.png'}
    }
    pipe = redis.pipeline()
    message = ""
    if action == "create":
        #创建签到规则
        message = lang.BENEFIT_SIGN_CREATE_SUCCESS_TXT%(title,'成功')
        sign_id = redis.incr(FISH_SIGN_ID_COUNT)
        if sign_id:
            pipe.rpush(FISH_SIGN_TABLE_LIST,sign_id)

    elif action == "edit":
        #编辑签到规则
        message = lang.BENEFIT_SIGN_EDIT_SUCCESS_TXT%(title,'成功')

    elif action == "remove":
        #删除签到规则
        message = lang.BENEFIT_SIGN_DELETE_SUCCESS_TXT%(title,'成功')
        do_sign_delete(redis,sign_id)
        return {'code':0,'msg':message,'jumpUrl':BACK_PRE+'/benefit/sign/list'}

    elif action == "open":
        #开启前电脑规则
        message = lang.BENEFIT_SIGN_OPEN_SUCCESS_TXT%(title,'成功')
        redis.set(FISH_TABLE_NOW_RUN,sign_id)
        return {'code':0,'msg':message,'jumpUrl':BACK_PRE+'/benefit/sign/list'}

    pipe.hmset(FISH_SIGN_TABLE%(sign_id),sign_data)
    pipe.execute()
    return {'code':0,'msg':message,'jumpUrl':BACK_PRE+'/benefit/sign/list'}

@admin_app.get('/benefit/save')
def get_benefit_save(redis,session):
    """ 救济金配置视图 """
    lang = getLang()
    conf_fields = ('save_times','save_money','save_min_money')
    save_times,save_money,save_min_money = redis.hmget(FISH_CONSTS_CONFIG,conf_fields)

    take_setting = [
            {'name':'save_money','title':'救济金金额','value':save_money,'desc':'用户每次可以领取的救济金金额'},
            {'name':'save_times','title':'救济金次数','value':save_times,'desc':'用户每日可以领取的救济金次数'},
            {'name':'save_min_money','title':'领取条件','value':save_min_money,'desc':'用户金额低于多少可以领取'}
    ]

    info = {
            'title'         :     lang.BENEFIT_SIGN_SETTING_TXT,
            'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
            'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH,
            'backUrl'                :       BACK_PRE+'/benefit/sign/list'
    }

    return template('admin_benefit_take_conf',info=info,lang=lang,take_setting=take_setting,RES_VERSION=RES_VERSION)

@admin_app.post('/benefit/save')
def do_benefit_save(redis,session):
    """ 救济金设置接口 """
    lang    = getLang()
    fields = ('save_money','save_times','save_min_money')
    for field in fields:
        exec('%s = request.forms.get("%s","")'%(field,field))

    try:
        log_debug('[try do_fish_setting] share_coin[%s] exchange_shop[%s]'%(save_money,save_times))
    except:
        return {'code':-300,'msg':'接口参数错误!'}

    if not save_times.isdigit():
        return {'code':1,'msg':'领取次数必须设置为整数'}

    if not save_money.isdigit():
        return {'code':1,'msg':'领取金额必须设置为整数'}

    if not save_min_money.isdigit():
        return {'code':1,'msg':'用户最低领取金额必须设置为整数'}

    update_info = {
        'save_money'           :    convert_util.to_int(save_money),
        'save_times'           :    convert_util.to_int(save_times),
        'save_min_money'       :    convert_util.to_int(save_min_money)
    }

    redis.hmset(FISH_CONSTS_CONFIG,update_info)
    return {'code':1,'msg':'更新成功'}
