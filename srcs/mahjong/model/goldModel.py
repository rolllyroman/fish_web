# -*- coding:utf-8 -*-
# !/usr/bin/python

"""

     金币场数据模型

"""
import time
import json
import random
from common.log import log_debug
from gold_db_define import *
from web_db_define import *
import uuid
import copy
import redis
import traceback
from datetime import datetime, timedelta, date

def get_uuid():
    return uuid.uuid4().hex

def getPrivateRedisInst(redisdb, gameid):
    """
        获取redis连接实例
    """
    try:
        if not redisdb.exists(GAME2REDIS % gameid):
            return None
        info = redisdb.hgetall(GAME2REDIS % gameid)
        ip = info['ip']
        passwd = info['passwd']
        port = int(info['port'])
        dbnum = int(info['num'])
        redisdb = redis.ConnectionPool(host=ip, port=port, db=dbnum, password=passwd)
        return redis.Redis(connection_pool=redisdb)
    except:
        traceback.print_exc()
        return None

def get_user_info(redis, account):
    """ 获取玩家信息"""
    info = {}
    user_table = redis.get(FORMAT_ACCOUNT2USER_TABLE % account)
    if not user_table:
        return info
    info = redis.hgetall(user_table)
    info['uid'] = user_table.split(':')[1]
    return info


def sendProtocolResult2Web(redis, _uuid, proto):
    """
        发送处理结果
    """
    redis.set(RESULT_GOLD_SERVICE_PROTOCOL % _uuid, json.dumps(proto))
    redis.expire(RESULT_GOLD_SERVICE_PROTOCOL % _uuid, 5)


def getProtocolResultFromGold(redis, _uuid, timeout=5):
    """ 
        gold server 结果消息返回
    """
    while timeout > 0:
        key = RESULT_GOLD_SERVICE_PROTOCOL % _uuid
        if redis.exists(key):
            return json.loads(redis.get(key))
        time.sleep(0.1)
        timeout = timeout - 0.1


def get_GoldGameList(redis):
    """
    获取金币场场次
    """
    res = []
    for gameid in redis.smembers(GOLD_GAMEID_SET):
        list = PARTY_GOLD_GAME_LIST.get(gameid, PARTY_GOLD_GAME_LIST.get('default'))
        data = copy.deepcopy(list)
        for item in data:
            if gameid == '555':
                item['gameName'] = '经典牛牛'
            elif gameid == '666':
                item['gameName'] = '欢乐牛牛'
            elif gameid == '556':
                item['gameName'] = '明牌牛牛'
            elif gameid == '444':
                item['gameName'] = '东胜麻将'
            elif gameid == '557':
                item['gameName'] = '欢乐拼点'
                item['hasOwner'] = '1' # 支持好友开房
            online = redis.scard(GOLD_ONLINE_PLAYID_ACCOUNT_SET % (gameid, item['id']))
            item['online'] = online
        res.append({'gameid': gameid, 'config': data})
    return res


LIST_CACHE_MAXNUM = 10000
LIST_CACHE_TTL = 5*60


