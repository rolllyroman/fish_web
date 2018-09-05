# -*- coding:utf-8 -*-
# !/usr/bin/python

"""
     消消乐模块
"""

from hall import hall_app
from hall_func import getUserByAccount
from bottle import request, response, template, static_file
from common.utilt import *
from common import web_util
from mahjong.model.xiaoxiaoleModel import *
from mahjong.model.xiaoxiaole_db_define import *
from mahjong.common.record_player_info import record_player_balance_change
from mahjong.bag.bag_config import bag_redis
import ast
import traceback
import json
import copy
import urllib

# 比例(下注1:1金币)
Proportion = 1


@hall_app.get('/xiaoxiaole/setting')
@web_util.allow_cross_request
def xiaoxiaole_setting(redis, session):
    uid = request.GET.get('uid', '').strip()
    sid = request.GET.get('sid', '').strip()
    if not uid:
        if not sid:
            return {'code': -5, 'msg': '该用户不存在'}
        SessionTable, account, uid, verfiySid = getInfoBySid(redis, sid)
        userTable = getUserByAccount(redis, account)
        uid = userTable.split(':')[-1]
    else:
        userTable = 'users:%s' % (uid)
    if not redis.exists(userTable):
        return {'code': -5, 'msg': '该用户不存在'}
    gold = int(redis.hget('users:%s' % (uid), 'gold') or 0)

    oddsTable = getXxlOdds(redis)
    return {'code': 0, 'gameinfo': oddsTable, 'max': int(gold / Proportion), 'money': 'gold'}


