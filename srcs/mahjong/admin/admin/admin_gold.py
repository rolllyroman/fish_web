#coding:utf-8
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    金币场
"""
from bottle import *
from admin import admin_app
from config.config import STATIC_LAYUI_PATH,STATIC_ADMIN_PATH,BACK_PRE,RES_VERSION
from common.utilt import *
from common.log import *
from datetime import datetime
from web_db_define import *
from model.protoclModel import *
from model.goldModel import *
from access_module import *

import hashlib
import json

@admin_app.get('/gold/field')
@checkAccess
def getGoldField(redis,session):

    lang    = getLang()
    isList  = request.GET.get('list','').strip()
    search = request.GET.get('search','').strip()

    if isList:
        # res = getGoldListInfos(redis,session)
        res = getGoldListInfos(redis,session,search)
        return json.dumps(res)
    else:
        info = {
                'title'                  :       '金币场用户数据总表',
                'listUrl'                :       BACK_PRE+'/gold/field?list=1',
                'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH,
                'searchTxt'              :       '搜索'
        }
        return template('admin_gold_field',PAGE_LIST=PAGE_LIST,info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/gold/operate')
@checkAccess
def getGoldOperate(redis,session):
    """
    金币场运营总表
    """
    curTime  = datetime.now()
    lang     = getLang()
    isList = request.GET.get('list','').strip()
    selfUid  = request.GET.get('id','').strip()
    startDate = request.GET.get('startDate','').strip()
    endDate  =  request.GET.get('endDate','').strip()
    date     =  request.GET.get('date','').strip()
    niuniu_type = request.GET.get('niuniu_type','1').strip()

    if isList:
        report = getGoldOperateInfos(redis,selfUid,startDate,endDate,niuniu_type)
        return json.dumps(report)
    else:
        online_people_sum,online_room_num,user_current_gold_sum = getOnlineOperateInfos(redis)
        info = {
                    'title'                  :       '金币场运营总表',
                    'listUrl'                :       BACK_PRE+'/gold/operate?list=1&niuniu_type='+niuniu_type,
                    'searchTxt'              :       '',
                    'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
                    'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH,
                    'online_people_sum'      :       online_people_sum,
                    'online_room_num'        :       online_room_num,
                    'user_current_gold_sum'  :       user_current_gold_sum,
                    'niuniu_type'            :       niuniu_type,

        }

    return template('admin_gold_operate',PAGE_LIST=PAGE_LIST,info=info,lang=lang,RES_VERSION=RES_VERSION)


@admin_app.get('/gold/ai')
@checkAccess
def getGoldAI(redis,session):
    """
        机器人数据表
    """
    curTime  = datetime.now()
    lang     = getLang()
    isList = request.GET.get('list','').strip()
    selfUid  = request.GET.get('id','').strip()
    startDate = request.GET.get('startDate','').strip()
    endDate  =  request.GET.get('endDate','').strip()
    date     =  request.GET.get('date','').strip()
    # B档 或 D档
    grade = request.GET.get('grade','b').strip()

    if isList:
        report = getGoldAIInfos(redis,selfUid,startDate,endDate,grade)
        return json.dumps(report)
    else:
        online_ai_sum, online_ai_room_num, cur_ai_gold_sum = getOnlineAIInfos(redis)
        info = {
                    'title'                  :       '金币场AI数据表',
                    'listUrl'                :       BACK_PRE+'/gold/ai?list=1',
                    'searchTxt'              :       '',
                    'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
                    'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH,
                    'online_ai_sum'          :       online_ai_sum,
                    'online_ai_room_num'     :       online_ai_room_num,
                    'cur_ai_gold_sum':  cur_ai_gold_sum,
                    'grade'                  :       grade,

        }

    return template('admin_gold_ai',PAGE_LIST=PAGE_LIST,info=info,lang=lang,RES_VERSION=RES_VERSION)


@admin_app.get('/gold/buy_record')
def get_buy_record(redis, session):
    """
        购买金币记录
    """
    lang = getLang()
    isList = request.GET.get('list', '').strip()
    account = request.GET.get('account', '').strip()
    if isList:
        if not account:
            res = []
        else:
            res = getBuyGoldRecord(redis, account)
        return {'code': 0, 'data': res}

    info = {
        "title":  '购买金币流水',
        "tableUrl": BACK_PRE + "/gold/buy_record?list=%s&account=%s" % (1, account),
        'searchTxt': 'uid',
        'STATIC_LAYUI_PATH': STATIC_LAYUI_PATH,
        'STATIC_ADMIN_PATH': STATIC_ADMIN_PATH,
        'back_pre': BACK_PRE,
        'backUrl': BACK_PRE + "/gold/filed" ,
    }
    return template('admin_gold_buy_record', info=info, lang=lang, RES_VERSION=RES_VERSION)

@admin_app.get('/gold/journal')
def get_journal(redis, session):
    """
        金币游戏记录
    """
    lang = getLang()
    isList = request.GET.get('list', '').strip()
    account = request.GET.get('account', '').strip()
    if isList:
        if not account:
            res = []
        else:
            res = getJournal(redis, account)
        return {'code': 0, 'data': res}

    info = {
        "title":  '金币战绩流水',
        "tableUrl": BACK_PRE + "/gold/journal?list=%s&account=%s" % (1, account),
        'searchTxt': 'uid',
        'STATIC_LAYUI_PATH': STATIC_LAYUI_PATH,
        'STATIC_ADMIN_PATH': STATIC_ADMIN_PATH,
        'back_pre': BACK_PRE,
        'backUrl': BACK_PRE + "/gold/filed" ,
    }
    return template('admin_gold_journal', info=info, lang=lang, RES_VERSION=RES_VERSION)


@admin_app.get('/gold/buy_record_info')
def get_buy_record_info(redis, session):
    """
        购买金币人数
    """
    lang = getLang()
    isList = request.GET.get('list', '').strip()
    date = request.GET.get('date', '').strip()
    if isList:
        if not date:
            res = []
        else:
            res = getBuyGoldAccounts(redis, date)
        return {'code': 0, 'data': res}

    info = {
        "title":  '购买金币玩家',
        "tableUrl": BACK_PRE + "/gold/buy_record_info?list=%s&date=%s" % (1, date),
        'searchTxt': 'uid',
        'STATIC_LAYUI_PATH': STATIC_LAYUI_PATH,
        'STATIC_ADMIN_PATH': STATIC_ADMIN_PATH,
        'back_pre': BACK_PRE,
        'backUrl': BACK_PRE + "/gold/operate" ,
    }
    return template('admin_gold_buy_record_info', info=info, lang=lang, RES_VERSION=RES_VERSION)