def getGoldListInfos(redis, session, search):
    """
        获取金币场用户数据
    """
    prredis = getPrivateRedisInst(redis, MASTER_GAMEID)
    # 如果缓存存在则直接去缓存中取数据
    if not search and redis.exists('gold:data:cache'):
        data = redis.get('gold:data:cache')
        data_list = json.loads(data)
        count = len(data_list)
        return {"count":count,"data": data_list}

    # 微信集合

    weixin_sets = prredis.smembers(GOLD_ACCOUNT_SET_TOTAL)
    weixin_sets = weixin_sets | redis.smembers(ACCOUNT4WEIXIN_SET)
    data_list =[]
    # 遍历微信集合，从对应表中取出数据字典放入data列表中
    for account in weixin_sets:
        user_info = get_user_info(redis, account)
        if not user_info:
            continue
        agentid = user_info['parentAg']
        reg_date = user_info['reg_date']
        last_login_date = user_info['last_login_date']
        uid = user_info['uid']
        gold = user_info.get('gold', '')
        roomcard = redis.get(USER4AGENT_CARD % (agentid, uid))
        gold_user_table = GOLD_USER_TABLE % account
        gold_dic = prredis.hgetall(gold_user_table)
        if not gold_dic:
            gold_dic['nickname'] = user_info['nickname']
            gold_dic['uid'] = uid
            gold_dic['agent'] = agentid
            gold_dic['account'] = account
        gold_dic['cur_diamond_num'] = roomcard
        gold_dic['first_log_date'] = reg_date
        gold_dic['last_log_date'] = last_login_date
        # gold_dic['buy_diamond_stream'] = 'buy_record?account=%s' % account
        gold_dic['buy_gold_stream'] = 'buy_record?account=%s' % account
        gold_dic['gold_record_stream'] = 'journal?account=%s' % account
        money = prredis.get(GOLD_BUY_RECORD_ACCOUNT_MOENY_SUM % account)
        if money:
            money = float(money)/100
        gold_dic['buy_gold_num'] = money
        if not gold_dic.get('agent', ''):
            gold_dic['agent'] = agentid
        # 财富排行
        rank = prredis.zrevrank(GOLD_MONEY_RANK_WITH_AGENT_ZSET % gold_dic['agent'],
                                account)
        if rank != None:
            gold_dic['agent_wealth_rank'] = int(rank) + 1
        else:
            gold_dic['agent_wealth_rank'] = u'无'
        # 胜局排行
        rank = prredis.zrevrank(GOLD_WIN_RANK_WITH_AGENT_ZSET % gold_dic['agent'],
                                account)
        if rank != None:
            gold_dic['agent_win_rank'] = int(rank) + 1
        else:
            gold_dic['agent_win_rank'] = u'无'
        # 胜率
        win = prredis.llen(GOLD_RECORD_ACCOUNT_WIN_LIST % account)
        total = prredis.llen(GOLD_RECORD_ACCOUNT_TOTAL_LIST % account)
        if total:
            gold_dic['gold_win_rate'] = '%.2f' % (win/float(total)*100 if total else 0)
        gold_dic['cur_gold_num'] = gold
        # 如果是查询,则对结果进行过滤
        if search:
            if search == gold_dic['uid'] or search == gold_dic['phone_num'] or \
                            search == gold_dic['account'] or search in gold_dic['nick_name'] or search == gold_dic['agent']:
                data_list.append(gold_dic)
        else:
            data_list.append(gold_dic)
    count = len(data_list)
    # 如果大于10000条数据做一个金币用户表data缓存
    if count >= LIST_CACHE_MAXNUM:
        data_cache = json.dumps(data_list)
        redis.set('gold:data:cache', data_cache)
        # 缓存5分钟
        redis.expire('gold:data:cache', LIST_CACHE_TTL)
    return {"count": count, "data": data_list}


