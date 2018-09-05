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
import md5
from fish_db_define import *
from aliyun_sms.buyu_send_sms import *

shield_words = set()
SEND_CODE_LIMIT = 30

'''

@fish_app.get('/house/search')
@allow_cross
def do_inner(redis,session):

    house_no = request.forms.get('house_no','').strip()
    player_num = redis.hget('fish:house:%s:info'%house_no,'player_num') 
    online_tables = redis.keys('hall:session:*')
    if dic:
        return {'code':0,'hosue_info':{'house_no':house_no,'player_num':player_num}}
    elif house_no in set([str(i) for i in range(1,12+len(online_tables))]):
        return {'code':0,'hosue_info':{'house_no':house_no,'player_num':0}}
    else:
        return {'code':1,'msg':'房间不存在！'}
'''

@fish_app.post('/vip/info')
@allow_cross
def do_inner(redis,session):
    '''
        vip info
    '''
    sid = request.forms.get('sid','').strip()
    uid = redis.hget('hall:session:%s'%sid,'uid')
    # uid = request.forms.get('uid','').strip()
    user_table = "users:%s"%uid
    vip_level,vip_charge = redis.hmget(user_table,'vip_level','vip_charge')  
    vip_level = int(vip_level or 0)
    vip_charge = int(vip_charge or 0)
    door = {
        0:1000,
        1:3000,
        2:6000,
        3:10000,
        4:20000,
        5:0,
    }.get(vip_level)
    level_distance = (door - vip_charge) if door else 0
    return {'code':0,'vip_level':vip_level,'vip_charge':vip_charge,'level_distance':level_distance}

@fish_app.get('/house/list')
@allow_cross
def do_inner(redis,session):
    '''
        房间列表
    '''
    free = request.GET.get('free','').strip()
    gameid = request.GET.get('gameid','').strip()

    online_tables = redis.keys('hall:session:*')

    house_nos = set([str(i) for i in range(1,12+len(online_tables))])
    for h in redis.smembers('fish:%s:house:set'%gameid):
        house_nos.add(h)

    data = []
    free = int(free or 0)
    for house_no in house_nos:
        player_num = redis.hget('fish:%s:house:%s:info'%(gameid,house_no),'player_num') 
        player_num = int(player_num or 0)
        if free:
            max_player_count = redis.hget('fish:channel:%s:info'%gameid,'max_player_count')
            if player_num < int(max_player_count or 4):
                data.append({
                    "house_no":int(house_no),
                    "player_num":int(player_num or 0),
                })
        else:
            data.append({
                "house_no":int(house_no),
                "player_num":int(player_num or 0),
            })

    data = sorted(data,key=lambda x:x['house_no'])

    return {'code':0,'data':data}
                

@fish_app.post('/forget/pwd/modify')
@allow_cross
def do_inner(redis,session):
    '''
        忘记密码修改密码
    '''
    nickname = request.forms.get('nickname','').strip()
    check_code = request.forms.get('check_code','').strip()
    pwd = uuid.uuid4().hex[:8]

    uid = redis.get('nickname2uid:%s'%nickname)
    phone = redis.hget('users:%s'%uid,'phone')
    if not uid:
        return {'code':1,'msg':'昵称有误！'}
    real_code = redis.get('user:%s:code:pwd'%phone)
    if not real_code:
        return {'code':1,'msg':'验证码已过期！'}
    if check_code != real_code:
        return {'code':1,'msg':'验证码不正确！'}

    if len(pwd) > 30:
        return {'code':1,'msg':'密码格式不正确！'}

    new_pwd = md5.new(pwd).hexdigest()
    redis.hset('users:%s'%uid,'password',new_pwd) 
    redis.delete('user:%s:code:pwd'%phone)

    params = json.dumps({'nickname':nickname,'pwd':pwd})
    res = execute_send_sms(redis,uid,phone,'SMS_139972516',params)
    if not res:
        return {'code':1,'msg':'请求失败!请稍后再试！'}

    p = phone[:3]+'****'+phone[-4:]
    return {'code':0,'msg':'密码找回成功！您的新密码已发送至您的手机号%s。'%p}


