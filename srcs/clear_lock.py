#-*- coding:utf-8 -*-
#!/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    DB初始化
"""

import sys
#sys.path.insert(0, 'mahjong')
sys.path.insert(0, 'server_common')
from web_db_define import *
from datetime import datetime,timedelta,time
#from admin import access_module
#from config.config import *
import redis
import hashlib

AGENT_COMPAY_RATE_DATE ='agent:%s:date:%s'

# 代理占成值集合表
AGENT_RATE_SET = 'agent:%s:rate:set'
# 房卡单价集合表
AGENT_ROOMCARD_PER_PRICE = 'agent:%s:roomcard:per:price'

def getInst(dbNum):
    global redisdb
    redisdb = redis.ConnectionPool(host="172.18.176.179", port=6379, db=dbNum, password='Fkkg65NbRwQOnq01OGMPy5ZREsNUeURm')
    #redisdb.connection_read_pool = redis.ConnectionPool(host="192.168.0.99", port=6000, db=dbNum, password='Fkkg65NbRwQOnq01OGMPy5ZREsNUeURm')
    return redis.Redis(connection_pool=redisdb)

redis = getInst(1)

#初始化管理账号
curTime = datetime.now()
pipe = redis.pipeline()

sysid = 1
# id


"""
    配置代理名称和房卡
    代理名称            ：       房卡数
"""
# print 'clean login pool...............'
# #print redis.srem(FORMAT_LOGIN_POOL_SET,'test38')
# print redis.smembers(FORMAT_LOGIN_POOL_SET)
# #redis.delete(FORMAT_LOGIN_POOL_SET)
# print 'clean success.......'

# """
# 查看捕鱼房间
# """
# print 'fish ids .........................'
# print redis.smembers(FISH_ROOM_ID_SETS)

# # print 'fish table 1'
#print redis.hgetall(FISH_ROOM_TABLE%(1))
# print redis.lrange(FISH_ROOM_LIST,0,-1)
# print redis.delete(FISH_ROOM_TABLE%('1'))
# print redis.delete(FISH_ROOM_ID_SETS)
# print redis.delete(FISH_ROOM_LIST)
# print redis.srem(GAMEID_SET,'5000')

# """
# 捕鱼投注明细
# """

# print redis.keys(ALL_FISH_BET_DATA_DETAIL%('*'))

#print redis.lrange("allFishBetDataDetail:day:2017-10-27:list",0,-1)

#print redis.keys(GM_CONTROL_DATA%('*'))

#print redis.hgetall("agentFishBetDayData:agent:363400:day:2017-11-01:hesh")

#print redis.lrange("GMControlData:uid:351:list",0,-1)



# print redis.delete(HALL_BRO_COUNT)
# print redis.delete(HALL_BRO_TABLE%("*"))
# print redis.delete(HALL_BRO_LIST)
# # print redis.delete(HALL_BRO_AG_LIST%("*"))
# for key in redis.keys(HALL_BRO_AG_LIST%('*')):
#      print redis.delete(key)
# print redis.delete(HALL_BRO_OUT_SET)
# print redis.delete(HALL_BRO_PLAY_SET)
# #print redis.smembers(GAME_DEFAULT_BIND)
# MEMBER_LIST_FIELDS = ('name','parentAg','roomCard','nickname','headImgUrl','last_login_date','last_logout_date','valid','open_auth')
# #pipe  = redis.pipeline()
# #hmset "test"
# redis_batch = redis.pipeline()
# print redis_batch.hmget("users:3075",MEMBER_LIST_FIELDS)

#print keys

#redis_batch.execute()
#AGENT_SALE_CARD_DATE

for key in redis.keys(AGENT_TABLE%('*')):
    agent_id = key.split(':')[2]
    if agent_id in ['1']:
        continue
    print 'agentId[%s] is add to set....'%(agent_id)
    redis.sadd(AGENT_ID_TABLE,agent_id)

startDate = datetime.strptime('2017-05-01','%Y-%m-%d')
endDate  = datetime.strptime('2017-11-30','%Y-%m-%d')
deltaTime = timedelta(1)
agent_ids = redis.smembers(AGENT_ID_TABLE) 
pipe = redis.pipeline()
now_time = datetime.now()
'''
批量刷新玩家的总售钻和总购钻记录
售钻记录表 ： AGENT_SALE_CARD_DATE
购钻记录表 :  AGENT_BUY_CARD_DATE
'''
for agent_id in agent_ids:
   print 'now setting agent_id[%s]'%(agent_id)
   startCopyDate = startDate
   totalBuy = 0
   while startCopyDate <= endDate:
       if startCopyDate > now_time:
           startCopyDate+=deltaTime
           continue
       dateStr = startCopyDate.strftime('%Y-%m-%d')
       buyReportTable = AGENT_SALE_CARD_DATE%(agent_id,dateStr)
       if not redis.exists(buyReportTable):
           startCopyDate+=deltaTime
           continue
       cardNums = redis.hget(buyReportTable,'cardNums')
       totalBuy+=int(cardNums)
       redis.hset(buyReportTable,'totalNums',totalBuy)
       print 'now setting agent_id[%s] table[%s] totalBuy[%s]'%(agent_id,buyReportTable,totalBuy)
       startCopyDate+=deltaTime
   
   print 'agent_id[%s] set total[%s]'%(agent_id,totalBuy)
   redis.set('agent:%s:sale:total'%(agent_id),totalBuy)

'''
生成代理日期索引
代理ID表 : AGENT_ID_TABLE
代理创建日期表 : AGENT_ID_CREATE_DATE
'''
AGENT_CREATE_DATE = "agent:create:date:%s"

for agent_id in redis.smembers[AGENT_ID_TABLE]:
    agent_create_date = redis.hget(AGENT_TABLE%(agent_id),'regDate')
    if not agent_create_date:
        continue 
    agent_create_date = agent_create_date.split(' ')[0]
    redis.sadd(AGENT_CREATE_DATE%(agent_create_date),agent_id)
    print 'agent_id[%s] is write to index date[%s].......'%(agent_id,agent_create_date)