# 金币场运营表
def getGoldOperateInfos(redis,selfUid,startDate,endDate,niuniu_type):
    prredis = getPrivateRedisInst(redis, MASTER_GAMEID)
    try:
        startDate = datetime.strptime(startDate, '%Y-%m-%d')
        endDate = datetime.strptime(endDate, '%Y-%m-%d')
    except:
        weekDelTime = timedelta(7)
        weekBefore = datetime.now() - weekDelTime
        startDate = weekBefore
        endDate = datetime.now()
    deltaTime = timedelta(1)
    res = []
    while startDate <= endDate:
        dateStr = endDate.strftime('%Y-%m-%d')
        gameid = '555'
        if niuniu_type == '1':
            gameid = '555'
        elif niuniu_type == '2':
            gameid = '556'
        elif niuniu_type == '3':
            gameid = '666'
        if prredis.exists(GOLD_OPERATE % (gameid, dateStr)):
            info = prredis.hgetall(GOLD_OPERATE % (gameid, dateStr))
            info['online_user_max'] = redis.hget(GOLD_ONLINE_MAX_ACCOUNT_TABLE % (gameid, dateStr), 'count')
            info['date'] = dateStr
            info['buy_gold_total'] = redis.get(DAILY_GOLD2_SUM % dateStr)
            info['buy_money'] = redis.get(DAILY_GOLD2_MONEY_SUM % dateStr)
            info['buy_money'] = float(info['buy_money']) / 100 if info['buy_money'] else 0
            info['buy_gold_count'] = redis.scard(DAILY_USER_GOLD2_SET % dateStr)
            info['buy_gold_people_num'] = 'buy_record_info?date=%s' % dateStr
            room_num = 0
            if datetime.now().strftime("%Y-%m-%d") == dateStr:
                info['online_user'] = redis.scard(GOLD_ONLINE_ACCOUNT_SET % gameid)
                for roomid in redis.smembers(GOLD_ONLINE_ROOM_SET % gameid):
                    room_table = ROOM2SERVER % roomid
                    pl_count = redis.hget(room_table, 'playerCount')
                    if not pl_count or pl_count <= '0':
                        continue
                    room_num += 1
                info['room_count'] = room_num
            res.append(info)
        endDate -= deltaTime
    return {"count": 1, "data": res}



# 金币场运营表在线人数及在线房间数
def getOnlineOperateInfos(redis):
    prredis = getPrivateRedisInst(redis, MASTER_GAMEID)
    # 总当前在线人数
    online_people_sum = redis.scard(GOLD_ONLINE_ACCOUNT_SET_TOTAL)
    # 当前在线房间数
    online_room_num = 0
    for roomid in redis.smembers(GOLD_ONLINE_ROOM_SET_TOTAL):
        room_table = ROOM2SERVER % roomid
        pl_count = redis.hget(room_table, 'playerCount')
        if not pl_count or pl_count == '0':
            continue
        online_room_num += 1
    # online_room_num = redis.scard(GOLD_ONLINE_ROOM_SET_TOTAL)
    # 当前玩家金币总数
    user_current_gold_sum = 0
    for account in prredis.smembers(GOLD_ACCOUNT_SET_TOTAL):
        user_table = redis.get(FORMAT_ACCOUNT2USER_TABLE % account)
        if not user_table:
            continue
        gold = redis.hget(user_table, 'gold')
        gold = int(gold) if gold else 0
        user_current_gold_sum += gold
    return online_people_sum, online_room_num, user_current_gold_sum

# 金币场在线AI总数及在线AI房间数
def getOnlineAIInfos(redis):
    online_ai_sum = 0
    cur_ai_gold_sum = 0
    online_ai_room_num_set = set()
    for key in redis.smembers('users:robot:accounts:set'):
        online, account, gold= redis.hmget(key, 'isOnline', 'account', 'gold')
        gold = int(gold) if gold else 0
        cur_ai_gold_sum += gold
        if online == '1':
            online_ai_sum += 1
            if redis.exists(GOLD_ROOM_ACCOUNT_KEY % account):
                online_ai_room_num_set.add(redis.get(GOLD_ROOM_ACCOUNT_KEY % account))
    return online_ai_sum, len(online_ai_room_num_set), cur_ai_gold_sum

