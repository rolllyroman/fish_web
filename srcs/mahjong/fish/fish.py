#-*- coding:utf-8 -*-
#!/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    捕鱼大厅接口
"""

from bottle import request, Bottle, redirect, response,default_app
from web_db_define import *
import mahjong_pb2
import poker_pb2
import replay4proto_pb2
from talk_data import sendTalkData
from wechat.wechatData import *
from common.install_plugin import install_redis_plugin,install_session_plugin
from common.log import *
from common.utilt import allow_cross,getInfoBySid
from fish_util.fish_func import *
from fish_util.fish_benefit_fun import can_take_benefit,get_should_sign_warheads
#from config.config import *
from fish_config import consts
from datetime import datetime, date, timedelta
from model.goodsModel import *
from model.userModel import do_user_modify_addr,do_user_del_addr,get_user_exchange_list
from model.hallModel import *
from model.protoclModel import sendProtocol2GameService
from model.mailModel import *
from model.fishModel import get_room_list, check_spring_time
from common import web_util,log_util,convert_util
import time
import urllib2
import json
import random
import md5
import re
import pdb
from urlparse import urlparse
#from pyinapp import *
ACCEPT_NUM_BASE = 198326
ACCEPT_TT = [md5.new(str(ACCEPT_NUM_BASE+i)).hexdigest() for i in xrange(10)]
SESSION_TTL = 60*60

#生成捕鱼APP
fish_app = Bottle()
#获取配置
conf = default_app().config
#安装插件
install_redis_plugin(fish_app)
install_session_plugin(fish_app)

import fish_broad
import fish_invite
import fish_pay
import fish_exchange
import fish_benefit
import fish_spring
import fish_friend
import fish_bag

FORMAT_PARAMS_POST_STR = "%s = request.forms.get('%s','').strip()"
FORMAT_PARAMS_GET_STR  = "%s = request.GET.get('%s','').strip()"
#用户信息
USER_INFO = ('headImgUrl', 'sex', 'isVolntExitGroup','coin','exchange_ticket')

@fish_app.post('/new/login')
@allow_cross
def do_inner(redis,session):
    '''
        一键注册登录 或 昵称登录
    '''
    clientType = request.forms.get('clientType', '').strip()
    action = request.forms.get('action', '').strip()
    nickname = request.forms.get('nickname', '').strip()
    pwd = request.forms.get('pwd', '').strip()

    curTime = datetime.now()
    ip = web_util.get_ip()
    getIp = request['REMOTE_ADDR']

    # 昵称登录
    if action == '1':
        return login_handler(redis,ip,nickname=nickname,passwd=pwd,login_type=6,clientType=clientType,session=session)
    # 一键注册
    elif action == '2':
        return login_handler(redis,ip,nickname=nickname,passwd=pwd,login_type=7,clientType=clientType,session=session)

"""
@fish_app.post('/create/role')
#@allow_cross
def do_inner(redis,session):
    '''
        创造二级账号
    '''
    sid = request.forms.get('sid', '').strip()
    nickname = request.forms.get('nickname', '').strip()

    if redis.sismember('fish:nickname:set',nickname):
        return {'code':-1,'msg':'创建失败!该昵称已存在!'}

    uid_1 = redis.hget(FORMAT_USER_HALL_SESSION%(sid),'uid')
    final_pwd,ip = redis.hmget('users:%s'%uid_1,'password','lastLoginIP')
    
    c_pwd,uid = register_by_nickname(redis,ip,nickname,passwd="",alevel=2,final_pwd=final_pwd,choose_flag=2)

    # 添加到一级账号的下级账号集合
    redis.sadd('user:%s:roles:set'%uid_1,nickname)
    # 二级拥有上级
    redis.hset('users:%s'%uid,'senior',uid_1)
    
    return {'code':0,'msg':'创建成功!','uid':uid}

@fish_app.post('/choose/enter')
#@allow_cross
def do_inner(redis,session):
    '''
        选择角色进入游戏
    '''
    sid = request.forms.get('sid', '').strip()
    nickname = request.forms.get('nickname', '').strip()

    uid_1 = redis.hget(FORMAT_USER_HALL_SESSION%(sid),'uid')
    clientType = redis.hget('users:%s'%uid_1,'lastClientLoginType')

    uid = redis.get('nickname2uid:%s'%nickname)

    if redis.hget('users:%s'%uid,'senior') != uid_1:
        return {'code':-1,'msg':'账号不匹配!'}
         
    final_pwd,ip = redis.hmget('users:%s'%uid,'password','lastLoginIP')
    return login_handler(redis,ip,nickname,'',6,clientType,session,choose_flag=1)
