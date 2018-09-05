#!/usr/bin/env python
#-*-coding:utf-8 -*-

"""
@Author: $Author$
@Date: $Date$
@version: $Revision$

Description:
捕鱼好友接口模块
"""
from bottle import request,response,error,hook
from fish import fish_app
from web_db_define import *

#from config.config import *
from fish_config import consts
from datetime import datetime,timedelta
from common import convert_util,web_util,json_util,wechat_util
from common.utilt import allow_cross,getInfoBySid
from urlparse import urlparse
import time
import uuid
import random
import json

@fish_app.post('/choose/attach')
@allow_cross
def do_inner(redis,session):
    """ 
        选择附件
    """
    sid = request.forms.get('sid', '').strip()
    SessionTable, account, uid, verfiySid = getInfoBySid(redis, sid)
    coin,warhead = redis.hmget('users:%s'%uid,'coin','warhead')
    warhead = int(warhead or 0)
    return {'code':0,'data':{'2':warhead}}
    
@fish_app.post('/get/attach')
@allow_cross
def do_inner(redis,session):
    """ 
        获得附件
    """
    eid = request.forms.get('eid', '').strip()
    sid = request.forms.get('sid', '').strip()
    SessionTable, account, uid, verfiySid = getInfoBySid(redis, sid)
    attach = redis.hget('fish:mail:%s'%eid,'attach')
    
    if attach:
        for c in eval(attach):
            if int(c['id']) == 1:
                coin = redis.hincrby('users:%s'%uid,'coin',int(c['num']))
            elif int(c['id']) == 2:
                redis.hincrby('users:%s'%uid,'warhead',int(c['num']))

        # 领取后删除邮件
        if redis.hget('fish:mail:%s'%eid,'type') == '0':
            mail_set = 'user:%s:system:mails'
        else:
            mail_set = 'user:%s:player:mails'

        redis.srem(mail_set%uid,eid)
        redis.delete('fish:mail:%s'%eid)
        return {'code':0,'msg':'ok'}
    else:
        return {'code':1,'msg':'领取失败！'}
    
    
@fish_app.post('/send/mail')
@allow_cross
def do_inner(redis,session):
    """ 
       发送邮件
    """
    sid = request.forms.get('sid', '').strip()
    SessionTable, account, uid, verfiySid = getInfoBySid(redis, sid)
    #uid = request.forms.get('uid', '').strip()
    recv_uid = request.forms.get('recv_uid', '').strip()
    coin = int(request.forms.get('1','').strip())
    warhead = int(request.forms.get('2', '').strip())

    coin = int(redis.hget('users:%s'%uid,'coin') or 0)
    if coin - 1000 < 0:
        return {'code':1,'msg':'发送失败！需要邮递费用1000金币!'}
    if redis.scard('user:%s:player:mail'%recv_uid) >= 20: 
        return {'code':1,'msg':'发送失败！对方邮件箱已满!'}

    redis.hincrby('users:%s'%uid,'coin',-1000)
    eid = uid + "|" + str(int(time.time()))
    redis.sadd('user:%s:player:mails'%recv_uid,eid)

    attach = []  
    if coin:
        attach.append({'id':1,'num':coin})
    if warhead:
        attach.append({'id':2,'num':warhead})

    redis.hmset('fish:mail:%s'%eid,{
        "eid":eid,
        "from":redis.hget('users:%s'%uid,'nickname'),
        'from_uid':uid,
        "attach":attach, 
        "timestamp":int(time.time()),
        "send_time":str(datetime.now())[:19],
        "type":1,
        "isRead":0,
    }) 

    return {'code':0,'msg':'发送成功!'}