@fish_app.post('/forget/pwd/code')
@allow_cross
def do_inner(redis,session):
    '''
        忘记密码发送验证码
    '''
    nickname = request.forms.get('nickname','').strip()

    uid = redis.get('nickname2uid:%s'%nickname)
    if not uid:
        return {'code':1,'msg':'该用户不存在！'}

    phone = redis.hget('users:%s'%uid,'phone')
    if not phone:
        return {'code':1,'msg':'该用户未完善信息！'}


    today = str(datetime.now())[:10]
    if int(redis.get('user:%s:date:%s:code:times'%(phone,today)) or 0) > SEND_CODE_LIMIT:
        return {'code':1,'msg':'今天发送验证码已达到上限！'}

    code = str(random.randint(1000,9999))
    redis.setex('user:%s:code:pwd'%phone,code,60*5)

    params = u'{"code":'+code+'}'
    res = execute_send_sms(redis,uid,phone,'SMS_140060199',params)
    if not res:
        return {'code':1,'msg':'发送验证码失败！'}

    redis.incrby('user:%s:date:%s:code:times'%(phone,today),1)
    redis.expire('user:%s:date:%s:code:times'%(phone,today),24*3600)
    if len(phone) == 11:
        show_phone = phone[:3]+'****'+phone[-4:]
        return {'code':0,'msg':'已发送验证码至%s！'%show_phone}
    else:
        return {'code':0,'msg':'发送验证码成功！'}

@fish_app.post('/info/check/code')
@allow_cross
def do_inner(redis,session):
    '''
        信息完善获取验证码
    '''
    sid = request.forms.get('sid','').strip()
    phone = request.forms.get('phone','').strip()

    uid = redis.hget('hall:session:%s'%sid,'uid')
    if not uid:
        return {'code':0,'msg':'登录超时！'}
    
    today = str(datetime.now())[:10]
    if int(redis.get('user:%s:date:%s:code:times'%(phone,today)) or 0) > SEND_CODE_LIMIT:
        return {'code':1,'msg':'今天发送验证码已达到上限！'}

    code = str(random.randint(1000,9999))
    redis.setex('user:%s:code:info'%phone,code,60*5)

    params = u'{"code":'+code+'}'
    res = execute_send_sms(redis,uid,phone,'SMS_140060199',params)
    if not res:
        return {'code':1,'msg':'发送验证码失败！'}
    
    redis.incrby('user:%s:date:%s:code:times'%(phone,today),1)
    redis.expire('user:%s:date:%s:code:times'%(phone,today),24*3600)
    return {'code':0,'msg':'发送验证码成功！'}

@fish_app.post('/info/complete/second/code')
@allow_cross
def do_inner(redis,session):
    '''
        二次信息完善验证码
    '''
    sid = request.forms.get('sid','').strip()
    uid = redis.hget('hall:session:%s'%sid,'uid')
    phone = redis.hget('users:%s'%uid,'phone')
    if not uid:
        return {'code':0,'msg':'登录超时！'}

    code = str(random.randint(1000,9999))
    redis.setex('user:%s:code:info'%phone,code,60*5)

    params = u'{"code":'+code+'}'
    res = execute_send_sms(redis,uid,phone,'SMS_140060199',params)
    if not res:
        return {'code':1,'msg':'发送验证码失败！'}

    p = phone[:3]+'****'+phone[-4:]
    return {'code':0,'msg':'验证码已发送至您的手机号%s。'%p}

@fish_app.post('/info/complete/second/pass')
@allow_cross
def do_inner(redis,session):
    '''
        二次信息完善通过
    '''
    sid = request.forms.get('sid','').strip()
    check_code = request.forms.get('check_code','').strip()
    uid = redis.hget('hall:session:%s'%sid,'uid')
    phone = redis.hget('users:%s'%uid,'phone')

    real_code = redis.get('user:%s:code:info'%phone)
    if check_code == real_code:
        return {'code':0,'msg':'验证成功！'}
    else:
        return {'code':1,'msg':'验证码不正确！'}

def get_shield_words():
    global shield_words

    if shield_words:
        return shield_words
    else:
        mysql = Mysql_instance()
        sql = "select distinct word from shield_words"
        mysql.cursor.execute(sql)
        res = mysql.cursor.fetchall()
        for row in res:
            shield_words.add(row[0])
        return shield_words
      
    

