#!/usr/bin/env python
# -*- coding:utf-8 -*-

# ~*~ coding: utf-8 ~*~

"删除多余的代理房间"

import redis
import json
from datetime import datetime


def getInst(dbNum):
    global redisdb
    # redisdb = redis.ConnectionPool(host='172.18.176.179', port=6379, db=dbNum, password="Fkkg65NbRwQOnq01OGMPy5ZREsNUeURm")
    redisdb = redis.ConnectionPool(host='172.18.10.13', port=6379, db=dbNum,
                                   password="Fkkg65NbRwQOnq01OGMPy5ZREsNUeURm")
    # redisdb = redis.ConnectionPool(host='120.78.80.115', port=6379, db=dbNum, password="168joyvick")
    return redis.Redis(connection_pool=redisdb)

"""
答题题库
'activice:question:hesh'  {@id : @params}
"""
ACTIVICE_QUESTION_ALL_HESH = 'activice:question:hesh'
"""
答题完毕玩家的集合
SADD activice:question:answer:set
"""
ACTIVICE_QUESTION_ANSWER = 'activice:question:answer:set'
# 已经点了开始的玩家的集合
ACTIVICE_QUESTION_START = 'activice:question:start:hesh'

"""
答题格式
{
	'question': "问题1，请问xxxx？",
	'answer': [
		"答案1",
		"答案2",
		"答案3",
	],
	'formType': 1, 	#表单类型 ： 1单选  2多选
	'correct' : 0 	#正确答案序号,0代表第一个，1代表第二个 以此类推,多个用","分隔
}
"""
QUESTION_BANK = [
    {
        'id': 1,
        'question': "第一届春节联欢晚会是在那一年举办的？",
        'answer': [
            "A.1982年",
            "B.1983年",
            "C.1984年",
            "D.1985年",
        ],
        'formType': 1,
        'correct': '2'
    },

    {
        'id': 2,
        'question': "2018年的生肖是什么？",
        'answer': [
            "A.狗",
            "B.蛇",
            "C.羊",
            "D.龙",
        ],
        'formType': 1,
        'correct': '0'
    },

    {
        'id': 3,
        'question': "春节所在的这一月叫？",
        'answer': [
            "A.腊月",
            "B.正月",
            "C.阳月",
            "D.桂月",
        ],
        'formType': 1,
        'correct': '1'
    },

    {
        'id': 4,
        'question': "旧年的最后一天夜里不睡觉叫？",
        'answer': [
            "A.跨春",
            "B.守春",
            "C.守岁",
            "D.度春",
        ],
        'formType': 1,
        'correct': '2'
    },

    {
        'id': 5,
        'question': "春节人们喜欢在窗户上贴得各种剪纸叫什么？",
        'answer': [
            "A.窗纸",
            "B.窗花",
            "C.窗贴",
            "D.贴纸",
        ],
        'formType': 1,
        'correct': '1'
    },

    {
        'id': 6,
        'question': "在我国北方，年夜饭必不可少的一道食物是？",
        'answer': [
            "A.汤圆",
            "B.鱼",
            "C.饺子",
            "D.腊肉",
        ],
        'formType': 1,
        'correct': '2'
    },

    {
        'id': 7,
        'question': "国家海洋局决定，从2008年开始启动全国“海洋宣传日”活动，我国的“海洋宣传日”定为每年的（）？",
        'answer': [
            "A.7月7日",
            "B.7月18日",
            "C.9月8日",
            "D.9月18日",
        ],
        'formType': 1,
        'correct': '1'
    },

    {
        'id': 8,
        'question': "中国入海河流中的第一大河是（）？",
        'answer': [
            "A.长江",
            "B.黄河",
            "C.淮河",
            "D.珠江",
        ],
        'formType': 1,
        'correct': '0'
    },

    {
        'id': 9,
        'question': "中国大陆边缘的四海中，最浅的海是（）？",
        'answer': [
            "A.渤海 ",
            "B.黄海",
            "C.东海",
            "D.南海",
        ],
        'formType': 1,
        'correct': '0'
    },

    {
        'id': 10,
        'question': "我国鱼种最多的海区是（）？",
        'answer': [
            "A.渤海海区",
            "B.黄海海区",
            "C.东海海区",
            "D.南海海区",
        ],
        'formType': 1,
        'correct': '3'
    },

    {
        'id': 11,
        'question': "（）是世界第二大洋？",
        'answer': [
            "A.太平洋",
            "B.印度洋",
            "C.大西洋",
            "D.北冰洋",
        ],
        'formType': 1,
        'correct': '2'
    },

    {
        'id': 12,
        'question': "我国最大的群岛是（）？",
        'answer': [
            "A.舟山群岛",
            "B.西沙群岛",
            "C.长山群岛",
            "D.南沙群岛",
        ],
        'formType': 1,
        'correct': '0'
    },

    {
        'id': 13,
        'question': "捕获“冰美人”会触发什么特殊效果？",
        'answer': [
            "A.全屏冰冻",
            "B.全屏爆炸",
            "C.特殊炮弹",
            "D.没效果",
        ],
        'formType': 1,
        'correct': '0'
    },

    {
        'id': 14,
        'question': "“金鲨”是多少倍的鱼？",
        'answer': [
            "A.70",
            "B.60",
            "C.50",
            "D.40",
        ],
        'formType': 1,
        'correct': '3'
    },

    {
        'id': 15,
        'question': "下列哪条鱼是蓝色的？",
        'answer': [
            "A.剑鱼",
            "B.魔鲸",
            "C.蝴蝶鱼",
            "D.小丑鱼",
        ],
        'formType': 1,
        'correct': '1'
    },

    {
        'id': 16,
        'question': "捕获“聚宝龙龟”会触发什么特殊效果？",
        'answer': [
            "A.特殊炮弹奖励",
            "B.全屏爆炸",
            "C.摇钱树奖励",
            "D.无效果",
        ],
        'formType': 1,
        'correct': '2'
    },

    {
        'id': 17,
        'question': "“金龟”是多少倍的鱼？",
        'answer': [
            "A.50",
            "B.45",
            "C.35",
            "D.30",
        ],
        'formType': 1,
        'correct': '2'
    },

    {
        'id': 18,
        'question': "下列哪条鱼不是蓝色的？",
        'answer': [
            "A.冰美人",
            "B.小章鱼",
            "C.灯笼鱼",
            "D.泰斗鱼",
        ],
        'formType': 1,
        'correct': '1'
    },

    {
        'id': 19,
        'question': "游戏大厅右上角的设置按钮里可以调节什么？",
        'answer': [
            "A.游戏音量",
            "B.游戏亮度",
            "C.炮台等级",
            "D.炮弹速度",
        ],
        'formType': 1,
        'correct': '0'
    },

    {
        'id': 20,
        'question': "炮弹“翻倍炮”有什么效果？",
        'answer': [
            "A.捕获鱼获得金币翻倍",
            "B.捕获鱼获得奖券翻倍",
            "C.金币消耗翻倍",
            "D.炮弹射速翻倍",
        ],
        'formType': 1,
        'correct': '0'
    },

    {
        'id': 21,
        'question': "排行榜只显示前多少名玩家？",
        'answer': [
            "A.50",
            "B.40",
            "C.20",
            "D.10",
        ],
        'formType': 1,
        'correct': '3'
    },

    {
        'id': 22,
        'question': "东胜财富榜每日几点更新？",
        'answer': [
            "A.18:00",
            "B.14:00",
            "C.12:00",
            "D.00:00",
        ],
        'formType': 1,
        'correct': '3'
    },
]