@fish_app.get('/show/mails')
@allow_cross
def do_inner(redis,session):
    """ 
       查看邮件
    """
    sid = request.GET.get('sid', '').strip()
    SessionTable, account, uid, verfiySid = getInfoBySid(redis, sid)

    eids = list(redis.smembers('user:%s:system:mails'%uid)) + list(redis.smembers('user:%s:player:mails'%uid))
    # 超过三十天则删除
    for eid in eids:
        now_ts = int(time.time())
        send_ts = int(eid.split('|')[1])

        if now_ts - send_ts > 3600*24*30:
            if redis.hget('fish:mail:%s'%eid,'type') == "0":
                mail_set = 'user:%s:system:mails'
            else:
                mail_set = 'user:%s:player:mails'

            redis.delete('fish:mail:%s'%eid)
            redis.srem(mail_set%uid,eid)

    # 获取未过期的所有邮件
    eids = list(redis.smembers('user:%s:system:mails'%uid)) + list(redis.smembers('user:%s:player:mails'%uid))
    data_not_read = []  
    data_is_read = []  
    if eids:
        for eid in eids:
            dic = redis.hgetall('fish:mail:%s'%eid)
            dic['attach'] = eval(dic['attach'])
            if redis.hget('fish:mail:%s'%eid,'isRead') == '0':
                data_not_read.append(dic)
            else:
                data_is_read.append(dic)

        
        data_not_read = sorted(data_not_read,key=lambda x:int(x['timestamp']),reverse=True)
        data_is_read = sorted(data_is_read,key=lambda x:int(x['timestamp']),reverse=True)
    data = data_not_read + data_is_read

    return {'code':0,'data':data}

@fish_app.post('/read/mail')
@allow_cross
def do_inner(redis,session):
    """ 
       邮件已读
    """
    eid = request.forms.get('eid', '').strip()
    redis.hset('fish:mail:%s'%eid,'isRead','1')
    return {'code':0,'msg':'ok!'}

@fish_app.post('/del/mail')
@allow_cross
def do_inner(redis,session):
    """ 
       删除邮件
    """
    eid = request.forms.get('eid', '').strip()
    sid = request.forms.get('sid', '').strip()
    SessionTable, account, uid, verfiySid = getInfoBySid(redis, sid)
    if redis.hget('fish:mail:%s'%eid,'type') == '0':
        mail_set = 'user:%s:system:mails'
    else:
        mail_set = 'user:%s:player:mails'

    redis.srem(mail_set%uid,eid)
    redis.delete('fish:mail:%s'%eid)
    return {'code':0,'msg':'删除成功!'}
    

@fish_app.post('/friend/del')
@allow_cross
def do_inner(redis,session):  
    '''
        删除好友
    '''
    sid = request.forms.get("sid","").strip()
    del_uid = request.forms.get("del_uid","").strip()
    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    redis.srem('user:%s:friend:set'%del_uid,uid)
    redis.srem('user:%s:friend:set'%uid,del_uid)
    return {'code':0,'msg':'删除成功！'}

@fish_app.post('/friend/comment')
@allow_cross
def do_inner(redis,session):  
    '''
        修改或添加备注
    '''
    sid = request.forms.get("sid","").strip()
    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    comment = request.forms.get("comment","").strip()
    redis.hset('users:%s'%uid,'comment',comment)

    return {'code':0,'msg':'ok'}

@fish_app.post('/friend/room/invite')
@allow_cross
def do_inner(redis,session):  
    '''
        房间发送邀请
    '''
    
    sid = request.forms.get("sid","").strip()
    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    invite_uid = request.forms.get("invite_uid","").strip()
    game_id = request.forms.get("game_id","").strip()
    room_no = request.forms.get("room_no","").strip()

    redis.setex('user:%s:invited:room:no'%room_no,room_no,30)
    
    if redis.llen('user:%s:invited:req'%invite_uid) > 3:
        redis.rpop('user:%s:invited:req'%invite_uid)
    nickname,headImgUrl = redis.hget('users:%s'%uid,'nickname','headImgUrl')
    info = json.dumps({
            "uid":uid,
            "nickname":nickname,
            "headImgUrl":headImgUrl,
            "game_id":game_id
    })

    redis.lpush('user:%s:invited:req'%invite_uid,info)
    return {"code":0,"msg":"ok!"}

def get_find_uids(redis,find_uids,self_uid):

    num = 10

    # 去掉自己
    if self_uid in find_uids:
        find_uids.remove(self_uid)

    friends = redis.smembers('user:%s:friend:set'%self_uid)
    for f in friends:
        find_uids.remove(f)

    if len(find_uids) < 10:
        return find_uids
    else:
        return random.sample(find_uids,10) 

