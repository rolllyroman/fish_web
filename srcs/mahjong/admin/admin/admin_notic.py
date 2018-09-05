#-*- coding:utf-8 -*-
#!/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    邮件公告模块
"""
import os
from bottle import *
from admin import admin_app
from config.config import STATIC_LAYUI_PATH,STATIC_ADMIN_PATH,BACK_PRE,PARTY_PLAYER_COUNT
from common.utilt import *
from common.log import *
from common import web_util,log_util
from datetime import datetime
from model.gameModel import *
from model.agentModel import *
from model.mailModel import *
from model.protoclModel import *
from model.userModel import getAgentAllMemberIds
from common import log_util,convert_util,json_util
import json

def get_new_path(img_path,old_path):
    """ 获取路径 """
    if img_path.startswith("mahjong/static"):#去掉头部
        ori_file_name = "mahjong/static"+old_path
        if os.path.exists(ori_file_name):
            #删除原来的图片。
            try:
                os.remove(ori_file_name)
            except Exception,e:
                log_debug('[try do_reward_modify] delete file[%s] error reason[%s]'%(ori_file_name,e))
        #生成新的路径
        img_path = img_path[14:]

    return img_path

def delete_img_path(img_path):
    """ 删除图片 """
    ori_file_name = "mahjong/static"+img_path
    if os.path.exists(ori_file_name):
        #删除图片
        try:
            os.remove(ori_file_name)
        except Exception,e:
            log_debug('[try do_reward_modify] delete file[%s] error reason[%s]'%(ori_file_name,e))

@admin_app.get('/notic/list')
@admin_app.get('/notic/list/<action>')
@checkLogin
def get_notic_list(redis,session,action='HALL'):
    lang = getLang()
    action = action.upper()
    fields = ('startDate','endDate','isList')
    for field in fields:
        exec('%s = request.GET.get("%s","").strip()'%(field,field))

    log_util.debug('[get_notic_list] get params startDate[%s] endDate[%s] isList[%s] action[%s]'\
                        %(startDate,endDate,isList,action))
    if isList:
        noticList = getNoticsList(redis,session,lang,session['id'],action)
        return json.dumps(noticList,cls=json_util.CJsonEncoder)
    else:
        info = {
                'title'                 :       lang.GAME_NOTIFY_LIST_TXT,
                'tableUrl'              :       BACK_PRE+'/notic/list/{}?isList=1'.format(action),
                'createUrl'             :       BACK_PRE+'/notice/create/{}'.format(action),
                'STATIC_LAYUI_PATH'     :       STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'     :       STATIC_ADMIN_PATH,
                'back_pre'              :       BACK_PRE,
                'addTitle'              :       lang.GAME_NOTIFY_CREATE_TXT
        }
        return template('admin_notice_list',info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/notice/create')
@admin_app.get('/notice/create/<action>')
def do_createNotice(redis,session,action="HALL"):
    """
        创建新公告
    """
    lang = getLang()
    selfUid = session['id']
    action = action.upper()

    # adminTable = AGENT_TABLE%(selfUid)
    # # adminType  = redis.hget(adminTable,'type')
    info = {
        "title"                 :   lang.GAME_NOTIFY_SEND_TXT,
        "submitUrl"             :   BACK_PRE+"/notice/create",
        'STATIC_LAYUI_PATH'     :   STATIC_LAYUI_PATH,
        'STATIC_ADMIN_PATH'     :   STATIC_ADMIN_PATH,
        'back_pre'              :   BACK_PRE,
        'action'                :   action,
        'backUrl'               :   BACK_PRE+"/notic/list/{}".format(action)
    }

    return template('admin_game_notice_create',selfUid=selfUid,MAIL_SETTING_INFO=MAIL_SETTING_INFO,info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.post('/notice/create')
@checkLogin
def do_createNotice(redis,session):

    lang = getLang()
    fields = {
            ('title','公告信息标题',''),
            ('validDate','有效日期',''),
            ('messageType','信息类型',''),
            ('content','信息内容',''),
            ('action','后台系统','')
    }

    for field in fields:
        exec('%s = web_util.get_form("%s","%s","%s")'%(field[0],field[0],field[1],field[2]))

    log_util.debug('[try do_createNotice] title[%s] validDate[%s] messageType[%s] content[%s] action[%s]'\
                            %(title,validDate,messageType,content,action))
    try:
        messageInfo = {
                'title'         :       title,
                'validDate'     :       validDate,
                'messageType'   :       messageType,
                'content'       :       content
        }
        createNotice(redis,session['id'],messageInfo,action)
    except Exception,e:
        log_util.debug('[try do_createNotice] ERROR reason[%s]'%(e))
        return {'code':1,'msg':'添加新公告失败'}

    #记录操作日志
    return {'code':0,'msg':lang.GAME_NOTIFY_SEND_SUCCESS_TXT,'jumpUrl':BACK_PRE+'/notic/list/{}'.format(action)}

@admin_app.get('/notice/del')
def getGameNoticeDel(redis,session):
    """
    删除公告消息
    """
    noticId = request.GET.get('id','').strip()
    if not noticId:
        return {'code':1,'msg':'noticId[%s]不存在'%(noticId)}

    noticListTable = FORMAT_GAMEHALL_NOTIC_LIST_TABLE
    noticTable = FORMAT_GAMEHALL_NOTIC_TABLE%(noticId)
    if not redis.exists(noticTable):
        return {'code':1,'msg':'noticId[%s]的公告已被删除.'}

    info = {
            'title'         :       lang.GAME_NOTIFY_DEL_TXT,
    }

    pipe = redis.pipeline()
    try:
        pipe.lrem(noticListTable,noticId)
        pipe.delete(noticTable)
    except:
        return {'code':1,'msg':lang.GAME_NOTIFY_DEL_ERR_TXT}

    pipe.execute()
    return {'code':0,'msg':lang.GAME_NOTIFY_DEL_SUCCESS_TXT,'jumpUrl':BACK_PRE+'/notic/list'}

@admin_app.get('/notice/modify')
@admin_app.get('/notice/modify/<action>')
def get_notice_modify(redis,session,action="HALL"):
    lang=getLang()
    action = action.upper()
    fields = {
            ('noticeId','公告信息ID','')
    }
    for field in fields:
        exec('%s = web_util.get_query("%s","%s","%s")'%(field[0],field[0],field[1],field[2]))

    noticTable = FORMAT_GAMEHALL_NOTIC_TABLE%(noticeId)
    if not redis.exists(noticTable):
        log_util.debug('[try get_notice_modify] noticeId[%s] is not exists.'%(noticeId))
        return {'code':'1','msg':'公告消息不存在.'}

    noticInfo = redis.hgetall(noticTable)
    info = {
          'title'                 :      lang.GAME_NOTIFY_MODIFY_TXT,
          'noticeId'              :       noticeId,
          'backUrl'               :       BACK_PRE+'/notic/list/{}'.format(action),
          'submitUrl'             :       BACK_PRE+'/notice/modify/{}'.format(action),
          'back_pre'              :       BACK_PRE,
          'STATIC_LAYUI_PATH'     :       STATIC_LAYUI_PATH,
          'STATIC_ADMIN_PATH'     :       STATIC_ADMIN_PATH,
    }

    return template('admin_game_notice_modify',info=info,MSGTYPE2DESC=MSGTYPE2DESC,noticInfo=noticInfo,MAIL_SETTING_INFO=MAIL_SETTING_INFO,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.post('/notice/modify')
@admin_app.post('/notice/modify/<action>')
def do_noticModify(redis,session,action="HALL"):
    lang = getLang()
    action = action.upper()
    fields = {
            ('noticeId','公告信息ID',''),
            ('title','公告信息标题',''),
            ('validDate','有效日期',''),
            ('messageType','信息类型',''),
            ('content','信息内容','')
    }
    for field in fields:
        exec('%s = web_util.get_form("%s","%s","%s")'%(field[0],field[0],field[1],field[2]))

    noticTable = FORMAT_GAMEHALL_NOTIC_TABLE%(noticeId)
    pipe  =  redis.pipeline()
    messageInfo = {
            'title'         :       title,
            'validDate'     :       validDate,
            'messageType'   :       DESC2MSGTYPE[messageType.encode('utf-8')],
            'content'       :       content
    }
    log_util.debug('[try do_noticModify] noticeId[%s] messageInfo[%s] action[%s]'%(noticeId,messageInfo,action))
    pipe.hmset(noticTable,messageInfo)

    pipe.execute()
    return {'code':0,'msg':lang.GAME_NOTIFY_MODIFY_SUC_TXT,'jumpUrl':BACK_PRE+'/notic/list/{}'.format(action)}

@admin_app.get('/notice/push')
@admin_app.get('/notice/push/<action>')
def pushNotices(redis,session,action='hall'):
    """
    将消息放进玩家的信息列表
    """
    type2Msg = {'0':'推送','1':'取消推送'}
    action = action.upper()
    timeStr = convert_util.to_dateStr(datetime.now())
    agentId  = session['id']
    noticId = request.GET.get('id','').strip()

    pipe = redis.pipeline()
    #超级管理员发的公告需要塞到所有玩家的信息盒子
    noticeTable = FORMAT_GAMEHALL_NOTIC_TABLE%(noticId)
    senderId = redis.hget(noticeTable,'groupId')
    if not senderId:
        senderId = 1

    if action == 'HALL':
        memberIdList = getAgentAllMemberIds(redis,senderId)
        user_msg_table_list = FORMAT_USER_MESSAGE_LIST
    else:
        userIdKey = []
        memberIds = redis.smembers(ACCOUNT4WEIXIN_SET4FISH)
        for memberId in memberIds:
            table = FORMAT_ACCOUNT2USER_TABLE%(memberId) #从账号获得账号信息，和旧系统一样
            userIdKey.append(table)
        memberIdList = [userId.split(":")[1] for userId in redis.mget(userIdKey)]
        user_msg_table_list = FORMAT_USER_MSG_FISH_LIST

    #推送所有公告
    status = convert_util.to_int(redis.hget(noticeTable,'status'))
    log_util.debug('[try pushNotices] agentId[%s] memberIds[%s] status[%s] action[%s]'%(agentId,memberIdList,status,action))
    try:
        if status == 0:
            for memberId in memberIdList:
                pipe.hset(FORMAT_GAMEHALL_NOTIC_TABLE%(noticId),'time',timeStr)
                pipe.lpush(user_msg_table_list%(memberId),noticId)
            pipe.hset(noticeTable,'status','1')
        else:
            for memberId in memberIdList:
                pipe.lrem(user_msg_table_list%(memberId),noticId)
                pipe.srem(FORMAT_MSG_READ_SET%(noticId),memberId)
            pipe.hset(noticeTable,'status','0')
    except Exception,e:
        log_util.debug('[try pushNotices] ERROR agentId[%s] reason[%s]'%(agentId,e))
        return {'code':1,'msg':type2Msg[str(status)]+'失败.'}

    pipe.execute()
    return {'code':0,'msg':type2Msg[str(status)]+'成功.','jumpUrl':BACK_PRE+'/notic/list/{}'.format(action)}

@admin_app.get('/notice/read')
def getNoticeReadPage(redis,session):
    """
    读取信息
    """
    curTime = datetime.now()
    lang    = getLang()
    msgType = request.GET.get('type','').strip()
    msgId   = request.GET.get('id','').strip()
    agentId = request.GET.get('agentId','').strip()
    memberId = request.GET.get('memberId','').strip()
    action   = request.GET.get('action','').strip()

    #log
    log_util.debug('[try getNoticeReadPage] msgId[%s] msgType[%s] agentId[%s] action[%s]'%(msgId,msgType,agentId,action))

    noticeItem = FORMAT_GAMEHALL_NOTIC_TABLE%(msgId)
    if not redis.exists(noticeItem):
        return template('notice_not_exists')

    noticeReads = FORMAT_MSG_READ_SET%(msgId)
    readList = redis.smembers(noticeReads)

    #设置消息为已读
    if memberId not in readList:
        redis.sadd(noticeReads,memberId)

    title,content = redis.hmget(noticeItem,('title','content'))
    bodyCorol = "#FFFFFF"
    if action == "FISH":
        bodyCorol = "#1874CD"
    if msgType == MAIL_TYPE:
        #setReward2User(msgId,userId)
        deleteMsg(redis,msgId,memberId)

    log_util.debug('[try getNoticeReadPage] RETURN msgId[%s] title[%s] content[%s] action[%s]'%(msgId,title,content,action))
    return template('notice_content_page',content=content,title=title)

@admin_app.get('/notic/active/list')
@admin_app.get('/notic/active/list/<action>')
@checkLogin
def get_active_lists(redis,session,action='HALL'):
    lang = getLang()
    action = action.upper()
    fields = ('startDate','endDate','isList')
    for field in fields:
        exec('%s = request.GET.get("%s","").strip()'%(field,field))

    log_util.debug('[get_active_list] get params startDate[%s] endDate[%s] isList[%s] action[%s]'\
                        %(startDate,endDate,isList,action))
    if isList:
        noticList = get_active_list(redis,session,lang,session['id'],action)
        return json.dumps(noticList,cls=json_util.CJsonEncoder)
    else:
        info = {
                'title'                 :       lang.GAME_NOTIFY_LIST_TXT,
                'tableUrl'              :       BACK_PRE+'/notic/active/list/{}?isList=1'.format(action),
                'createUrl'             :       BACK_PRE+'/notice/active/create/{}'.format(action),
                'STATIC_LAYUI_PATH'     :       STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'     :       STATIC_ADMIN_PATH,
                'back_pre'              :       BACK_PRE,
                'addTitle'              :       '创建新活动'
        }
        return template('admin_active_list',info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/notice/active/create')
@admin_app.get('/notice/active/create/<action>')
def do_createNotice(redis,session,action="HALL"):
    """
        创建新公告
    """
    lang = getLang()
    selfUid = session['id']
    action = action.upper()

    # adminTable = AGENT_TABLE%(selfUid)
    # # adminType  = redis.hget(adminTable,'type')
    info = {
        "title"                 :   lang.GAME_NOTIFY_SEND_TXT,
        "submitUrl"             :   BACK_PRE+"/notice/active/create",
        'STATIC_LAYUI_PATH'     :   STATIC_LAYUI_PATH,
        'STATIC_ADMIN_PATH'     :   STATIC_ADMIN_PATH,
        'back_pre'              :   BACK_PRE,
        'upload_url'            :   BACK_PRE+'/goods/reward/upload',
        'action'                :   action,
        'backUrl'               :   BACK_PRE+"/notic/active/list/{}".format(action)
    }

    return template('admin_active_create',selfUid=selfUid,MAIL_SETTING_INFO=MAIL_SETTING_INFO,info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.post('/notice/active/create')
@checkLogin
def do_createActive(redis,session):
    """ 创建活动接口 """
    lang = getLang()
    fields = {
            ('title','活动名称',''),
            ('action','系统参数',''),
            ('sort','排序值',''),
            ('imgPath1','活动标签图1',''),
            ('imgPath2','活动标签图2',''),
            ('imgPath3','活动内容图',''),
    }

    for field in fields:
        exec('%s = web_util.get_form("%s","%s","%s")'%(field[0],field[0],field[1],field[2]))

    log_util.debug('[try do_createActive] title[%s]  imgPath1[%s] imgPath2[%s] action[%s]'\
                            %(title,imgPath1,imgPath2,action))
    try:
        messageInfo = {
                'title'         :       title,
                'sort'          :       sort,
                'imgPath1'      :       imgPath1[14:],
                'imgPath2'      :       imgPath2[14:],
                'imgPath3'      :       imgPath3[14:]
        }
        create_active(redis,session['id'],messageInfo,action)
    except Exception,e:
        log_util.debug('[try do_createNotice] ERROR reason[%s]'%(e))
        return {'code':1,'msg':'添加新公告失败'}

    #记录操作日志
    return {'code':0,'msg':lang.GAME_NOTIFY_SEND_SUCCESS_TXT,'jumpUrl':BACK_PRE+'/notic/active/list/{}'.format(action)}

@admin_app.get('/notice/active/push')
@admin_app.get('/notice/active/push/<action>')
def pushNotices(redis,session,action='hall'):
    """
    将消息放进玩家的信息列表
    """
    type2Msg = {'0':'推送','1':'取消推送'}
    action = action.upper()
    timeStr = convert_util.to_dateStr(datetime.now())
    agentId  = session['id']
    active_id = request.GET.get('active_id','').strip()

    pipe = redis.pipeline()
    #超级管理员发的公告需要塞到所有玩家的信息盒子
    active_table = FORMAT_GAMEHALL_ACTIVE_TABEL%(active_id)
    senderId = redis.hget(active_table,'groupId')
    if not senderId:
        senderId = 1

    if action == 'HALL':
        memberIdList = getAgentAllMemberIds(redis,senderId)
        user_msg_table_list = FORMAT_USER_ACTIVE_LIST
    else:
        userIdKey = []
        memberIds = redis.smembers(ACCOUNT4WEIXIN_SET4FISH)
        for memberId in memberIds:
            table = FORMAT_ACCOUNT2USER_TABLE%(memberId) #从账号获得账号信息，和旧系统一样
            userIdKey.append(table)
        memberIdList = [userId.split(":")[1] for userId in redis.mget(userIdKey)]
        user_msg_table_list = FORMAT_USER_ACTIVE_FISH_LIST

    #推送所有公告
    status = convert_util.to_int(redis.hget(active_table,'status'))
    log_util.debug('[try pushNotices] agentId[%s] memberIds[%s] status[%s] action[%s]'%(agentId,memberIdList,status,action))
    try:
        if status == 0:
            for memberId in memberIdList:
                pipe.hset(FORMAT_GAMEHALL_ACTIVE_TABEL%(active_id),'time',timeStr)
                pipe.lpush(user_msg_table_list%(memberId),active_id)
            pipe.hset(active_table,'status',1)
        else:
            for memberId in memberIdList:
                pipe.lrem(user_msg_table_list%(memberId),active_id)
                pipe.srem(FORMAT_ACT_READ_SET%(active_id),memberId)
            pipe.hset(active_table,'status',0)
    except Exception,e:
        log_util.debug('[try pushNotices] ERROR agentId[%s] reason[%s]'%(agentId,e))
        return {'code':1,'msg':type2Msg[str(status)]+'失败.'}

    pipe.execute()
    return {'code':0,'msg':type2Msg[str(status)]+'成功.','jumpUrl':BACK_PRE+'/notic/active/list/{}'.format(action)}

@admin_app.get('/notice/active/modify')
@admin_app.get('/notice/active/modify/<action>')
def get_notice_modify(redis,session,action="HALL"):
    lang=getLang()
    action = action.upper()
    fields = {
            ('noticeId','公告信息ID','')
    }
    for field in fields:
        exec('%s = web_util.get_query("%s","%s","%s")'%(field[0],field[0],field[1],field[2]))

    active_table = FORMAT_GAMEHALL_ACTIVE_TABEL%(noticeId)
    if not redis.exists(active_table):
        log_util.debug('[try get_notice_modify] noticeId[%s] is not exists.'%(noticeId))
        return {'code':'1','msg':'公告消息不存在.'}

    active_info = redis.hgetall(active_table)
    if not active_info.has_key('title'):
        active_info['title'] = '测试活动'

    info = {
          'title'                 :       '活动信息更改',
          'activeId'              :       noticeId,
          'backUrl'               :       BACK_PRE+'/notic/active/list/{}'.format(action),
          'submitUrl'             :       BACK_PRE+'/notice/active/modify/{}'.format(action),
          'back_pre'              :       BACK_PRE,
          'upload_url'            :       BACK_PRE+'/goods/reward/upload',
          'STATIC_LAYUI_PATH'     :       STATIC_LAYUI_PATH,
          'STATIC_ADMIN_PATH'     :       STATIC_ADMIN_PATH,
    }

    return template('admin_active_modify',info=info,MSGTYPE2DESC=MSGTYPE2DESC,active_info=active_info,MAIL_SETTING_INFO=MAIL_SETTING_INFO,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.post('/notice/active/modify')
@admin_app.post('/notice/active/modify/<action>')
def do_noticModify(redis,session,action="HALL"):
    lang = getLang()
    action = action.upper()
    fields = {
            ('activeId','公告信息ID',''),
            ('title','活动标题',''),
            ('sort','排序值',''),
            ('imgPath1','活动标签图1',''),
            ('imgPath1_old','',''),
            ('imgPath2','活动标签图2',''),
            ('imgPath2_old','',''),
            ('imgPath3','活动内容图',''),
            ('imgPath3_old','','')
    }
    for field in fields:
        exec('%s = web_util.get_form("%s","%s","%s")'%(field[0],field[0],field[1],field[2]))

    imgPath1 = get_new_path(imgPath1,imgPath1_old)
    imgPath2 = get_new_path(imgPath2,imgPath2_old)
    imgPath3 = get_new_path(imgPath3,imgPath3_old)

    active_table = FORMAT_GAMEHALL_ACTIVE_TABEL%(activeId)
    pipe  =  redis.pipeline()
    messageInfo = {
            'title'         :       title,
            'sort'         :       sort,
            'imgPath1'     :       imgPath1,
            'imgPath2'     :       imgPath2,
            'imgPath3'     :       imgPath3,
    }
    log_util.debug('[try do_noticModify] activeId[%s] messageInfo[%s] action[%s]'%(activeId,messageInfo,action))
    pipe.hmset(active_table,messageInfo)
    pipe.execute()
    return {'code':0,'msg':lang.GAME_NOTIFY_MODIFY_SUC_TXT,'jumpUrl':BACK_PRE+'/notic/active/list/{}'.format(action)}

@admin_app.get('/notice/active/read')
def get_active_read(redis,session):
    """
    读取信息
    """
    curTime = datetime.now()
    lang    = getLang()
    msgId   = request.GET.get('id','').strip()
    agentId = request.GET.get('agentId','').strip()
    memberId = request.GET.get('memberId','').strip()
    action   = request.GET.get('action','').strip()

    #log
    log_util.debug('[try getNoticeReadPage] msgId[%s] agentId[%s] action[%s]'%(msgId,agentId,action))

    active_item = FORMAT_GAMEHALL_ACTIVE_TABEL%(msgId)
    if not redis.exists(active_item):
        return template('notice_not_exists')

    title,contentPath = redis.hmget(active_item,('title','imgPath3'))
    #设置消息为已读
    if not redis.sismember(FORMAT_ACT_READ_SET%(msgId),memberId):
        redis.sadd(FORMAT_ACT_READ_SET%(msgId),memberId)

    #log_util.debug('[try getNoticeReadPage] RETURN msgId[%s] title[%s] content[%s] action[%s]'%(msgId,title,content,action))
    return template('active_page_content',contentPath=contentPath,title=title)

@admin_app.get('/notice/active/del')
@admin_app.get('/notice/active/del/<action>')
def getGameNoticeDel(redis,session,action="hall"):
    """
    删除活动消息
    """
    lang = getLang()
    action = action.upper()
    active_id = request.GET.get('active_id','').strip()
    if not active_id:
        return {'code':1,'msg':'active_id[%s]不存在'%(active_id)}

    active_table = FORMAT_GAMEHALL_ACTIVE_TABEL%(active_id)
    senderId = redis.hget(active_table,'groupId')
    if not senderId:
        senderId = 1

    if action == 'HALL':
        active_list_table = FORMAT_GAMEHALL_ACTIVE_LIST_TABLE
        memberIdList = getAgentAllMemberIds(redis,senderId)
        user_msg_table_list = FORMAT_USER_MESSAGE_LIST
    else:
        active_list_table = FORMAT_FISHHALL_ACTIVE_LIST_TABLE
        userIdKey = []
        memberIds = redis.smembers(ACCOUNT4WEIXIN_SET4FISH)
        for memberId in memberIds:
            table = FORMAT_ACCOUNT2USER_TABLE%(memberId) #从账号获得账号信息，和旧系统一样
            userIdKey.append(table)
        memberIdList = [userId.split(":")[1] for userId in redis.mget(userIdKey)]
        user_msg_table_list = FORMAT_USER_ACTIVE_FISH_LIST

    imgPath1,imgPath2,imgPath3 = redis.hmget(active_table,('imgPath1','imgPath2','imgPath3'))
    if not redis.exists(active_table):
        return {'code':1,'msg':'noticeIds not exists.'}

    info = {
            'title'         :       lang.GAME_NOTIFY_DEL_TXT,
    }

    pipe = redis.pipeline()
    try:
        pipe.lrem(active_list_table,active_id)
        pipe.delete(active_table)
        for memberId in memberIdList:
            pipe.lrem(user_msg_table_list%(memberId),active_id)
        pipe.delete(FORMAT_ACT_READ_SET%(active_id))
    except:
        return {'code':1,'msg':lang.GAME_NOTIFY_DEL_ERR_TXT}

    delete_img_path(imgPath1)
    delete_img_path(imgPath2)
    delete_img_path(imgPath3)
    pipe.execute()
    return {'code':0,'msg':lang.GAME_ACTIVE_DEL_SUCCESS_TXT,'jumpUrl':BACK_PRE+'/notic/active/list/{}'.format(action)}