@hall_app.get('/xiaoxiaole/run')
@web_util.allow_cross_request
def xiaoxiaole_run(redis, session):
    uid = request.GET.get('uid', '').strip()
    sid = request.GET.get('sid', '').strip()
    Rtype = request.GET.get('Rtype', '').strip()
    try:
        Rtype = int(Rtype)
    except:
        Rtype = 0

    if not uid:
        if not sid:
            return {'code': -5, 'msg': '该用户不存在'}
        SessionTable, account, uid, verfiySid = getInfoBySid(redis, sid)
        userTable = getUserByAccount(redis, account)
        uid = userTable.split(':')[-1]
    else:
        userTable = 'users:%s' % (uid)
        account = redis.hget(userTable, 'account')
    if not redis.exists(userTable):
        return {'code': -5, 'msg': '该用户不存在'}
    bets = ast.literal_eval(request.GET.get('bets', '{}').strip())
    print '/xiaoxiaole/run', uid, bets
    try:
        bets = urllib.unquote(bets)
    except:
        pass
        # traceback.print_exc()

    if not isinstance(bets, dict):
        return {'code': -1, 'msg': u'参数错误'}

    nickname, gold = redis.hmget(userTable, ('nickname', 'coin'))
    print u'开始金币', gold

    totalPayGold = sum(bets.values())
    print u'总下注', totalPayGold

    if not gold or int(totalPayGold) > int(gold):
        return {'code': -1, 'msg': u'金币不足'}

    if not redis.exists(XXL_OODS_DEFAULT):
        return {'code': -1, 'msg': u'配置错误'}

    isMore100 = False
    moneyType = GOLD
    for _bet in bets.values():
        if _bet / 100 >= 1:
            isMore100 = True
            break

    if isMore100:
        moneyType = getMoneyType(redis, account, uid, totalPayGold)

    if moneyType == GOLD:
        Rtype = KIND_CHANCE
    else:
        Rtype = KIND_MATHS

    # Rtype = KIND_MATHS

    if Rtype == KIND_RANDOM:
        Mgr = xiaoxiaoleMgr(kind=KIND_RANDOM)
    elif Rtype == KIND_CHANCE:
        changeTableType = getXxlChangeTableType(redis)
        print '概率表%s' % (changeTableType)
        changeTable = getXxlChanceTable(redis, changeTableType)
        result, changeTable = dict_to_int_int(changeTable)
        Mgr = xiaoxiaoleMgr(kind=KIND_CHANCE, chance_table=changeTable)
    elif Rtype == KIND_MATHS:
        mathsDict_type_len = {5: 3, 4: 4, 3: 4, 2: 5, 1: 5}

        mathsList_type_len = []

        for _num in xrange(1, TYPECount + 1):
            if _num in bets.keys() or str(_num) in bets.keys():
                if bets[_num] / 100 >= 1:
                    mathsList_type_len.append((_num, mathsDict_type_len[_num]))
            else:
                for x in xrange(random.randint(0, 2)):
                    _tmp_num = random.choice([0, 3, 4, 5])
                    if _tmp_num >= 3:
                        mathsList_type_len.append((_num, _tmp_num))
        Rprint('mathsList_type_len:%s' % mathsList_type_len)
        Mgr = xiaoxiaoleMgr(kind=KIND_MATHS, mathsList_type_len=mathsList_type_len)
    else:
        return {'code': -1, 'msg': u'参数错误'}

    results = Mgr.run()

    oddsTable = getXxlOdds(redis)

    datas = []
    winScore = 0
    for _result in results:
        numtype = int(_result["type"])
        numlen = int(_result["len"])
        rep = {
            'len': numlen,
            'coordinates': _result["coordinates"],
            'type': numtype,
        }
        if moneyType == GOLD:
            rep['score'] = (bets.get(numtype, 0) or bets.get(str(numtype), 0)) * getOdds(oddsTable, numtype, numlen)
        else:
            rep['score'] = (bets.get(numtype, 0) or bets.get(str(numtype), 0)) / 100 * getOdds(oddsTable, numtype, numlen)

        rep["score"] = int(rep["score"])
        winScore += rep["score"]
        # print rep
        datas.append(rep)
    matrix = Mgr.getCanvas().tolist()

    redis.hincrby(userTable, 'coin', -totalPayGold)
    print u'扣除金币', totalPayGold

    record_player_balance_change(bag_redis, userTable, 2, -totalPayGold, redis.hget(userTable, 'coin'), 9, game_id='xxl')

    redis.hincrby(userTable, moneyType, winScore)
    gold, honor = redis.hmget(userTable, 'coin', 'honor')
    if not honor:
        honor = 0
    if not gold:
        gold = 0

    if moneyType == HONOR:
        record_player_balance_change(bag_redis, userTable, 16, winScore, honor, 9, game_id='xxl')
    else:
        record_player_balance_change(bag_redis, userTable, 2, winScore, gold, 9, game_id='xxl')

    print u'增加%s=>%s个' % (moneyType, winScore)
    # print datas
    print u'剩余金币', gold
    print u'剩余荣誉', honor
    try:
        saveXxlRecord(redis, get_gold=totalPayGold, put_gold=winScore, money=moneyType, uid=uid)
    except:
        traceback.print_exc()
    if moneyType == HONOR:
        saveXxlHonorTrade(redis, uid=uid, winHonor=winScore)
    #游玩次数统计
    saveXxlPlayRecord(redis,uid,moneyType=moneyType)

    # 默认加金币
    gold = redis.hincrby('users:%s'%uid,'coin',winScore)

    return {'code': 0, 'msg': u'成功', 'winScore': winScore, 'money': (1 if moneyType == 'honor' else 0),
            'matrix': matrix, 'datas': datas, 'gold_coin': gold, 'honor_coin': honor}


@hall_app.get('/xiaoxiaole/testrun')
@web_util.allow_cross_request
def xiaoxiaole_testrun(redis, session):
    count = request.GET.get('count', '').strip()

    try:
        count = int(count)
    except:
        return {'code': -1, 'msg': '参数错误'}

    if count > 1000:
        return {'code': -1, 'msg': '小子,不要搞事情'}

    # changeTableType = getXxlChangeTableType(redis)

    changeTableType = DEFAULT

    print '概率表%s' % (changeTableType)
    changeTable = getXxlChanceTable(redis, changeTableType)
    result, changeTable = dict_to_int_int(changeTable)
    Mgr = xiaoxiaoleMgr(kind=KIND_CHANCE, chance_table=changeTable)

    type_lian = {}

    for x in xrange(count):
        results = Mgr.run()
        datas = []
        for _result in results:
            numtype = int(_result["type"])
            numlen = int(_result["len"])
            rep = {
                'len': numlen,
                'coordinates': _result["coordinates"],
                'type': numtype,
            }
            # print rep
            datas.append(rep)
            if numlen > 10:
                numlen = 10

            type_lian.setdefault(numtype, {})
            type_lian[numtype].setdefault(numlen, 0)
            type_lian[numtype][numlen] += 1
    print type_lian
    return {'code': 0, 'data': type_lian}