@fish_app.get('/friend/find/list')
@allow_cross
def do_inner(redis,session):  
    '''
        寻找列表
    '''
    sid = request.GET.get("sid","").strip()
    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)

    cur_day = datetime.now()       
    day7ago = cur_day - timedelta(7)
    uids = []
    while cur_day >= day7ago: 
        date_str = str(cur_day)[:10]
        uids += list(redis.smembers('active:users:date:%s'%date_str))      
        cur_day -= timedelta(1)
        
    uids = list(set(uids))

    find_uids = get_find_uids(redis,uids,uid)
    
    data = []
    for friend in find_uids:
        uid = friend
        today = str(datetime.now())[:10]
        today_fish = redis.get('user:%s:gain:fish:date:%s'%(uid,today)) 
        today_coins = redis.get('user:%s:gain:coins:date:%s'%(uid,today)) 
        today_warheads = redis.get('user:%s:gain:warheads:date:%s'%(uid,today))

        headImgUrl,nickname,last_login_date,comment = redis.hmget('users:%s'%friend,'headImgUrl','nickname','last_login_date','comment')
        if not comment:
            comment = "这个人很懒，还没有备注。"
        dic = {
                "uid":friend,
                "headImgUrl":headImgUrl,
                "nickname":nickname,
                "last_login_date":last_login_date,
                "comment":comment,
                "today_fish":today_fish or 0,
                "today_coins":today_coins or 0,
                "today_warheads":today_warheads or 0,
        }
        data.append(dic)

    return {'code':0,'data':data}
    
@fish_app.get('/friend/search')
@allow_cross
def do_inner(redis,session):  
    '''
        查找好友
    '''
    search_id = request.GET.get("search_id","").strip()
    if not redis.exists('users:%s'%search_id):
        return {'code':1,'msg':'用户不存在！'}
    headImgUrl,nickname,last_login_date,comment = redis.hmget('users:%s'%search_id,'headImgUrl','nickname','last_login_date','comment')
    uid = search_id
    today = str(datetime.now())[:10]
    today_fish = redis.get('user:%s:gain:fish:date:%s'%(uid,today)) 
    today_coins = redis.get('user:%s:gain:coins:date:%s'%(uid,today)) 
    today_warheads = redis.get('user:%s:gain:warheads:date:%s'%(uid,today))
    userInfo = {
                "search_id":search_id,
                "headImgUrl":headImgUrl,
                "nickname":nickname,
                "last_login_date":last_login_date,
                "comment":comment or '',
                "today_fish":today_fish or 0,
                "today_coins":today_coins or 0,
                "today_warheads":today_warheads or 0,
    }

    return {'code':0,'userInfo':userInfo}
    

@fish_app.get('/friend/list')
@allow_cross
def do_inner(redis,session):  
    '''
        好友列表
    '''
    sid = request.GET.get("sid","").strip()
    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    friends = redis.smembers('user:%s:friend:set'%uid)
    data = []
    for friend in friends:
        uid = friend
        today = str(datetime.now())[:10]
        today_fish = redis.get('user:%s:gain:fish:date:%s'%(uid,today)) 
        today_coins = redis.get('user:%s:gain:coins:date:%s'%(uid,today)) 
        today_warheads = redis.get('user:%s:gain:warheads:date:%s'%(uid,today))

        headImgUrl,nickname,last_login_date,comment = redis.hmget('users:%s'%friend,'headImgUrl','nickname','last_login_date','comment')
        dic = {
                "uid":friend,
                "headImgUrl":headImgUrl,
                "nickname":nickname,
                "last_login_date":last_login_date,
                "comment":comment or '这个人很懒，还没有备注。',
                "today_fish":today_fish or 0,
                "today_coins":today_coins or 0,
                "today_warheads":today_warheads or 0,
        }
        data.append(dic)
    return {'code':0,'data':data}

