#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
火山引擎API签名工具
基于火山引擎官方demo优化，增强错误处理和安全性
"""

import datetime
import hashlib
import hmac
import json
from urllib.parse import quote
from typing import Dict, Any


def norm_query(params: Dict[str, Any]) -> str:
    """标准化查询参数"""
    query = ""
    for key in sorted(params.keys()):
        if isinstance(params[key], list):
            for k in params[key]:
                query += quote(key, safe="-_.~") + "=" + quote(str(k), safe="-_.~") + "&"
        else:
            query += quote(key, safe="-_.~") + "=" + quote(str(params[key]), safe="-_.~") + "&"
    query = query[:-1]
    return query.replace("+", "%20")


def hmac_sha256(key: bytes, content: str) -> bytes:
    """HMAC-SHA256加密"""
    return hmac.new(key, content.encode("utf-8"), hashlib.sha256).digest()


def hash_sha256(content: str) -> str:
    """SHA256哈希"""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def get_x_date(date: datetime.datetime = None) -> str:
    """获取X-Date时间戳"""
    if date is None:
        date = datetime.datetime.now(datetime.timezone.utc)
    return date.strftime("%Y%m%dT%H%M%SZ")


def get_url(host: str, action: str, version: str, region: str) -> str:
    """构建请求URL"""
    return f"https://{host}/?Action={action}&Version={version}"


def get_authorization(access_key: str, secret_key: str, method: str, host: str, 
                     x_date: str, body_sha256: str, action: str, version: str, 
                     region: str, service: str = "imagination") -> str:
    """
    生成Authorization头
    
    Args:
        access_key: 访问密钥ID
        secret_key: 秘密访问密钥  
        method: HTTP方法 (GET/POST)
        host: 请求主机
        x_date: X-Date时间戳
        body_sha256: 请求体SHA256哈希
        action: API操作名
        version: API版本
        region: 区域
        service: 服务名
    
    Returns:
        Authorization头字符串
    """
    # 构建查询参数
    query = {"Action": action, "Version": version}
    
    # 构建请求头
    headers = {
        "Content-Type": "application/json",
        "Host": host,
        "X-Date": x_date,
        "X-Content-Sha256": body_sha256
    }
    
    # 计算签名
    short_x_date = x_date[:8]
    signed_headers_str = "content-type;host;x-content-sha256;x-date"
    
    # 构建规范化请求字符串
    canonical_request_str = "\n".join([
        method,
        "/",
        norm_query(query),
        "\n".join([
            f"content-type:{headers['Content-Type']}",
            f"host:{headers['Host']}",
            f"x-content-sha256:{body_sha256}",
            f"x-date:{x_date}",
        ]),
        "",
        signed_headers_str,
        body_sha256,
    ])
    
    # 计算规范化请求的哈希
    hashed_canonical_request = hash_sha256(canonical_request_str)
    
    # 构建签名范围
    credential_scope = "/".join([short_x_date, region, service, "request"])
    
    # 构建待签名字符串
    string_to_sign = "\n".join([
        "HMAC-SHA256",
        x_date,
        credential_scope,
        hashed_canonical_request
    ])
    
    # 计算签名
    k_date = hmac_sha256(secret_key.encode("utf-8"), short_x_date)
    k_region = hmac_sha256(k_date, region)
    k_service = hmac_sha256(k_region, service)
    k_signing = hmac_sha256(k_service, "request")
    signature = hmac_sha256(k_signing, string_to_sign).hex()
    
    # 构建Authorization头
    return "HMAC-SHA256 Credential={}/{}, SignedHeaders={}, Signature={}".format(
        access_key, credential_scope, signed_headers_str, signature
    )


def create_request_headers(access_key: str, secret_key: str, method: str, 
                          host: str, body: str, action: str, version: str, 
                          region: str, service: str = "imagination") -> Dict[str, str]:
    """
    创建完整的请求头
    
    Args:
        access_key: 访问密钥ID
        secret_key: 秘密访问密钥
        method: HTTP方法
        host: 请求主机
        body: 请求体内容
        action: API操作名
        version: API版本
        region: 区域
        service: 服务名
    
    Returns:
        包含所有必要头的字典
    """
    # 计算请求体哈希
    body_sha256 = hash_sha256(body)
    
    # 生成时间戳
    x_date = get_x_date()
    
    # 基础头部
    headers = {
        "Content-Type": "application/json",
        "Host": host,
        "X-Date": x_date,
        "X-Content-Sha256": body_sha256
    }
    
    # 生成授权头
    authorization = get_authorization(
        access_key, secret_key, method, host, x_date, body_sha256,
        action, version, region, service
    )
    headers["Authorization"] = authorization
    
    return headers


def prepare_request_data(data: Dict[str, Any]) -> str:
    """
    准备请求数据，转换为JSON字符串
    
    Args:
        data: 要发送的数据字典
    
    Returns:
        JSON格式的字符串
    """
    return json.dumps(data, ensure_ascii=False, separators=(',', ':'))