@fish_app.post('/info/complete')
@allow_cross
def do_inner(redis,session):
    '''
        信息完善
    '''
    sid = request.forms.get('sid','').strip()
    phone = request.forms.get('phone','').strip()
    check_code = request.forms.get('check_code','').strip()
    real_name = request.forms.get('real_name','').strip()
    id_card_no = request.forms.get('id_card_no','').strip()
    nickname = request.forms.get('nickname','').strip()
    #pwd = request.forms.get('pwd','').strip()

    uid = redis.hget('hall:session:%s'%sid,'uid')
    if not uid:
        return {'code':0,'msg':'登录超时！'}
    past_nn,openid,info_comp = redis.hmget('users:%s'%uid,'nickname','openid','info_comp')

    if len(phone) != 11:
        return {'code':1,'msg':'手机号必须是11位！'}

    '''
    if len(nickname) > 30:
        return {'code':1,'msg':'昵称不符合规范!'}
    if len(phone) > 11:
        return {'code':1,'msg':'号码不符合规范!'}

    sw = get_shield_words()
    for w in sw:
        if w in nickname:
            return {'code':1,'msg':'昵称包含敏感字!','word':w}
    '''

    if nickname in redis.smembers('fish:nickname:set'):
        return {'code':1,'msg':'昵称已存在!'}

    real_cc = redis.get('user:%s:code:info'%phone)   
    if not real_cc:
        return {'code':1,'msg':'验证码无效！'}
    if check_code != real_cc:
        return {'code':1,'msg':'验证码不正确！'}

    pwd = uuid.uuid4().hex[:8]
    new_pwd = md5.new(pwd).hexdigest()
    dic = {
            'password':new_pwd,
            'phone':phone,
            'nickname':nickname,
            'info_comp':1,
            'id_card_no':id_card_no,
            'real_name':real_name,
    }
    #redis.sadd('fish:phone:set',phone)

    #params = u'{"nickname":'+nickname+',"pwd":'+pwd+'}'
    params = json.dumps({'nickname':nickname,'pwd':pwd})
    res = execute_send_sms(redis,uid,phone,'SMS_139972516',params)
    if not res:
        return {'code':1,'msg':'信息完善失败!请稍后再试！'}

    if openid:
        del dic['password']
    pipe = redis.pipeline()
    pipe.hmset('users:%s'%uid,dic)
    pipe.delete('user:%s:code:info'%uid)   
    pipe.set('nickname2uid:%s'%nickname,uid)
    pipe.delete('nickname2uid:%s'%past_nn)
    pipe.srem('fish:nickname:set',past_nn)
    pipe.sadd('fish:nickname:set',nickname)
    pipe.execute()

    p = phone[:3]+'****'+phone[-4:]
    return {'code':0,'msg':'信息完善成功！您的新密码已发送至您的手机号%s。'%p}

@fish_app.get('/bag/list')
@allow_cross
def do_inner(redis,session):
    '''
        玩家背包道具列表
    '''
    sid = request.GET.get('sid','').strip()
    uid = redis.hget('hall:session:%s'%sid,'uid')
    headImgUrl,diamond,coin = redis.hmget('users:%s'%uid,'headImgUrl','diamond','coin') 
    diamond = int(diamond or 0)
    coin = int(coin or 0)
    box_diamond,box_coin = redis.hmget('box:user:%s:hesh'%uid,'1','2') 
    box_diamond = int(box_diamond or 0)
    box_coin = int(box_coin or 0)
    userInfo = {
            'headImgUrl':headImgUrl,
            'diamond':diamond,
            'coin':coin,
            'box_diamond':box_diamond,
            'box_coin':box_coin,
    }
    dic = redis.hgetall('player:item:uid:%s:hesh'%uid)    
    data = []
    for k,v in dic.items():
        if k == '1' or k == '2':
            continue
        d = redis.hgetall('attrs:itemid:%s:hesh'%k)
        d['num'] = int(v)
        d['item_id'] = int(k)
        data.append(d)

    bag_data = sorted(data,key=lambda x:x['item_id'])


    return {'code':0,'userInfo':userInfo,'bag_data':bag_data}

@fish_app.get('/box/status')
@allow_cross
def do_inner(redis,session):
    '''
        获取安全箱是否加密
    '''
    sid = request.GET.get('sid','').strip()
    uid = redis.hget('hall:session:%s'%sid,'uid')
    #box_lock = int(redis.hget('users:%s'%uid,'box_lock') or 0)
    box_pwd = redis.hget('users:%s'%uid,'box_pwd') or 0
    if box_pwd:
        box_pwd = 1
    return {'code':0,'box_lock':box_pwd}

