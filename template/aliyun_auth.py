#!/usr/bin/env python3
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkalidns.request.v20150109 import AddDomainRecordRequest
import os
import time
import json


# 创建 AcsClient 实例
client = AcsClient(
    os.environ.get('ALI_KEY'),
    os.environ.get('ALI_SECRET'),
    "cn-hangzhou",
)
print('[INFO] CERTBOT_DOMAIN:', os.environ.get('CERTBOT_DOMAIN'))
# 创建 AddDomainRecordRequest 实例
domains = os.environ.get('CERTBOT_DOMAIN').split('.')
request = AddDomainRecordRequest.AddDomainRecordRequest()
request.set_DomainName('.'.join(domains[-2:]))
request.set_RR('.'.join(['_acme-challenge'] + domains[:-2]))
request.set_Type("TXT")
request.set_Value(os.environ.get('CERTBOT_VALIDATION'))

# 发送请求并处理响应
try:
    response = client.do_action_with_exception(request)
    response_dict = json.loads(response)
    record_id = response_dict.get('RecordId')

    # 将记录ID写入环境变量文件，供cleanup脚本使用
    with open('/tmp/CERTBOT_AUTH_STATUS', 'a') as f:
        f.write(f"{os.environ.get('CERTBOT_DOMAIN')}:{os.environ.get('CERTBOT_VALIDATION')}:{record_id}\n")

    print("添加 TXT 记录成功:", response)
    print("等待10秒")
    time.sleep(10)
except ServerException as e:
    print("服务器异常:", e)
except ClientException as e:
    print("客户端异常:", e)