# -*- encoding: utf-8 -*-
'''
@Time     :   2026/04/02 02:56:20
@Author   :   QuYue
@File     :   send_test.py
@Email    :   quyue1541@gmail.com
@Desc:    :   send_test
'''

#%%
#%% Import Packages
# Basic
import os
import requests

#%%
url = "https://www.yue.yueming.top/alfred/send"
d = requests.post(url, json={
    "user": ["qy"],
    "context": "hello"
})
print(d.json())
# %%