"""
答题奖励相关
"""
ACTIVICE_QUESTION_REWARD_LIST = 'activice:question:reward:hesh'
"""
记录每种礼品被领取次数
@rid 奖品id
"""
ACTIVICE_QUESTION_REWARD_COUNT = 'activice:question:reward:%s:count:hesh'
#记录每日红包领取数量
ACTIVICE_QUESTION_REDPACK_MAX = 4000
ACTIVICE_QUESTION_REDPACK_COUNT = 'activice:question:redpack:hesh'
#记录每日发送金币数
ACTIVICE_QUESTION_GOLD_MIN = 10000
ACTIVICE_QUESTION_GOLD_MAX = 50000

ACTIVICE_SEND_GOLD_COUNT = 'activice:question:send:gold:hesh'
ACTIVICE_SEND_REDPACK_COUNT = 'activice:question:send:redpack:hesh'
ACTIVICE_SEND_TICK_COUNT = 'activice:question:send:tick:hesh'


QUESTION_REDPACK_LIST = [
    {
        'id': 1,
        'title': '礼券8张',
        'total': 1,
        'max': 3000,
    },
    {
        'id': 2,
        'title': '礼券56张',
        'total': 7,
        'max': 600,
    },
    {
        'id': 3,
        'title': '礼券120张',
        'total': 15,
        'max': 300,
    },
    {
        'id': 4,
        'title': '礼券240张',
        'total': 30,
        'max': 100,
    },
]



