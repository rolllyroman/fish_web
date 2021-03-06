#-*- coding:utf-8 -*-
#!/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    大厅Model
"""

from web_db_define import *
from datetime import datetime,timedelta
from wechat.wechatData import *
from admin  import access_module
from config.config import *
from datetime import datetime
import mahjong_pb2
import poker_pb2
import replay4proto_pb2
from mahjong.model.agentModel import getTopAgentId
from common import log_util
import time
import uuid

# 昵称注册
def register_by_account(redis,ip,account,passwd,agent_id):

    curTime = datetime.now()
    curRegDateTable = FORMAT_REG_DATE_TABLE%(curTime.strftime("%Y-%m-%d"))
    #创建新的用户数据
    uid = redis.incr(FORMAT_USER_COUNT_TABLE)
    # 随机昵称和密码
    table = FORMAT_USER_TABLE%(uid)
    pipe = redis.pipeline()
    pipe.hmset(table, 
        {
            'account'       :   account, 
            'password'      :   md5.new(passwd).hexdigest() ,
            'nickname'      :   account,
            'name'          :   '',
            'currency'      :   'CNY', #国家需要做微信到数据库的变换映射
            'money'         :   0.0,
            'wallet'        :   0.0,
            'vip_level'     :   0,
            'exp'           :   0,
            'level'         :   0,
            'charge'        :   0.0,
            'charge_count'  :   0,
            'game_count'    :   0,
            'coin_delta'    :   0,
            'parentAg'      :   agent_id, #上线代理需要获得
            'email'         :   '',
            'phone'         :   '',
            'valid'         :   1,
            'lastJoinIP'  :   '',
            'lastJoinDate':   '',
            'lastExitIP'  :   '',
            'lastExitDate':   '',
            'lastLoginIP' :   '',
            'lastLoginDate':  '',
            'lastLogoutIP':   '',
            'lastLogoutDate': '',
            'lastPresentDate' : '',
            'newcomer_present_date' : '',
            'reg_ip'        :   ip,
            'reg_date'      :   curTime.strftime("%Y-%m-%d %H:%M:%S"),
            'coin'          :   0,
            'accessToken'   :   '',#accessToken, #以下新增
            'refreshToken'  :   '',#refreshToken,
            'openid'        :   '',#openID,
            'sex'           :   '1',#userData['sex'], #性别
            'roomCard'      :   5,
            'headImgUrl'    :   '',#userData['headimgurl'], #头像
            'unionID'       :   '',#userData['unionid'],
            'playCount'     :   0,
            'info_comp'        :   0,
        }
    )
    # 添加昵称到uid映射
    account2user_table = FORMAT_ACCOUNT2USER_TABLE%(account)
    # 账号uid映射
    pipe.set(account2user_table, table)
    # 日期注册账号集合
    pipe.sadd(FORMAT_REG_DATE_TABLE4FISH%(curTime.strftime("%Y-%m-%d")), account)
    # 账号注册账号集合
    pipe.sadd("register:account:set",account)
    # 公会所属uid集合
    pipe.sadd(FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE%agent_id,uid)
    pipe.execute()    
    return uid

def onRegFish_new(redis,account,passwd,type,ip,clientType,session): #传入参数：账号，密码，类型

    curTime = datetime.now()

    log_util.debug('[try onReg] account[%s] passwd[%s] type[%s]'%(account,passwd,type))

    if type == 1: #微信code登录
        tokenMessage = checkWeixinCode4fish(account)
        if tokenMessage:
            password = account
            accessToken = tokenMessage["access_token"]
            refreshToken = tokenMessage["refresh_token"]
            openID = tokenMessage["openid"]
            userData = getWeixinData(openID, accessToken)
            unionid = userData['unionid']
            if redis.exists(WEIXIN2ACCOUNT%(unionid)):# or redis.exists(WEIXIN2ACCOUNT%(unionid)):
                realAccount = redis.get(WEIXIN2ACCOUNT%(unionid))
                if not realAccount:
                    realAccount = redis.get(WEIXIN2ACCOUNT%(unionid))
                account2user_table = FORMAT_ACCOUNT2USER_TABLE%(realAccount)
                table = redis.get(account2user_table)
                redis.hmset(table, {'accessToken':accessToken, 'refreshToken':refreshToken, 'password':md5.new(password).hexdigest()})
            else:
                setOpenid2account4fish(openID, accessToken, refreshToken, ip, redis, account)
            redis.srem(FORMAT_LOGIN_POOL_SET,account)
            return unionid, password
        redis.srem(FORMAT_LOGIN_POOL_SET,account)
    elif type == 2:
        if redis.exists(WEIXIN2ACCOUNT%(account)):#  or redis.exists(WEIXIN2ACCOUNT%(account)):
            realAccount = redis.get(WEIXIN2ACCOUNT%(account))
            if not realAccount:
                realAccount = redis.get(WEIXIN2ACCOUNT%(account))
            account2user_table = FORMAT_ACCOUNT2USER_TABLE%(realAccount)
            table = redis.get(account2user_table)
            truePassword, openID, accessToken = redis.hmget(table, ('password', 'openid', 'accessToken'))
            log_util.debug('type 2:passwd[%s] md5[%s] truePassword[%s]'%(md5.new(passwd).hexdigest(), passwd, truePassword))
            if truePassword == md5.new(passwd).hexdigest():
                userData = getWeixinData(openID, accessToken)
                log_util.debug('onReg for type 2, userData:%s'%(userData))
                if userData:
                    redis.hmset(table,
                        {
                            'nickname'      :   userData['nickname'],
                            'sex'           :   userData['sex'],
                            'headImgUrl'    :   userData['headimgurl']
                        }
                    )
                redis.srem(FORMAT_LOGIN_POOL_SET,account)
                return account, passwd
        redis.srem(FORMAT_LOGIN_POOL_SET,account)
    elif type == 3: #微信WEBcode登录
        tokenMessage = checkWeixinCodeWEB(account)
        if tokenMessage:
            password = account
            accessToken = tokenMessage["access_token"]
            refreshToken = tokenMessage["refresh_token"]
            openID = tokenMessage["openid"]
            userData = getWeixinData(openID, accessToken)
            unionid = userData['unionid']
            if redis.exists(WEIXIN2ACCOUNT%(unionid)):#  or redis.exists(WEIXIN2ACCOUNT%(unionid)):
                realAccount = redis.get(WEIXIN2ACCOUNT%(unionid))
                if not realAccount:
                    realAccount = redis.get(WEIXIN2ACCOUNT%(unionid))
                account2user_table = FORMAT_ACCOUNT2USER_TABLE%(realAccount)
                table = redis.get(account2user_table)
                redis.hmset(table, {'accessToken':accessToken, 'refreshToken':refreshToken, 'password':md5.new(password).hexdigest()})
            else:
                setOpenid2account4fish(openID, accessToken, refreshToken, ip, redis, account)
            redis.srem(FORMAT_LOGIN_POOL_SET,account)
            return unionid, password
        redis.srem(FORMAT_LOGIN_POOL_SET,account)
    # 测试账号登录
    elif type == 0:
        account2user_table = FORMAT_ACCOUNT2USER_TABLE%(account)
        if redis.exists(account2user_table):
            table = redis.get(account2user_table)
            truePassword,nickname = redis.hgmet(table, 'password','nickname')
            return login_handler(redis,ip,nickname,passwd,login_type,clientType,session)  
    redis.srem(FORMAT_LOGIN_POOL_SET,account)
    return {'code':-3,'msg':'账号不存在！'}

def onReg(redis, account, passwd, type, ip): #传入参数：账号，密码，类型；返回参数：成功返回账号和密码，失败返回None, None

    curTime = datetime.now()

    #print
    log_util.debug('[try onReg] account[%s] passwd[%s] type[%s]'%(account,passwd,type))

    if type == 1: #微信code登录
        tokenMessage = checkWeixinCode(account)
        if tokenMessage:
            password = account
            accessToken = tokenMessage["access_token"]
            refreshToken = tokenMessage["refresh_token"]
            openID = tokenMessage["openid"]
            userData = getWeixinData(openID, accessToken)
            unionid = userData['unionid']
            if redis.exists(WEIXIN2ACCOUNT%(unionid)):
                realAccount = redis.get(WEIXIN2ACCOUNT%(unionid))
                account2user_table = FORMAT_ACCOUNT2USER_TABLE%(realAccount)
                table = redis.get(account2user_table)
                redis.hmset(table, {'accessToken':accessToken, 'refreshToken':refreshToken, 'password':md5.new(password).hexdigest()})
            else:
                setOpenid2account(openID, accessToken, refreshToken, ip, redis, account)
            redis.srem(FORMAT_LOGIN_POOL_SET,account)
            return unionid, password
        redis.srem(FORMAT_LOGIN_POOL_SET,account)
    elif type == 2:
        if redis.exists(WEIXIN2ACCOUNT%(account)):
            realAccount = redis.get(WEIXIN2ACCOUNT%(account))
            account2user_table = FORMAT_ACCOUNT2USER_TABLE%(realAccount)
            table = redis.get(account2user_table)
            truePassword, openID, accessToken = redis.hmget(table, ('password', 'openid', 'accessToken'))
            log_util.debug('type 2:passwd[%s] md5[%s] truePassword[%s]'%(md5.new(passwd).hexdigest(), passwd, truePassword))
            if truePassword == md5.new(passwd).hexdigest():
                userData = getWeixinData(openID, accessToken)
                log_util.debug('onReg for type 2, userData:%s'%(userData))
                if userData:
                    redis.hmset(table,
                        {
                            'nickname'      :   userData['nickname'],
                            'sex'           :   userData['sex'],
                            'headImgUrl'    :   userData['headimgurl']
                        }
                    )
                redis.srem(FORMAT_LOGIN_POOL_SET,account)
                return account, passwd
        redis.srem(FORMAT_LOGIN_POOL_SET,account)
    elif type == 3: #微信WEBcode登录
        tokenMessage = checkWeixinCodeWEB(account)
        if tokenMessage:
            password = account
            accessToken = tokenMessage["access_token"]
            refreshToken = tokenMessage["refresh_token"]
            openID = tokenMessage["openid"]
            userData = getWeixinData(openID, accessToken)
            unionid = userData['unionid']
            if redis.exists(WEIXIN2ACCOUNT%(unionid)):
                realAccount = redis.get(WEIXIN2ACCOUNT%(unionid))
                account2user_table = FORMAT_ACCOUNT2USER_TABLE%(realAccount)
                table = redis.get(account2user_table)
                redis.hmset(table, {'accessToken':accessToken, 'refreshToken':refreshToken, 'password':md5.new(password).hexdigest()})
            else:
                setOpenid2account(openID, accessToken, refreshToken, ip, redis, account)
            redis.srem(FORMAT_LOGIN_POOL_SET,account)
            return unionid, password
        redis.srem(FORMAT_LOGIN_POOL_SET,account)
    elif type == 4: #微信WEBcode登录
        tokenMessage = checkWeixinCodeWEB(account)
        if tokenMessage:
            password = account
            accessToken = tokenMessage["access_token"]
            refreshToken = tokenMessage["refresh_token"]
            openID = tokenMessage["openid"]
            userData = getWeixinData(openID, accessToken)
            unionid = userData['unionid']
            if redis.exists(WEIXIN2ACCOUNT%(unionid)):
                realAccount = redis.get(WEIXIN2ACCOUNT%(unionid))
                account2user_table = FORMAT_ACCOUNT2USER_TABLE%(realAccount)
                table = redis.get(account2user_table)
                redis.hmset(table, {'accessToken':accessToken, 'refreshToken':refreshToken, 'password':md5.new(password).hexdigest()})
            else:
                setOpenid2account(openID, accessToken, refreshToken, ip, redis, account)
            redis.srem(FORMAT_LOGIN_POOL_SET,account)
            return unionid, password
        redis.srem(FORMAT_LOGIN_POOL_SET,account)
    elif type == 0:
        account2user_table = FORMAT_ACCOUNT2USER_TABLE%(account)
        if redis.exists(account2user_table):
            table = redis.get(account2user_table)
            truePassword = redis.hget(table, 'password')
            if truePassword == md5.new(passwd).hexdigest():
                return account, passwd
    redis.srem(FORMAT_LOGIN_POOL_SET,account)
    return None, None

def onRegFish(redis, account, passwd, type, ip): #传入参数：账号，密码，类型；返回参数：成功返回账号和密码，失败返回None, None

    curTime = datetime.now()


    log_util.debug('[try onReg] account[%s] passwd[%s] type[%s]'%(account,passwd,type))

    if type == 1: #微信code登录
        tokenMessage = checkWeixinCode4fish(account)
        if tokenMessage:
            password = account
            accessToken = tokenMessage["access_token"]
            refreshToken = tokenMessage["refresh_token"]
            openID = tokenMessage["openid"]
            userData = getWeixinData(openID, accessToken)
            unionid = userData['unionid']
            if redis.exists(WEIXIN2ACCOUNT%(unionid)):# or redis.exists(WEIXIN2ACCOUNT%(unionid)):
                realAccount = redis.get(WEIXIN2ACCOUNT%(unionid))
                if not realAccount:
                    realAccount = redis.get(WEIXIN2ACCOUNT%(unionid))
                account2user_table = FORMAT_ACCOUNT2USER_TABLE%(realAccount)
                table = redis.get(account2user_table)
                redis.hmset(table, {'accessToken':accessToken, 'refreshToken':refreshToken, 'password':md5.new(password).hexdigest()})
            else:
                setOpenid2account4fish(openID, accessToken, refreshToken, ip, redis, account)
            redis.srem(FORMAT_LOGIN_POOL_SET,account)
            return unionid, password
        redis.srem(FORMAT_LOGIN_POOL_SET,account)
    elif type == 2:
        if redis.exists(WEIXIN2ACCOUNT%(account)):#  or redis.exists(WEIXIN2ACCOUNT%(account)):
            realAccount = redis.get(WEIXIN2ACCOUNT%(account))
            if not realAccount:
                realAccount = redis.get(WEIXIN2ACCOUNT%(account))
            account2user_table = FORMAT_ACCOUNT2USER_TABLE%(realAccount)
            table = redis.get(account2user_table)
            truePassword, openID, accessToken = redis.hmget(table, ('password', 'openid', 'accessToken'))
            log_util.debug('type 2:passwd[%s] md5[%s] truePassword[%s]'%(md5.new(passwd).hexdigest(), passwd, truePassword))
            if truePassword == md5.new(passwd).hexdigest():
                userData = getWeixinData(openID, accessToken)
                log_util.debug('onReg for type 2, userData:%s'%(userData))
                if userData:
                    redis.hmset(table,
                        {
                            'nickname'      :   userData['nickname'],
                            'sex'           :   userData['sex'],
                            'headImgUrl'    :   userData['headimgurl']
                        }
                    )
                redis.srem(FORMAT_LOGIN_POOL_SET,account)
                return account, passwd
        redis.srem(FORMAT_LOGIN_POOL_SET,account)
    elif type == 3: #微信WEBcode登录
        tokenMessage = checkWeixinCodeWEB(account)
        if tokenMessage:
            password = account
            accessToken = tokenMessage["access_token"]
            refreshToken = tokenMessage["refresh_token"]
            openID = tokenMessage["openid"]
            userData = getWeixinData(openID, accessToken)
            unionid = userData['unionid']
            if redis.exists(WEIXIN2ACCOUNT%(unionid)):#  or redis.exists(WEIXIN2ACCOUNT%(unionid)):
                realAccount = redis.get(WEIXIN2ACCOUNT%(unionid))
                if not realAccount:
                    realAccount = redis.get(WEIXIN2ACCOUNT%(unionid))
                account2user_table = FORMAT_ACCOUNT2USER_TABLE%(realAccount)
                table = redis.get(account2user_table)
                redis.hmset(table, {'accessToken':accessToken, 'refreshToken':refreshToken, 'password':md5.new(password).hexdigest()})
            else:
                setOpenid2account4fish(openID, accessToken, refreshToken, ip, redis, account)
            redis.srem(FORMAT_LOGIN_POOL_SET,account)
            return unionid, password
        redis.srem(FORMAT_LOGIN_POOL_SET,account)
    elif type == 4: #微信WEBcode登录
        tokenMessage = checkWeixinCodeWEB(account)
        tokenMessage = checkWeixinCodeWEB(account)
        if tokenMessage:
            password = account
            accessToken = tokenMessage["access_token"]
            refreshToken = tokenMessage["refresh_token"]
            openID = tokenMessage["openid"]
            userData = getWeixinData(openID, accessToken)
            unionid = userData['unionid']
            if redis.exists(WEIXIN2ACCOUNT%(unionid)):#  or redis.exists(WEIXIN2ACCOUNT%(unionid)):
                realAccount = redis.get(WEIXIN2ACCOUNT%(unionid))
                if not realAccount:
                    realAccount = redis.get(WEIXIN2ACCOUNT%(unionid))
                account2user_table = FORMAT_ACCOUNT2USER_TABLE%(realAccount)
                table = redis.get(account2user_table)
                redis.hmset(table, {'accessToken':accessToken, 'refreshToken':refreshToken, 'password':md5.new(password).hexdigest()})
            else:
                setOpenid2account4fish(openID, accessToken, refreshToken, ip, redis, account)
            redis.srem(FORMAT_LOGIN_POOL_SET,account)
            return unionid, password
        redis.srem(FORMAT_LOGIN_POOL_SET,account)
    elif type == 0:
        tokenMessage = checkWeixinCodeWEB(account)
        account2user_table = FORMAT_ACCOUNT2USER_TABLE%(account)
        if redis.exists(account2user_table):
            table = redis.get(account2user_table)
            truePassword = redis.hget(table, 'password')
            if truePassword == md5.new(passwd).hexdigest():
                return account, passwd
    redis.srem(FORMAT_LOGIN_POOL_SET,account)
    return None, None

def saveHotUpDateSetting(redis,settingInfo,sys="HALL"):
    """
    保存热更新配置
    """
    if sys == 'HALL':
        hot_table = HOTUPDATE_TABLE
    else:
        hot_table = FISH_HOTUPDATE_TABLE

    return redis.hmset(hot_table,settingInfo)

def getHotSettingField(redis,field):
    """
    获取单个配置信息
    """
    return redis.hget(HOTUPDATE_TABLE,field)

def getHotSettingAll(redis):
    return redis.hgetall(HOTUPDATE_TABLE)

def get_fish_hall_setting(redis):
    return redis.hgetall(FISH_HOTUPDATE_TABLE)

def getUserByAccount(redis, account):
    """
    通过account获取玩家数据
    """
    account2user_table = FORMAT_ACCOUNT2USER_TABLE%(account)
    userTable = redis.get(account2user_table)
    return userTable

def do_sessionExpire(redis,session,SessionTable,SESSION_TTL):
    """
    刷新session
    """
    #refresh session
    redis.expire(session['session_key'],60*60)
    redis.expire(SessionTable,60*10)
    session.expire()

def check_session_verfiy(redis,api_name,SessionTable,account,sid,verfiySid):
    '''
    验证session是否合法
    return code,msg
    '''
    log_util.debug('[on refresh] account[%s] sid[%s]'%(account, sid))


    if verfiySid and sid != verfiySid:
        #session['member_account'],session['member_id'] = '',''
        return -4,'账号已在其他地方登录',False,'1'

    if redis.exists('kick:session:%s'%sid):
        return -4,'账号已在其他地方登录',False,'1'

    if not redis.exists(SessionTable) :
        return -3,'sid 超时',False,'',

    user_table = getUserByAccount(redis, account)
    if not redis.exists(user_table):
        return -5,'该用户不存在',False,''

    return 0,True,user_table,''

def packPrivaTeData4Game(chair, data, resp, proto):
    privateResp = proto()
    privateResp.ParseFromString(resp.privateData)
    for data in privateResp.data.gameInfo.roomInfo.playerList:
        if int(data.side) == int(chair):
            print 'replay side get,side:%s nickname:%s'%(data.side, data.nickname)
            privateResp.data.gameInfo.selfInfo.side = data.side
            privateResp.data.gameInfo.selfInfo.nickname = data.nickname
            privateResp.data.gameInfo.selfInfo.coin = data.coin
            privateResp.data.gameInfo.selfInfo.ip = data.ip
            privateResp.data.gameInfo.selfInfo.sex = data.sex
            privateResp.data.gameInfo.selfInfo.headImgUrl = data.headImgUrl
            privateResp.data.gameInfo.selfInfo.roomCards = 0
    resp.privateData = privateResp.SerializeToString()
    replayStr = resp.SerializeToString()
    return replayStr

def packPrivaTeData(chair, data):
    resp = replay4proto_pb2.ReplayData()
    resp.ParseFromString(data)
    refreshDataNameProtos = [mahjong_pb2.S_C_RefreshData, poker_pb2.S_C_RefreshData]
    for proto in refreshDataNameProtos:
        try:
            replayStr = packPrivaTeData4Game(chair, data, resp, proto)
            break
        except Exception as e:
            print 'packPrivaTeData error', e
    return replayStr

def getRuleText(rule, gameId, redis):
    ruleList = eval(rule)
    ruleText = '底分: %s\n'%(max(int(ruleList[-1]), 1))
    gameTable = GAME_TABLE%(gameId)

    for data in redis.lrange(USE_ROOM_CARDS_RULE%(gameId), 0, -1):
        datas = data.split(':')
        name, cards = datas[0], datas[1]
        try:
            playCount = int(datas[2])
        except:
            playCount = name
        if int(cards) == ruleList[-2]:
            ruleText += '局数: %s\n'%(playCount)

    num = 0
    for ruleNum in redis.lrange(GAME2RULE%(gameId), 0, -1):
        ruleTile, ruleType, rule = redis.hmget(GAME2RULE_DATA%(gameId, ruleNum), ('title', 'type', 'rule'))
        ruleDataList = rule.split(',')
        if int(ruleType) == 1:
            print '[on getRuleText]get ruleList[%s] num[%s]'%(ruleList, num)
            try:
                ruleText += '%s: %s\n'%(ruleTile, ruleDataList[int(ruleList[num])])
            except:
                ruleText += '%s: %s\n'%(ruleTile, ruleDataList[int(ruleList[num][0])])
        else:
            text = '%s: '%(ruleTile)
            textList = []
            for ruleData in ruleList[num]:
                textList.append(ruleDataList[ruleData])
            textData = ','.join(textList)
            text += textData
            ruleText =ruleText + text + '\n'
        num += 1
    ruleText = ruleText.decode('utf-8')
    return ruleText

def tryExitGroup(redis, userTable, account, id, groupId):
    pipe = redis.pipeline()
    key = redis.get(ACCOUNT2WAIT_JOIN_PARTY_TABLE%account)
    # for key in redis.keys(WAIT_JOIN_PARTY_ROOM_PLAYERS%('*', '*', '*')): #在等待匹配娱乐模式的话则离开列表
    if key:
        waitJoinList = redis.lrange(key, 0, -1)
        if account in waitJoinList:
            pipe.lrem(key, account)
    pipe.srem(FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE%(groupId), id) #上线代理需要获得
    pipe.hmset(userTable, {'parentAg':'', 'isVolntExitGroup':1,'lastGroup':groupId})
    #记录到省级公会的房卡
    topAgId = getTopAgentId(redis,groupId)
    roomcard = redis.get(USER4AGENT_CARD%(groupId,id))
    if not roomcard:
        roomcard = 0
    print '[try exitGroup] topAgId[%s] roomCards[%s]'%(topAgId,roomcard)
    pipe.set(USER4AGENT_CARD%(topAgId,id),int(roomcard))
    pipe.execute()

def getGroupIds(redis,groupId):
    """
    获取所有上级代理ID
    """
    Ids = []
    if redis.exists(AGENT_TABLE%(groupId)):
        parentId = redis.get(AGENT2PARENT%(groupId))
        if parentId:
            if int(parentId) == 1:
                return ['1']
            Ids.extend(getGroupIds(redis,parentId))
        else:
            Ids.append(parentId)

    return Ids

def getBroadcasts(redis,groupId,isNew=''):
    """
    获取广播列表
    """
    bIds = redis.lrange(HALL_BROADCAST_LIST,0,-1)
    broadInfos = []
    groupIds = getGroupIds(redis,groupId)
    groupIds.append(groupId)
    log_util.debug('[groupIds][%s] bids[%s]'%(groupIds,bIds))
    for bid in bIds:
        if redis.exists(FORMAT_BROADCAST_TABLE%(bid)):
            bInfos = redis.hgetall(FORMAT_BROADCAST_TABLE%(bid))
            if bInfos['ag'] in groupIds:
                broadInfos.append(bInfos)
        else:
            redis.lrem(FORMAT_BROADCAST_LIST_TABLE,'1',bid)

    broadcasts = {'broadcasts':broadInfos}

    if isNew:
        broadcasts['isNew'] = isNew

    return broadcasts

def getHallBroadInfo(redis,group_id,broad_table,broad_belone):
    """
    获取大厅广播列表
    """
    play_set = redis.smembers(HALL_BRO_PLAY_SET)
    broads = redis.lrange(broad_table%(1),0,-1)
    broad_list = []
    for broad in broads:
        if broad in play_set:
            broadDetail = {}
            broadInfo = redis.hgetall(HALL_BRO_TABLE%(broad))
            broadDetail['content'] = broadInfo['content']
            broadDetail['repeatInterval'] = int(broadInfo['per_sec'])
            broad_list.append(broadDetail)

    broads = redis.lrange(broad_table%(0),0,-1)
    for broad in broads:
        if broad in play_set:
            broadDetail = {}
            broadInfo = redis.hgetall(HALL_BRO_TABLE%(broad))
            broadDetail['content'] = broadInfo['content']
            broadDetail['repeatInterval'] = int(broadInfo['per_sec'])
            broad_list.append(broadDetail)
            return broad_list

    if broad_belone == 'HALL':
        broads = redis.lrange(HALL_BRO_CONTAIN_AG_LIST%(2,group_id),0,-1)
        for broad in broads:
            if broad in play_set:
                broadDetail = {}
                broadInfo = redis.hgetall(HALL_BRO_TABLE%(broad))
                broadDetail['content'] = broadInfo['content']
                broadDetail['repeatInterval'] = int(broadInfo['per_sec'])
                broad_list.append(broadDetail)
                return broad_list

        broads = redis.lrange(HALL_BRO_CONTAIN_AG_LIST%(3,group_id),0,-1)
        for broad in broads:
            if broad in play_set:
                broadDetail = {}
                broadInfo = redis.hgetall(HALL_BRO_TABLE%(broad))
                broadDetail['content'] = broadInfo['content']
                broadDetail['repeatInterval'] = int(broadInfo['per_sec'])
                broad_list.append(broadDetail)
                return broad_list

    return broad_list

def extendSession(redis,session,SessionTable):
    """
    延长session有效时间
    """
    redis.expire(session['session_key'],60*60)
    redis.expire(SessionTable,60*40)
