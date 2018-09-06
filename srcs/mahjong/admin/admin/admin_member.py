#-*- coding:utf-8 -*-
#!/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    系统会员模块
"""
from bottle import *
from admin import admin_app
from config.config import STATIC_LAYUI_PATH,STATIC_ADMIN_PATH,BACK_PRE,PLAYER_BASE_SCORE,DEFAULT_BASE_SCORE,RES_VERSION
from common.utilt import *
from common.log import *
from datetime import datetime
from web_db_define import *
from model.agentModel import *
from model.protoclModel import *
from model.userModel import *
from model.orderModel import *
from common import encrypt_util,convert_util,json_util,web_util
import hashlib
import json

@admin_app.get('/member/list')
@checkLogin
def get_member_list(redis,session):
    """
    获取会员列表接口
    """
    lang    =  getLang()
    curTime =  datetime.now()
    fields = ('isList','startDate','endDate','pageSize','pageNumber','searchId','sort_name','sort_method')
    for field in fields:
        exec("%s = request.GET.get('%s','').strip()"%(field,field))

    selfUid  = session['id']
    if not pageNumber:
        pageNumber = 1
    else:
        pageNumber = convert_util.to_int(pageNumber)

    if isList:
        res = getMemberList(redis,session,selfUid,searchId,lang,pageSize,pageNumber,sort_name,sort_method)
        return json.dumps(res)
    else:
        info = {
                'title'                  :           lang.MEMBER_LIST_TITLE_TXT,
                'listUrl'                :           BACK_PRE+'/member/list?isList=1&pageNumber={}&pageSize={}'.format(pageNumber,pageSize),
                'searchTxt'              :           lang.MEMBER_INPUT_TXT,
                'sort_bar'               :           True,#开启排序
                'member_page'            :           True,#开启排序
                'cur_page'               :           pageNumber,
                'cur_size'               :           pageSize,
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'remove_type'            :           'cards',
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH
        }

        return template('admin_member_list',info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/member/kick')
def do_kickDirectMember(redis,session):
    """
    踢出直属会员
    """
    lang    =  getLang()
    curTime =  datetime.now()
    selfUid  = session['id']
    memberId = request.GET.get('id','').strip()

    userTable = FORMAT_USER_TABLE%(memberId)
    userParent = redis.hget(userTable,'parentAg')
    userParentTable = FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE%(userParent)
    if not userParent:
        return {'code':1,'msg':'会员编号[%s]的公会不存在.'%(memberId)}
    #print userTable
    pipe = redis.pipeline()
    try:
        pipe.srem(userParentTable, memberId) #上线代理需要获得
        pipe.hset(userTable, 'parentAg', '')
    except Exception,e:
        log_debug('[%s][member][kick][error] agentId[%s] member[%s] kick error,reason[%s]'%(curTime,selfUid,memberId,e))

    pipe.execute()
    #记录操作日志
    logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                        'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE['uncheckMember']%(memberId)}
    writeAgentOpLog(redis,selfUid,logInfo)

    return {'code':0,'msg':'移除会员[%s]成功'%(memberId),'jumpUrl':BACK_PRE+'/member/list'}

@admin_app.get('/member/removeCard')
@admin_app.get('/member/removeCard/<remove_type>')
def get_removeCard(redis,session,remove_type="cards"):
    """
    移除会员的钻石
    """
    curTime = datetime.now()
    lang    = getLang()
    memberId =  request.GET.get('id','').strip()
    pageNumber = request.GET.get('cur_page','').strip()

    if not memberId:
        return {'code':'1','msg':'非法操作!'}

    if not pageNumber:
        pageNumber = 1
    else:
        pageNumber = convert_util.to_int(pageNumber)

    if remove_type == 'cards':
        """ 移除钻石操作 """

        page_title =  '移除会员(%s)钻石'%(memberId)
        parentAg   =   redis.hget(FORMAT_USER_TABLE%(memberId),'parentAg')
        room_card  =   redis.get(USER4AGENT_CARD%(parentAg, memberId))
        back_url   =   BACK_PRE+'/member/list?pageNumber={}'.format(pageNumber)
    else:

        """ 移除金币操作 """
        page_title =  '移除会员[%s]金币'%(memberId)
        room_card  =   redis.hget(FORMAT_USER_TABLE%(memberId),'coin')
        room_card  =   convert_util.to_int(room_card)
        back_url   =   BACK_PRE+'/fish/member/list?pageNumber={}'.format(pageNumber)

    memberInfo = {
            'title'         :       page_title,
            'backUrl'       :       back_url,
            'agentId'       :       parentAg if remove_type=='cards' else '',
            'memberId'      :       memberId,
            'submitUrl'     :       BACK_PRE+'/member/removeCard/{}/{}'.format(pageNumber,remove_type),
            'roomcard'      :       room_card,
            'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
            'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH
    }

    return template('admin_member_removeCard',page=remove_type,info=memberInfo,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.post('/member/removeCard')
@admin_app.post('/member/removeCard/<page:int>/<remove_type>')
@checkLogin
def do_removeCard(redis,session,page=1,remove_type="cards"):
    """
    移除会员的钻石接口
    page:当前是操作第几页
    """
    curTime = datetime.now()
    lang    = getLang()
    fields = ('roomcard','agentId','remove','memberId')
    for field in fields:
        exec("%s = request.forms.get('%s','').strip()"%(field,field))

    if not remove:
        return {'code':1,'msg':lang.MEMBER_DIOMAN_INPUT_TXT}

    if isinstance(remove,float):
        return {'code':1,'msg':lang.MEMBER_DIOMAN_INPUT_NUM_TXT}

    remove   = convert_util.to_int(remove)
    roomcard = convert_util.to_int(roomcard)
    if remove > roomcard:
        return {'code':1,'msg':lang.MEMBER_DIOMAN_GT_TXT}
    try:
        if remove_type == 'cards':
            jump_url = "/admin/member/list?&pageNumber={}".format(page)
            success_msg = lang.MEMBER_DIOMAN_REMOVE_SUCCESS
            redis.incrby(USER4AGENT_CARD%(agentId, memberId),-remove)
        else:
            jump_url = "/admin/fish/member/list?&pageNumber={}".format(page)
            success_msg = lang.MEMBER_COIN_REMOVE_SUCCESS
            redis.hincrby(FORMAT_USER_TABLE%(memberId),'coin',-remove)

        logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                            'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE['removeRoomCard']%(memberId,remove)}
        writeAgentOpLog(redis,agentId,logInfo)
    except Exception,e:
        log_util.debug('[try do_removeCard] remove Exception reason[%s]'%(e))
        return {'code':1,'msg':'移除失败'}

    return {'code':0,'msg':success_msg%(memberId,remove),'jumpUrl':jump_url}

@admin_app.get('/member/addCard')
@admin_app.get('/member/addCard/<remove_type>')
def get_addCard(redis,session,remove_type="cards"):
    """
    增加会员钻石接口
    """
    curTime = datetime.now()
    lang    = getLang()
    memberId =  request.GET.get('id','').strip()
    pageNumber = request.GET.get('cur_page','').strip()
    if not pageNumber:
        pageNumber = 1
    else:
        pageNumber = convert_util.to_int(pageNumber)

    if not memberId:
        return {'code':'1','msg':'非法操作!'}

    if remove_type == 'cards':
        """ 增加钻石操作 """

        page_title =  '增加会员(%s)钻石'%(memberId)
        parentAg   =   redis.hget(FORMAT_USER_TABLE%(memberId),'parentAg')
        room_card  =   redis.get(USER4AGENT_CARD%(parentAg, memberId))
        back_url   =   BACK_PRE+'/member/list?pageNumber={}'.format(pageNumber)
    else:

        """ 存金币操作 """
        page_title =  '增加会员[%s]金币'%(memberId)
        room_card  =   redis.hget(FORMAT_USER_TABLE%(memberId),'coin')
        room_card  =   convert_util.to_int(room_card)
        back_url   =   BACK_PRE+'/fish/member/list?pageNumber={}'.format(pageNumber)

    parentAg =  redis.hget(FORMAT_USER_TABLE%(memberId),'parentAg')
    memberTable = FORMAT_USER_TABLE%(memberId)
    name,headImgUrl = redis.hmget(memberTable,('nickname','headImgUrl'))

    memberInfo = {
            'title'         :       page_title,
            'backUrl'       :       back_url,
            'agentId'       :       parentAg,
            'memberId'      :       memberId,
            'submitUrl'     :       BACK_PRE+'/member/addCard/{}/{}'.format(pageNumber,remove_type),
            'roomcard'      :       room_card,
            'name'          :       name,
            'headImgUrl'    :       headImgUrl,
            'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
            'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH
    }

    return template('admin_member_addCard',page=remove_type,info=memberInfo,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.post('/member/addCard')
@admin_app.post('/member/addCard/<page:int>/<remove_type>')
def do_addCard(redis,session,page=1,remove_type="cards"):
    """
    增加会员钻石接口
    """
    curTime = datetime.now()
    lang    = getLang()
    fields = ('roomcard','agentId','add','memberId')
    for field in fields:
        exec("%s = request.forms.get('%s','').strip()"%(field,field))
    selfUid = session['id']

    if not add:
        return {'code':1,'msg':lang.MEMBER_DIOMAN_INPUT_TXT}

    if isinstance(add,float):
        return {'code':1,'msg':lang.MEMBER_DIOMAN_INPUT_NUM_TXT}

    add      = convert_util.to_int(add)
    roomcard = convert_util.to_int(roomcard)
    if add <= 0 :
        return {'code':1,'msg':lang.MEMBER_DIOMAN_LT_TXT}
    try :
        if remove_type == 'cards':
            jump_url    = "/admin/member/list?&pageNumber={}".format(page)
            #提示成功
            success_msg = lang.MEMBER_DIOMAN_ADD_SUCCESS
            redis.incrby(USER4AGENT_CARD%(agentId, memberId),add)
        else:
            jump_url = "/admin/fish/member/list?&pageNumber={}".format(page)
            success_msg = lang.MEMBER_COIN_ADD_SUCCESS
            redis.hincrby(FORMAT_USER_TABLE%(memberId),'coin',add)

        logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                            'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE['addRoomCard']%(memberId,add)}
        writeAgentOpLog(redis,agentId,logInfo)
    except Exception,e:
        return {'code':1,'msg':lang.MEMBER_DIOMAN_INPUT_NUM_TXT}


    return {'code':0,'msg':success_msg%(memberId,add),'jumpUrl':jump_url}

@admin_app.get('/member/modify')
@admin_app.get('/member/modify/<modify_type>')
def get_modifyMember(redis,session,modify_type="cards"):
    """
    修改代理下属玩家信息
    """
    curTime = datetime.now()
    lang    = getLang()
    memberId =   request.GET.get('id','').strip()
    pageNumber = request.GET.get('cur_page','').strip()
    if not pageNumber:
        pageNumber = 1
    else:
        pageNumber = convert_util.to_int(pageNumber)

    if not memberId:
        return {'code':'1','msg':'非法操作!'}

    memberTable = FORMAT_USER_TABLE%(memberId)
    maxScore,baseScore   = redis.hmget(memberTable,('maxScore','baseScore'))

    if modify_type == 'cards':
        page_title  =    "棋牌会员[%s]-信息修改"%(memberId),
        back_url    =    BACK_PRE+'/member/list?pageNumber={}'.format(pageNumber)
    else:
        page_title  =    "捕鱼会员[%s]-信息修改"%(memberId)
        back_url = BACK_PRE+'/fish/member/list?pageNumber={}'.format(pageNumber)
    memberInfo = {
            'title'         :       page_title,
            'backUrl'       :       back_url,
            'memberId'      :       memberId,
            'submitUrl'     :       BACK_PRE+'/member/modify/{}'.format(modify_type),
            'maxScore'      :       maxScore if maxScore else 1,
            'baseScore'     :       baseScore if baseScore else DEFAULT_BASE_SCORE,
            'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
            'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH
    }

    return template('admin_member_modify',baseScore=PLAYER_BASE_SCORE,info=memberInfo,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.post('/member/modify')
@admin_app.post('/member/modify/<modify_type>')
@checkLogin
def do_modifyMember(redis,session,modify_type='cards'):
    """
    修改会员信息接口
    """
    curTime = datetime.now()
    lang     = getLang()
    selfUid  = session['id']

    fields = (
                'memberId',
                'maxScore',
                'score1',
                'score2',
                'score3',
                'score4',
                'score5',
                'score6',
                'score7',
                'score8',
                'score9',
                'score10',
                'score11',
                'score12',
                'score13',
                'score14',
                'score15',
                'score16',
                'score17',
                'score18',
                'score19',
                'score20',
                'cur_page'
    )

    for field in fields:
        exec("%s = request.forms.get('%s','').strip()"%(field,field))

    if not cur_page:
        cur_page = 1
    else:
        cur_page = convert_util.to_int(cur_page)

    if not memberId:
        return {'code':1,'msg':'非法修改会员!'}

    base_score_list = []
    score_list = [score1,score2,score3,score4,score5,score6,score7,score8,score9,\
                        score10,score11,score12,score13,score14,score15,score16,score17,score18,score19,score20]

    for score in score_list:
        if score:
            base_score_list.append(score)

    pipe = redis.pipeline()
    memebrTable  =  FORMAT_USER_TABLE%(memberId)
    try:
        pipe.hmset(memebrTable,{'maxScore':max(score_list)})
        pipe.hmset(memebrTable,{'baseScore':base_score_list})
    except Exception,e:
        log_util.debug('[try ModifyMember][error] memberId[%s] modify info error. reason[%s]'%(memberId,e))
        return {'code':1,'msg':'修改会员[%s]信息失败'%(memberId)}

    #记录操作日志
    logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                        'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE['modifyMember']%(memberId)}
    writeAgentOpLog(redis,selfUid,logInfo)

    if modify_type =='cards':
        """ 修改捕鱼玩家 """
        jump_url = '/admin/member/list?&pageNumber={}'.format(cur_page)
    else:
        jump_url = '/admin/fish/member/list?&pageNumber={}'.format(cur_page)

    pipe.execute()
    return {'code':0,'msg':'修改会员(%s)成功'%(memberId),'jumpUrl':jump_url}

@admin_app.get('/member/search')
@admin_app.get('/member/search/<action>')
@checkAccess
def getMemberSearch(redis,session,action="hall"):
    """
    会员查询充卡
    """
    action = action.upper()
    curTime = datetime.now()
    lang    = getLang()
    memberId = request.GET.get('memberId','').strip()

    info = {
                'title'             :               lang.MENU_MEMBER_SEARCH_TXT if action=='HALL' else lang.MENU_MEMBER_SEARCH_COIN_TXT,
                'memberId'          :               memberId,
                'searchUrl'         :               BACK_PRE+'/member/recharge/{}'.format(action),
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH
    }

    return template('admin_member_search',info=info,message=None,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/member/recharge')
@admin_app.get('/member/recharge/<action>')
@checkLogin
def getMemberRecharge(redis,session,action="hall"):
    """
    会员充卡
    """
    curTime = datetime.now()
    lang    = getLang()
    action = action.upper()
    dateStr = curTime.strftime('%Y-%m-%d')

    selfAccount,selfUid = session['account'],session['id']
    fields = ('memberId',)
    for field in fields:
        exec('%s = request.GET.get("%s","").strip()'%(field,field))

    memberTable = FORMAT_USER_TABLE%(memberId)
    if action == 'HALL':
        memberChildIds = redis.smembers(FORMAT_ADMIN_ACCOUNT_MEMBER_TABLE%(selfUid))
        if not redis.exists(memberTable) or (memberId not in memberChildIds):
            info = {
                    'title'             :                lang.MENU_MEMBER_SEARCH_TXT,
                    'memberId'          :                memberId,
                    'searchUrl'         :                BACK_PRE+'/member/recharge/{}'.format(action),
                    'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                    'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH
            }
            log_debug('[%s][roomCard][member recharge] memberId[%s] is not exists.'%(curTime,memberId))
            return template('admin_member_search',info=info,message='会员[%s]不存在'%(memberId),lang=lang,RES_VERSION=RES_VERSION)

        account,name,openID,headImgUrl = redis.hmget(memberTable,('account','nickname','openid','headImgUrl'))
        if not redis.exists(USER4AGENT_CARD%(selfUid,memberId)):
            redis.set(USER4AGENT_CARD%(selfUid,memberId),0)

        roomcard     = redis.get(USER4AGENT_CARD%(selfUid,memberId))
        title = '钻石充值 [当前会员:%s]'%(account)
        back_url = '/admin/member/list'
        submit_utl = '/admin/member/recharge'
        recharge_type = ROOMCARD2TYPE['member.cards']
    else:
        account,name,openID,headImgUrl = redis.hmget(memberTable,('account','nickname','openid','headImgUrl'))
        if not redis.sismember(ACCOUNT4WEIXIN_SET4FISH,account):
            info = {
                    'title'             :                lang.MENU_MEMBER_SEARCH_COIN_TXT,
                    'memberId'          :                memberId,
                    'searchUrl'         :                BACK_PRE+'/member/recharge/{}'.format(action),
                    'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                    'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH
            }
            return template('admin_member_search',action=action,info=info,message='会员[%s]不存在'%(memberId),lang=lang,RES_VERSION=RES_VERSION)

        roomcard = redis.hget(memberTable,'coin')
        title = '金币充值[当前会员:%s]'%(account)
        back_url = '/admin/fish/member/list'
        submit_utl = '/admin/member/recharge/coin'
        recharge_type = ROOMCARD2TYPE['member.coin']

    token_value  = str(memberId)+str(time.time())
    #生成页面提交token
    submit_token = encrypt_util.to_md5(token_value)
    session['recharge_token'] = submit_token

    info = {
                'title'             :           title,
                'submitUrl'         :           submit_utl,
                'backUrl'           :            back_url,
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH,
                'memberId'          :           memberId,
                'account'           :           account,
                'name'              :           name,
                'roomCard'          :           roomcard,
                'headImgUrl'        :           headImgUrl,
                'submit_token'      :           submit_token,
                'rechargeTypes'     :           recharge_type,
                'openId'            :           openID
    }

    return template('admin_member_recharge',action=action,info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.post('/member/recharge')
@checkLogin
def do_memberRecharge(redis,session):
    """
    会员充卡逻辑
    """
    curTime  =  datetime.now()
    lang     =  getLang()
    dateStr  =  curTime.strftime('%Y-%m-%d')
    selfAccount,selfUid = session['account'],session['id']

    fields = ('memberId','cardNums','passwd','token')
    for field in fields:
        exec('%s = request.forms.get("%s",'').strip()'%(field,field))

    if session.get('recharge_token') == None:
        log_debug('session[%s]'%(session['recharge_token']))
        return {'code':1,'msg':'非法提交订单'}

    if token != session['recharge_token']:
        log_debug('[try do_memberRecharge] token is not match. submit_token[%s] session_token[%s]'%(token,session['recharge_token']))
        return {'code':0,'msg':'不能重复确认订单.','jumpUrl':BACK_PRE+'/member/search'}

    userTable  = FORMAT_USER_TABLE%(memberId)
    roomCard2AgentTable = USER4AGENT_CARD%(selfUid,memberId)
    agentTable = AGENT_TABLE%(selfUid)
    roomcard,name,selfPasswd,type,parent_id = redis.hmget(agentTable,('roomcard','name','passwd','type','parentAg'))

    info  =  {
                'title'             :       '会员钻石充值',
                'backUrl'           :       BACK_PRE+'/member/list'
    }

    checkNullFields = [
        {'field':cardNums,'msg':'充值钻石数不能为空'},
        {'field':passwd,'msg':'请输入你的密码'}
    ]

    for check in checkNullFields:
        if not check['field']:
            return {'code':1,'msg':check['msg']}

    if selfPasswd != encrypt_util.to_sha256(passwd):
        return {'code':1,'msg':'您的密码不正确'}

    pipe  =  redis.pipeline()
    if int(type) not in [0,1]:
        if int(roomcard) < int(cardNums):
            return {'code':4,'msg':lang.CARD_NOT_ENGOUGHT_TXT,'jumpUrl':BACK_PRE+'/order/buy'}
        pipe.hincrby(agentTable,'roomcard',-int(cardNums))

    pipe.incrby(roomCard2AgentTable,cardNums)
    orderNo = getOrderNo(selfUid)
    orderInfo = {
            'orderNo'                :       orderNo,
            'cardNums'               :       cardNums,
            'applyAccount'           :       memberId+"(玩家)",
            'status'                 :       1,
            'apply_date'             :       curTime.strftime('%Y-%m-%d %H:%M:%S'),
            'finish_date'            :       curTime.strftime('%Y-%m-%d %H:%M:%S'),
            'type'                   :       0,
            'note'                   :       '',
            'saleAccount'            :       selfAccount
    }

    session['recharge_token'] = None
    cardNums = convert_util.to_int(cardNums)
    if createOrder(redis,orderInfo):
        #创建订单
        pipe.lpush(AGENT_SALE_ORDER_LIST%(selfUid,dateStr),orderNo)
        pipe.lpush(AGENT_SALESUCCESS_ORDER_LIST%(selfUid,dateStr),orderNo)

        if redis.exists(AGENT_SALE_CARD_DATE%(selfUid,dateStr)):
            pipe.hincrby(AGENT_SALE_CARD_DATE%(selfUid,dateStr),'cardNums',cardNums)
            pipe.hincrby(AGENT_SALE_CARD_DATE%(selfUid,dateStr),'totalNums',cardNums)
        else:
            try:
                his_total_nums = redis.get(AGENT_SALE_TOTAL%(selfUid))
                if not his_total_nums:
                    his_total_nums = 0
            except:
                his_total_nums = 0
            pipe.hmset(AGENT_SALE_CARD_DATE%(selfUid,dateStr),{'cardNums':cardNums,'date':dateStr,'totalNums':int(his_total_nums)+cardNums})

        pipe.execute()
        return {'code':0,'msg':'成功向[%s]充值了钻石[%s]张'%(memberId,cardNums),'jumpUrl':BACK_PRE+'/member/search/hall'}

    return {'code':1,'msg':'充值失败'}

@admin_app.post('/member/recharge/coin')
@checkLogin
def do_memberRechargeCoin(redis,session):
    """
    代理给会员充值金币接口
    """
    selfUid = session['id']

    fields = ('memberId','cardNums','passwd','token')
    for field in fields:
        exec('%s = request.forms.get("%s",'').strip()'%(field,field))

    if session.get('recharge_token') == None:
        log_debug('session[%s]'%(session['recharge_token']))
        return {'code':1,'msg':'非法提交订单'}

    if token != session['recharge_token']:
        log_debug('[try do_memberRecharge] token is not match. submit_token[%s] session_token[%s]'%(token,session['recharge_token']))
        return {'code':0,'msg':'不能重复确认订单.','jumpUrl':BACK_PRE+'/member/search'}

    user_table = FORMAT_USER_TABLE%(memberId)
    agent_table = AGENT_TABLE%(selfUid)
    selfPasswd = redis.hget(agent_table,'passwd')

    info  =  {
                'title'             :       '会员金币充值',
                'backUrl'           :       BACK_PRE+'/fish/member/list'
    }

    checkNullFields = [
        {'field':cardNums,'msg':'充值金币数不能为空'},
        {'field':passwd,'msg':'请输入你的密码'}
    ]

    for check in checkNullFields:
        if not check['field']:
            return {'code':1,'msg':check['msg']}

    if selfPasswd != encrypt_util.to_sha256(passwd):
        return {'code':1,'msg':'您的密码不正确'}

    pipe = redis.pipeline()
    try:
        cardNums = convert_util.to_int(cardNums)
        pipe.hincrby(user_table,'coin',cardNums)
    except Exception,e:
        log_util.debug('[try do_memberRechargeCoin] ERROR. memberId[%s] reason[%s]'%(memberId,e))
        return {'code':1,'msg':'充值失败'}

    pipe.execute()
    return {'code':0,'msg':'成功向[%s]充值了金币[%s]个'%(memberId,cardNums),'jumpUrl':BACK_PRE+'/member/search/fish'}

@admin_app.get('/member/joinList')
def getMemberApplyList(redis,session):
    """
    获取下线代理申请列表
    """
    curTime = datetime.now()
    lang    = getLang()
    selfAccount,selfUid  =  session['account'],session['id']

    isList = request.GET.get('list','').strip()

    if isList:
        applyLists = getmemberApplyList(redis,selfUid)
        return json.dumps(applyLists)
    else:
        info = {
                    'title'                  :          '玩家申请列表',
                    'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                    'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH,
                    'listUrl'                :           BACK_PRE+'/member/joinList?list=1'
        }

        return template('admin_member_apply_list',info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.post('/member/join/comfirm')
def do_memberJoinComfirm(redis,session):
    """
    审核会员加入公会
    """
    curTime = datetime.now()
    lang    = getLang()
    selfAccount,selfUid   =   session['account'],session['id']

    memberId  =  request.forms.get('id','').strip()
    if not memberId:
        return {'code':1,'msg':'会员编号[%s]错误'%(memberId)}

    try:
        memberJoinComfirm(redis,selfUid,memberId)
    except Exception,e:
        print '[%s][join Comfirm][error] reason[%s]'%(curTime,e)
        return {'code':1,'msg':'审核会员异常'}

    #记录操作日志
    logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                        'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE['checkMember']%(memberId)}
    writeAgentOpLog(redis,selfUid,logInfo)
    return {'code':0,'msg':'会员[%s]审核通过.'%(memberId),'jumpUrl':BACK_PRE+'/member/modify?id=%s'%(memberId)}

@admin_app.post('/member/join/reject')
def do_memberJoinReject(redis,session):
    """
    拒绝会员加入公会
    """
    curTime = datetime.now()
    lang = getLang()
    selfAccount,selfUid  =  session['account'],session['id']

    memberId   =   request.forms.get('id','').strip()
    if not memberId:
        return {'code':1,'msg':'会员编号[%s]错误'%(memberId)}

    pipe = redis.pipeline()
    try:
        log_debug('[%s][reject Member][info] agentId[%s] reject memberId[%s]'%(curTime,selfUid,memberId))
        pipe.lrem(JOIN_GROUP_LIST%(selfUid),memberId)
    except Exception,e:
        log_debug('[%s][reject member][error] memberId[%s] reject error. reason[%s]'%(curTime,memberId,e))
        return {'code':1,'msg':'会员[%s]拒绝失败'%(memberId)}

    pipe.execute()
    #记录操作日志
    logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                        'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE['rejectMember']%(memberId)}
    writeAgentOpLog(redis,selfUid,logInfo)
    return {'code':0,'msg':'会员[%s]已拒绝加入公会'%(memberId),'jumpUrl':BACK_PRE+'/member/joinList'}

@admin_app.get('/member/kicks')
@checkLogin
def do_memberKick(redis,session):
    """
    踢出会员
    """
    account = request.GET.get('account','').strip()

    account2user_table = FORMAT_ACCOUNT2USER_TABLE%(account)
    memberTable = redis.get(account2user_table)
    if not redis.exists(memberTable):
        return {'code':1,'msg':'会员[%s]不存在'%(account)}

    #发送提出玩家协议给服务端
    sendProtocol2AllGameService(redis,HEAD_SERVICE_PROTOCOL_KICK_MEMBER%(account))

    return {'code':0,'msg':'会员(%s)已被踢出游戏!'%(account),'jumpUrl':BACK_PRE+'/agent/member/curOnline'}

@admin_app.get('/member/gm/list')
def getGmsList(redis,session):
    """
    获取gm列表
    """
    lang    =  getLang()
    curTime =  datetime.now()
    #接收的值
    fileds = ('show_list','pageSize','pageNumber','searchId')
    for filed in fileds:#动态定义
        exec("%s = request.GET.get('%s','').strip()"%(filed,filed))

    if show_list:
        res = getGmList(redis,session,searchId,int(pageSize),int(pageNumber))
        return json.dumps(res)
    else:
        info = {
                'title'                  :           'GM玩家列表',
                'listUrl'                :           BACK_PRE+'/member/gm/list?show_list=1',
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH,
                'searchTxt'              :               '输入玩家编号',
                'cur_page'               :           pageNumber,
                'cur_size'               :           pageSize,
                'removeUrl'              :           BACK_PRE + '/member/gm/kick',
                'addGMUrl'               :           BACK_PRE + '/member/gm/add'
        }

        return template('admin_member_gm_list',PAGE_LIST=PAGE_LIST,info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/member/gm/kick')
def do_kickGmMember(redis,session):
    """
    移除会员GM权限接口
    """
    lang    =  getLang()
    curTime =  datetime.now()
    selfUid  = session['id']
    gm_ids = request.GET.get('id','').strip()

    if not gm_ids:
        log_debug('[try do_kickGmMember] gm_ids[%s] is not illegs.'%(gm_ids))
        return {'code':1,'msg':'GM_IDS参数错误.'}

    gm_ids = gm_ids.split(",")
    gm_table = 'GMAccount:set'

    pipe = redis.pipeline()

    for gm_id in gm_ids:
        if not redis.sismember(gm_table,gm_id):
            continue
        pipe.srem(gm_table, gm_id) #上线代理需要获得

    logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                        'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE['kickGm']%(gm_ids)}
    writeAgentOpLog(redis,selfUid,logInfo)
    pipe.execute()
    return {'code':0,'msg':'移除玩家[%s]GM权限成功'%(gm_ids),'jumpUrl':BACK_PRE+'/member/gm/list'}

@admin_app.get('/member/gm/add')
@checkLogin
def get_addGmMember(redis,session):
    curTime = datetime.now()
    lang    = getLang()
    info = {
                'title'             :               '添加GM权限',
                'addUrl'            :               BACK_PRE+'/member/gm/add',
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH
    }

    return template('admin_member_gm_add',info=info,message=None,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/member/gm/showHis')
@checkLogin
def get_addGmMember(redis,session):
    curTime = datetime.now()
    lang    = getLang()
    userId  = request.GET.get('userId','').strip()
    isList  = request.GET.get('list','').strip()

    if not userId:
        return

    if isList:
        gm_his = get_gm_op_list(redis,userId)
        return json.dumps(gm_his)
    else:
        info = {
                    'title'             :               '玩家[%s]GM历史'%(userId),
                    'addUrl'            :               BACK_PRE+'/member/gm/list',
                    'dataUrl'           :               BACK_PRE+'/member/gm/showHis?list=1&userId=%s'%(userId),
                    'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                    'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH
        }

        return template('admin_member_gm_his',info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.post('/member/gm/add')
@checkLogin
def do_addGmMember(redis,session):
    curTime = datetime.now()
    lang    = getLang()
    memberId = request.forms.get('memberId','').strip()
    memberTable = FORMAT_USER_TABLE%(memberId)
    selfUid = session['id']

    if not redis.exists(memberTable):
        return {'code':1,'msg':'会员[%s]不存在'%(memberId)}

    account = redis.hget(memberTable,'account')

    gmTable = 'GMAccount:set'

    if redis.sismember(gmTable,account):
        return {'code':1,'msg':'会员[%s]已经拥有gm权限'%(memberId)}
    try:
        redis.sadd(gmTable,account) #上线代理需要获得
    except Exception,e:
        log_debug('[%s][member][gm][add][error] gmAccount[%s]  add error,reason[%s]'%(curTime,account,e))
        return {'code':1,'msg':'添加会员[%s] gm权限失败'%(account)}

    logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                        'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE['addGm']%(account)}
    writeAgentOpLog(redis,selfUid,logInfo)
    return {'code':0,'msg':'给会员[%s]设置gm权限成功'%(memberId),'jumpUrl':BACK_PRE+'/member/gm/list'}

@admin_app.get('/member/freeze')
@admin_app.get('/member/freeze/<action>')
@checkLogin
def do_freezeMember(redis,session,action='hall'):
    """
    冻结玩家操作接口
    """
    action = action.upper()
    curTime = datetime.now()
    lang    = getLang()
    memberId = request.GET.get('id','').strip()
    pageNumber = request.GET.get('cur_page','').strip()
    if not pageNumber:
        pageNumber = 1
    else:
        pageNumber = convert_util.to_int(pageNumber)

    freezeDesc = {
            '1'     :     '冻结成功',
            '0'     :     '解冻成功'
    }

    if not memberId:
        return {'code':1,'msg':'memberId请求错误'}


    memberTable = FORMAT_USER_TABLE%(memberId)
    if not redis.exists(memberTable):
        return {'code':1,'msg':'会员[%s]不存在'%(memberId)}

    valid = redis.hget(memberTable,'valid')
    pipe = redis.pipeline()
    if valid == '1':
        pipe.hset(memberTable,'valid','0')
    else:
        pipe.hset(memberTable,'valid','1')

    pipe.execute()

    if action in ['HALL','hall']:
        jump_url = BACK_PRE+'/member/list?pageNumber={}'.format(pageNumber)
    else:
        jump_url = BACK_PRE+'/fish/member/list?pageNumber={}'.format(pageNumber)

    return {'code':0,'msg':'会员[%s] %s'%(memberId,freezeDesc[valid]),'jumpUrl':jump_url}

@admin_app.get('/member/dayUseCard')
def get_member_day_useCard(redis,session):
    """
    玩家每日消耗房卡数统计
    """
    curTime = datetime.now()
    lang = getLang()
    isList = request.GET.get('list','').strip()
    startDate = request.GET.get('startDate','').strip()
    endDate = request.GET.get('endDate','').strip()
    memberId = request.GET.get('searchId','').strip()

    if isList:
        if not memberId:
            return []
        res = getMemberUseCardsByDay(redis,startDate,endDate,memberId)
        return json.dumps(res)
    else:
        info = {
                'title'     :       '玩家每日消耗钻石数',
                'listUrl'                :           BACK_PRE+'/member/dayUseCard?list=1&searchId=0',
                'searchTxt'              :           '会员编号',
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH
        }

        return template('admin_member_dayuser',PAGE_LIST=PAGE_LIST,info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.post('/member/open_auth')
def do_openAuth(redis,session):
    """
    开启玩家的代开房间权限
    """
    curTime = datetime.now()
    lang    = getLang()
    selfAccount,selfUid = session['account'],session['id']
    memberId = request.forms.get('id','').strip()

    login_info_dict = {
            '0'             :       'openMemberAuth',
            '1'             :       'unOpenMemberAuth'
    }

    memberTable = FORMAT_USER_TABLE%(memberId)
    if not redis.exists(memberTable):
        log_debug('[try do_openAuth][error] member[%s] is not exists!'%(memberId))
        return {'code':1,'msg':lang.MEMBER_NOT_EXISTES_TXT%(memberId)}

    open_auth = redis.hget(memberTable,'open_auth')
    if not open_auth:
        open_auth = '0'

    if open_auth == '0':
        redis.hset(memberTable,'open_auth',1)
        #doAgentChange(redis,agentId,'open_auth',1)
    else:
        redis.hset(memberTable,'open_auth',0)

    #记录操作日志
    logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                    'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE[login_info_dict[open_auth]]%(memberId)}
    writeAgentOpLog(redis,selfUid,logInfo)
    return {'code':0,'msg':lang.GROUP_CHECK_SETTING_SUCCESS,'jumpUrl':BACK_PRE+'/member/list'}
