# -*- encoding: utf-8 -*-
'''
@Time     :   2024/03/28 15:46:47
@Author   :   QuYue
@File     :   WaitingPrint.py
@Email    :   quyue1541@gmail.com
@Desc:    :   WaitingPrint
'''

#%% Import Packages
# Basic
import os
import time
import threading

# Add Path
if __package__ is None:
    os.chdir(os.path.dirname(__file__))


#%% Waiting Print
class WaitingPrint(object):
    def __init__(self, start_desc="Waiting", end_desc="Finished.", show_waiting_time=True, update_time=0.25, if_print=True):
        self.start_desc = start_desc
        self.end_desc = end_desc
        self.update_time = update_time
        self.is_waiting = False
        self.show_waiting_time = show_waiting_time
        self.time = [0, 0]
        self.process = None
        self.max_text_len = 0
        self.if_print = if_print

    def waiting_print(self):
        if not self.if_print:
            return None
        list_circle = ["\\", "|", "/", "-"]
        i = 0
        while self.is_waiting:
            time.sleep(self.update_time)
            text = f"\r{self.start_desc} {list_circle[i % 4]}"
            if len(text) > self.max_text_len:
                self.max_text_len = len(text)
            elif len(text) < self.max_text_len:
                text += " "*(self.max_text_len-len(text))
            print(text, end="", flush=True)
            i += 1
        end_text = f"{self.end_desc}"
        if self.show_waiting_time:
            end_text += f" [{self.time[1]-self.time[0]:.2f}s]"
        print(f"\r{end_text}{' '*(self.max_text_len-len(end_text))}", flush=True)

    def start(self, start_desc=None):
        if not self.if_print:
            return None
        if isinstance(start_desc, str):
            self.start_desc = start_desc
        self.time[0] = time.time()
        self.is_waiting = True
        self.process = threading.Thread(target=self.waiting_print)
        self.process.start()
    
    def update(self, update_desc=None):
        if not self.if_print:
            return None
        if self.is_waiting:
            self.start_desc = update_desc

    def end(self, end_desc=None):
        if not self.if_print:
            return None
        if isinstance(end_desc, str):
            self.end_desc = end_desc
        self.time[1] = time.time()
        self.is_waiting = False
        while self.process.is_alive():
            time.sleep(self.update_time+0.05)
        self.max_text_len = 0


#%% Main Function
if __name__ == '__main__':
    waiting = WaitingPrint(if_print=True)
    waiting.start("Task Runing")
    time.sleep(5)
    waiting.update("Task Saving")
    time.sleep(5)
    waiting.end("Task Finished!")
