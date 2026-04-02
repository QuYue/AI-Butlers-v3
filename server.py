# -*- encoding: utf-8 -*-
'''
@Time     :   2026/04/02 00:18:20
@Author   :   QuYue
@File     :   server.py
@Email    :   quyue1541@gmail.com
@Desc:    :   AI Butlers Server
'''

#%% Import Packages
# Basic
import os
from flask import Flask, request, jsonify
import yaml


# Add Path
if __package__ is None or __package__ == '':
    os.chdir(os.path.dirname(__file__))

# Self-defined
import wecom_app
import utils

#%% APPlication
class Config(utils.MyStruct):
    def __init__(self, config_path):
        super().__init__()
        self.add_yaml(config_path)
        self.get_access_token(self.corp_id, self.secret)

    def get_user(self, user_id):
        for u in self.users.dict.keys():
            user = self.users.dict[u]
            if user.id == user_id:
                return u
        return None

    def get_access_token(self, corp_id, secret):
        self.agent_access_token = wecom_app.get_access_token(corp_id, secret)

config = Config("config.yaml")
app = Flask(__name__)

#%% Routes
# Home Page
@app.route("/")
def home():
    return "Hello, Flask!"

# Echo
@app.route("/echo", methods=["POST"])
def echo():
    data = request.get_json(silent=True) or {}
    return jsonify({
        "received": data
    })

# Send
@app.route("/send", methods=["POST"])
def send():
    data = request.get_json(silent=True)
    context = data['context']
    user_list = data['user']
    resp = wecom_app.send_message(context, user_list, config)
    return jsonify({
        "status": "success",
        "response": resp
    })


# Chat
@app.route("/chat", methods=["GET", "POST"])
def chat():
    # get data
    if request.method == "GET":
        return wecom_app.verify_url(request, config.verity_token, config.verity_EncodingAESKey, config.corp_id)
    else:
        message =  wecom_app.receive_message(request, config.verity_token, config.verity_EncodingAESKey, config.corp_id)
        if message is None:
            return None
        user = config.get_user(message.get("FromUserName"))
        context = message.get("Content")
        print("Received chat data:", context)
        resp = wecom_app.send_message(context, [user], config)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)