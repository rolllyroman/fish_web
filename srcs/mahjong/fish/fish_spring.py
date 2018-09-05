#-*- coding:utf-8 -*-
#!/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    捕鱼邀请接口相关
"""
from bottle import request,response,default_app
from web_db_define import *
from fish import fish_app
from common.log import *
from datetime import datetime, date, timedelta
from model.fishModel import get_room_list, check_spring_time
from model.goodsModel import *
from model.userModel import *
from common.utilt import allow_cross,getInfoBySid
from common import web_util,log_util,convert_util
import json
import random



@fish_app.post("/actives")
@web_util.allow_cross_request
def doActives(redis, session):
    """ 活动接口

    :param redis:
    :param session:
    :return:
    """
    curTime = datetime.now()

    try:
        sid = request.forms.get('sid', '').strip()
    except Exception as err:
        return {"code": 1, 'msg': "参数错误"}

    SessionTable, account, uid, verfiySid = getInfoBySid(redis, sid)
    if not redis.exists(SessionTable):
        return {'code': -3, 'msg': 'sid 超时'}

    data = []
    # 是否春节期间
    isSpring, springInfo = check_spring_time(redis, False)
    if isSpring:
        # 获取活动时间
        activeList = redis.smembers(ACTIVE_CONFIG_ALL_LIST)
        for activeId in activeList:
            tempData = redis.hgetall(ACTIVE_CONFIG_ONE_HESH % activeId)
            # s_time = time.mktime(time.strptime(tempData['start_time'], '%Y-%m-%d'))  # get the seconds for specify date
            # e_time = time.mktime(time.strptime(tempData['end_time'], '%Y-%m-%d'))
            # log_time = time.mktime(time.strptime(curTime.strftime("%Y-%m-%d"), '%Y-%m-%d'))
            # isOpen = (float(log_time) >= float(s_time)) and (float(log_time) <= float(e_time))
            isOpen = True
            if isOpen:
                tempData["route"] = json.loads(tempData["route"])
                tempData["code"] = int(tempData["code"])
                data.append(tempData)


    return {"code": 0, "data": data, "msg": '成功'}

@fish_app.post("/question")
@web_util.allow_cross_request
def getQuestion(redis, session):
    """
    答题题目接口
    """
    curTime = datetime.now()
    curDate = curTime.strftime('%Y-%m-%d')
    try:
        sid = request.forms.get('sid', '').strip()
    except Exception as err:
        return {'code': 1, 'msg': '参数错误'}

    SessionTable, account, uid, verfiySid = getInfoBySid(redis, sid)
    if not redis.exists(SessionTable):
        return {'code': -3, 'msg': 'sid超时'}

    # 检查是否到活动时间
    isIntime, info = check_spring_time(redis, 4)
    if not isIntime:
        return {'code': 1, 'msg': info}

    #检查是否答过题
    answer = redis.hget(ACTIVICE_QUESTION_ANSWER, account)
    isStart = redis.hget(ACTIVICE_QUESTION_START, account)
    if answer == curDate or isStart == curDate:
        return {'code': 1, 'msg': '你已经答过题了'}

    #获取题目
    questions = redis.hkeys(ACTIVICE_QUESTION_ALL_HESH)
    selectCount = min(ACTIVICE_QUESTION_SELECT, len(questions))
    selectKeys = random.sample(questions, selectCount)
    selectQuestion = []
    for key in selectKeys:
        q = redis.hget(ACTIVICE_QUESTION_ALL_HESH, key)
        selectQuestion.append(json.loads(q))

    data = {
        'list': selectQuestion,
        'title': ACTIVICE_QUESTION_TITLE,
        'desc': ACTIVICE_QUESTION_DESC,
        'timeLimit': ACTIVICE_QUESTION_TIME,
        'route': {
            'method': 'POST',
            'url': '/fish/question/answer',
            "params": {}
        }
    }
    return {'code': 0, 'msg': '获取题库成功', 'data': data}

@fish_app.post("/question/opening")
@web_util.allow_cross_request
def setQuestionStart(redis, session):
    """"
    点击了开始答题
    """

    log_debug('点击了开始答题')
    curTime = datetime.now()
    curDate = curTime.strftime('%Y-%m-%d')
    log_debug('点击了开始答题2')

    try:
        sid = request.forms.get('sid', '').strip()
    except Exception as err:
        return {'code': 1, 'msg': '参数错误'}

    SessionTable, account, uid, verfiySid = getInfoBySid(redis, sid)
    if not redis.exists(SessionTable):
        return {'code': -3, 'msg': 'sid超时'}

    # 检查是否到活动时间
    isIntime, info = check_spring_time(redis, 4)
    if not isIntime:
        return {'code': 1, 'msg': info}

    # 设置为已经答题
    redis.hset(ACTIVICE_QUESTION_START, account, curDate)

    return {'code': 0, 'msg': '开始答题'}

@fish_app.post("/question/answer")
@web_util.allow_cross_request
def getQuestion(redis, session):
    """
    答题接收答案接口

    赠送奖券的位置在这
    fish:redpick:account:hesh
    @account : 1    (等于8个奖券)
    """
    curTime = datetime.now()
    curDate = curTime.strftime('%Y-%m-%d')

    try:
        sid = request.forms.get('sid', '').strip()
        data = request.forms.get('data','').strip()
        anwser = json.loads(data)
    except Exception as err:
        return {'code': 1, 'msg': '参数错误'}

    SessionTable, account, uid, verfiySid = getInfoBySid(redis, sid)
    if not redis.exists(SessionTable):
        return {'code': -3, 'msg': 'sid超时'}

    log_debug('//////答题接收答案接口{0}'.format(anwser))
    # 检查是否到活动时间
    isIntime, info = check_spring_time(redis, 4)
    if not isIntime:
        return {'code': 1, 'msg': info}


    # 检查是否答过题
    lastDate = redis.hget(ACTIVICE_QUESTION_ANSWER, account)
    if lastDate and lastDate == curDate:
        return {'code': 1, 'msg': '你已经答过题了'}

    # 获取题目编号
    questions = redis.hkeys(ACTIVICE_QUESTION_ALL_HESH)
    selectCount = min(ACTIVICE_QUESTION_SELECT, len(questions))

    #检查答案数量
    if len(anwser) < selectCount:
        return {'code': 1, 'msg': '请提交完整答案'}

    #检查答对数量
    correctCount = 0
    for tid, ans in anwser.items():
        try:
            info = redis.hget(ACTIVICE_QUESTION_ALL_HESH, tid)
            info = json.loads(info)
            if info['correct'] == ','.join([str(i) for i in ans]):
                correctCount += 1
        except:
            pass
    if correctCount == 0:
        return {'code': 1, 'msg': '您没有答对题，请明天再试一次。'}

    #检查奖励
    pool = {} #可领取奖品池 {id:item}
    probabilitys = []#概率
    rewards = redis.hgetall(ACTIVICE_QUESTION_REWARD_LIST)
    log_debug('//////rewards{0}'.format(rewards))

    for idx, item in rewards.items():
        item = json.loads(item)
        rid = item['id']
        maxCount = item['max'] = int(item['max'])
        curCount = redis.hget(ACTIVICE_QUESTION_REWARD_COUNT % rid, curDate)
        curCount = curCount or 0
        curCount = int(curCount)
        if curCount < maxCount:
            item['last'] = maxCount - curCount
            probabilitys.extend([rid] * item['last'])
            pool[rid] = item

    log_debug('//////probabilitys{0}, {1}'.format(probabilitys, pool) )

    #轮询奖励，不足的奖励用金币凑
    goldPreMin = ACTIVICE_QUESTION_GOLD_MIN / correctCount
    goldPreMax = ACTIVICE_QUESTION_GOLD_MAX / correctCount
    goldTotal = 0
    tickTotal = 0
    sendPool = []
    for i in xrange(correctCount):
        try:
            r_rid = random.choice(probabilitys)

            probabilitys.remove(r_rid)
            choice_item = pool[r_rid]
            redis.hincrby(ACTIVICE_QUESTION_REWARD_COUNT % r_rid, curDate,1)

        except:
            choice_item = False

        if not choice_item:
            #该奖励已发放完毕凑金币
            r_gold = random.randint(goldPreMin, goldPreMax)
            goldTotal += r_gold
            sendPool.append({
                'title': '金币{0}'.format(r_gold),
                'total': r_gold,
            })
        else:
            #写入奖励
            sendPool.append(choice_item)
            tickTotal += choice_item['total']


    account2user_table = FORMAT_ACCOUNT2USER_TABLE % (account)
    userTable = redis.get(account2user_table)
    pipe = redis.pipeline()
    #记录红包数
    pipe.hincrby(ACTIVICE_SEND_REDPACK_COUNT, curDate, correctCount)
    if goldTotal:
        pipe.hincrby(userTable, "coin", goldTotal)
        # 记录金币数
        pipe.hincrby(ACTIVICE_SEND_GOLD_COUNT, curDate, goldTotal)
    if tickTotal:
        pipe.hincrby("fish:redpick:account:hesh", account, tickTotal)
        # 1张tick = 8张奖券
        realTickTotal = tickTotal * 8
        pipe.hincrby(userTable, "exchange_ticket", realTickTotal)
        # 记录奖券数
        pipe.hincrby(ACTIVICE_SEND_TICK_COUNT, curDate, realTickTotal)

    # 设置为已经答题
    pipe.hset(ACTIVICE_QUESTION_ANSWER, account, curDate)
    pipe.execute()



    return {'code': 0, 'msg': '恭喜您获得{0}个红包'.format(correctCount), 'data':sendPool}


@fish_app.post("/surver")
@web_util.allow_cross_request
def getSurver(redis, session):
    """
    问卷调查接口
    """
    try:
        sid = request.forms.get('sid', '').strip()
    except Exception as err:
        return {'code': 1, 'msg': '参数错误'}

    SessionTable, account, uid, verfiySid = getInfoBySid(redis, sid)
    if not redis.exists(SessionTable):
        return {'code': -3, 'msg': 'sid超时'}

    # 检查是否答过题
    isAnswer = redis.sismember(ACTIVICE_SURVER_ANSWER % SURVER_NUMBER, account)
    if isAnswer:
        return {'code': 1, 'msg': '你已经回答过问卷了'}

    #获取题目
    questions = redis.lrange(ACTIVICE_SURVER_NUMBER_LIST % SURVER_NUMBER, 0, -1)
    selectQuestion = []
    for temp in questions:
        selectQuestion.append(json.loads(temp))

    data = {
        'list': selectQuestion,
        'title': ACTIVICE_SURVER_TITLE,
        'desc': ACTIVICE_SURVER_DESC,
        'route': {
            'method': 'POST',
            'url': '/fish/surver/answer',
            "params": {}
        }
    }
    return {'code': 0, 'msg': '获取题库成功', 'data': data}

@fish_app.post("/surver/answer")
@web_util.allow_cross_request
def getQuestion(redis, session):
    """
    问卷调查接口
    """
    curTime = datetime.now()
    curDate = curTime.strftime('%Y-%m-%d')
    try:
        sid = request.forms.get('sid', '').strip()
        data = request.forms.get('data', '').strip()
        anwser = json.loads(data)
    except Exception as err:
        return {'code': 1, 'msg': '参数错误'}

    SessionTable, account, uid, verfiySid = getInfoBySid(redis, sid)
    if not redis.exists(SessionTable):
        return {'code': -3, 'msg': 'sid超时'}

    # 检查是否答过题
    isAnswer = redis.sismember(ACTIVICE_SURVER_ANSWER % SURVER_NUMBER, account)
    if isAnswer:
        return {'code': 1, 'msg': '你已经回答过问卷了'}

    account2user_table = FORMAT_ACCOUNT2USER_TABLE % (account)
    userTable = redis.get(account2user_table)
    #记录数据
    pipe = redis.pipeline()
    for tid, ans in anwser.items():
        for aid in ans:
            pipe.hincrby(ACTIVICE_SURVER_RESULT % (SURVER_NUMBER, tid), str(aid), 1)

    #送出奖励
    goldTotal = SURVER_SEND_GOLD
    pipe.hincrby(userTable, "coin", goldTotal)
    # 记录金币数
    pipe.hincrby(ACTIVICE_SEND_SURVER_GOLD_COUNT % SURVER_NUMBER, curDate, goldTotal)
    #记录已答题
    pipe.sadd(ACTIVICE_SURVER_ANSWER % SURVER_NUMBER, account)
    pipe.execute()

    return {'code': 0, 'msg': '感谢您完成问卷，谢谢您的大力支持！\n获得{0}金币'.format(goldTotal), 'data':''}
