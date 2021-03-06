#-*- coding:utf-8 -*-
#!/usr/bin/python
"""
Author:$Author$
Date:$Date$
Revision:$Revision$

Description:
    this is Description
"""
from bottle import response,request,template,redirect
from admin import admin_app
from config.config import STATIC_LAYUI_PATH,STATIC_ADMIN_PATH,BACK_PRE,PARTY_PLAYER_COUNT
from common.utilt import *
from common.log import *
from common import log_util,convert_util,web_util,menu_util
from datetime import datetime
from model.gameModel import *
from model.agentModel import *
from model.protoclModel import *
from model import userModel
from model.fishModel import *
import json
import access_module
import traceback

FORMART_POST_STR = "%s = request.forms.get('%s','').strip()"
FORMART_GET_STR  = "%s = request.GET.get('%s','').strip()"

MAIL_ITEMS = [
    {'title':'金币','id':'1'},
    {'title':'弹头','id':'2'},
]

@admin_app.get('/fish/send/system/mail')
@checkAccess
def send_mail(redis,session):
    """
        发送系统邮件页面
    """

    lang    = getLang()
    post_res = request.GET.get('post_res','').strip()

    info = {
            'title'                  :       '发送邮件',
            'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
            'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH,
            'submitUrl'              :       BACK_PRE + "/bag/send/mail"
    }

    return template('admin_fish_send_mail',info=info,lang=lang,RES_VERSION=RES_VERSION,post_res=post_res,items=MAIL_ITEMS)