# 金币场AI数据总表
def getGoldAIInfos(redis,selfUid,startDate,endDate,grade):
    prredis = getPrivateRedisInst(redis, MASTER_GAMEID)
    try:
        startDate = datetime.strptime(startDate, '%Y-%m-%d')
        endDate = datetime.strptime(endDate, '%Y-%m-%d')
    except:
        weekDelTime = timedelta(7)
        weekBefore = datetime.now() - weekDelTime
        startDate = weekBefore
        endDate = datetime.now()
    deltaTime = timedelta(1)
    res = []
    while startDate <= endDate:
        dateStr = endDate.strftime('%Y-%m-%d')
        info = {}
        join_ai_sum = prredis.scard(GOLD_AI_ACCOUNT_SET_BYDAY % dateStr)
        if join_ai_sum:
            ai_room_sum = prredis.scard(GOLD_AI_ROOM_SET_BYDAY % dateStr)
            ai_gold_sum = prredis.llen(GOLD_AI_RECORD_LIST_BYDAY % dateStr)
            info['date'] = dateStr
            info['join_ai_sum'] = join_ai_sum
            info['ai_room_sum'] = ai_room_sum
            info['ai_gold_sum'] = ai_gold_sum
            info['cur_ai_gold_num'] = redis.get('robot:gold:sum:%s' % dateStr)
            res.append(info)
        endDate -= deltaTime

    return {"count": len(res), "data": res}


def saveBuyGoldRecord(redis, account, data):
    """ 
        保存金币流水
    """
    try:
        if not redis.sismember(GOLD_ACCOUNT_SET_TOTAL, account):
            redis.sadd(GOLD_ACCOUNT_SET_TOTAL, account)
        prredis = getPrivateRedisInst(redis, MASTER_GAMEID)
        num = prredis.incr(GOLD_BUY_RECORD_COUNT_TABLE)
        record_key = GOLD_BUY_RECORD_TABLE % num
        pipe = prredis.pipeline()
        data['account'] = account
        pipe.hmset(record_key, data)
        pipe.expire(record_key, GOLD_ROOM_MAX_TIME)
        pipe.lpush(GOLD_BUY_RECORD_ACCOUNT_LIST % account, record_key)
        pipe.lpush(GOLD_BUY_RECORD_LIST_TOTAL, record_key)
        pipe.incr(GOLD_BUY_RECORD_ACCOUNT_GOLD_SUM % account, data['gold'])
        pipe.incr(GOLD_BUY_RECORD_ACCOUNT_MOENY_SUM % account, data['money'])
        pipe.execute()
        user_info = get_user_info(redis, account)
        if not user_info:
            return
        agentid = user_info['parentAg']
        gold = user_info['gold']
        prredis.zadd(GOLD_MONEY_RANK_WITH_AGENT_ZSET % agentid, account, gold)
    except Exception, ex:
        traceback.print_exc()


def player_add_gold(redis, account, gold):
    user_table = redis.get(FORMAT_ACCOUNT2USER_TABLE % account)
    if not user_table:
        return
    redis.hincrby(user_table, 'gold', gold)

    prredis = getPrivateRedisInst(redis, MASTER_GAMEID)
    user_info = get_user_info(redis, account)
    if not user_info:
        return
    agentid = user_info['parentAg']
    gold = user_info['gold']
    prredis.zadd(GOLD_MONEY_RANK_WITH_AGENT_ZSET % agentid, account, gold)

    return True


def player_set_gold(redis, account, gold):
    user_table = redis.get(FORMAT_ACCOUNT2USER_TABLE % account)
    if not user_table:
        return
    redis.hset(user_table, 'gold', gold)

    prredis = getPrivateRedisInst(redis, MASTER_GAMEID)
    user_info = get_user_info(redis, account)
    if not user_info:
        return
    agentid = user_info['parentAg']
    gold = user_info['gold']
    prredis.zadd(GOLD_MONEY_RANK_WITH_AGENT_ZSET % agentid, account, gold)

    return True


def do_PlayerWelfareSign(redis, account):
    """ 
        签到接口
    """
    today = datetime.now().strftime("%Y-%m-%d")
    key = WELFARE_USER_SIGN % (account, today)
    if redis.exists(key):
        return
    gold = 2000
    if not player_add_gold(redis, account, gold):
        return
    redis.set(key, 1)
    return gold


