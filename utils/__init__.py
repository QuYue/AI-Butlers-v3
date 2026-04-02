# -*- encoding: utf-8 -*-
'''
@Time     :   2024/03/28 14:58:13
@Author   :   QuYue
@File     :   __init__.py
@Email    :   quyue1541@gmail.com
@Desc:    :   __init__
'''

#%% Import Packages
# Add Path
if __package__ is None or __package__ == '':
    # Basic
    import os
    os.chdir(os.path.dirname(__file__))
    # Self-defined
    from MyStruct import MyStruct
    from WaitingPrint import WaitingPrint
    from Logger import Logger
    from Reloader import reload
else:
    # Self-defined
    from .MyStruct import MyStruct
    from .WaitingPrint import WaitingPrint
    from .Logger import Logger
    from .Reloader import reload
    
    
#%% Main Function
if __name__ == '__main__':
    pass
