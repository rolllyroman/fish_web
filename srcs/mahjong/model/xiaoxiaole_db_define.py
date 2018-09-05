# coding=utf-8

# 消消乐常用变量



'''
    概率表ID
{
    1: 0,
    2: 0,
    3: 0,
    4: 0,
    5: 10,
}
'''
XXL_CHANCE_TALBE_DEFAULT = 'xxl:chance:default:hesh'
XXL_CHANCE_TALBE_RELEASE = 'xxl:chance:release:hesh'
XXL_CHANCE_TALBE_RECOVERY = 'xxl:chance:recovery:hesh'
'''
{
    'release':放水比率,
    'recovery':收水比率
}
'''
XXL_CHANCE_TALBE_PCT = 'xxl:chance:percent:hesh'

XXL_OODS_DEFAULT = 'xxl:oods:default:hesh'

'''
{
    'start_day'     :开始日期
    'get_gold'      :获取的金币(下注总额)
    'put_gold'      :放出的金币
    'put_honor'     :放出的荣誉
    'now_type'      :当前采用的概率表
}
'''
XXL_MONEY_RECORD_DAY = 'xxl:record:money:day:%s'
XXL_MONEY_RECORD_WEEK = 'xxl:record:money:week:%s'
XXL_MONEY_RECORD_PLAYER = 'xxl:record:money:player:%s'

'''
#玩家的消消乐属性 
XXL_SHONOR_PLAYER_INFO
sHonor => switchHonor
{
    sHonor_Total    :总转换荣誉值
    sHonor_Surplus  :总剩余转换荣誉值
    sHonor_Converted:总已转换荣誉值
}
'''
XXL_SHONOR_PLAYER_INFO = 'xxl:sHonor:users:%s'

'''
#总计的消消乐属性(总)
XXL_SHONOR_TOTAL_INFO
#总计的消消乐属性(每日)
XXL_SHONOR_TOTAL_DATE

sHonor => switchHonor
{
    sHonor_Total    :总转换荣誉值
    sHonor_Surplus  :总剩余转换荣誉值
    sHonor_Converted:总已转换荣誉值
}
'''
XXL_SHONOR_TOTAL_INFO = 'xxl:sHonor:total'
XXL_SHONOR_TOTAL_DATE = 'xxl:sHonor:total:%s'

'''
每日统计次数
XXL_PLAY_TOTAL_DATE
{
    'PlayNumTotal':总游玩次数
    'PlayNum_Gold':总游玩金币次数
    'PlayNum_Honor':总游玩荣誉次数
}
XXL_PLAYER_TOTAL_DATE
存放玩家
{
    'uid':'次数'
}

第一个%s是日期 第二个是类型 有total gold honor 3种
'''
XXL_PLAYNUM_RECORD_DATE = 'xxl:record:playNum:%s'
XXL_PLAYERNUM_RECORD_DATE = 'xxl:record:playerNum:%s:%s'


GOLD = 'gold'
HONOR = 'honor'

# 行和列
HEIGHT = 8
WIDTH = 8
# 公仔类型种类 初始为1, 1-5
TYPECount = 5

# 默认赔概率表
DEFAULT = 1
# 放水赔概率表
RELEASE = 2
# 收水赔概率表
RECOVERY = 3

from datetime import datetime, timedelta


def getNowTimeInfo():
    now_time = datetime.now()
    week = now_time.strftime('%W')
    weekday = int(now_time.strftime('%w')) - 1
    if weekday:
        week_startDay = getday(now_time.year, now_time.month, now_time.day, n=weekday)
    else:
        week_startDay = now_time

    day = now_time.day
    date = now_time.strftime('%Y-%m-%d')
    # print date,week,day,week_startDay
    return date, week, day, week_startDay


def getday(y, m, d, n):
    the_date = datetime(y, m, d)
    result_date = the_date + timedelta(days=-n)
    d = result_date.strftime('%Y-%m-%d')
    return d


def dict_to_int_int(Tdict):
    if not isinstance(Tdict, dict):
        return False, {}
    New_dict = {}
    try:
        for _key, _value in Tdict.iteritems():
            New_dict[int(_key)] = int(_value)
    except Exception as error:
        # traceback.print_exc()
        error = 'dict:%s error:%s' % (str(Tdict), str(error))
        print error
        return False, error
    else:
        return True, New_dict


def dict_to_int_float(Tdict):
    if not isinstance(Tdict, dict):
        return False, {}
    New_dict = {}
    try:
        for _key, _value in Tdict.iteritems():
            New_dict[int(_key)] = float(_value)
    except Exception as error:
        # traceback.print_exc()
        error = 'dict:%s error:%s' % (str(Tdict), str(error))
        print error
        return False, error
    else:
        return True, New_dict
