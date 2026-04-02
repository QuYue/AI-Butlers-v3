# -*- encoding: utf-8 -*-
'''
@Time     :   2026/02/09 16:29:05
@Author   :   QuYue
@File     :   Reloader.py
@Email    :   quyue1541@gmail.com
@Desc:    :   Reloader
'''

#%% Import Packages
# Basic
import os
import sys
import importlib
# Add Path
if __package__ is None:
    os.chdir(os.path.dirname(__file__))

#%%
def reload(package):
    """
    Reload a package and its submodules
    递归重载一个包及其所有已加载的子模块。
    """
    package_name = package.__name__
    importlib.reload(package)  # 先重载主包(可以让新增的模块被识别)
    # 获取所有属于该包及其子包的已加载模块名
    modules_to_reload = [
        name for name in sys.modules 
        if name == package_name or name.startswith(package_name + ".")
    ]
    
    # 排序确保父模块在子模块之后重载，或者简单循环重载
    # 实际上由于 Python 的 cache 机制，多次 reload 是安全的
    for module_name in sorted(modules_to_reload, key=lambda x: x.count('.'), reverse=True):
        try:
            importlib.reload(sys.modules[module_name])
        except Exception as e:
            print(f"Failed to reload {module_name}: {e}")
    
    print(f"✅ Reloaded {len(modules_to_reload)} modules under '{package_name}'")


