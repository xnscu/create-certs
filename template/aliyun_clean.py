#!/usr/bin/env python3
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkalidns.request.v20150109 import DeleteDomainRecordRequest
import os

# 创建 AcsClient 实例
client = AcsClient(
    os.environ.get('ALI_KEY'),
    os.environ.get('ALI_SECRET'),
    "cn-hangzhou",
)

try:
    # 从状态文件中查找对应的记录ID
    current_domain = os.environ.get('CERTBOT_DOMAIN')
    current_validation = os.environ.get('CERTBOT_VALIDATION')
    records_to_delete = []
    new_lines = []

    with open('/tmp/CERTBOT_AUTH_STATUS', 'r') as f:
        lines = f.readlines()

    # 找出所有匹配的记录
    for line in lines:
        DOMAIN, validation, rid = line.strip().split(':')
        print(DOMAIN, current_domain , validation , current_validation )
        if DOMAIN == current_domain and validation == current_validation:
            records_to_delete.append(rid)
        else:
            new_lines.append(line)

    # 删除所有匹配的记录
    for record_id in records_to_delete:
        # 创建删除请求
        request = DeleteDomainRecordRequest.DeleteDomainRecordRequest()
        request.set_RecordId(record_id)

        # 发送删除请求
        response = client.do_action_with_exception(request)
        print(f"删除 TXT 记录成功 (ID: {record_id}):", response)

    # 只有在有记录被删除时才更新状态文件
    if records_to_delete:
        # 更新状态文件
        with open('/tmp/CERTBOT_AUTH_STATUS', 'w') as f:
            f.writelines(new_lines)

except ServerException as e:
    print("服务器异常:", e)
except ClientException as e:
    print("客户端异常:", e)
except FileNotFoundError:
    print("未找到记录ID文件")