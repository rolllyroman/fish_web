# -*- coding: utf-8 -*-
import sys
from aliyunsdkdysmsapi.request.v20170525 import SendSmsRequest
from aliyunsdkdysmsapi.request.v20170525 import QuerySendDetailsRequest
from aliyunsdkcore.client import AcsClient
import uuid
from aliyunsdkcore.profile import region_provider
from aliyunsdkcore.http import method_type as MT
from aliyunsdkcore.http import format_type as FT
import const
import json
from datetime import datetime

try:
    reload(sys)
    sys.setdefaultencoding('utf8')
except NameError:
    pass
except Exception as err:
    raise err

# 注意：不要更改
REGION = "cn-hangzhou"
PRODUCT_NAME = "Dysmsapi"
DOMAIN = "dysmsapi.aliyuncs.com"

acs_client = AcsClient(const.ACCESS_KEY_ID, const.ACCESS_KEY_SECRET, REGION)
region_provider.add_endpoint(PRODUCT_NAME, REGION, DOMAIN)

def send_sms(business_id, phone_numbers, sign_name, template_code, template_param=None):
    smsRequest = SendSmsRequest.SendSmsRequest()
    # 申请的短信模板编码,必填
    smsRequest.set_TemplateCode(template_code)

    # 短信模板变量参数
    if template_param is not None:
        smsRequest.set_TemplateParam(template_param)

    # 设置业务请求流水号，必填。
    smsRequest.set_OutId(business_id)

    # 短信签名
    smsRequest.set_SignName(sign_name)
	
    # 数据提交方式
	# smsRequest.set_method(MT.POST)
	
	# 数据提交格式
    # smsRequest.set_accept_format(FT.JSON)
	
    # 短信发送的号码列表，必填。
    smsRequest.set_PhoneNumbers(phone_numbers)

    # 调用短信发送接口，返回json
    smsResponse = acs_client.do_action_with_exception(smsRequest)

    # TODO 业务处理

    return smsResponse



'''
# 验证码
def execute_send(phone,check_code):
    __business_id = uuid.uuid1()
    params = u'{"code":'+check_code+'}'
    print phone 
    print check_code
    print(send_sms(__business_id, phone, "东胜网络", "SMS_140060199", params))
   
# 完善信息 新密码
def send_box_pwd(phone,nickname,pwd):
    __business_id = uuid.uuid1()
    params = u'{"nickname":'+nickname+',"pwd":'+pwd+'}'
    print(send_sms(__business_id, phone, "东胜网络", "SMS_139982509", params))
    
# 保管箱密码
def send_info_pwd(phone,nickname,pwd):
    __business_id = uuid.uuid1()
    params = u'{"nickname":'+nickname+',"pwd":'+pwd+'}'
    print(send_sms(__business_id, phone, "东胜网络", "SMS_139972516", params))
'''
    
def execute_send_sms(redis,uid,phone,temp_id,params):
    if redis.get('send:control:%s'%uid):
        return False
    __business_id = uuid.uuid1()
    res = send_sms(__business_id, phone, "东胜网络", temp_id, params)
    log_to_send_record(uid,phone,temp_id,res)
    dic = json.loads(res)
    if dic.get('Code')=='OK':
        return True
        redis.setex('send:control:%s'%uid,60,60)
    
def log_to_send_record(uid,phone,temp_id,res):
    log_name = '/home/ubuntu/web_server/srcs/mahjong/aliyun_sms/log/'+'log'+str(datetime.now())[:10]
    content = "用户:%s\n手机号:%s\n短信模板:%s\n发送时间:%s\n发送结果:%s\n"%(uid,phone,temp_id,str(datetime.now())[:19],res)+'-'*66+'\n'
    with open(log_name,'a') as f:
        f.write(content)
