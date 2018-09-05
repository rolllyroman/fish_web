# -*- coding:utf-8 -*-

def record_player_balance_change(redis_ins,user_table,currency_id,quantity_change,quantity_final,type_id,game_id='',extra1='',extra2='',extra3='',extra4=''):
    """
    记录账户每一笔变化
    params: redis_ins 存入数据的redis 请传入mahjong.bag.bag_config import bag_redis
    params: user_table 
            1,真实账户格式 'users:%s' % uid ,例子 users:123
            2,机器人账户格式 'users:robot:level:%s:%s|%s' % (arg,uid,level), 例子 users:robot:level:2:20000|A
    params: currency 货币类型 传入道具id。道具id可参照后台系统 背包系统->道具列表。特殊的用法：-1表示没有意义，-2 表示游戏时长。
    params: quantity_change 改变的数量 
    params: quantity_final 改变后的数量
    params: type_id 变化的类型：
             {0:签到,1:分享,2:破产,3:新手礼包,4:七天奖励,5:十五天奖励,6:月签到奖励,7:元宝低保,8:宝箱任务，9:游戏输赢,10:房费,11:记牌器
              ,12:钻石兑换金币(金币变化),13:钻石兑换元宝（元宝变化）,14:钻石兑换房卡（房卡变化）,15:钻石兑换金币(钻石变化)，
               16:钻石兑换元宝(钻石变化)，17:钻石兑换房卡(钻石变化),18:金币兑换记牌器1局（记牌器变化） 19:钻石兑换记牌器10局（记牌器变化）,
               20:钻石兑换记牌器1天（记牌器变化）21:钻石兑换记牌器7天（记牌器变化）,22:金币兑换记牌器1局（金币变化）,
               23:钻石兑换记牌器10局（钻石变化）,24:钻石兑换记牌器1天（钻石变化）,25:钻石兑换记牌器7天（钻石变化）,26:保险箱取款手续费,
               27:存入保险箱（账号金额变化），28:存入保险箱（保险箱金额变化），
               29:取出保险箱（账号金额变化），30:取出保险箱（保险箱金额变化）,
               31:充值钻石,32:报名费支出，33：报名费反还
               34:补签费用，35:补签奖励,36:每日领取门票,37:3局红包赛奖励 38:比赛场奖励
               39:荣誉商城兑换物品,40:游戏时长,41:成就奖励,42:邀请好友获得的收益,
               43:代理获得下线的贡献值,44:邀请好友的宝箱奖励,45:达到成就,
               46:用户注册,47:邀请好友每日结算的荣誉，48:代理下线每日结算的贡献值,49:福利券，50:荣誉兑换商品
               51:钻石兑换定时赛门票（门票变化）, 52:钻石兑换定时赛门票（钻石变化）
               53:金币兑换记牌器10局（记牌器变化）,54:金币兑换记牌器（金币变化）,
               55:邀请好友成功记录,56,发送福利券 57:领取福利券,
               58:荣誉商城兑换奖品（荣誉或福利券变化）,59:客服同意发放奖品。
               }
    params: game_id 游戏的id
    params: extra1 保留的参数，如果是游戏，这个参数代表，这场游戏的uuid
    params: extra2 保留的参数，如果是游戏，这个参数代表，这场游戏的房间号
    params: extra3 保留的参数，如果是游戏，这个参数代表，这场游戏的开始时间
    params: extra4 保留的参数，如果是游戏，0代表随机场，1代表好友开房
    } 
    调用例子：
    1， 统计输赢，用户9527玩跑得快，盈了1000金币，结算后金币是10000,uuid是12345,房号是128.
        record_player_balance_change(redis,'users:9527',2,1000,11000,9,"559",extra1='12345',extra2='128')
    2， 统计房费，用户9527玩跑得快，房费10金币，结算后金币是11000,uuid是12345,房号是128.
        record_player_balance_change(redis,'users:9527',2,10,11000,10,extra1='12345',extra2='128')
    3， 统计输赢，用户9527玩跑得快，输了10元宝，结算后元宝数是110元宝,uuid是12345,房号是128.
        record_player_balance_change(redis,'users:9527',3,-10,110,9,extra1='12345',extra2='128')
    4， 统计时长，用户9527玩跑得快，游戏时长是300秒,总游戏时长12000秒,uuid是12345,房号是128,开始时间是'2018-07-02 11:12:00'.
        注：游戏时长的currency参数 是 -2 
        record_player_balance_change(redis,'users:9527',-2,300,12000,40,"559",extra1='12345',extra2='128',extra3='2018-07-02 11:12:00')
    """
    # currency_dic = {'gold':2,'yuanbao':3,'diamond':1,'room_card':6,'redpacket':4,'jipai_1s':9,'jipai_10s':10,'jipai_1day':11,'jipai_7days':12}
    # currency_id = currency_dic[currency]
    sql_str_format = 'insert into income_and_fee_detail' +\
                        ' (user_id,quantity_change,quantity_final,currency,type_id,game_id,create_time,extra1,extra2,extra3,extra4)' +\
                        " values ('{0}',{1},{2},{3},{4},'{5}','{6}','{7}','{8}','{9}','{10}');"

    import time
    create_time = time.strftime('%Y-%m-%d %H:%M:%S')
    sql_str = sql_str_format.format(user_table,quantity_change,quantity_final,currency_id,type_id,game_id,create_time,\
        extra1,extra2,extra3,extra4)
    redis_ins.lpush('player:balance_change',sql_str)