def doPatchSign(redis, account, date):
    """ 
        补签接口
        补签需要消耗2张房卡
    """
    user_info = get_user_info(redis, account)
    uid = user_info['uid']
    agentid = user_info['parentAg']
    roomcard = redis.get(USER4AGENT_CARD % (agentid, uid))
    roomcard = int(roomcard) if roomcard else 0

    if roomcard < PATCH_SIGN_FEE:
        return {'code': 1, 'msg': "钻石不足"}

    month = datetime.strptime(date, '%Y-%m-%d').month
    key = WELFARE_USER_PATCH_SIGN % (account, month)

    if redis.sismember(key, date):
        return {'code': 1, 'msg': "已补签过"}

    times = redis.scard(key)
    # 每月补签次数是否达到上限
    if times and int(times) > PATCH_SIGN_MAX:
        return {'code': 1, 'msg': "当月补签已达上限"}
    redis.sadd(key, date)
    return {'code': 0, 'msg': "补签成功"}


def doWelfareById(redis, uid, account, id):
    """ 
        福利
    """
    today = datetime.now().strftime("%Y-%m-%d")
    if id == '2':
        playerCoin = redis.hget(FORMAT_USER_TABLE % uid, 'gold')
        playerCoin = playerCoin if playerCoin else 0
        if int(playerCoin) >= SIGN_LINE:
            return {'code': 1, 'msg': u'未达到低保线无法领取'}
        key = WELFARE_USER_INSURANCE % (account, today)
        if redis.llen(key) >= SIGN_MAX:
            return {'code': 1, 'msg': u'已经领取了 {0} 次'.format(SIGN_MAX)}
        redis.lpush(key, SIGN_COINNUM)
        player_add_gold(redis, account, SIGN_COINNUM)
    elif id == '1':
        # 新手礼包
        if redis.hget(GOLD_REWARD_NEW_PRESENT_HASH, account) == MESSION_STATUS_OVER:
            return {'code': 1, 'msg': u'您已领取，无法再次领取'}
        redis.hset(GOLD_REWARD_NEW_PRESENT_HASH, account, MESSION_STATUS_OVER)
    elif id == '0':
        # 每日首冲奖励
        if not redis.sismember(DAILY_USER_GOLD2_SET % today, account):
            return {'code': 1, 'msg': u'您今日还未完成首冲'}
        elif redis.hget(GOLD_REWARD_DAY_BUY_GOLD_HASH % today, account) == MESSION_STATUS_OVER:
            return {'code': 1, 'msg': u'您已领取，无法再次领取'}
        redis.hget(GOLD_REWARD_DAY_BUY_GOLD_HASH % today, account, MESSION_STATUS_OVER)

    return {'code': 0, 'msg': u'领取成功'}


def doSignRewardById(redis, uid, account, id):
    """ 
        签到奖励
    """
    today = datetime.now().strftime("%Y-%m-%d")
    if id == '0':
        # 七天奖励
        pass
    elif id == '1':
        # 十五天奖励
        pass
    elif id == '2':
        # 月奖励
        pass
    return {'code': 0, 'msg': u'领取成功'}


