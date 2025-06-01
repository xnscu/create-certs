#!/usr/bin/env python3
import os
import time
import hashlib
from alibabacloud_cdn20180510.client import Client as Cdn20180510Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_cdn20180510 import models as cdn_20180510_models
from alibabacloud_tea_util import models as util_models

def create_cdn_client() -> Cdn20180510Client:
    """
    使用AK&SK初始化账号Client
    @return: Client
    @throws Exception
    """
    config = open_api_models.Config(
        access_key_id=os.environ['ALI_KEY'],
        access_key_secret=os.environ['ALI_SECRET']
    )
    # Endpoint 请参考 https://api.aliyun.com/product/Cdn
    config.endpoint = f'cdn.aliyuncs.com'
    return Cdn20180510Client(config)

def calculate_cert_fingerprint(cert_content):
    """
    计算证书的SHA256指纹
    """
    # 移除证书头尾和换行符，只保留证书内容
    cert_lines = cert_content.strip().split('\n')
    cert_data = ''.join([line for line in cert_lines if not line.startswith('-----')])

    # 计算SHA256指纹
    fingerprint = hashlib.sha256(cert_data.encode()).hexdigest()
    return fingerprint

def get_current_cert_fingerprint(cdn_client, domain_name):
    """
    获取当前CDN域名的证书指纹
    """
    try:
        request = cdn_20180510_models.DescribeDomainCertificateInfoRequest(
            domain_name=domain_name
        )
        runtime = util_models.RuntimeOptions()
        response = cdn_client.describe_domain_certificate_info_with_options(request, runtime)

        if response.body.cert_infos and response.body.cert_infos.cert_info:
            cert_info = response.body.cert_infos.cert_info[0]
            if cert_info.server_certificate:
                return calculate_cert_fingerprint(cert_info.server_certificate)
    except Exception as e:
        print(f"获取当前证书信息失败: {e}")

    return None

# 添加 TXT 记录成功后,执行上传证书到CDN的动作
DOMAIN = os.environ.get('DOMAIN')
CDN_DOMAIN = os.environ.get('CDN_DOMAIN')
cert_path = f"/etc/letsencrypt/live/{DOMAIN}/fullchain.pem"
key_path = f"/etc/letsencrypt/live/{DOMAIN}/privkey.pem"

# 读取新证书内容
with open(cert_path, 'r') as f:
    new_cert_content = f.read()

# 计算新证书指纹
new_cert_fingerprint = calculate_cert_fingerprint(new_cert_content)

cdn_client = create_cdn_client()

# 获取当前证书指纹
current_cert_fingerprint = get_current_cert_fingerprint(cdn_client, CDN_DOMAIN)

# 比较证书指纹
if current_cert_fingerprint and current_cert_fingerprint == new_cert_fingerprint:
    print(f"域名 {DOMAIN} 的证书指纹相同，跳过上传")
    print(f"当前证书指纹: {current_cert_fingerprint}")
    print(f"新证书指纹: {new_cert_fingerprint}")
else:
    print(f"证书指纹不同，开始上传新证书")
    if current_cert_fingerprint:
        print(f"当前证书指纹: {current_cert_fingerprint}")
    else:
        print("未找到当前证书")
    print(f"新证书指纹: {new_cert_fingerprint}")

    # 生成唯一的证书名称，使用时间戳避免重复
    timestamp = int(time.time())
    cert_name = f'{CDN_DOMAIN}_cert_{timestamp}'

    set_cdn_domain_sslcertificate_request = cdn_20180510_models.SetCdnDomainSSLCertificateRequest(
        domain_name=CDN_DOMAIN,
        cert_name=cert_name,  # 使用带时间戳的唯一证书名称
        cert_type='upload',
        sslprotocol='on',
        sslpub=new_cert_content,
        sslpri=open(key_path).read()
    )
    runtime = util_models.RuntimeOptions()
    try:
        cdn_client.set_cdn_domain_sslcertificate_with_options(set_cdn_domain_sslcertificate_request, runtime)
        print(f"上传域名 {DOMAIN} 的SSL证书到CDN成功，证书名称: {cert_name}")
    except Exception as error:
        print(f"上传域名 {DOMAIN} 的SSL证书到CDN失败: {error.message}")
        print(error.data.get("Recommend"))