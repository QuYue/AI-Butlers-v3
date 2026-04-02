# -*- encoding: utf-8 -*-
'''
@Time     :   2026/04/02 02:10:45
@Author   :   QuYue
@File     :   verity.py
@Email    :   quyue1541@gmail.com
@Desc:    :   verity
'''

#%% Import Packages
# Basic
import os
import requests
from flask import Flask, request
import base64
import hashlib
import struct
from Crypto.Cipher import AES
import urllib.parse
import xmltodict


#%% Verity
# --------------------------
# PKCS7 padding
# --------------------------
class PKCS7Encoder:
    block_size = 32

    @staticmethod
    def decode(text):
        pad = text[-1]
        return text[:-pad]

# --------------------------
# AES 解密
# --------------------------
def decrypt(echostr, corp_id, verity_EncodingAESKey):
    aes_key = base64.b64decode(verity_EncodingAESKey + "=")
    iv = aes_key[:16]

    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(base64.b64decode(echostr))
    decrypted = PKCS7Encoder.decode(decrypted)
    content = decrypted[16:]  # 去掉 random

    msg_len = struct.unpack(">I", content[:4])[0]
    msg = content[4:4 + msg_len]
    r_corp_id = content[4 + msg_len:].decode()
    if r_corp_id != corp_id:
        raise Exception("corp_id mismatch")
    return msg.decode()

# --------------------------
# 签名验证
# --------------------------
def verify_signature(verity_token, timestamp, nonce, encrypt_str, signature):
    tmp_list = [verity_token, timestamp, nonce, encrypt_str]
    tmp_list.sort()
    tmp_str = "".join(tmp_list)
    sha1 = hashlib.sha1(tmp_str.encode("utf-8")).hexdigest()
    return sha1 == signature

# --------------------------
# 验证 URL
# --------------------------
def verify_url(request,verity_token, verity_EncodingAESKey, corp_id):
    msg_signature = request.args.get("msg_signature")
    timestamp = request.args.get("timestamp")
    nonce = request.args.get("nonce")
    echostr = request.args.get("echostr")
    print("request args:", request.args)
    print("Received parameters:", msg_signature, timestamp, nonce, echostr)

    # 1. URL decode
    echostr = urllib.parse.unquote(echostr)

    # 2. 校验签名
    if not verify_signature(verity_token, timestamp, nonce, echostr, msg_signature):
        return "invalid signature", 403
    print("Signature verified successfully")

    # 3. 解密
    try:
        decrypted = decrypt(echostr, corp_id, verity_EncodingAESKey)
        print(decrypted)
    except Exception as e:
        return str(e), 500

    # 4. 原样返回（不能有任何多余字符）
    print("Decrypted echostr:", decrypted)
    return decrypted


#%% Get Access Token
def get_access_token(corpid, secret):
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corpid}&corpsecret={secret}"
    print(f"请求Access Token")
    response = requests.get(url).json()
    
    if response.get("errcode") == 0:
        return response.get("access_token")
    else:
        print(f"获取失败: {response.get('errmsg')}")
        return None


#%% Receive Message
def receive_message(request, verity_token, verity_EncodingAESKey, corp_id):
    # 1. 获取参数
    msg_signature = request.args.get("msg_signature")
    timestamp = request.args.get("timestamp")
    nonce = request.args.get("nonce")

    xml_str = request.data.decode("utf-8")
    data = xmltodict.parse(xml_str)["xml"]
    encrypt = data.get("Encrypt")
    agent_id = data.get("AgentID")

    if verify_signature(verity_token, timestamp, nonce, encrypt, msg_signature):
        message = decrypt(encrypt, corp_id, verity_EncodingAESKey)
        message = xmltodict.parse(message)["xml"]
        return message
    else:
        print("Signature verification failed")
        return None


#%% Send Message
def send_message(context, user_list, config):
    user_id = [config.users.dict[u].id for u in user_list]
    user_id = "|".join(user_id)
    send_context = {
        "touser" : user_id,
        "msgtype" : "text",
        "agentid" : config.agent_id,
        "text" : {
            "content" : context
        },
        "safe":0,
        "enable_id_trans": 0,
        "enable_duplicate_check": 0,
        "duplicate_check_interval": 1800
        }
    resp = send_out(send_context, config)
    return resp

def send_out(context, config):
    url = f"{config.proxy_url}/cgi-bin/message/send?access_token={config.agent_access_token}"
    headers={
        "X-Proxy-Token": config.proxy_token,
        "Content-Type": "application/json; charset=utf-8",
    }
    response = requests.post(url, json=context, headers=headers).json()
    print("Send message response:", response)

    if response.get("errcode") == 42001:
        print("Access token expired, refreshing...")
        config.get_access_token(config.corp_id, config.secret)
        response = requests.post(url, json=context, headers=headers).json() 
    elif response.get("errcode") != 0:
        print(f"发送失败: {response.get('errmsg')}")
    return response