"""
问卷相关
'activice:surver:%s:list' %  @问卷编号
"""
ACTIVICE_SURVER_NUMBER_LIST = 'activice:surver:%s:list'
"""
玩家是否完成问卷
SADD 'activice:surver:answer:%s:set' % @问卷编号
"""
ACTIVICE_SURVER_ANSWER = 'activice:surver:answer:%s:set'
"""
问卷每个答案的数据
HINCRBY 'activice:surver:result:%s:hash'  % (@问卷编号, @题目id): @答案序号:0
"""
ACTIVICE_SURVER_RESULT = 'activice:surver:result:%s:%s:hesh'
"""
问卷送出金币数
HINCRBY 'activice:surver:send:%s:hesh'  % (@问卷编号) : @date:0
"""
ACTIVICE_SEND_SURVER_GOLD_COUNT = 'activice:surver:send:%s:hesh'

"""
问卷格式
{
	'question': "问题1，请问xxxx？",
	'answer': [
		"答案1",
		"答案2",
		"答案3",
	],
	'formType': 1, 	#表单类型 ： 1单选  2多选
}
"""
SURVER_COVER = True         #是否每次运行脚本都清空该问卷数据
SURVER_NUMBER = 'lws_001'   #问卷编号
SURVER_BANK = [
    {
        'id': 1,
        'question': "《东胜捕鱼》的画面如何？",
        'answer': [
            "很喜欢",
            "还好吧",
            "一般",
            "不感兴趣"
        ],
        'formType': 1,
    }, {
        'id': 2,
        'question': "《东胜捕鱼》开炮频率如何？",
        'answer': [
            "很喜欢",
            "能接受",
            "再慢一点",
            "再快一点"
        ],
        'formType': 1,
    }, {
        'id': 3,
        'question': "《东胜捕鱼》的渔场鱼数感觉如何？",
        'answer': [
            "太多了",
            "刚刚好",
            "太少了",
            "没有想法"
        ],
        'formType': 1,
    }, {
        'id': 4,
        'question': "《东胜捕鱼》的奖票获得感觉如何？",
        'answer': [
            "感觉不错",
            "还行，没想法",
            "太少了",
            "不合理"
        ],
        'formType': 1,
    }, {
        'id': 5,
        'question': "《东胜捕鱼》过程当中最喜欢的是什么？【多选】",
        'answer': [
            "捕获感",
            "画面",
            "声音",
            "没有喜欢"
        ],
        'formType': 2,
    }, {
        'id': 6,
        'question': "《东胜捕鱼》你希望有什么功能？【多选】",
        'answer': [
            "养鱼场",
            "银行（储钱库）",
            "俱乐部房间场",
            "更对兑换奖品"
        ],
        'formType': 2,
    }, {
        'id': 7,
        'question': "《东胜捕鱼》你觉得以下问题哪些技术问题需要优化的？ 【多选】",
        'answer': [
            "安装经常失败",
            "网络延迟、卡顿",
            "画面卡顿难忍",
            "没有需要优化的"
        ],
        'formType': 2,
    }, {
        'id': 8,
        'question': "《东胜捕鱼》游戏时，你认为游戏难度如何？",
        'answer': [
            "简单",
            "普通",
            "略难",
            "极难"
        ],
        'formType': 1,
    }, {
        'id': 9,
        'question': "《东胜捕鱼》你认为在游戏中有哪些东西还需要优化的呢？【多选】",
        'answer': [
            "炮台类型不足",
            "鱼的种类过少",
            "增加boss鱼",
            "画面不够精美"
        ],
        'formType': 2,
    }, {
        'id': 10,
        'question': "《东胜捕鱼》你认为在游戏中有需要哪些活动【多选】",
        'answer': [
            "每日抽奖",
            "有奖问答",
            "活动红包鱼",
            "限时boss"
        ],
        'formType': 2,
    }, {
        'id': 11,
        'question': "《东胜捕鱼》与市场上的捕鱼相比，效果如何？【多选】",
        'answer': [
            "有竞争力",
            "功能太少",
            "体验很差",
            "玩法不够新颖"
        ],
        'formType': 2,
    }
]