@fish_app.post('/set/box/pwd')
@allow_cross
def do_inner(redis,session):
    '''
        设置保管箱密码
    '''
    sid = request.forms.get('sid','').strip()
    box_pwd = request.forms.get('box_pwd','').strip()
    uid = redis.hget('hall:session:%s'%sid,'uid')

    redis.hmset('users:%s'%uid,{'box_pwd':md5.new(box_pwd).hexdigest(),'box_lock':1})

    return {'code':0,'msg':'设置成功！'}

@fish_app.get('/box/lock')
@allow_cross
def do_inner(redis,session):
    '''
        关闭背包锁上安全箱
    '''
    sid = request.GET.get('sid','').strip()

    uid = redis.hget('hall:session:%s'%sid,'uid')
    if not uid:
        return {'code':1,'msg':'sid过期！'}

    box_lock = redis.hget('users:%s'%uid,'box_lock')
    if not box_lock:
        return {'code':1,'msg':'安全箱未加密!'}

    redis.hset('users:%s'%uid,'box_lock',1)
    return {'code':0,'msg':'安全箱已上锁!'}

@fish_app.post('/box/unlock')
@allow_cross
def do_inner(redis,session):
    '''
        解锁安全箱
    '''
    sid = request.forms.get('sid','').strip()
    box_pwd = request.forms.get('box_pwd','').strip()

    uid = redis.hget('hall:session:%s'%sid,'uid')

    box_lock = redis.hget('users:%s'%uid,'box_lock')
    if not uid:
        return {'code':1,'msg':'sid过期！'}
    real_bpwd = redis.hget('users:%s'%uid,'box_pwd')
    if md5.new(box_pwd).hexdigest() != real_bpwd:
        return {'code':1,'msg':'密码不正确！','box_lock':box_lock}
    else:
        redis.hset('users:%s'%uid,'box_lock',2)
        box_lock = redis.hget('users:%s'%uid,'box_lock')
        return {'code':0,'msg':'安全箱已解锁！','box_lock':box_lock}


@fish_app.get('/box/show')
@allow_cross
def do_inner(redis,session):
    '''
        显示保管箱物品
    '''
    sid = request.GET.get('sid','').strip()
    uid = redis.hget('hall:session:%s'%sid,'uid')

    box_lock,headImgUrl,diamond,coin = redis.hmget('users:%s'%uid,'box_lock','headImgUrl','diamond','coin')
    diamond = int(diamond or 0)
    coin = int(coin or 0)
    if box_lock == '1':
        return {'code':2,'msg':'请先解锁!'}

    dic = redis.hgetall('box:user:%s:hesh'%uid)
    data = []
    userInfo = {'headImgUrl':headImgUrl,'box_diamond':0,'box_coin':0,'diamond':diamond,'coin':coin}
    x = dic.items()
    for iid,num in x:
        dic = redis.hgetall('attrs:itemid:%s:hesh'%iid)
        if int(iid) == 1:
            userInfo['box_diamond'] = num
        elif int(iid) == 2:
            userInfo['box_coin'] = num
        else:
            dic['item_id'] = int(iid)
            dic['num'] = int(num)
            data.append(dic)

    res = {'code':0,'bag_data':data,'userInfo':userInfo}
    print res
    return res
     
@fish_app.post('/box/save')
@allow_cross
def do_inner(redis,session):
    '''
        存放保管箱物品
    '''
    sid = request.forms.get('sid','').strip()
    item_id = request.forms.get('item_id','').strip()
    num = request.forms.get('num','').strip()

    if int(num) <= 0:
        return {'code':1,'msg':'无效的数量！'}
    
    uid = redis.hget('hall:session:%s'%sid,'uid')
    if not uid:
        return {'code':1,'msg':'登录超时！'}

    if item_id == '1':
        cur_d = int(redis.hget('users:%s'%uid,'diamond') or 0)
        if int(num) > cur_d:
            return {'code':1,'msg':'钻石数量不足！'}

        redis.hincrby('box:user:%s:hesh'%uid,1,num)
        redis.hincrby('users:%s'%uid,'diamond',-int(num)) 
    elif item_id == '2':
        cur_c = int(redis.hget('users:%s'%uid,'coin') or 0)
        if int(num) > cur_c:
            return {'code':1,'msg':'金币数量不足！'}

        redis.hincrby('box:user:%s:hesh'%uid,2,num)
        redis.hincrby('users:%s'%uid,'coin',-int(num)) 
    else:
        cur_item_num = int(redis.hget('player:item:uid:%s:hesh'%uid,item_id) or 0)
        title = redis.hget('attrs:itemid:%s:hesh'%item_id,'title')
        if int(num) > cur_item_num:
            return {'code':1,'msg':title+'数量不足！'}

        redis.hincrby('box:user:%s:hesh'%uid,item_id,num)
        redis.hincrby('player:item:uid:%s:hesh'%uid,item_id,-int(num))

    return {'code':0,'msg':'存放成功！'}