@fish_app.post('/friend/invite')
@allow_cross
def do_inner(redis,session):  
    '''
        发送好友请求
    '''
    msg = request.forms.get("msg","").strip()
    sid = request.forms.get("sid","").strip()
    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    nickname = redis.hget('users:%s'%uid,'nickname')
    to_uid = request.forms.get("to_uid","").strip()

    if uid == to_uid:
        return {'code':1,'msg':'您不能添加自己为好友！'}

    if uid in redis.smembers('user:%s:friend:set'%to_uid):
        return {'code':1,'msg':'您已是对方好友，不能重复发送好友请求！'}

    if to_uid in redis.smembers('user:%s:friend:set'%uid):
        return {'code':1,'msg':'对方好友已是您好友，不能重复发送好友请求！'}

    if int(redis.scard('user:%s:friend:set'%uid) or 0) > 30:
        return {'code':1,'msg':'您的好友已达到上限,无法添加好友！'}

    if int(redis.scard('user:%s:friend:set'%to_uid) or 0) > 30:
        return {'code':1,'msg':'对方好友已达到上限,无法添加好友！'}

    account = redis.hget('users:%s'%to_uid,'account')
    #if account not in redis.smembers('account4weixin:set'):
    #    return {'code':1,'msg':'用户不存在！'}

    #检验对方好友申请中是否存在
    iids = redis.lrange('user:%s:friend:req:list'%to_uid,0,-1)
    for iid in iids:
        if iid.split('|')[0] == uid:
            return {'code':1,'msg':'您已发送过好友请求，不可重复发送！'}


    send_time = str(datetime.now())[:19]

    invite_id = uid + "|" + str(int(time.time()))
    if redis.llen('user:%s:friend:req:list'%to_uid) > 30:
        reids.rpop('user:%s:friend:req:list'%to_uid)

    redis.lpush('user:%s:friend:req:list'%to_uid,invite_id)
    redis.hmset('friend:invite:%s'%invite_id,{
        "uid":uid,
        "msg":msg,
        "send_time":send_time,
        "nickname":nickname,
    })

    return {'code':0,'msg':'发送成功！'}

@fish_app.post('/friend/accept/invite')
@allow_cross
def do_inner(redis,session):  
    '''
        接受好友申请
    '''
    sid = request.forms.get("sid","").strip()
    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    from_uid = request.forms.get("from_uid","").strip()
    invite_id = request.forms.get("invite_id","").strip()

    if int(redis.scard('user:%s:friend:set'%uid) or 0) > 30:
        return {'code':1,'msg':'添加失败，您的好友已达到上限！'}

    if int(redis.scard('user:%s:friend:set'%from_uid) or 0) > 30:
        return {'code':1,'msg':'添加失败，对方好友已达到上限！'}

    redis.sadd('user:%s:friend:set'%uid,from_uid)
    redis.sadd('user:%s:friend:set'%from_uid,uid)
    redis.delete('friend:invite:%s'%invite_id)
    redis.lrem('user:%s:friend:req:list'%uid,invite_id)

    return {'code':0,'msg':'添加成功！'}

@fish_app.post('/friend/refuse/invite')
@allow_cross
def do_inner(redis,session):  
    '''
        拒绝好友申请
    '''
    sid = request.forms.get("sid","").strip()
    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    invite_id = request.forms.get("invite_id","").strip()
    redis.lrem('user:%s:friend:req:list'%uid,invite_id)
    redis.delete('friend:invite:%s'%invite_id)
    return {'code':0,'msg':'ok！'}

@fish_app.get('/friend/req/list')
@allow_cross
def do_inner(redis,session):  
    '''
        获取好友申请列表
    '''
    sid = request.GET.get("sid","").strip()
    SessionTable,account,uid,verfiySid = getInfoBySid(redis,sid)
    reqs = redis.lrange('user:%s:friend:req:list'%uid,0,-1)
    data = []
    for req in reqs: 
        uid = req.split('|')[0]
        today = str(datetime.now())[:10]
        today_fish = redis.get('user:%s:gain:fish:date:%s'%(uid,today)) 
        today_coins = redis.get('user:%s:gain:coins:date:%s'%(uid,today)) 
        today_warheads = redis.get('user:%s:gain:warheads:date:%s'%(uid,today))

        dic = redis.hgetall('friend:invite:%s'%req)
        dic['invite_id'] = req
        dic['comment'] = redis.hget('users:%s'%uid,'comment') or '这个人很懒，还没有备注。'
        dic['today_fish'] = today_fish or 0
        dic['today_coins'] = today_coins or 0
        dic['today_warheads'] = today_warheads or 0
        data.append(dic)
    return {'code':0,'data':data}