"""

# 昵称登录处理方法
def login_handler(redis,ip,nickname,passwd,login_type,clientType,session,choose_flag=0):

    if choose_flag != 2:
        curTime = str(datetime.now())[:10]
        uid = redis.get('nickname2uid:%s'%nickname)
        '''
        # 首次昵称登录即注册 
        if not uid:
            # 判断昵称是否重复    
            if redis.sismember('fish:nickname:set',nickname):
                return {'code':-1,'msg':'昵称已存在！请换个昵称！'}
            # 不重复则注册
            c_pwd,uid = register_by_nickname(redis,ip,nickname,passwd,1) 
        '''

    # 快速注册登录处理
    is_new_reg = 0
    if login_type == 7:
        c_pwd,uid = register_by_nickname(redis,ip,nickname,passwd,1,7) 
        is_new_reg = 1
        passwd = c_pwd
    
    # 直接登录 或 注册后登录验证
    # 用户信息
    alevel,account,valid,real_pwd,last_login_date = redis.hmget('users:%s'%uid,'alevel','account','valid','password','lastLoginDate') 

    # 验证密码
    if md5.new(passwd).hexdigest()!=real_pwd and choose_flag==0:
        return {'code':4,'msg':'密码错误!'}
      
    # 冻结后不能登录
    if int(valid) == 0:
        redis.srem(FORMAT_LOGIN_POOL_SET,account)
        return {'code':105,'msg':'该帐号被冻结,请与客服联系'}

    # 已登录则踢除大厅中的账号
    exist_sid = redis.get('session:%s'%uid)
    redis.delete('hall:session:%s'%exist_sid) 
    redis.set('kick:session:%s'%exist_sid,str(uid))
    redis.expire('kick:session:%s'%exist_sid,200)

    # 账号游戏中则踢除
    if redis.sismember(ONLINE_ACCOUNTS_TABLE4FISH, account):
        key = FORMAT_CUR_USER_GAME_ONLINE%(account)
        if key:
            gameNum = redis.hget(key, 'game')
            if gameNum:
                # gameId = redis.hget(ROOM2SERVER%(gameNum), 'gameid')
                playerSid = redis.get(FORMAT_USER_PLATFORM_SESSION%(uid))
                sendProtocol2GameService(redis, gameNum, HEAD_SERVICE_PROTOCOL_KICK_MEMBER4REPEAT%(account, playerSid))

    # 生成sid
    sid = md5.new(str(uid)+str(time.time())).hexdigest()
    SessionTable = FORMAT_USER_HALL_SESSION%(sid)
    if redis.exists(SessionTable):
        log_util.debug("[try do_login] account[%s] sid[%s] is existed."%(curTime,realAccount,sid))
        redis.srem(FORMAT_LOGIN_POOL_SET,account)
        return {'code':1, 'msg':'链接超时'}

    loginMsg = []
    isSpring = ''
    # 每日签到 送金币
    last_sign_date = redis.hget("users:%s"%uid,"last_sign_date")
    if last_sign_date != str(datetime.now())[:10]:
        # redis.hincrby('users:%s'%uid, 'coin', consts.GIVE_COIN_FIRST_LOGIN)
        sign_warheads = get_should_sign_warheads(redis,uid)
        loginMsg.append('恭喜您获得内测每天奖励%s金币'%(sign_warheads))

    redis.set(FORMAT_USER_PLATFORM_SESSION%(uid),sid)
    redis.sadd(FORMAT_LOGIN_POOL_SET,account)

    #更新登录IP和登陆日期
    redis.hmset('users:%s'%uid, {'lastLoginIp':request.remote_addr, 'lastLoginDate':datetime.now().strftime("%Y-%m-%d %H:%M:%S"), \
            'lastLoginClientType':clientType})

    #记录session信息
    session['member_id'] = uid
    session['member_account'] = account
    session['member_lastIp'] = ip
    session['member_lastDate'] = last_login_date
    session['session_key']  = sid
    pipe = redis.pipeline()
    pipe.hmset(SessionTable, {'account':account,'uid':uid,'sid':sid,'loginIp':ip})
    pipe.set('session:%s'%uid,sid)
    # session有效时间
    pipe.expire(SessionTable, 60*40)
    pipe.execute()

    nickname,openid = redis.hmget('users:%s'%uid,'nickname','openid') 
    userInfo = {'passwd':passwd,'name':nickname,'isTrail':1,'shop':1,'group_id':1,'account':account,'uid':uid,'is_weixin_user':1 if openid else 0}

    roles = []
    if alevel == '1':
        roles = list(redis.smembers('user:%s:roles:set'%uid))
    roles.append(redis.hget('users:%s'%uid,'nickname'))

    res = {'isSpring':False,'code':0, 'sid':sid, 'userInfo':userInfo, 'loginMsg': loginMsg,'is_new_reg':is_new_reg}#'roles':roles}

    # 登录时默认给安全箱上锁
    if redis.hget('users:%s'%uid,'box_pwd'):
        redis.hset('users:%s'%uid,'box_lock','1')
    
    if is_new_reg:
        pass
        #res['c_pwd'] = c_pwd
    return res

@fish_app.post('/login')
@allow_cross
def do_login(redis,session):
    """
    大厅登录接口
    """

    tt = request.forms.get('tt', '').strip()
    curTime = datetime.now()
    ip = web_util.get_ip()
    getIp = request['REMOTE_ADDR']
    _account = request.forms.get('account', '').strip()
    nickname = request.forms.get('nickname', '').strip()
    clientType = request.forms.get('clientType', '').strip()
    if not clientType:
        clientType = 0
    passwd = request.forms.get('passwd', '').strip()
    login_type = request.forms.get('type', '').strip() #登录类型
    login_type = int(login_type or 0)
    sid=0

    """
    # 昵称登录
    if login_type in [6,7]:
        return login_handler(redis,ip,nickname,passwd,login_type,clientType,session)
    # 新微信登录 或 测试账号登录
    else:
        # flag
        pass
        #return onRegFish_new(redis,_account,passwd,login_type,ip,clientType,session)
    """

    try:
        log_util.debug('[on login]account[%s] clientType[%s] passwd[%s] type[%s]'%(_account, clientType, passwd, login_type))
    except Exception as e:
        print 'print error File', e

    login_pools = redis.smembers(FORMAT_LOGIN_POOL_SET)
    log_util.debug('[try do_login] account[%s] login_pools[%s]'%(_account,login_pools))

    '''
    if _account in login_pools:
        log_util.debug('[try do_login] account[%s] is already login.'%(_account))
        return {'code':-2,'msg':'account in login_pools'}
    '''

    redis.sadd(FORMAT_LOGIN_POOL_SET,_account)
    log_util.debug('[try do_login] account[%s] login_pools[%s]'%(_account,login_pools))
    reAccount, rePasswd = onRegFish(redis, _account, passwd, login_type, ip)

    if reAccount:
        if login_type:
            realAccount = redis.get(WEIXIN2ACCOUNT%(reAccount))
            # if not realAccount:
                # realAccount = redis.get(WEIXIN2ACCOUNT%(reAccount))
                # redis.set(WEIXIN2ACCOUNT%(reAccount), realAccount)
        else:
            realAccount = reAccount
        #读取昵称和group_id
        account2user_table = FORMAT_ACCOUNT2USER_TABLE%(realAccount)
        userTable = redis.get(account2user_table)
        id = userTable.split(':')[1]
        # 登录时默认给安全箱上锁
        if redis.hget('users:%s'%id,'box_pwd'):
            redis.hset('users:%s'%id,'box_lock','1')
        if not redis.sismember(ACCOUNT4WEIXIN_SET4FISH, realAccount): #初次登录
            redis.sadd(ACCOUNT4WEIXIN_SET4FISH, realAccount)
            redis.sadd(FORMAT_REG_DATE_TABLE4FISH%(curTime.strftime("%Y-%m-%d")), realAccount)
            redis.hset(userTable, 'coin', consts.GIVE_COIN_FIRST_LOGIN)
        if redis.exists(UNIONID2GROUP%reAccount):
            unionId = reAccount
            needJoinGroup = redis.get(UNIONID2GROUP%unionId)
            adminTable = AGENT_TABLE%(needJoinGroup)
            if redis.exists(adminTable):
                agValid, auto_check, groupType = redis.hmget(adminTable, ('valid', 'auto_check', 'type'))
                if agValid == '1' and groupType != '1':
                    if not auto_check:
                        auto_check = CHECK_SUCCESS
                    pipe = redis.pipeline()
                    if auto_check == CHECK_SUCCESS:
                        pipe.hset(FORMAT_USER_TABLE%(id), 'parentAg', needJoinGroup)
                        pipe.sadd(FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE%(needJoinGroup), id)
                    pipe.lpush(JOIN_GROUP_LIST%(needJoinGroup), id)
                    pipe.set(JOIN_GROUP_RESULT%(id), '%s:%s:%s'%(needJoinGroup, auto_check, curTime.strftime('%Y-%m-%d %H:%M:%S')))
                    pipe.execute()
        account, name, groupId,loginIp, loginDate, picUrl, gender,valid, lockCount,openid = \
                redis.hmget(userTable, ('account', 'nickname', 'parentAg', 'lastLoginIp',\
                'lastLoginDate', 'picUrl', 'gender','valid', 'lockCount','openid'))
        if not lockCount:
            lockCount = 0
        else:
            lockCount = int(lockCount)
        agentTable = AGENT_TABLE%(groupId)
        isTrail,shop = redis.hmget(agentTable,('isTrail','recharge'))
        if not isTrail:
            isTrail = 0

        #默认开放上次
        shop = 1

        shop = int(shop)
        if int(valid) == 0:
            #冻结后不能登录
            redis.srem(FORMAT_LOGIN_POOL_SET,_account)
            return {'code':105,'msg':'该帐号被冻结,请与客服联系'}

        #会话信息
        type2Sid = {
            True     :  sid,
            False    :  md5.new(str(id)+str(time.time())).hexdigest()
        }
        sid = type2Sid[login_type == 3]
        SessionTable = FORMAT_USER_HALL_SESSION%(sid)
        if redis.exists(SessionTable):
            log_util.debug("[try do_login] account[%s] sid[%s] is existed."%(curTime,realAccount,sid))
            redis.srem(FORMAT_LOGIN_POOL_SET,account)
            return {'code':-1, 'msg':'链接超时'}

        #同一账号不能同时登录
        loginMsg = []
        isSpring = ''
        if type==3:##网页登录不更新session
            pass
        else:
            redis.set(FORMAT_USER_PLATFORM_SESSION%(id),sid)

        #更新登录IP和登陆日期
            redis.hmset(userTable, {'lastLoginIp':request.remote_addr, 'lastLoginDate':datetime.now().strftime("%Y-%m-%d %H:%M:%S"), \
                    'lastLoginClientType':clientType})

            #记录session信息
            session['member_id'] = id
            session['member_account'] = account
            session['member_lastIp'] = loginIp
            session['member_lastDate'] = loginDate
            session['session_key']  = sid
            pipe = redis.pipeline()
            pipe.hmset(SessionTable, {'account':account,'uid':id,'sid':sid,'loginIp':ip})
            pipe.expire(SessionTable, 60*40)
            pipe.execute()

            # 春节活动
            isSpring, springInfo = check_spring_time(redis, False)

            #if (not loginDate) or loginDate.split(' ')[0] != datetime.now().strftime("%Y-%m-%d"): #当日没登录过，即第一次登录
            if redis.hget("users:%s"%id,"last_sign_date") != datetime.now().strftime("%Y-%m-%d"): 
                # redis.hincrby(userTable, 'coin', consts.GIVE_COIN_DAY_LOGIN)
                sign_warheads = get_should_sign_warheads(redis,id)  
                loginMsg.append('恭喜您获得内测每天奖励%s金币'%(sign_warheads))
                if lockCount < consts.GIVE_LOCK_COUNT_DAY_LOGIN_MAX:
                    addLockCount = min(consts.GIVE_LOCK_COUNT_DAY_LOGIN_MAX - lockCount, consts.GIVE_LOCK_COUNT_DAY_LOGIN)
                    redis.hincrby(userTable, 'lockCount', addLockCount)

                curDate = str(datetime.now().date())
                print(u"判断当天时间%s" % curDate)
                '''
                if curDate in ["2018-02-08", "2018-02-17", "2018-02-21"]:
                    print(u"领取排行榜的奖品:%s" % curDate)
                    order = redis.hgetall("fish:redpick:account:hesh")
                    __switch = {
                        0: 8000000,
                        1: 6000000,
                        2: 4000000,
                        3: 3000000,
                        4: 3000000,
                        5: 2000000,
                        6: 2000000,
                        7: 2000000,
                        8: 1000000,
                        9: 1000000,
                    }
                    order = sorted(order.items(), key=lambda x: -int(x[1]))[:10]
                    if account in dict(order).keys():
                        for index, value in enumerate(order):
                            if value[0] == account:
                                loginMsg.append("奖券排行榜第%s名,获得金币%s"% (index+1, __switch[index]))
                                redis.hincrby(userTable, 'coin', __switch[index])
                                break
                '''



        urlRes = urlparse(request.url)
        serverIp = ''
        serverPort = 0
        gameid = 0
        # exitPlayerData = EXIT_PLAYER%(realAccount)
        # print '[hall][login]exitPlayerData[%s]'%(exitPlayerData)
        # if redis.exists(exitPlayerData):
            # serverIp, serverPort, game = redis.hmget(exitPlayerData, ('ip', 'port', 'game'))
            # print '[hall][login]exitPlayerData get succed, ip[%s], serverPort[%s], game[%s]'%(serverIp, serverPort, game)
            # serverIp = urlRes.netloc.split(':')[0]
            # gameid = redis.hget(ROOM2SERVER%(game), 'gameid')
            # try:
                # int(gameid)
            # except:
                # serverIp = ''
                # serverPort = 0
                # gameid = 0
                # redis.delete(exitPlayerData)
                # print '[hall][login][delete] exitPlayerData[%s]'%(exitPlayerData)
        if redis.sismember(ONLINE_ACCOUNTS_TABLE4FISH, realAccount):
            key = FORMAT_CUR_USER_GAME_ONLINE%(realAccount)
            if key:
                gameNum = redis.hget(key, 'game')
                if gameNum:
                    # gameId = redis.hget(ROOM2SERVER%(gameNum), 'gameid')
                    playerSid = redis.get(FORMAT_USER_PLATFORM_SESSION%(id))
                    sendProtocol2GameService(redis, gameNum, HEAD_SERVICE_PROTOCOL_KICK_MEMBER4REPEAT%(realAccount, playerSid))

        userInfo = {'name':name,'isTrail':int(isTrail),'shop':int(shop),'group_id':groupId,'account':reAccount ,'passwd':rePasswd,'is_weixin_user':1 if openid else 0}
        joinNum = ''
        id = userTable.split(':')[1]
        joinMessage = redis.get(JOIN_GROUP_RESULT%(id))
        if joinMessage:
            joinMessage = joinMessage.split(':')
            joinNum = int(joinMessage[0])
            joinResult = int(joinMessage[1])
            userInfo['applyId'] = joinNum
            if joinResult == 1:
                redis.delete(JOIN_GROUP_RESULT%(id))

        key = redis.get(ACCOUNT2WAIT_JOIN_PARTY_TABLE%account)
        # for key in redis.keys(WAIT_JOIN_PARTY_ROOM_PLAYERS%('*', '*', '*')):
        if key:
            if account in redis.lrange(key, 0, -1):
                try:
                    gameId, serviceTag = redis.get('account:%s:wantServer'%account).split(',')
                    message = HEAD_SERVICE_PROTOCOL_NOT_JOIN_PARTY_ROOM%(account, ag)
                    redis.lpush(FORMAT_SERVICE_PROTOCOL_TABLE%(gameId, serviceTag), message)
                except:
                    print '[account wantServer][%s]'%(redis.get('account:%s:wantServer'%account))
                redis.lrem(key, account)
        coin = redis.hincrby(userTable, 'coin', 0)
        redis.zadd(FORMAT_USER_COIN_TABLE, account, coin)
        if not redis.zscore(FORMAT_USER_COINDELTA_TABLE, account):
            redis.zadd(FORMAT_USER_COINDELTA_TABLE, account, 0)

            

        if serverIp:
            urlRes = urlparse(request.url)
            domain = urlRes.netloc.split(':')[0]
            gameInfo = {'ip':domain, 'port':int(serverPort), 'gameid':gameid}

            gameState = {}
            gameTable = GAME_TABLE%(gameid)
            if redis.exists(gameTable):
                name, webTag, version,packName = redis.hmget(gameTable, ('name', 'web_tag', 'version','pack_name'))
                gameState[gameid] = {
                    'id'                :           gameid,
                    'name'              :           name,
                    'web_tag'           :           webTag,
                    'version'           :           version,
                    'downloadUrl'       :           packName
                }

            if joinNum:
                redis.srem(FORMAT_LOGIN_POOL_SET,_account)
                return {'code':0, 'sid':sid, 'userInfo':userInfo,\
                    'gameInfo':gameInfo, 'joinResult':joinResult, 'gameState':gameState}
            redis.srem(FORMAT_LOGIN_POOL_SET,_account)
            return {'code':0, 'sid':sid, 'userInfo':userInfo, 'gameInfo':gameInfo, 'gameState':gameState}
        else:
            if joinNum:
                redis.srem(FORMAT_LOGIN_POOL_SET,_account)
                return {'code':0, 'sid':sid, 'userInfo':userInfo, 'joinResult':joinResult, 'loginMsg':loginMsg, 'isSpring':isSpring}
            redis.srem(FORMAT_LOGIN_POOL_SET,account)
            return {'code':0, 'sid':sid, 'userInfo':userInfo, 'loginMsg': loginMsg, 'isSpring':isSpring}
    else: #失败
        redis.srem(FORMAT_LOGIN_POOL_SET,_account)
        return {'code':101, 'msg':'账号或密码错误或者微信授权失败'}

@fish_app.post('/refresh')
@allow_cross
def do_refresh(redis,session):
    """
    Refresh接口
    """
    ip = web_util.get_ip()
    curTime = datetime.now()
    fields = ('sid',)
    for field in fields:
        exec(FORMAT_PARAMS_POST_STR%(field,field))

    try:
        log_util.debug('[try do_refresh] get params sid[%s]'%(sid))
    except:
        return {'code':-300,'msg':'接口参数请求失败'}

    k_uid=redis.get('kick:session:%s'%sid)
    if k_uid:
        return {'code':-4,'msg':'您的账号已在其它地方登录。','osid':'1'}

    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    check_code,check_msg,user_table,osid = check_session_verfiy(redis,'/fish/refresh/',SessionTable,account,sid,verfiySid)
    log_util.debug('[try do_refresh] check_code[%s] check_msg[%s]'%(check_code,check_msg))
    if int(check_code)<0:
        if check_code == -4:
            return {'code':check_code,'msg':check_msg,'osid':'1'}
        return {'code':check_code,'msg':check_msg}

    #refresh session
    do_sessionExpire(redis,session,SessionTable,SESSION_TTL)
    #获取用户信息
    head_url, gender, isVolntExitGroup,coin,exchange_ticket = redis.hmget(user_table,USER_INFO)
    diamond,warhead,info_comp,openid,vip_level,vip_charge = redis.hmget(user_table,'diamond','warhead','info_comp','openid','vip_level','vip_charge')
    info_comp = int(info_comp or 0)
    log_util.debug('[try do_refresh] userId[%s] gender[%s] coin[%s]'%(uid,gender,coin))
    #group_table = AGENT_TABLE%(groupId)
    #isTrail = redis.hget(group_table,'isTrail')
    #isTrail = convert_util.to_int(isTrail)
    exchange_ticket = convert_util.to_int(exchange_ticket)

    #hasBroad = False
    # if redis.exists(FORMAT_BROADCAST_LIST_TABLE):
    #     #有广播内容
    #     hasBroad = True
    timestamp = time.strftime("%Y-%m-%d",
                              time.localtime(time.time()))
    #判断是否能领取奖励
    if redis.sismember(FISH_SHARE_NOT_TAKE_SETS,uid):
        is_take_reward = 1
    elif redis.sismember(FISH_SHARE_TAKE_SETS % timestamp,uid):
        is_take_reward = 2
    else: #未分享
        is_take_reward = 0

    #判断是否能领取救济金
    code,_,_, = can_take_benefit(redis,uid,user_table)
    if code < 0:
        canTakeBenefit = 0
    else:
        canTakeBenefit = 1

    share_coin,exchange_shop,hall_shop,shop_version,exchange_shop_ver = \
                    redis.hmget(FISH_CONSTS_CONFIG,('share_coin','exchange_shop','hall_shop','shop_version','exchange_shop_ver'))

    today = str(datetime.now())[:10]
    today_fish = redis.get('user:%s:gain:fish:date:%s'%(uid,today)) 
    today_coins = redis.get('user:%s:gain:coins:date:%s'%(uid,today)) 
    today_warheads = redis.get('user:%s:gain:warheads:date:%s'%(uid,today)) 
    userInfo = {  #用户数据
            'diamond'           :       int(diamond or 0),
            'warhead'           :       int(warhead or 0),
            'id'                :       uid,
            'ip'                :       ip,
            'picUrl'            :       head_url,
            'exchangeTicket'    :       exchange_ticket,                         #兑换券
            'isTakeReward'      :       is_take_reward,                          # 0-为分享 1-未领取 2-已领取
            'shareCoin'         :       convert_util.to_int(share_coin),             #分享赠送金币金额
            'gender'            :       gender,
            'isTrail'           :       0,
            'shop'              :       convert_util.to_int(hall_shop),             #大厅商城是否开放
            'exchangeShop'      :       convert_util.to_int(exchange_shop),         #兑换商城是否开放
            'coin'              :       convert_util.to_int(coin),
            'canTakeBenefit'    :       canTakeBenefit,                              #是否能领取救济金
            'info_comp'         :       info_comp,
            'is_weixin_user'    :       1 if openid else 0,
            'today_fish'        :       today_fish or 0,
            'today_coins'       :       today_coins or 0,
            'today_warheads'    :       today_warheads or 0,
            'vip_levels'        :       int(vip_level or 0),
            'vip_charge'        :       int(vip_charge or 0),
    }

    lobbyInfo = get_fish_hall_setting(redis)
    #获取roomInfo
    roomInfo  = get_room_list(redis,False,False)
    lobbyInfo['hotUpdateURL'] = lobbyInfo['hotUpdateURL']+"/"+lobbyInfo['packName']
    log_util.info('[try do_refresh] roomInfo[%s] userInfo[%s] lobbyInfo[%s]'%(roomInfo,userInfo,lobbyInfo))


    return {
                'code':0,
                'lobbyInfo':lobbyInfo,
                'hasBroad':False,
                'shopVerison':convert_util.to_int(shop_version),
                'exchangeShopVersion':convert_util.to_int(exchange_shop_ver),
                'roomInfo':roomInfo,
                'userInfo':userInfo
     }

@fish_app.post('/getShopInfo')
@allow_cross
def get_fish_goods_info(redis,session):
    '''
    捕鱼获取商城商品接口
    '''
    fields = ('sid',)
    for field in fields:
        exec(FORMAT_PARAMS_POST_STR%(field,field))

    try:
        log_util.debug('[try get_fish_goods_info] get params sid[%s]'%(sid))
    except:
        return {'code':-300,'msg':'接口参数请求错误'}

    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    check_code,check_msg,user_table,osid = check_session_verfiy(redis,'/fish/getShopInfo/',SessionTable,account,sid,verfiySid)

    log_util.debug('[try do_refresh] check_code[%s] check_msg[%s]'%(check_code,check_msg))
    if int(check_code)<0:
        if check_code == -4:
            return {'code':check_code,'msg':check_msg,'osid':osid}
        return {'code':check_code,'msg':check_msg}

    goods_info = get_coin_goods_list(redis)
    # ----------------添加兑换套餐信息--------------------
    exchangesInfo = []
    for cid in redis.smembers('currency:change:course:set'):
        dic = redis.hgetall("currency:change:course:%s:hesh"%cid)    
        dic['cid'] = cid
        exchangesInfo.append(dic)
    # ----------------添加兑换套餐信息--------------------
    log_util.debug('[try get_fish_goods_info]  sid[%s] goodsInfo[%s]'%(sid,goods_info))
    return {'code':0,'goodsInfo':goods_info,'exchangesInfo':exchangesInfo}

@fish_app.post('/onGetShareReward')
@allow_cross
def get_fish_share_reward(redis,session):
    """
    金币分享获取金币接口
      分享游戏成功后回调获取分享金币
    """
    fields = ('sid',)
    for field in fields:
        exec(FORMAT_PARAMS_POST_STR%(field,field))

    try:
        log_util.debug('[try get_fish_share_reward] get params sid[%s]'%(sid))
    except:
        return {'code':-300,'msg':'接口请求参数错误'}

    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    check_code,check_msg,user_table,osid = check_session_verfiy(redis,'/fish/getRewardInfo/',SessionTable,account,sid,verfiySid)
    log_util.debug('[try do_refresh] check_code[%s] check_msg[%s]'%(check_code,check_msg))
    if int(check_code)<0:
        if check_code == -4:
            return {'code':check_code,'msg':check_msg,'osid':osid}
        return {'code':check_code,'msg':check_msg}
    timestamp = time.strftime("%Y-%m-%d",
                              time.localtime(time.time()))
    has_share_users = uid in redis.smembers(FISH_FIRST_SHARE_PER_DAY_SET % timestamp)
    is_ready_share    = uid in redis.smembers(FISH_SHARE_NOT_TAKE_SETS)
    is_take_share    = uid in redis.smembers(FISH_SHARE_TAKE_SETS % timestamp)

    # if not has_share_users:
    #     return {'code':-3000,'msg':'你今天还未分享过游戏,赶快去分享吧!'}
    #
    if is_take_share:
        return {'code':-3002,'msg':'你今天已经领取过奖励!'}

    share_coin = redis.hget(FISH_CONSTS_CONFIG,'share_coin')
    if not share_coin:
        return {'code':-3001,'msg':'error in get share_coin,try again.'}
    pipe = redis.pipeline()
    try:
        pipe.srem(FISH_SHARE_NOT_TAKE_SETS,uid)
        pipe.sadd(FISH_SHARE_TAKE_SETS % timestamp,uid)
        pipe.hincrby(user_table,'coin',share_coin)
    except:
        return {'code':-3003,'msg':'数据错误'}

    pipe.execute()
    coin = convert_util.to_int(redis.hget(user_table,'coin'))
    log_util.debug('[try get_fish_share_reward] sid[%s] get shareCoin[%s] after user coin[%s]'%(sid,share_coin,coin))
    return {'code':0,'coin':coin}

@fish_app.post('/onShareCallback')
@allow_cross
def on_shareCallback(redis,session):
    """
    用户分享回调接口
    :params  sid 用户sid
    :return code 0 成功  -1<均视为失败
    """
    fields = ('sid',)
    for field in fields:
        exec(FORMAT_PARAMS_POST_STR%(field,field))

    try:
        log_util.debug('[try on_shareCallback] get params sid[%s]'%(sid))
    except:
        return {'code':-300,'msg':'接口请求参数错误'}

    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    check_code,check_msg,user_table,osid = check_session_verfiy(redis,'/fish/onShareCallback',SessionTable,account,sid,verfiySid)
    log_util.debug('[try do_refresh] check_code[%s] check_msg[%s]'%(check_code,check_msg))
    if int(check_code)<0:
        if check_code == -4:
            return {'code':check_code,'msg':check_msg,'osid':osid}
        return {'code':check_code,'msg':check_msg}
    timestamp = time.strftime("%Y-%m-%d",
                              time.localtime(time.time()))
    if uid in redis.smembers(FISH_FIRST_SHARE_PER_DAY_SET % timestamp):
        return {'code':-4001,'msg':'uid[%s] already share.'%(uid)}

    pipe = redis.pipeline()
    try:
        pipe.sadd(FISH_FIRST_SHARE_PER_DAY_SET % timestamp,uid)
        pipe.sadd(FISH_SHARE_NOT_TAKE_SETS,uid)
        pipe.incr(FISH_SHARE_TOTAL,1)
    except:
        log_util.error('[try on_shareCallback] add to set error. sid[%s] reason[%s]'%(sid,e))
        return {'code':-4000,'msg':'data error. retry please!'}

    pipe.execute()
    return {'code':0}

@fish_app.get('/getHallVersion')
@allow_cross
def getHallVersion(redis,session):
    """
    获取捕鱼更新包接口
    """
    HALL2VERS = get_fish_hall_setting(redis)
    HALL2VERS['hotUpdateURL'] = HALL2VERS['hotUpdateURL']+"/"+HALL2VERS['packName']
    return HALL2VERS

@fish_app.get('/extendSession')
@allow_cross
def do_extendSession(redis,session):
    """
    游戏中延长session有效时间接口
    """
    ip = web_util.get_ip()
    api_path = request.path
    log_util.debug('user ip[%s] remote_ip[%s] path[%s]'%(ip,request['REMOTE_ADDR'],request.path))
    sid = request.GET.get('sid','').strip()

    SessionTable = FORMAT_USER_HALL_SESSION%(sid)
    if not redis.exists(SessionTable):
        return {'code':1}

    extendSession(redis,session,SessionTable)
    return {'code':0}


@fish_app.post('/joinRoom')
@allow_cross
def do_joinRoom(redis,session):
    """
    加入房间接口
    """
    fields = ('sid','gameid')#,'house_no')
    for field in fields:
        exec('%s = request.forms.get("%s",'').strip()'%(field,field))

    house_no = request.forms.get("house_no",'').strip()
    # 判断该房间是否满员
    if house_no:
        max_player_count = int(redis.hget('fish:channel:%s:info'%gameid,'max_player_count'))
        player_num = int(redis.hget('fish:%s:house:%s:info'%(gameid,house_no),'player_num') or 0)
        online_tables = redis.keys('hall:session:*') 
        if house_no not in set([str(i) for i in range(1,12+len(online_tables))]):
            return {'code':1,'msg':'房间不存在！'}
        if player_num >= max_player_count:
            return {'code':1,'msg':'房间已满员！'}
      

    try:
        log_util.debug('[try do_joinRoom] get params sid[%s] gameid[%s]'%(sid,gameid))
        gameId = int(gameid)
    except:
        return {'code':-300,'msg':'接口参数错误'}

    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    # 将uid加入每日活跃统计用户表
    now_day = str(datetime.now())[:10]
    if uid:
        redis.sadd('active:users:date:%s'%now_day,uid)

    check_code,check_msg,user_table,osid = check_session_verfiy(redis,'/fish/getRewardInfo/',SessionTable,account,sid,verfiySid)
    log_util.debug('[try do_refresh] check_code[%s] check_msg[%s]'%(check_code,check_msg))
    if int(check_code)<0:
        if check_code == -4:
            return {'code':check_code,'msg':check_msg,'osid':osid}
        return {'code':check_code,'msg':check_msg}

    ag = redis.hget(user_table, 'parentAg')
    adminTable = AGENT_TABLE%(ag)
    agValid = redis.hget(adminTable,'valid')
    # if agValid != '1':
        # print  '[CraeteRoom][info] agentId[%s] has freezed. valid[%s] '%(ag,agValid)
        # return {'code':-7,'msg':'该公会已被冻结,不能创建或加入该公会的房间'}

    countPlayerLimit = 0
    gameTable = GAME_TABLE%(gameId)
    maxRoomCount = redis.hget(gameTable,'maxRoomCount')
    if not maxRoomCount:
        maxRoomCount = 0
    maxPlayerCount = redis.hget(FISH_ROOM_TABLE%(gameId), 'max_player_count')
    if maxRoomCount and maxPlayerCount:
        countPlayerLimit = int(maxRoomCount) * maxPlayerCount

    reservedServers = []
    serverList = redis.lrange(FORMAT_GAME_SERVICE_SET%(gameId), 0, -1)
    for serverTable in serverList:
        playerCount = redis.hincrby(serverTable, 'playerCount', 0)
        roomCount = redis.hincrby(serverTable, 'roomCount', 0)
        if not playerCount:
            playerCount = 0
        if not roomCount:
            roomCount = 0
        playerCount = int(playerCount)
        roomCount = int(roomCount)
        countPlayerLimit = int(countPlayerLimit)
        if countPlayerLimit and (playerCount >= countPlayerLimit or roomCount >= maxRoomCount):
            continue
        _, _, _, currency, ipData, portData = serverTable.split(':')
        reservedServers.append((currency, ipData, portData))

    if reservedServers:
        currency, serverIp, serverPort = reservedServers[0]
        if redis.exists(EXIT_PLAYER_FISH%(account, gameId)):
            ip, port = redis.hmget(EXIT_PLAYER_FISH%(account, gameId), ('ip', 'port'))
            for reservedServer in reservedServers:
                _currency, _serverIp, _serverPort = reservedServer
                if _serverIp == ip and _serverPort == port:
                    currency, serverIp, serverPort = reservedServer
                    break
        # ruleText = getRuleText(rule, gameId, redis)
        # if isOther:
            # params = eval(rule)
            # params.append(int(hidden))
            # rule = str(params)
            # protocolStr = HEAD_SERVICE_PROTOCOL_CREATE_OTHER_ROOM%(account, ag, rule, ruleText)
            # redis.rpush(FORMAT_SERVICE_PROTOCOL_TABLE%(gameId, '%s:%s:%s'%(currency, serverIp, serverPort)), protocolStr)
            # return {'code':0, 'msg':'房间开启成功', 'ip':'', 'port':''}

        # redis.hmset(SessionTable,
            # {
                # 'action'   :   1,
                # 'rule'     :   rule,
                # 'ruleText' :   ruleText,
                # 'hidden'   :   hidden,
            # }
        # )
        urlRes = urlparse(request.url)
        domain = urlRes.netloc.split(':')[0]

        # 房间号
        if house_no:
            redis.setex('fish:%s:player:%s:houseNo'%(gameid,uid),house_no,60)

        return {'code' : 0, 'ip' : domain, 'port' : serverPort}
    else:
        return {'code':-1, 'msg':'服务器忙碌或维护中'}

@fish_app.post('/getWarRank')
@allow_cross
def do_getRank(redis,session):
    warhead_list = eval(redis.get('gain:rank:list'))
    active_list = eval(redis.get('cost:rank:list'))

    warhead_rank_info = []
    for index,t in enumerate(warhead_list):
        nickname,headImgUrl = redis.hmget('users:%s'%t[0],'nickname','headImgUrl')
        uid = t[0]
        today = str(datetime.now())[:10]
        today_fish = redis.get('user:%s:gain:fish:date:%s'%(uid,today)) 
        today_coins = redis.get('user:%s:gain:coins:date:%s'%(uid,today)) 
        today_warheads = redis.get('user:%s:gain:warheads:date:%s'%(uid,today))
        warhead_rank_info.append({
            "rank":index+1,
            "uid":t[0],
            "gain_warhead":t[1],
            "nickname":nickname,
            "headImgUrl":headImgUrl,
            "today_fish":today_fish or 0,
            "today_coins":today_coins or 0,
            "today_warheads":today_warheads or 0,
        })

    active_rank_info = []
    for index,t in enumerate(active_list):
        nickname,headImgUrl = redis.hmget('users:%s'%t[0],'nickname','headImgUrl')
        uid = t[0]
        today = str(datetime.now())[:10]
        today_fish = redis.get('user:%s:gain:fish:date:%s'%(uid,today)) 
        today_coins = redis.get('user:%s:gain:coins:date:%s'%(uid,today)) 
        today_warheads = redis.get('user:%s:gain:warheads:date:%s'%(uid,today))

        active_rank_info.append({
            "rank":index+1,
            "uid":t[0],
            "cost_warhead":t[1],
            "nickname":nickname,
            "headImgUrl":headImgUrl,
            "today_fish":today_fish or 0,
            "today_coins":today_coins or 0,
            "today_warheads":today_warheads or 0,
        })

    return {'code':0,'warhead_rank_info':warhead_rank_info,'active_rank_info':active_rank_info}
    

@fish_app.post('/getRank')
@allow_cross
def do_getRank(redis,session):
    """
    加入房间接口
    """
    fields = ('sid',)
    for field in fields:
        exec('%s = request.forms.get("%s",'').strip()'%(field,field))

    try:
        log_util.debug('[try do_getRank] get params sid[%s]'%(sid))
    except:
        return {'code':-300,'msg':'接口参数错误'}

    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    check_code,check_msg,user_table,osid = check_session_verfiy(redis,'/fish/getRank/',SessionTable,account,sid,verfiySid)
    log_util.debug('[try do_refresh] check_code[%s] check_msg[%s]'%(check_code,check_msg))
    if int(check_code)<0:
        if check_code == -4:
            return {'code':check_code,'msg':check_msg,'osid':osid}
        return {'code':check_code,'msg':check_msg}

    curTable = redis.get(FORMAT_ACCOUNT2USER_TABLE % (account))
    curScore = redis.hget(curTable, 'coin')


    today = date.today()
    yesterday = today - timedelta(days=1)
    rankInfo = {'rankForCoin':[], 'rankForProfit':[]}

    #获取盈利排行
    lastRank = MY_MAX_RANK-1
    lastPlayers = redis.zrevrange(TMP_FORMAT_USER_COINDELTA_TABLE, lastRank, lastRank, True, int)
    if lastPlayers:
        lastPlayers = redis.zrevrangebyscore(TMP_FORMAT_USER_COINDELTA_TABLE, lastPlayers[0][1], lastPlayers[0][1], score_cast_func = int)
        lastRank = redis.zrevrank(TMP_FORMAT_USER_COINDELTA_TABLE, lastPlayers[0]) + len(lastPlayers) - 1
    players = redis.zrevrange(TMP_FORMAT_USER_COINDELTA_TABLE, 0, lastRank, True, int)
    #更低排名玩家的还存不存在，不存在则屏蔽盈利0分玩家
    zeroPlayers = redis.zrevrangebyscore(TMP_FORMAT_USER_COINDELTA_TABLE, 0, 0, score_cast_func = int)
    if zeroPlayers:
        less0Rank = redis.zrevrank(TMP_FORMAT_USER_COINDELTA_TABLE, zeroPlayers[-1])
        less0RankPlayers = redis.zrevrange(TMP_FORMAT_USER_COINDELTA_TABLE, less0Rank+1, less0Rank+1, False, int)
    else:
        less0RankPlayers = None
    rank = prevRank = 1
    sameCount = 0
    prevCoinDelta = players[0][1] if players else 0
    selfRank = 0
    selfTicketDelta = 0
    log_util.debug('[try get rank profit] players[%s]'%(players))
    for player in players:
        if player[1] >= prevCoinDelta:
            rank = prevRank
            sameCount += 1
        else:
            rank = prevRank + sameCount
            sameCount = 1
        prevRank = rank
        prevCoinDelta = player[1]
        playerAccount = player[0]
        if prevCoinDelta < 0:
            continue
        playerTable = redis.get(FORMAT_ACCOUNT2USER_TABLE%(playerAccount))
        nickname, headImgUrl = redis.hmget(playerTable, ('nickname', 'headImgUrl'))
        uid = int(playerTable.split(':')[1])
        if playerAccount == account:
            selfRank = rank
            selfTicketDelta = player[1]
            pbAppendRank(rankInfo['rankForProfit'], rank, nickname, headImgUrl, player[1], uid)
        else:
            if player[1] or less0RankPlayers:
                pbAppendRank(rankInfo['rankForProfit'], rank, nickname, headImgUrl, player[1], uid)
    if not selfRank:
        selfTicketDelta = redis.zscore(TMP_FORMAT_USER_COINDELTA_TABLE, account)
        if not selfTicketDelta:
            selfRank = NOT_RANK_USE_NUM
            selfTicketDelta = 0
        else:
            selfTicketDelta = int(selfTicketDelta)
            selfRankPlayers = redis.zrevrangebyscore(TMP_FORMAT_USER_COINDELTA_TABLE, selfTicketDelta, selfTicketDelta, score_cast_func = int)
            if selfRankPlayers:
                selfRank = redis.zrevrank(TMP_FORMAT_USER_COINDELTA_TABLE, selfRankPlayers[0]) + 1
            else:
                selfRank = rank + 1
    nickname, headImgUrl = redis.hmget(user_table, ('nickname', 'headImgUrl'))
    uid = int(user_table.split(':')[1])
    # rankInfo['rankForProfit'] = rankInfo['rankForProfit'][:MAX_SEE_RANK]
    if rankInfo['rankForProfit']:
        rankList = [rankInfo['rankForProfit'][0]]
        for rankData in rankInfo['rankForProfit'][1:]:
            for index, otherData in enumerate(rankList):
                if rankData['score'] == otherData['score'] and rankData['uid'] < otherData['uid']:
                    rankList.insert(index, rankData)
                    break
            if rankData not in rankList:
                rankList.append(rankData)
        for _rank, data in enumerate(rankList):
            data['rank'] = _rank + 1
            if data['uid'] == uid:
                selfRank = _rank + 1
        rankInfo['rankForProfit'] = rankList[:RANK_COUNT]
    if selfRank > MY_MAX_RANK:
        selfRank = NOT_RANK_USE_NUM
    if selfTicketDelta < 0:
        selfTicketDelta = 0
    pbAppendRank(rankInfo['rankForProfit'], selfRank, nickname, headImgUrl, selfTicketDelta, uid)

    #获取金币排行
    lastRank = MY_MAX_RANK-1
    lastPlayers = redis.zrevrange(TMP_FORMAT_USER_COIN_TABLE, lastRank, lastRank, True, int)
    if lastPlayers:
        lastPlayers = redis.zrevrangebyscore(TMP_FORMAT_USER_COIN_TABLE, lastPlayers[0][1], lastPlayers[0][1], score_cast_func = int)
        lastRank = redis.zrevrank(TMP_FORMAT_USER_COIN_TABLE, lastPlayers[0]) + len(lastPlayers) - 1
    players = redis.zrevrange(TMP_FORMAT_USER_COIN_TABLE, 0, lastRank, True, int)
    #更低排名玩家的还存不存在，不存在则屏蔽盈利0分玩家
    zeroPlayers = redis.zrevrangebyscore(TMP_FORMAT_USER_COIN_TABLE, 0, 0, score_cast_func = int)
    if zeroPlayers:
        less0Rank = redis.zrevrank(TMP_FORMAT_USER_COIN_TABLE, zeroPlayers[-1])
        less0RankPlayers = redis.zrevrange(TMP_FORMAT_USER_COIN_TABLE, less0Rank+1, less0Rank+1, False, int)
    else:
        less0RankPlayers = None
    rank = prevRank = 1
    sameCount = 0
    prevCoinDelta = players[0][1] if players else 0
    selfRank = 0
    selfTicketDelta = 0
    log_util.debug('[try get rank coin] players[%s]'%(players))
    for player in players:
        if player[1] >= prevCoinDelta:
            rank = prevRank
            sameCount += 1
        else:
            rank = prevRank + sameCount
            sameCount = 1
        prevRank = rank
        prevCoinDelta = player[1]
        playerAccount = player[0]
        playerTable = redis.get(FORMAT_ACCOUNT2USER_TABLE%(playerAccount))
        nickname, headImgUrl = redis.hmget(playerTable, ('nickname', 'headImgUrl'))
        uid = int(playerTable.split(':')[1])
        if playerAccount == account:
            selfRank = rank
            selfTicketDelta = player[1]
            pbAppendRank(rankInfo['rankForCoin'], rank, nickname, headImgUrl, player[1], uid)
        else:
            if player[1] or less0RankPlayers:
                pbAppendRank(rankInfo['rankForCoin'], rank, nickname, headImgUrl, player[1], uid)
    if not selfRank:
        selfTicketDelta = redis.zscore(TMP_FORMAT_USER_COIN_TABLE, account)
        if not selfTicketDelta:
            selfRank = NOT_RANK_USE_NUM
            selfTicketDelta = 0
        else:
            selfTicketDelta = int(selfTicketDelta)
            selfRankPlayers = redis.zrevrangebyscore(TMP_FORMAT_USER_COIN_TABLE, selfTicketDelta, selfTicketDelta, score_cast_func = int)
            if selfRankPlayers:
                selfRank = redis.zrevrank(TMP_FORMAT_USER_COIN_TABLE, selfRankPlayers[0]) + 1
            else:
                selfRank = rank + 1
    nickname, headImgUrl = redis.hmget(user_table, ('nickname', 'headImgUrl'))
    uid = int(user_table.split(':')[1])
    # rankInfo['rankForCoin'] = rankInfo['rankForCoin'][:MAX_SEE_RANK]
    if rankInfo['rankForCoin']:
        rankList = [rankInfo['rankForCoin'][0]]
        for rankData in rankInfo['rankForCoin'][1:]:
            for index, otherData in enumerate(rankList):
                if rankData['score'] == otherData['score'] and rankData['uid'] < otherData['uid']:
                    rankList.insert(index, rankData)
                    break
            if rankData not in rankList:
                rankList.append(rankData)
        for _rank, data in enumerate(rankList):
            data['rank'] = _rank + 1
            if data['uid'] == uid:
                selfRank = _rank + 1
        rankInfo['rankForCoin'] = rankList[:RANK_COUNT]
    if selfRank > MY_MAX_RANK:
        selfRank = NOT_RANK_USE_NUM
    if selfTicketDelta < 0:
        selfTicketDelta = 0
    pbAppendRank(rankInfo['rankForCoin'], selfRank, nickname, headImgUrl, curScore, uid)

    return {'code' : 0, 'rankInfo' : rankInfo}


@fish_app.post('/mailRefresh')
@web_util.allow_cross_request
def do_mailRefresh(redis,session):
    """
    邮件轮询接口
    """
    curTime = datetime.now()
    ip = request.remote_addr
    sid = request.forms.get('sid','').strip()

    log_util.info('do_activeRefresh')

    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    check_code,check_msg,user_table,osid = check_session_verfiy(redis,'/fish/getRewardInfo/',SessionTable,account,sid,verfiySid)
    log_util.debug('[try do_refresh] check_code[%s] check_msg[%s]'%(check_code,check_msg))
    if int(check_code)<0:
        if check_code == -4:
            return {'code':check_code,'msg':check_msg,'osid':osid}
        return {'code':check_code,'msg':check_msg}

    userMailList = []
    unReadMailList = []
    userMailTable = FORMAT_USER_MSG_FISH_LIST%(uid)
    mailIds = redis.lrange(userMailTable,0,-1)
    for mailId in mailIds:
        mailTable = FORMAT_GAMEHALL_NOTIC_TABLE%(mailId)
        noticeReads = FORMAT_MSG_READ_SET%(mailId)
        readList = redis.smembers(noticeReads)
        mailInfo = redis.hgetall(mailTable)
        if uid in readList:
            mailInfo['read'] = '1'
            userMailList.append(mailInfo)
        else:
            mailInfo['read'] = '0'
            unReadMailList.append(mailInfo)

        log_util.info('[do_activeRefresh] active_id[%s] active_info[%s] acitve_list[%s]'%(mailId,mailInfo,readList))

    #合并消息
    userMailList = unReadMailList + userMailList

    return {'code':0,'mailList':userMailList,'unReadNums':len(unReadMailList)}

@fish_app.post('/activeRefresh')
@web_util.allow_cross_request
def do_activeRefresh(redis,session):
    """
    活动接口
    """
    curTime = datetime.now()
    ip = request.remote_addr
    sid = request.forms.get('sid','').strip()

    log_util.info('do_activeRefresh')

    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    check_code,check_msg,user_table,osid = check_session_verfiy(redis,'/fish/getRewardInfo/',SessionTable,account,sid,verfiySid)
    log_util.debug('[try do_refresh] check_code[%s] check_msg[%s]'%(check_code,check_msg))
    if int(check_code)<0:
        if check_code == -4:
            return {'code':check_code,'msg':check_msg,'osid':osid}
        return {'code':check_code,'msg':check_msg}

    userMailList = []
    unReadMailList = []
    user_mail_table = FORMAT_USER_ACTIVE_FISH_LIST%(uid)
    mail_ids = redis.lrange(user_mail_table,0,-1)
    for mail_id in mail_ids:
        if not mail_id:
            continue
        mailTable = FORMAT_GAMEHALL_ACTIVE_TABEL%(mail_id)
        noticeReads = FORMAT_ACT_READ_SET%(mail_id)
        mailInfo = redis.hgetall(mailTable)
        mailInfo['sort'] = convert_util.to_int(mailInfo['sort'])
        if redis.sismember(noticeReads,uid):
            mailInfo['read'] = '1'
            userMailList.append(mailInfo)
        else:
            mailInfo['read'] = '0'
            unReadMailList.append(mailInfo)

        log_util.info('[mailRefresh] mail_id[%s] mail_info[%s]'%(mail_id,mailInfo))

    #合并消息
    userMailList = unReadMailList + userMailList

    return {'code':0,'activeList':userMailList,'unReadNums':len(unReadMailList)}


@fish_app.post('/exchageCode')
@web_util.allow_cross_request
def doExchageCode(redis, session):

    try:
        sid = request.forms.get('sid', '').strip()
        code = request.forms.get('code', '').strip()
        # club_number = request.forms.get("club_number", '').strip()
        # allow = int(request.forms.get("allow", '').strip())
    except Exception as err:
        return {"code": 1, 'msg': "参数错误"}
    SessionTable, account, uid, verfiySid = getInfoBySid(redis, sid)
    if not redis.exists(SessionTable):
        return {'code': -3, 'msg': 'sid 超时'}
    if redis.hget("fish:exchageCode:hesh", account) == "1":
        return {"code": 1, "msg": "你已经领取过了"}

    if code == "4c445de82c3537a5995a497b1c8202d7":
        redis.hset("fish:exchageCode:hesh", account, 1)
        # 金币 1
        # 奖券 2
        account2user_table = FORMAT_ACCOUNT2USER_TABLE % (account)
        userTable = redis.get(account2user_table)
        redis.hincrby(userTable, "coin", 888888)
        # redis.hincrby(userTable, "exchange_ticket", 200)

        coin, exchange_ticket = redis.hmget(userTable, 'coin', "exchange_ticket")
        res = {"code": 1, "number": 888888, "type": "金币", "curCoin": coin}
        #res1 = {"code": 2, "number": 200, "type": "奖券" , "curTicket": exchange_ticket}
        return {"code": 0, "msg": "成功", 'info': [
            res
        ]}

    return {"code": 1, "msg": "失败, 兑换码不正确"}

@fish_app.post("/exchageCodeCheck")
@web_util.allow_cross_request
def doExchageCode(redis, session):

    try:
        sid = request.forms.get('sid', '').strip()
        # club_number = request.forms.get("club_number", '').strip()
        # allow = int(request.forms.get("allow", '').strip())
    except Exception as err:
        return {"code": 1, 'msg': "参数错误"}
    SessionTable, account, uid, verfiySid = getInfoBySid(redis, sid)
    if not redis.exists(SessionTable):
        return {'code': -3, 'msg': 'sid 超时'}
    isExchange = redis.hget("fish:exchageCode:hesh", account) or 0
    print(isExchange)
    if not isExchange:
        isExchange == 0
    isExchange = int(isExchange)
    return {"code": 0, "msg": "成功", "status": isExchange}

@fish_app.post("/redPickOrder")
@web_util.allow_cross_request
def redPackOrder(redis, session):
    """ 红包排行榜 """
    try:
        sid = request.forms.get('sid', '').strip()
    except Exception as err:
        return {"code": 1, 'msg': "参数错误"}

    SessionTable, account, uid, verfiySid = getInfoBySid(redis, sid)
    if not redis.exists(SessionTable):
        return {'code': -3, 'msg': 'sid 超时'}
    # 获取自己的
    curPick = redis.hget("fish:redpick:account:hesh", account)
    curPickData = {}
    account2user_table = FORMAT_ACCOUNT2USER_TABLE % (account)
    userTable = redis.get(account2user_table)
    userName, headImgUrl = redis.hmget(userTable, "nickname", "headImgUrl")
    userTable = redis.get(account2user_table)
    curPickData["userNmae"] = userName
    curPickData["headImgUrl"] = headImgUrl
    curPickData["userType"] = u"普通用户"
    if not curPick:
        curPickData["redPickNumber"] = 0
        curPickData["redPick"] = 0
    else:
        curPickData["redPickNumber"] = int(curPick)
        curPickData["redPick"] = int(curPick) * 8
    curUp = 0
    order = redis.hgetall("fish:redpick:account:hesh")
    result = []
    for _account in order:
        account2user_table = FORMAT_ACCOUNT2USER_TABLE % (_account)
        userTable = redis.get(account2user_table)
        userName, headImgUrl = redis.hmget(userTable, "nickname", "headImgUrl")
        userTypeStr = u"普通用户"


        result.append(
            {"userName": userName,
             "redPickNumber":  int(order[_account]),
             "redPick": int(order[_account]) * 8,
             "headImgUrl": headImgUrl,
             "userType": userTypeStr,
             "account": _account}
        )

    result = sorted(result, key=lambda x: -x["redPickNumber"])[:10]
    curIndex = 0
    for index, item in enumerate(result):
        if account == item["account"]:
            curIndex = index + 1
            curUp = 1
    curPickData["state"] = curUp
    curPickData["index"] = curIndex
    return {"code": 0, "data": result, "msg": "成功", "curPlayer": curPickData}