@fish_app.post('/box/take')
@allow_cross
def do_inner(redis,session):
    '''
        提取保管箱物品
    '''
    sid = request.forms.get('sid','').strip()
    item_id = request.forms.get('item_id','').strip()
    num = request.forms.get('num','').strip()

    if int(num) < 0:
        return {'code':-1,'msg':'非法数值！'}

    uid = redis.hget('hall:session:%s'%sid,'uid')
    box_lock = redis.hget('users:%s'%uid,'box_lock')
    if box_lock != '2':
        return {'code':'1','msg':'请先解锁！'}

    dic = redis.hgetall('box:user:%s:hesh'%uid)
    cur_num = redis.hget('box:user:%s:hesh'%uid,item_id)
    if int(num) > int(cur_num or 0):
        return {'code':2,'msg':'数量不足！'}

    if item_id == '1':
        redis.hincrby('users:%s'%uid,'diamond',num)         
    if item_id == '2':
        redis.hincrby('users:%s'%uid,'coin',num)         
    else:
        redis.hincrby('player:item:uid:%s:hesh'%uid,item_id,num)         

    redis.hincrby('box:user:%s:hesh'%uid,item_id,-int(num))

    return {'code':0,'msg':'提取成功!'}

@fish_app.post('/box/check/code')
@allow_cross
def do_inner(redis,session):
    '''
        获取验证码
    '''
    sid = request.forms.get('sid','').strip()
    #phone = request.forms.get('phone','').strip()

    uid = redis.hget('hall:session:%s'%sid,'uid')
    today = str(datetime.now())[:10]
    phone = redis.hget('users:%s'%uid,'phone')
    if int(redis.get('user:%s:date:%s:code:times'%(phone,today)) or 0) > SEND_CODE_LIMIT:
        return {'code':1,'msg':'今天发送验证码已达到上限！'}

    if not phone:
        return {'code':1,'msg':'请先绑定手机号！'}
    check_code = str(random.randint(1000,9999))

    params = u'{"code":'+check_code+'}'
    res = execute_send_sms(redis,uid,phone,'SMS_140060199',params)
    if not res:
        return {'code':1,'msg':'发送验证码失败！'}

    redis.setex('user:%s:code:box'%phone,check_code,60*5)
    redis.incrby('user:%s:date:%s:code:times'%(phone,today),1)
    redis.expire('user:%s:date:%s:code:times'%(phone,today),24*3600)
    return {'code':0,'msg':'发送验证码成功！'}


@fish_app.post('/box/find/pwd')
@allow_cross
def do_inner(redis,session):
    '''
        保管箱找回密码
    '''
    sid = request.forms.get('sid','').strip()
    check_code = request.forms.get('check_code','').strip()
    #new_box_pwd = request.forms.get('new_box_pwd','').strip()

    uid = redis.hget('hall:session:%s'%sid,'uid')
    phone,nickname = redis.hmget('users:%s'%uid,'phone','nickname')
    real_cc = redis.get('user:%s:code:box'%phone)
    if not real_cc:
        return {'code':1,'msg':'验证码已过期!'}
    if real_cc != check_code:
        return {'code':1,'msg':'验证码不正确!'}

    new_box_pwd = str(random.randint(100000,999999))[:6]
    real_np = md5.new(new_box_pwd).hexdigest()


    p = phone[:3]+'****'+phone[-4:]

    #params = u'{"nickname":'+nickname+',"pwd":'+pwd+'}'
    params = json.dumps({'nickname':nickname,'pwd':new_box_pwd})
    res = execute_send_sms(redis,uid,phone,'SMS_139982509',params)
    if not res:
        return {'code':1,'msg':'修改失败！'}

    redis.hset('users:%s'%uid,'box_pwd',real_np)
    redis.delete('user:%s:code:box'%phone)
    return {'code':0,'msg':'修改成功！您的保管箱新密码已发送至您的手机号%s。'%p}
    

           