@admin_app.post('/fish/room/list')
@checkAccess
def getFishRoomList(redis,session):
    """
    捕鱼房间列表
    """
    lang = getLang()
    isList = request.GET.get('list','').strip()
    info = {
            'title'         :     lang.FISH_ROOM_LIST_TXT,
            'addTitle'      :     lang.FISH_ROOM_CREATE_TXT,
            'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
            'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH,
            'serversUrl'    :     BACK_PRE+'/game/server/list?list=1',
            'tableUrl'      :     BACK_PRE+'/fish/room/list?list=1'
    }
    #accesses = eval(session['access'])
    if isList:
        res = get_room_list(redis,False,True)
        return json.dumps(res)
    else:
        #info['createAccess'] = True if BACK_PRE+'/game/create' in accesses else False
        info['createUrl']   = BACK_PRE+'/fish/room/create'
        return template('admin_fish_room_list',info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/fish/room/create')
@checkAccess
def getFishRoomCreate(redis,session):
    """
    创建捕鱼房间
    """
    lang = getLang()

    info = {
            'title'             :       lang.FISH_ROOM_CREATE_TXT,
            'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
            'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH,
            'back_pre'          :       BACK_PRE,
            'backUrl'           :       BACK_PRE+'/fish/room/list',
            'submitUrl'         :       BACK_PRE+'/fish/room/create',
    }

    return template('admin_fish_room_create',info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.post('/fish/room/create')
def do_createFishRoom(redis,session):
    """
    创建捕鱼房间
    """
    lang = getLang()
    curTime = datetime.now()
    #获取数据
    for FIELDS in FISH_FIELDS:
        exec(FORMART_POST_STR%(FIELDS,FIELDS))

    log_debug('[try do_createFishRoom]')

    checkNullFields = [
        {'field':room_name,'msg':lang.FISH_ROOM_NAME_EMPTY_TXT},
        {'field':room_id,'msg':lang.FISH_ROOM_ID_EMPTY_TXT},
        {'field':base_coin,'msg':lang.FISH_ROOM_BASE_EMPTY_TXT},
        {'field':max_base_coin,'msg':lang.FISH_ROOM_MAX_BASE_EMPTY_TXT},
        {'field':step_base_coin,'msg':lang.FISH_ROOM_STEP_BASE_EMPTY_TXT}
    ]

    for check in checkNullFields:
        if not check['field']:
            return {'code':1,'msg':check['msg']}

    fish_ids = redis.smembers(GAMEID_SET)
    if room_id in fish_ids:
        #房间ID不能重复
        return {'code':1,'msg':'房间ID[%s]已经存在!'%(room_id)}

    roomInfo = {
            'room_id'            :       room_id,
            'room_name'          :       room_name,
            'min_coin'           :       min_coin,
            'max_coin'           :       max_coin,
            'ip_mask'            :       ip_mask,
            'max_player_count'   :       max_player_count,
            'base_coin'          :       base_coin,
            'max_base_coin'      :       max_base_coin,
            'step_base_coin'     :       step_base_coin,
            'status'             :       0,
            'need_coin'          :       need_coin  if need_coin else 0,
            'coin_value'         :       coin_value if coin_value else 0,
            'isTrail'            :       isTrail,
            'tax_rate'           :       tax_rate if tax_rate else 0,
            'get_rate'           :       get_rate if get_rate else '',
            'fish_limit_count'   :       fish_limit_count if fish_limit_count else 0,
            'fish_need_count'    :       fish_need_count if fish_need_count else 0,
            'max_add'            :       max_add if max_add else 0,
            'ticket_wait_time'            :       ticket_wait_time if ticket_wait_time else '[]',
            'max_ticket_count'            :       max_ticket_count if max_ticket_count else 0,
    }

    try:
        create_fish_room(redis,roomInfo)
        log_util.debug('[try do_createFishRoom] room_id[%s] roomInfo[%s] create success.'%(room_id,roomInfo))
    except Exception,e:
        return {'code':2,'msg':'reason[%s]'%(e)}

    #记录操作日志
    logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                    'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE['createFishRoom']%(room_name)}
    #记录日志
    writeAgentOpLog(redis,session['id'],logInfo)
    return {'code':0,'msg':'房间[%s]创建成功.'%(room_name),'jumpUrl':BACK_PRE+'/fish/room/list'}

@admin_app.post('/fish/room/delete')
@checkLogin
def do_fishroom_delete(redis,session):
    """
    捕鱼房间列表删除接口
    :params room_id 删除的房间ID
    """
    fields = {
        ('room_id','房间ID','')
    }
    for field in fields:
        exec("%s = web_util.get_form('%s','%s','%s')"%(field[0],field[0],field[1],field[2]))

    try:
        delete_fishroom(redis,room_id)
    except:
        log_util.debug('[do_fishroom_delete] error[%s]'%(e))
        return web_util.do_response(1,'删除失败!')

    return web_util.do_response(0,'删除成功',jumpUrl=BACK_PRE+'/fish/room/list')

@admin_app.get('/fish/room/modify')
@admin_app.get('/fish/room/info/<rooms_id:int>')
@checkLogin
def getFishRoomModify(redis,session,rooms_id=None):
    """
    修改捕鱼房间
    """
    lang = getLang()
    room_id = request.GET.get('room_id','').strip()

    if rooms_id:
        #请求数据接口
        log_util.debug('[try getFishRoomModify] rooms_id[%s]'%(rooms_id))
        room_info  =  get_fish_room_info(redis,rooms_id)
        #避免新增字段
        if 'need_coin' not in room_info.keys():
            room_info['need_coin'] = 0
        if 'coin_value' not in room_info.keys():
            room_info['coin_value'] = 0
        return {'room_info':room_info}
    else:

        info = {
                'title'             :       lang.FISH_ROOM_MODIFY_TXT,
                'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH,
                'backUrl'           :       BACK_PRE+'/fish/room/list',
                'submitUrl'         :       BACK_PRE+'/fish/room/modify',
                'back_pre'          :       BACK_PRE
        }

        return template('admin_fish_room_modify',info=info,room_id=room_id,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.post('/fish/room/modify')
@checkLogin
def do_modifyFishRoom(redis,session):
    """
    修改捕鱼房间接口
    """
    lang = getLang()
    curTime = datetime.now()
    #获取数据
    for FIELDS in FISH_FIELDS:
        exec(FORMART_POST_STR%(FIELDS,FIELDS))

    checkNullFields = [
        {'field':room_name,'msg':lang.FISH_ROOM_NAME_EMPTY_TXT},
        {'field':room_id,'msg':lang.FISH_ROOM_ID_EMPTY_TXT},
        {'field':base_coin,'msg':lang.FISH_ROOM_BASE_EMPTY_TXT},
        {'field':max_base_coin,'msg':lang.FISH_ROOM_MAX_BASE_EMPTY_TXT},
        {'field':step_base_coin,'msg':lang.FISH_ROOM_STEP_BASE_EMPTY_TXT}
    ]

    for check in checkNullFields:
        if not check['field']:
            return {'code':1,'msg':check['msg']}

    roomInfo = {
            'room_id'            :       room_id,
            'room_name'          :       room_name,
            'min_coin'           :       min_coin,
            'max_coin'           :       max_coin,
            'ip_mask'            :       ip_mask,
            'max_player_count'   :       max_player_count,
            'base_coin'          :       base_coin,
            'max_base_coin'      :       max_base_coin,
            'step_base_coin'     :       step_base_coin,
            'status'             :       0,
            'isTrail'            :       isTrail,
            'need_coin'          :       need_coin  if need_coin else 0,
            'coin_value'         :       coin_value if coin_value else 0,
            'tax_rate'           :       tax_rate if tax_rate else 1,
            'get_rate'           :       get_rate if get_rate else '',
            'fish_limit_count'   :       fish_limit_count if fish_limit_count else 0,
            'fish_need_count'    :       fish_need_count if fish_need_count else 0,
            'max_add'            :       max_add if max_add else 0,
            'min_add'            :       min_add if min_add else 0,
            'ticket_wait_time'            :       ticket_wait_time if ticket_wait_time else '[]',
            'max_ticket_count'            :       max_ticket_count if max_ticket_count else 0,
            
    }

    try:
        modify_fish_room(redis,roomInfo)
        sendProtocol2GameService(redis,room_id,HEAD_SERVICE_PROTOCOL_GAME_CONFIG_REFRESH)
        log_debug('[try do_modifyFishRoom] room_id[%s] roomInfo[%s] modify success.'%(room_id,roomInfo))
    except Exception,e:
        return {'code':2,'msg':'reason[%s]'%(e)}

    #记录操作日志
    logInfo = {'datetime':curTime.strftime('%Y-%m-%d %H:%M:%S'),\
                    'ip':request.remote_addr,'desc':lang.AGENT_OP_LOG_TYPE['modifyFishRoom']%(room_name)}
    #记录日志
    writeAgentOpLog(redis,session['id'],logInfo)
    return {'code':0,'msg':'房间[%s]修改成功.'%(room_name),'jumpUrl':BACK_PRE+'/fish/room/list'}

@admin_app.get('/fish/bet/list')
@checkAccess
def get_betlist(redis,session):
    """
    获取投注明细列表
    """
    lang = getLang()
    fields = ('isList','startDate','endDate','room_id','pageSize','pageNumber','sort_name','sort_method','user_id')
    for field in fields:
        exec('%s = request.GET.get("%s","").strip()'%(field,field))

    log_util.debug('isList[%s] startDate[%s] [%s] [%s] [%s] [%s]'%(isList,startDate,endDate,room_id,pageSize,pageNumber))
    page_info = {   #分页数据
            'page_size'     :       pageSize,
            'page_number'   :       pageNumber
    }

    sort_info = {   #排序数据
            'sort_name'     :       sort_name,
            'sort_method'   :       sort_method
    }

    if isList:
        bet_records = get_bet_list(redis,startDate,endDate,room_id,user_id,page_info,sort_info)
        return json.dumps(bet_records)
    else:
        info = {
                    'title'                  :       '胜负统计',
                    'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
                    'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH,
                    'back_pre'               :       BACK_PRE,
                    'room_search'            :       True,#房间搜索
                    'user_search'            :       True,
                    'rooms'                  :       get_room_list(redis),
                    'tableUrl'               :       BACK_PRE+'/fish/bet/list?isList=1'
        }

        return template('admin_fish_room_bet',PAGE_LIST=PAGE_LIST,info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/fish/bet/report')
def get_betReport(redis,session):
    """
    捕鱼投注输赢报表
    """
    lang = getLang()
    fields = ('isList','startDate','endDate','memberId','group_id')
    for field in fields:
        exec('%s= request.forms.get("%s","")'%(field,field))

    log_util.debug('[try get_betReport] memberId[%s] group_id[%s] startDate[%s] endDate[%s]'\
                    %(memberId,group_id,startDate,endDate))
    if isList:
        bet_records = get_bet_reports(redis,startDate,endDate,group_id)
        return json.dumps(bet_records)
    else:
        info = {
                    'title'                  :       lang.MENU_FISH_AGENT_REPORT_TXT,
                    'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
                    'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH,
                    'back_pre'               :       BACK_PRE,
                    'group_search'           :       True,#开启代理ID查询
                    'tableUrl'               :       BACK_PRE+'/fish/bet/report?isList=1'
        }

        return template('admin_fish_room_report',PAGE_LIST=PAGE_LIST,info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/fish/bet/replay')
def get_fish_replay(redis,session):
    """
    打开捕鱼回放数据
    """
    lang = getLang()
    replay_id = request.GET.get('replay_id','').strip()
    if not replay_id:
        return {'code':0,'msg':'回放参数错误.'}

    log_debug('[try get_fish_replay] replay_id[%s]'%(replay_id))
    info = {
            'title'                  :       'ID[%s]游戏记录'%(replay_id),
            'STATIC_LAYUI_PATH'      :       STATIC_LAYUI_PATH,
            'STATIC_ADMIN_PATH'      :       STATIC_ADMIN_PATH,
            'dataUrl'                :       BACK_PRE+'/fish/bet/replayData?replay_id=%s'%(replay_id)
    }

    return template('admin_fish_replay',info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/fish/bet/replayData')
def get_replay_data(redis,session):
    """
    return data
    """
    replay_id = request.GET.get('replay_id','').strip()

    replay_info = get_replay_info(redis,replay_id)
    log_debug('[try get_replay_data] replayId[%s] replay_info[%s]'%(replay_id,replay_info))

    return json.dumps(replay_info)

@admin_app.get('/fish/data/query')
def get_fish_data_query(redis,session):
    """
    后台捕鱼数据查询接口
    """
    lang = getLang()
    fields = ('isList','start_date','end_date')
    for field in fields:
        exec('%s=request.GET.get("%s","").strip()'%(field,field))

    log_util.debug('[try get_fish_data_query] isList[%s] start_date[%s] end_date[%s]'%(isList,start_date,end_date))
    if isList:
        fish_system_datas = get_fish_sys_datas(redis,start_date,end_date)
        return json.dumps(fish_system_datas)
    else:
        timestamp = time.strftime("%Y-%m-%d", time.localtime())
        number = redis.get("fish:redpick:fish:%s:number" % timestamp) or 0

        #统计数据
        fish_static_datas = get_fish_cal_data(redis)
        info = {
                    'title'                  :           lang.MENU_FISH_DATA_REAL_TXT,
                    'listUrl'                :           BACK_PRE+'/fish/data/query?isList=1',
                    'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                    'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH,
                    "otherData"              :           ""
        }
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
        info["otherData"] = result
        info["redPickNumber"] = number
        return template('admin_fish_sys_data',
                    info=info,
                    log_per_day=fish_static_datas['log_per_day'],
                    reg_per_day=fish_static_datas['reg_per_day'],
                    total_member =fish_static_datas['total_member'],
                    login_per_rate=fish_static_datas['login_per_rate'],
                    recharge_per_rate = fish_static_datas['recharge_per_rate'],
                    share_per_day = fish_static_datas['share_per_day'],
                    total_share = fish_static_datas['total_share'],
                    lang=lang,
                    RES_VERSION=RES_VERSION,
        )

@admin_app.get('/fish/order/level/query_list')
def get_fish_level_query(redis, session):
    """
    后台鱼等级数据查询
    """
    lang = getLang()
    fields = ('isList',)
    for field in fields:
        exec ('%s=request.GET.get("%s","").strip()' % (field, field))

    log_util.debug('[try get_fish_level_query] isList[%s] ' % (isList))

    if isList:
        # fish_system_datas = get_fish_sys_datas(redis, start_date, end_date)
        level_order_list = redis.smembers("fish:level:order:set")
        result = []
        if not level_order_list:
            for i in range(1, 35):
                order_data = dict(
                modes_count_range = json.dumps({
                    0: "(1, 1)",
                }),
                order = i,
                rate_appear = 0,
                limit_count = 0,
                rate_pick_range = (0.0045, 0.0045),
                multiple_range = (20, 20),
                speed_range = (54, 63),  # (60,70),
                dice_odds = 0,
                rot_range = (-5, 5),
                rot_speed_range = (10, 10),
                per_time_range = (3, 8),
                times_count_range = (2, 4),
                width = 132,
                height = 118,
                seq_offset = 10,
                min_limit_time = 0,
                max_limit_time = 0,
                max_together_count = 0,
                fishname = '')
                redis.hmset("fish:level:%s:hesh" % i, order_data)
                redis.sadd("fish:level:order:set", i)
                result.append({
                    "order": int(order_data["order"]),
                    "name" : order_data["fishname"],
                    "op": [{'url': '/admin/fish/order/level/query_one?id=%s' % order_data["order"], 'method': 'GET', 'txt': '修改'}]
                })
        else:
            for order in level_order_list:
                order_data = redis.hgetall("fish:level:%s:hesh" % order)
                op = []
                result.append({
                    "order": int(order_data["order"]),
                    "name" : order_data["fishname"],
                    "op": [{'url': '/admin/fish/order/level/query_one?id=%s' % order_data["order"], 'method': 'GET', 'txt': '修改'}]
                })
        result = sorted(result, key=lambda x: x["order"])
        return json.dumps({"status": 200, "data": result})

    else:
        info =  {
                        'title'                  :           lang.MENU_FISH_DATA_REAL_TXT,
                        'listUrl'                :           BACK_PRE+'/fish/order/level/query_list?isList=1',
                        'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                        'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH
                }
        return template("admin_fish_level_order", info =info,
                lang=lang,
                RES_VERSION=RES_VERSION )

@admin_app.get('/fish/order/level/query_one')
def get_fish_level_query_one(redis, session):
    """
    单条鱼属性查询
    """
    lang = getLang()
    fields = ('id', )
    for field in fields:
        exec ('%s=request.GET.get("%s","").strip()' % (field, field))

    order_data = redis.hgetall("fish:level:%s:hesh" % id)
    info = {
        'title': lang.MENU_FISH_DATA_REAL_TXT,
        'listUrl': BACK_PRE + '/fish/order/level/query_list?isList=1',
        'STATIC_LAYUI_PATH': STATIC_LAYUI_PATH,
        'STATIC_ADMIN_PATH': STATIC_ADMIN_PATH
    }
    result = []

    for name, value in order_data.items():
        print('"%s ", ' % name)
        temp = {}
        temp["name"] = name
        temp["value"] = value
        if name == "modes_count_range":
            temp["desc"] = """
            0:#单体，随机自由游动
            1:#集群，有一个母鱼随机移动，其它集群分子会随母鱼方向及速度而变
            2:#一条条首尾相随的鱼
            3:#一条条平行并肩的鱼
            """
        else:
            temp["desc"] = ''
        temp["title"] = name
        result.append(temp)
    result.append(
        {"name": "id", "value": id, "desc": "不能修改", "title": "ID"}
    )
    result = sorted(result, key=lambda x: x["name"])
    return template("admin_fish_setting_level_order", info =info,
                lang=lang,
                RES_VERSION=RES_VERSION, order_data = result)



@admin_app.post("/fish/order/level/query_one")
@checkLogin
def get_fish_level_edit_one(redis, session):
    """
    修改单条鱼属性
    """
    fields = (
    "id",
    "speed_range",
    "min_limit_time",
    "seq_offset",
    "multiple_range",
    "times_count_range",
    "rot_range",
    "max_together_count",
    "rot_speed_range",
    "dice_odds",
    "limit_count",
    "height",
    "max_limit_time",
    "width",
    "fishname",
    "rate_appear",
    "modes_count_range",
    "per_time_range",
    "order",
    "rate_pick_range")
    try:
        for field in fields:
            exec ('%s=request.forms.get("%s","").strip()' % (field, field))

        id = int(id)

        order_data = dict(
            speed_range = tuple(eval(speed_range)),
            multiple_range = tuple(eval(multiple_range)),
            times_count_range = tuple(eval(times_count_range)),
            rot_speed_range = tuple(eval(rot_speed_range)),
            per_time_range = tuple(eval(per_time_range)),
            rate_pick_range = tuple(eval(rate_pick_range)),
            modes_count_range = json.dumps(json.loads(modes_count_range)),
            max_together_count=int(max_together_count),
            min_limit_time = int(min_limit_time),
            seq_offset = int(seq_offset),
            dice_odds = int(dice_odds),
            limit_count = int(limit_count),
            height = int(height),
            max_limit_time = int(max_limit_time),
            width = int(width),
            fishname = str(fishname),
            rate_appear = int(rate_appear),
            order = int(order),
        )
        # print(order_data)
        redis.hmset("fish:level:%s:hesh" % id, order_data)
        return {'code': 1, 'msg': '更新成功'}
    except Exception as err:
        print(err)
        traceback.print_exc()
        return {'code': 1, 'msg': '更新失败'}
####################################################################################################
#  会员相关
####################################################################################################
@admin_app.get('/fish/member/list')
@checkLogin
def getDirectMemberList(redis,session):
    """
    获取捕鱼会员列表接口
    """
    lang    =  getLang()
    curTime =  datetime.now()
    fields = ('isList','startDate','endDate','pageSize','pageNumber','searchId','sort_name','sort_method')
    selfUid  = session['id']
    for field in fields:
        exec("%s = request.GET.get('%s','').strip()"%(field,field))

    if not pageNumber:
        pageNumber = 1
    else:
        pageNumber = convert_util.to_int(pageNumber)

    if isList:
        res = userModel.get_fish_member_list(redis,session,selfUid,searchId,lang,int(pageSize),pageNumber,sort_name,sort_method)
        return json.dumps(res)
    else:
        info = {
                'title'                  :           lang.MEMBER_LIST_TITLE_TXT,
                'listUrl'                :           BACK_PRE+'/fish/member/list?isList=1&pageNumber={}&pageSize={}'.format(pageNumber,pageSize),
                'searchTxt'              :           lang.MEMBER_INPUT_TXT,
                'fish'                   :           True,
                'sort_bar'               :           True,#开启排序
                'member_page'            :           True,#开启排序
                'cur_size'               :           pageSize,
                'cur_page'               :           pageNumber,
                'remove_type'            :           'coin',
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH
        }
        log_debug('pageNumber[%s]'%(info['cur_page']))
        return template('admin_member_list',info=info,lang=lang,RES_VERSION=RES_VERSION)

@admin_app.get('/fish/member/kicks')
def do_fish_memberKick(redis,session):
    """
    捕鱼会员踢出游戏接口
    """
    lang = getLang()
    fields = ('account',)
    for field in fields:
        exec('%s = request.GET.get("%s","").strip()'%(field,field))

    account2user_table = FORMAT_ACCOUNT2USER_TABLE%(account)
    member_table = redis.get(account2user_table)
    if not redis.exists(member_table):
        return {'code':1,'msg':'会员[%s]不存在'%(account)}

    #发送提出玩家协议给服务端
    sendProtocol2AllGameService(redis,HEAD_SERVICE_PROTOCOL_KICK_MEMBER%(account),game="FISH")

    log_util.debug('[try do_fish_memberKick] send protol[%s] to kick account[%s] out'%(HEAD_SERVICE_PROTOCOL_KICK_MEMBER%(account),account))
    return web_util.do_response(0,'会员(%s)已被踢出游戏!'%(account),jumpUrl=BACK_PRE+'/fish/online/list')

@admin_app.get('/fish/online/list')
@checkLogin
def get_fish_online_page(redis,session):
    """
    获取捕鱼在线接口
    """
    curTime =  datetime.now()
    isList  =  request.GET.get('list','').strip()
    lang = getLang()
    if isList:
        fish_online_datas = get_fish_online(redis,lang)
        return json.dumps(fish_online_datas)
    else:
        info = {
                'title'                  :           lang.MENU_FISH_ONLINE_REAL_TXT,
                'listUrl'                :           BACK_PRE+'/fish/online/list?list=1',
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH,
                'fish'                   :           True
        }

        return template('admin_fish_online',info=info,lang=lang,RES_VERSION=RES_VERSION)


@admin_app.get('/fish/actives')
@checkLogin
def get_fish_online_page(redis,session):
    """
    获取捕鱼在线接口

    """
    curTime =  datetime.now()
    isList  =  request.GET.get('list','').strip()
    lang = getLang()
    if isList:
        fish_online_datas = get_fish_online(redis,lang)
        return json.dumps(fish_online_datas)
    else:
        info = {
                'title'                  :           lang.MENU_FISH_ONLINE_REAL_TXT,
                'listUrl'                :           BACK_PRE+'/fish/online/list?list=1',
                'STATIC_LAYUI_PATH'      :           STATIC_LAYUI_PATH,
                'STATIC_ADMIN_PATH'      :           STATIC_ADMIN_PATH,
                'fish'                   :           True
        }

        return template('admin_fish_online',info=info,lang=lang,RES_VERSION=RES_VERSION)