ACTIVE_CONFIG_ALL_LIST = "active:configs:all:set"
"""

"""
ACTIVE_CONFIG_ONE_HESH = "active:configs:%s:hesh"
""" 每个活动的匹配
id         = 活动的ID
code       = 活动的固定CODE
start_time = 活动的开始时间
end_time   = 活动的结束时间
route      = 请求的ROUTE地址
posterUrl  = 图片
name       = 活动名称
"""

CHECK_PARTY_COMPETITION = "1"  # 竞技场
CHECK_PARTY_GOLD = "2"  # 金币场
CHECK_PARTY_MATCH = "3"  # 比赛场
CHECK_CREATE_ROOM = "4"  # 创房界面
CHECK_ACTIVICE = "5"  # 活动界面
CHECK_MALL = "6"  # 商城
CHECK_SHARE = "7"  # 分享
CHECK_FISH_INFO = "100"  # 捕鱼个人信息
CHECK_FISH_PACK = "101"  # 捕鱼背包
CHECK_FISH_SHARE = "102"  # 捕鱼分享
CHECK_FISH_MALL = "103"  # 捕鱼商店
CHECK_FISH_EXCHAGE = "104"  # 捕鱼兑换
CHECK_FISH_ORDER = "105"  # 捕鱼排行
CHECK_FISH_ACTIVE = "106"  # 捕鱼活动 1=活动 2=公告
CHECK_FISH_WELFARE = "107"  # 捕鱼福利 type = 1:签到 2:每日护航
CHECK_FISH_ROOM = "109"  # 捕鱼创房 params=1,2,3
CHECK_FISH_SURVER = "110"  # 捕鱼问卷
CHECK_FISH_QUESTION = "111"  # 捕鱼答题