def getJournal(redis, account):
    """

    """
    prredis = getPrivateRedisInst(redis, MASTER_GAMEID)
    res = []
    for table in prredis.lrange(GOLD_RECORD_ACCOUNT_TOTAL_LIST % account, 0, -1):
        info = prredis.hgetall(table)
        if not info.get('start_time', ''):
            continue
        info['rid'] = table.split(':')[4]
        info['start_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(info['start_time']) / 1000))
        info['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(info['end_time']) / 1000))
        res.append(info)
    return res

def getBuyGoldRecord(redis, account):
    """
        
    """
    prredis = getPrivateRedisInst(redis, MASTER_GAMEID)
    res = []
    for table in prredis.lrange(GOLD_BUY_RECORD_ACCOUNT_LIST % account, 0, -1):
        info = prredis.hgetall(table)
        info['money'] = float(info['money'])/100
        res.append(info)
    return res


def getBuyGoldAccounts(redis, date):
    """

    """
    res = []
    for account in redis.smembers(DAILY_USER_GOLD2_SET % date):
        info = {}
        info['date'] = date
        info['gold'] = redis.get(DAILY_ACCOUNT_GOLD2_SUM % (account, date))
        money = redis.get(DAILY_ACCOUNT_GOLD2_MONEY_SUM % (account, date))
        info['money'] = float(money) / 100
        info['account'] = account
        res.append(info)
    return res

GOLD_RANK_CACHE = 'gold:rank:cache:%s'


def first_day_of_week():
    """ 
        获取本周第一天
    """
    return date.today() - timedelta(days=date.today().weekday())


def get_gold_week_win_rank(redis, groupid):
    first = first_day_of_week()
    last = first + timedelta(7)
    keys = []
    while first <= last:
        keys.append(GOLD_WIN_RANK_WITH_AGENT_ZSET_BYDAY % (groupid, first.strftime("%Y-%m-%d")))
        first += timedelta(1)
    redis.zunionstore('gold:win:rank:%s:thisweek:zset' % groupid, keys, aggregate='MAX')
    return redis.zrevrange('gold:win:rank:%s:thisweek:zset' % groupid, 0, 10 - 1, True)


def get_gold_rank(redis, groupid, account):
    """
        获取排行榜        
    """
    sortby = 'week'

    prredis = getPrivateRedisInst(redis, MASTER_GAMEID)
    today = datetime.now().strftime("%Y-%m-%d")

    # if redis.exists(GOLD_RANK_CACHE % account):
    #     return json.loads(redis.get(GOLD_RANK_CACHE % account))

    res = {}
    res['gold_rank'] = []
    res['win_rank'] = []
    my_user_info = get_user_info(redis, account)

    # 财富排行榜
    rank = 0
    for _account, value in prredis.zrevrange(GOLD_MONEY_RANK_WITH_AGENT_ZSET % groupid, 0, 10 - 1, True):
        rank += 1
        value = int(value)
        user_info = get_user_info(redis, _account)
        if not user_info:
            continue
        res['gold_rank'].append({'rank': rank, 'nickname': user_info['nickname'], 'value': value,
                                 'account': _account, 'headImgUrl': user_info['headImgUrl']})

    myrank = prredis.zrevrank(GOLD_MONEY_RANK_WITH_AGENT_ZSET % groupid, account)
    myvalue = prredis.zscore(GOLD_MONEY_RANK_WITH_AGENT_ZSET % groupid, account)
    if my_user_info and myrank != None:
        res['gold_rank'].append({'rank': int(myrank)+1, 'nickname': my_user_info['nickname'], 'value': myvalue,
                                'account': account, 'headImgUrl': my_user_info['headImgUrl'], 'self': '1'})
    else:
        res['gold_rank'].append({'nickname': my_user_info['nickname'],
                                'account': account, 'headImgUrl': my_user_info['headImgUrl'], 'self': '1'})
    # 胜局排行榜
    rank = 0
    for _account, value in get_gold_week_win_rank(prredis, groupid):
        rank += 1
        value = int(value)
        user_info = get_user_info(redis, _account)
        if not user_info:
            continue
        res['win_rank'].append({'rank': rank, 'nickname': user_info['nickname'], 'value': value,
                                'desc': '本周胜局', 'account': _account, 'headImgUrl': user_info['headImgUrl']})
    myrank = prredis.zrevrank('gold:win:rank:%s:thisweek:zset' % groupid, account)
    myvalue = prredis.zscore('gold:win:rank:%s:thisweek:zset' % groupid, account)
    if my_user_info and myrank != None:
        res['win_rank'].append({'rank': int(myrank)+1, 'nickname': my_user_info['nickname'], 'value': myvalue,
                                'desc': '本周胜局', 'account': account, 'headImgUrl': my_user_info['headImgUrl'],
                                'self': '1'})
    else:
        res['win_rank'].append({'nickname': my_user_info['nickname'],
                                'account': account, 'headImgUrl': my_user_info['headImgUrl'], 'self': '1'})
    redis.set(GOLD_RANK_CACHE % account, json.dumps(res))
    redis.expire(GOLD_RANK_CACHE % account, 300)
    return res


def first_day_of_month():
    """ 
        获取本月第一天
    """
    day = date.today().strftime('%d')
    day = int(day)
    return date.today() - timedelta(days=day-1)


def get_welfare_info(redis, account):
    today = datetime.now().strftime("%Y-%m-%d")
    first = first_day_of_month()
    last = date.today() - timedelta(days=1)
    res = copy.deepcopy(WELFARE_CONFIG)
    res['date'] = today
    res['signed'] = []
    res['unsinged'] = []
    # 今天是否签到
    if redis.exists(WELFARE_USER_SIGN % (account, today)):
        res['issigned'] = 1
    else:
        res['issigned'] = 0

    while first <= last:
        if redis.exists(WELFARE_USER_SIGN % (account, first)):
            res['signed'].append(first.strftime('%d'))
        elif redis.sismember(WELFARE_USER_PATCH_SIGN % (account, first.strftime("%m")), first.strftime('%Y-%m-%d')):
            res['signed'].append(first.strftime('%d'))
        else:
            res['unsinged'].append(first.strftime('%d'))
        first += timedelta(1)

    # 七天奖励
    if not redis.exists(GOLD_WELFARE_SIGN_7DAYS):
        res['rewardlist'][0]['status'] = MESSION_STATUS_NO
    elif redis.hget(GOLD_WELFARE_SIGN_7DAYS, account) == MESSION_STATUS_OVER:
        res['rewardlist'][0]['status'] = MESSION_STATUS_OVER
    else:
        res['rewardlist'][0]['status'] = MESSION_STATUS_OK

    # 十五天奖励
    if not redis.exists(GOLD_WELFARE_SIGN_15DAYS):
        res['rewardlist'][0]['status'] = MESSION_STATUS_NO
    elif redis.hget(GOLD_WELFARE_SIGN_15DAYS, account) == MESSION_STATUS_OVER:
        res['rewardlist'][0]['status'] = MESSION_STATUS_OVER
    else:
        res['rewardlist'][0]['status'] = MESSION_STATUS_OK

    # 月奖励
    if not redis.exists(GOLD_WELFARE_SIGN_MONTH):
        res['rewardlist'][0]['status'] = MESSION_STATUS_NO
    elif redis.hget(GOLD_WELFARE_SIGN_MONTH, account) == MESSION_STATUS_OVER:
        res['rewardlist'][0]['status'] = MESSION_STATUS_OVER
    else:
        res['rewardlist'][0]['status'] = MESSION_STATUS_OK

    # 每日首冲奖励
    if not redis.sismember(DAILY_USER_GOLD2_SET % today, account):
        res['messionlist'][0]['status'] = MESSION_STATUS_NO
        res['messionlist'][0]['parent_mode'] = CHECK_MALL
    else:
        if redis.hget(GOLD_REWARD_DAY_BUY_GOLD_HASH % today, account) == MESSION_STATUS_OVER:
            res['messionlist'][0]['status'] = MESSION_STATUS_OVER
        else:
            res['messionlist'][0]['status'] = MESSION_STATUS_OK

    # 新手礼包
    if redis.hget(GOLD_REWARD_NEW_PRESENT_HASH, account) == MESSION_STATUS_OVER:
        res['messionlist'][1]['status'] = MESSION_STATUS_OVER
    else:
        res['messionlist'][1]['status'] = MESSION_STATUS_OK

    # 破产补助
    key = WELFARE_USER_INSURANCE % (account, today)
    if not redis.exists(WELFARE_USER_INSURANCE % (account, today)):
        res['messionlist'][2]['status'] = MESSION_STATUS_OK
    else:
        if redis.llen(key) >= SIGN_MAX:
            res['messionlist'][2]['status'] = MESSION_STATUS_OVER
        else:
            res['messionlist'][2]['status'] = MESSION_STATUS_OK

    return res
