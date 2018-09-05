#-*- coding:utf-8 -*-
#!/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    捕鱼模块模型
"""
from web_db_define import *
from admin  import access_module
from datetime import datetime,timedelta
from config.config import *
from common import convert_util,log_util,string_util
from common.log import *
from common.utilt import formatCredit,ServerPagination
import random
from datetime import datetime,timedelta
from operator import itemgetter
import json
import time

#房间数据字段
FISH_FIELDS = ('room_id','room_name','min_coin','max_coin','base_coin',\
               'max_base_coin','step_base_coin','isTrail','max_player_count',\
               'status','ip_mask','need_coin','coin_value','tax_rate','get_rate',\
               'fish_need_count','fish_limit_count','max_add','min_add','max_ticket_count','ticket_wait_time'
               )
#投注记录字段
BET_FIELDS = ('')

#充值记录字段
RECHARGE_FIELDS = ('')

#在线列表要显示的数据
FISH_ONLINE_FIELDS = ('nickname','headImgUrl','parentAg','lastLoginClientType','coin')

#捕鱼房间列表可操作列表
FISH_OP_LIST = [
                    {'url':BACK_PRE+'/fish/room/modify','txt':'修改','method':'GET'},\
                    {'url':BACK_PRE+'/fish/room/delete','txt':'删除','method':'POST'},\
                    # {'url':BACK_PRE+'/game/editDesc','txt':'规则介绍修改','method':'GET'}\
]

#投注明细可操作列表
BET_OP_LIST = {
        'url':BACK_PRE+'/fish/bet/replay','txt':'查看回放','method':'POST'
}

#投注记录查询映射
SEARCH_KEY_2_TABLE = {
    'room_id'           :       FISH_BET_DATA_DETAIL4ROOM,
    'user_id'           :       ''
}

def getItemListInfo(redis):
    iids = redis.smembers('item:id:set')
    data = []
    for iid in iids: 
        dic = redis.hgetall('attrs:itemid:%s:hesh'%iid)
        dic['item_id'] = int(iid)
        data.append(dic)

    return json.dumps({'count':len(data),'data':data})

def getPresetValueInfo(redis):
    return {
            "preset_value":redis.get('fish:preset:value'),
            "down_chance":redis.get('fish:down:chance'),
            "up_chance":redis.get('fish:up:chance'),
            "diff_value":redis.get('play:difference:value') 
    }

def setStatisticZero(redis,uid):
    redis.set('user:%s:play:in'%uid,0)
    redis.set('user:%s:play:out'%uid,0)

def setStatisticZeroTest(redis,uid):
    redis.set('test:%s:play:in'%uid,0)
    redis.set('test:%s:play:out'%uid,0)

# 新手场玩入玩出统计
def getFishStatisTestInfo(redis):
    uids = redis.smembers('fish:test:player:set')
    data = []
    z_cost = 0   
    z_gain = 0
    z_play_in = 0
    z_play_out = 0
    for uid in uids:
        dic = {}
        dic['uid'] = uid
        dic['cost_coin_sum'] = redis.get('test:%s:cost:sum'%uid)
        dic['gain_coin_sum'] = redis.get('test:%s:gain:sum'%uid)
        dic['play_in_sum'] = redis.get('test:%s:play:in'%uid)
        dic['play_out_sum'] = redis.get('test:%s:play:out'%uid)
        dic['cur_rate'] = round(float(dic['play_out_sum'] or 0)/(int(dic['play_in_sum'] or 1)),3)
        dic['pre_rate'] = redis.get('fish:preset:value') or 0.995
        dic['under_rate'] = redis.get('fish:up:chance') or 1.10
        dic['above_rate'] = redis.get('fish:down:chance') or 0.99
        dic['play_difference_value'] = redis.get('play:difference:value') or 100000000 
        data.append(dic)
        z_cost += int(dic['cost_coin_sum'] or 0)
        z_gain += int(dic['gain_coin_sum'] or 0)
        z_play_in += int(dic['play_in_sum'] or 0)
        z_play_out += int(dic['play_out_sum'] or 0)

    return json.dumps({'count':len(data),'data':data,'z_cost':z_cost,'z_gain':z_gain,'z_play_in':z_play_in,'z_play_out':z_play_out})

# 总玩入玩出统计
def getFishCoinAndWarheadStatis(redis):
    uids = redis.smembers('fish:coin:player:set')
    data = []
    z_cost = 0   
    z_gain = 0
    z_play_in = 0
    z_play_out = 0
    for uid in uids:
        dic = {}
        dic['uid'] = uid
        dic['cost_coin_sum'] = redis.get('user:%s:cost:sum'%uid)
        dic['gain_coin_sum'] = redis.get('user:%s:gain:sum'%uid)
        dic['play_in_sum'] = redis.get('user:%s:play:in'%uid)
        dic['play_out_sum'] = redis.get('user:%s:play:out'%uid)
        try:
            dic['cur_rate'] = round(float(dic['play_out_sum'] or 0)/(int(dic['play_in_sum'] or 1)),3)
        except Exception as e:
            print str(e)
        dic['pre_rate'] = redis.get('fish:preset:value') or 0.995
        dic['under_rate'] = redis.get('fish:up:chance') or 1.10
        dic['above_rate'] = redis.get('fish:down:chance') or 0.99
        dic['play_difference_value'] = redis.get('play:difference:value') or 100000000 
        data.append(dic)
        z_cost += int(dic['cost_coin_sum'] or 0)
        z_gain += int(dic['gain_coin_sum'] or 0)
        z_play_in += int(dic['play_in_sum'] or 0)
        z_play_out += int(dic['play_out_sum'] or 0)

    return json.dumps({'count':len(data),'data':data,'z_cost':z_cost,'z_gain':z_gain,'z_play_in':z_play_in,'z_play_out':z_play_out})

'''
def getFishCoinAndWarheadStatis(redis):
    pcs = redis.get('produce:coin:sum')
    ecs = redis.get('earnings:coin:sum')
    pws = redis.get('produce:warhead:sum')
    ews = redis.get('earnings:warhead:sum')
    res = {
            "count":1,
            "data":[{
                "diamond_charge_sum":redis.get('fish:diamond:charge:sum'),
                "diamond_to_coin":redis.get('fish:diamond2coin:sum'),
                "produce_coin":pcs,
                "earnings_coin":ecs,
                "produce_warhead":pws,
                "earnings_warhead":ews,
                "coin_rate":round(float(pcs)/float(int(ecs) or 1) ,3) if ecs else 0,
                "warhead_rate":round(float(pws)/float(int(ews) or 1) ,3) if ews else 0,
                "preset_value":redis.get('fish:preset:value'),
                "greater_than":redis.get('fish:down:chance'),
                "less_than":redis.get('fish:up:chance'),
            }]
    }

    return json.dumps(res)
'''

def get_room_list(redis,searchId=False,op=False):
    """
    获取捕鱼房间列表1
    params: redis,searchId(是否查询指定列表)
    """
    room_ids = redis.lrange(FISH_ROOM_LIST,0,-1)
    room_list = []
    log_debug('[try get_room_list] room_ids[%s]'%(room_ids))
    trans2IntList = ('min_coin','max_coin','base_coin','max_base_coin','step_base_coin','max_player_count')
    for room_id in room_ids:
        room_info = redis.hgetall(FISH_ROOM_TABLE%(room_id))
        room_info['room_id'] = int(room_id)
        room_info['need_coin']  = room_info['need_coin']  if 'need_coin'  in room_info.keys() else 0
        room_info['coin_value'] = room_info['coin_value'] if 'coin_value' in room_info.keys() else 0
        ft = room_info.get('field_type')
        if ft:
            room_info['field_type'] = int(ft)
        for transkey in trans2IntList:
            if room_info[transkey]:
                room_info[transkey] = convert_util.to_int(room_info[transkey])
        if op:
            room_info['op'] = FISH_OP_LIST
        room_list.append(room_info)
    room_list = sorted(room_list, key=itemgetter('room_id'))
    if not op:
        return room_list
    count = len(room_list)
    log_debug('[try get_room_list] dataLen[%s] room_list[%s]'%(count,room_list))
    return {'data':room_list,'count':count}

def create_fish_room(redis,roomInfo):
    """
    创建捕鱼房间
    :params: redis,
    :params: roomInfo(创建的房间信息)
    """
    channel_id = roomInfo['room_id']
    room_table = FISH_ROOM_TABLE%(channel_id)
    log_util.debug('[try create_fish_room] room_id[%s] room_table[%s]'%(channel_id,room_table))
    pipe  =  redis.pipeline()
    try:
        pipe.hmset(room_table,roomInfo)
        pipe.sadd(FISH_ROOM_ID_SETS,channel_id)
        pipe.sadd(GAMEID_SET,channel_id)
        pipe.lpush(FISH_ROOM_LIST,channel_id)
    except Exception,e:
        log_util.error('[try create_fish_room] room_id[%s] create error.reason[%s]'%(channel_id,e))
        return

    pipe.execute()

def modify_fish_room(redis,roomInfo):
    """
    创建捕鱼房间
    params: redis,roomInfo(创建的房间信息)
    """
    channel_id = roomInfo['room_id']
    room_table = FISH_ROOM_TABLE%(channel_id)
    log_util.debug('[try modify_fish_room] room_id[%s] room_table[%s]'%(channel_id,room_table))
    pipe  =  redis.pipeline()
    pipe.hmset(room_table,roomInfo)
    pipe.execute()

def delete_fishroom(redis,room_id):
    """
    删除捕鱼房间
    :params redis 数据库实例
    :params room_id 捕鱼房间ID
    """
    room_table = FISH_ROOM_TABLE%(room_id)
    if not redis.exists(room_table):
        log_util.debug('[try delete_fishroom] room_table[%s] already delete.'%(room_table))
        return
    pipe = redis.pipeline()
    try:
        pipe.delete(room_table)
        pipe.delete(FISH_BET_DATA4ROOM%(room_table))
        pipe.lrem(FISH_ROOM_LIST,room_id)
        pipe.srem(GAMEID_SET,room_id)
        for day_key in redis.keys(FISH_BET_DATA4DAY4ROOM%(room_id,'*')):
            pipe.delete(day_key)
    except Exception,e:
        log_util.error('[try delete_fishroom] delete room[%s] error.reason[%s]'%(room_id,e))
        return

    pipe.execute()

def get_bet_list(redis,startDate,endDate,room_id,user_id,page_info,sort_info,userId=None,groupId=None):
    """
    获取捕鱼投注明细数据
    params: reids,condition(查询条件列表)
    """
    try:
        startDate = datetime.strptime(startDate,'%Y-%m-%d')
        endDate   = datetime.strptime(endDate,'%Y-%m-%d')
    except:
        weekDelTime = timedelta(7)
        weekBefore = datetime.now()-weekDelTime
        startDate = weekBefore
        endDate   = datetime.now()

    deltaTime = timedelta(1)

    bet_table = ALL_FISH_BET_DATA_DETAIL
    sum_table = ALL_FISH_BET_DATA4DAY
    if user_id:#根据玩家ID搜索
        bet_table = PLAYER_FISH_BET_DATA_DETAIL4DAY%(user_id,'%s')
        sum_table= PLAYER_FISH_BET_DATA4DAY%(user_id,'%s')

    elif room_id:#根据房间号查询
        bet_table = FISH_BET_DATA_DETAIL4ROOM%(room_id,'%s')
        sum_table = FISH_BET_DATA4DAY4ROOM%(room_id,'%s')

    res,totalBetMoney,totalWinLostMoney,winLostRate,totalTickets = [],0,0,0,0
    total_datas = []
    now_time = datetime.now()
    log_debug('[try get_bet_list] startDate->[%s]'%(datetime.now()))
    while endDate >= startDate:
        if endDate > now_time:#不查没有数据的时间
            endDate-=deltaTime
            continue
        dateStr = endDate.strftime('%Y-%m-%d')
        bet_records = redis.lrange(bet_table%(dateStr),0,-1)
        #记录总投注额
        betMoney,winLostMoney,ticket_total = redis.hmget(sum_table%(dateStr),('bet','profit','ticket'))
        betMoney = convert_util.to_float(betMoney)
        winLostMoney = convert_util.to_float(winLostMoney)
        ticket_total = convert_util.to_float(ticket_total)

        totalBetMoney+=betMoney
        totalWinLostMoney+=winLostMoney
        totalTickets+=ticket_total
        #索引出所有数据
        total_datas.extend(bet_records)

        endDate -= deltaTime

    total = len(total_datas)
    for bet_record in total_datas:
        bet_record = eval(bet_record)
        bet_keys = bet_record.keys()
        betInfo = {}
        betInfo['win'] = bet_record['win']
        betInfo['bet_id'] = bet_record['bet_id']
        betInfo['room_id'] = bet_record['room_id']
        betInfo['bet'] = bet_record['bet']
        betInfo['uid'] = bet_record['uid']
        betInfo['datetime'] = bet_record['datetime']
        betInfo['init_coin'] = int(bet_record['init_coin']) if 'init_coin' in bet_keys else 0
        betInfo['add_coin'] = bet_record['add_coin'] if 'add_coin' in bet_keys else 0
        betInfo['login_time'] = bet_record['login_time'] if 'login_time' in bet_keys else '未知'
        betInfo['add_ticket'] = bet_record['add_ticket'] if 'add_ticket' in bet_keys else 0
        betInfo['op'] = []
        betInfo['op'].append(BET_OP_LIST)
        res.append(betInfo)

    if totalWinLostMoney:
        winLostRate = round(((totalBetMoney-totalWinLostMoney)/totalBetMoney)*100,2)
        if winLostRate > 0.00:
            winLostRate=-winLostRate
        else:
            winLostRate=abs(winLostRate)

    if sort_info['sort_name']:
        #如果排序
        res = sorted(res, key=itemgetter(sort_info['sort_name']),reverse=FONT_CONFIG['STR_2_SORT'][sort_info['sort_method']])

    #分页处理，客户端每次只渲染15条
    res = ServerPagination(res,page_info['page_size'],page_info['page_number'])
    log_util.debug('[try get_bet_list] endDtime->[%s]'%(datetime.now()))
    return {'result':res,'count':total,'betTotal':totalBetMoney,'ticketTotal':totalTickets,'winLostTotal':totalWinLostMoney,'winLostRate':winLostRate}

def get_bet_reports(redis,startDate,endDate,agent_id,userId=None,groupId=None):
    """
    获取捕鱼投注明细数据
    params: reids,condition(查询条件列表)
    """
    if agent_id:
        #按代理查询
        agent_lines = [agent_id]
    else:
        agent_lines = redis.smembers(AGENT_CHILD_TABLE%(1))

    try:
        startDate = datetime.strptime(startDate,'%Y-%m-%d')
        endDate   = datetime.strptime(endDate,'%Y-%m-%d')
    except:
        weekDelTime = timedelta(7)
        weekBefore = datetime.now()-weekDelTime
        startDate = weekBefore
        endDate   = datetime.now()

    tempStartDate,tempEndDate = startDate,endDate
    deltaTime = timedelta(1)
    now_time = datetime.now()
    res= []

    for agent in agent_lines:
        betInfo = {}
        totalBetMoney,totalWinLostMoney = 0,0
        startDate,endDate = tempStartDate,tempEndDate
        agent_account = redis.hget(AGENT_TABLE%(agent),'account')
        while endDate >= startDate:
            if endDate > now_time:
                endDate-=deltaTime
                continue
            dateStr = endDate.strftime('%Y-%m-%d')
            betMoney,winLostMoney = redis.hmget((AGENT_FISH_BET_DATA4DAY%(agent,dateStr)),('bet','win'))
            if not betMoney:
                betMoney = 0
            if not winLostMoney:
                winLostMoney = 0
            betMoney,winLostMoney = float(betMoney),float(winLostMoney)
            totalBetMoney+=betMoney
            totalWinLostMoney+=winLostMoney

            endDate -= deltaTime
        betInfo['agent_id'] = agent
        betInfo['agent_account'] = agent_account
        betInfo['bet'] = totalBetMoney
        betInfo['win'] = totalWinLostMoney
        res.append(betInfo)

    return {'data':res,'count':len(res)}

def get_recharge_list(redis,condition=[]):
    """
    获取金币充值列表
    params: redis,condition(查询条件)
    """
    pass

def get_fish_room_info(redis,room_id):
    """
    获取捕鱼房间信息
    params: redis, room_id
    """
    return redis.hgetall(FISH_ROOM_TABLE%(room_id))

def get_replay_info(redis,replay_id):
    """
    获取当局游戏的回放记录
    params: redis,replay_id(投注记录ID)
    """
    replayData = []
    datas = redis.zrangebyscore(PLAYER_REPLAY_SET, int(replay_id), int(replay_id))

    return {"data":eval(",".join(datas))}

def get_fish_online(redis,lang):
    """
    获取捕鱼在线玩家数据
    params:redis,lang
    """
    online_list = []

    online_members = redis.smembers(ONLINE_ACCOUNTS_TABLE4FISH)
    if not online_members:
        return {
            'count' :   0,   \
            'data'  :   online_list
        }
    for online_member in online_members:
        onLineTable = FORMAT_CUR_USER_GAME_ONLINE%(online_member)
        date,roomTag,serviceTag,ip = redis.hmget(onLineTable,\
                                                        ('date','game','serviceTag','ip'))
        account2user_table = FORMAT_ACCOUNT2USER_TABLE%(online_member) #从账号获得账号信息，和旧系统一样
        table = redis.get(account2user_table)
        userId = table.split(':')[1]
        name,imgUrl,parentAg,clientKind,coin = redis.hmget(table,FISH_ONLINE_FIELDS)
        if not coin:
            coin = 0
        online_list.append({
                'id'            :       userId,
                'account'       :       online_member,
                'name'          :       name,
                'coin'          :       coin,
                'roomTag'       :       roomTag if roomTag else '正在闲逛',
                'date'          :       date,
                'serverTag'     :       serviceTag,
                'clientKind'    :       lang.CLINET_KIND_TXTS[clientKind] if clientKind else '未知设备',
                'login_ip'      :       ip,
                'parentAg'      :       parentAg
        })

    return {
        'count' :   len(online_list),   \
        'data'  :   online_list
    }

def get_fish_sys_datas(redis,start_date,end_date):
    """
    获取捕鱼系统统计数据
    params: redis, start_date,end_date
    """
    start_date = convert_util.to_datetime(start_date)
    end_date = convert_util.to_datetime(end_date)

    one_day = timedelta(1)
    now_date = datetime.now()
    total_members = convert_util.to_int(redis.scard(ACCOUNT4WEIXIN_SET4FISH))
    total_recharge = convert_util.to_int(redis.get(FISH_SYSTEM_RECHARGE_TOTAL))
    data_list = []
    while end_date >= start_date:
        if end_date > now_date:
            end_date-=one_day
            continue
        today = convert_util.to_dateStr(end_date)
        today_reg = redis.scard(FORMAT_REG_DATE_TABLE4FISH%(today))
        today_active = convert_util.to_int(redis.scard(FORMAT_LOGIN_DATE_TABLE4FISH%(today)))
        today_sys_user_total,today_sys_coin_total = redis.hmget(FISH_SYSTEM_DATE_RECHARGE_TOTAL%(today),('recharge_user_total','recharge_coin_total'))
        today_sys_user_total = convert_util.to_int(today_sys_user_total)
        today_sys_coin_total  = convert_util.to_float(today_sys_coin_total)
        try:
            average_val = round(today_sys_coin_total/today_active,2)
        except:
            average_val = 0.00
        data_list.append({
            'today'         :   today,
            'today_reg'     :   today_reg,
            'today_active'  :   today_active,
            'today_sys_user_total' : today_sys_user_total,
            'today_sys_coin_total' : today_sys_coin_total,
            'average_val' :  average_val,
            'money_total' :  string_util.format_credit(total_recharge),
        })
        end_date-=one_day

    # 查詢奖池情况
    jackpot = redis.hgetall("fish:room:jackpot:hesh")
    if not jackpot:
        jackpot = {}

    __swit = {
        "5000": "十炮场",
        "5001": "百炮场",
        "5002": "千炮场",
        "5003": "万炮场"
    }
    result = []
    for gameId, value in jackpot.items():
        result.append({
            "name": __swit[gameId],
            "gameId": gameId,
            "value": value
        })
    timestamp = time.strftime("%Y-%m-%d", time.localtime())
    number = redis.get("fish:redpick:fish:%s:number" % timestamp) or 0
    return {'data':data_list, "water": result, "fishRedPick": number}

def get_fish_cal_data(redis):
    """
    获取捕鱼的每日数据更新
    """
    curTime = convert_util.to_dateStr(datetime.now())

    log_per_day = convert_util.to_int(redis.scard(FORMAT_LOGIN_DATE_TABLE4FISH%(curTime)))
    reg_per_day = convert_util.to_int(redis.scard(FORMAT_REG_DATE_TABLE4FISH%(curTime)))
    total_member = convert_util.to_int(redis.scard(ACCOUNT4WEIXIN_SET4FISH))
    login_per_rate = convert_util.to_int(redis.get("fish:per:login:rate"))
    recharge_per_rate = convert_util.to_int(redis.get("fish:per:recharge:rate"))
    share_per_day  = convert_util.to_int(redis.scard(FISH_FIRST_SHARE_PER_DAY_SET))
    total_share    = convert_util.to_int(redis.get(FISH_SHARE_TOTAL))
    log_util.debug('[get_fish_cal_data] log_per_day[%s] reg_per_day[%s] total_member[%s] login_per_rate[%s] recharge_per_rate[%s]'\
                        %(log_per_day,reg_per_day,total_member,login_per_rate,recharge_per_rate))

    return {
            'log_per_day'        :   log_per_day,
            'reg_per_day'        :   reg_per_day,
            'total_member'       :   total_member,
            'login_per_rate'     :   login_per_rate,
            'recharge_per_rate'  :   recharge_per_rate,
            'share_per_day'      :   share_per_day,
            'total_share'        :   total_share
    }

def check_spring_time(redis, active_id = False):
    '''
    检查是否春节活动时间
    active_id:
        福禄双收   1
        三阳开泰   2
        红包鱼     3
        答题       4
    '''
    curTime = convert_util.to_dateStr(datetime.now())
    key = ACTIVICE_SPRING_TIME if active_id == False else ACTIVE_CONFIG_ONE_HESH % active_id

    if active_id == False:
        springTime = redis.get(key)
        springTime = json.loads(springTime)
        start_date = springTime['from']
        end_date = springTime['to']
    else:
        springTime = redis.exists(key)
        start_date, end_date = redis.hmget(key, ('start_time', 'end_time'))


    if springTime:
        s_time = time.mktime(time.strptime(start_date, '%Y-%m-%d'))  # get the seconds for specify date
        e_time = time.mktime(time.strptime(end_date, '%Y-%m-%d'))
        log_time = time.mktime(time.strptime(curTime, '%Y-%m-%d'))
        if float(log_time) < float(s_time):
            return False, '活动未开始'
        if float(log_time) > float(e_time):
            return False, '活动已结束'
        return True, '活动开放中'
    else:
        return False, '活动未开始'