"""活动信息"""
SERVER = 'http://a5.dongshenggame.cn:9790'
actives = [
    dict(
        active_id=1,
        code=19999,
        title = '福禄双收',
        start_time="2018-02-10",
        end_time="2018-02-22",
        state=1,
        # LOCAL = 本地模块
        route=json.dumps({
            "method": "LOCAL",
            "url": CHECK_FISH_WELFARE,
            "params": {'type': 1}
        }),
        posterUrl= SERVER + "/spring_active_poster1.jpg"
    ),
    dict(
        active_id=2,
        code=19999,
        title='三阳开泰',
        start_time="2018-02-10",
        end_time="2018-02-22",
        state=1,
        # LOCAL = 本地模块
        route=json.dumps({
            "method": "LOCAL",
            "url": CHECK_FISH_WELFARE,
            "params": {'type': 2}
        }),
        posterUrl = SERVER + "/spring_active_poster2.jpg"
    ),
    dict(
        active_id=3,
        code=19999,
        title='红包降临',
        start_time="2018-02-10",
        end_time="2018-02-22",
        state=1,
        # LOCAL = 本地模块
        route=json.dumps({
            "method": "LOCAL",
            "url": CHECK_FISH_ROOM,
            "params": {}
        }),
        posterUrl= SERVER + "/spring_active_poster3.jpg"
    ),
    dict(
        active_id=4,
        code=19999,
        title='有奖问答',
        start_time="2018-02-16",
        end_time="2018-02-22",
        state=1,
        # LOCAL = 本地模块
        route=json.dumps({
            "method": "LOCAL",
            "url": CHECK_FISH_QUESTION,
            "params": {}
        }),
        posterUrl= SERVER + "/spring_active_poster4.jpg"
    ),
]

"""
活动日期
一帆风顺：0 : '2018-2-7,2018-2-22'
"""
ACTIVICE_SPRING_TIME = 'activice:setting:time'

if __name__ == "__main__":

    redis = getInst(1)

    # 春节活动起止时间
    # date = json.dumps({'from': '2018-2-10', 'to': '2018-2-22'})
    # print u'一帆风顺活动起止时间:{0}'.format(date)
    # redis.set(ACTIVICE_SPRING_TIME, date)

    # 插入活动
    print u'插入活动数据'
    redis.delete(ACTIVE_CONFIG_ALL_LIST)
    for idx, item in enumerate(actives):
        redis.sadd(ACTIVE_CONFIG_ALL_LIST, item["active_id"])
        redis.hmset(ACTIVE_CONFIG_ONE_HESH % item["active_id"], item)

    # 更新题库
    print u'更新题库数据'
    pipe = redis.pipeline()
    count = 0
    for idx, item in enumerate(QUESTION_BANK):
        try:
            pipe.hset(ACTIVICE_QUESTION_ALL_HESH, item['id'], json.dumps(item))
            count += 1
        except Exception:
            print u'更新题目出错,id:%s ' % item['id']
    pipe.execute()
    print(u'更新题目完毕, %s / %s' % (count, len(QUESTION_BANK)))

    # 更新答题奖品
    print u'更新答题奖品'
    redis.delete(ACTIVICE_QUESTION_REWARD_LIST)
    pipe = redis.pipeline()
    count = 0
    for idx, item in enumerate(QUESTION_REDPACK_LIST):
        count += 1
        tid = item['id']
        curTime = datetime.now().strftime('%Y-%m-%d')
        redis.hdel(ACTIVICE_QUESTION_REWARD_COUNT % tid, curTime)
        try:
            pipe.hset(ACTIVICE_QUESTION_REWARD_LIST, tid, json.dumps(item))
            pipe.hincrby(ACTIVICE_QUESTION_REWARD_COUNT % tid, curTime, 0)
        except Exception:
            print u'更新答题奖品出错'
    pipe.execute()
    print(u'更新答题奖品完毕, %s / %s' % (count, len(QUESTION_REDPACK_LIST)))

    # 更新问卷题库
    print u'更新问卷数据'
    count = 0
    number = SURVER_NUMBER
    if SURVER_COVER:
        redis.delete(ACTIVICE_SURVER_NUMBER_LIST % number)
    pipe = redis.pipeline()
    for idx, item in enumerate(SURVER_BANK):
        try:
            pipe.lpush(ACTIVICE_SURVER_NUMBER_LIST % number, json.dumps(item))
            count += 1
        except Exception:
            print u'更新问卷出错,id:%s ' % item['id']
    pipe.execute()
    print(u'更新问卷完毕, %s / %s' % (count, len(SURVER_BANK)))

