# -*- encoding: utf-8 -*-
'''
@Time     :   2024/03/28 15:00:00
@Author   :   QuYue
@File     :   MyStruct.py
@Email    :   quyue1541@gmail.com
@Desc:    :   MyStruct
'''

#%% Import Packages
# Basic
import os
# Add Path
if __package__ is None:
    os.chdir(os.path.dirname(__file__))


#%% MyStruct
class MyStruct():
    """
    A template of structure (class)
    """
    def __init__(self):
        pass

    def add_json(self, json_data):
        """
        Add data from json file
        """
        import json
        with open(json_data, "r") as f:
            json_data = json.load(f)
        self.add_dict(json_data)

    def add_yaml(self, yaml_data):
        """
        Add data from yaml file
        """
        import yaml
        with open(yaml_data, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)
        self.add_dict(yaml_data)

    def add_dict(self, add_data):
        """
        Add data from dict
        """
        for key, value in add_data.items():
            if key[0] == "@":
                continue
            if key in self.__dict__:
                if isinstance(value, dict):
                    if isinstance(self.__dict__[key], MyStruct):
                        self.__dict__[key].add_dict(value)
                    else:
                        temp = MyStruct()
                        temp.add_dict(value)
                        self.__dict__[key] = temp
                else:
                    self.__dict__[key] = value
            else:
                if isinstance(value, dict):
                    temp = MyStruct()
                    temp.add_dict(value)
                    self.__dict__[key] = temp
                else:
                    self.__dict__[key] = value

    def to_json(self):
        """
        Return the structure as a json
        """
        struct_dict = self.__dict__.copy()
        for key, value in struct_dict.items():
            if isinstance(value, MyStruct):
                struct_dict[key] = value.to_json()
            elif isinstance(value, list) or isinstance(value, tuple):
                struct_dict[key] = self.__list_to_json__(value)
            elif isinstance(value, str) or isinstance(value, int) or isinstance(value, float):
                struct_dict[key] = value
            else:
                struct_dict[key] = str(value)
        return struct_dict
    
    def __list_to_json__(self, list_data):
        """
        Return the list as a json
        """
        list_json = []
        for i, val in enumerate(list_data):
            if isinstance(val, str) or isinstance(val, int) or isinstance(val, float):
                list_json.append(val)
            elif isinstance(val, MyStruct):
                list_json.append(val.to_json())
            elif isinstance(val, list) or isinstance(val, tuple):
                list_json.append(self.__list_to_json__(val))
            else:
                list_json.append(str(val))
        return list_json
    
    def __list_to_parm__(self, list_data):
        """
        Return the list as a json
        """
        list_parm = []
        for i, val in enumerate(list_data):
            if isinstance(val, MyStruct):
                list_parm.append(None)
            elif isinstance(val, list) or isinstance(val, tuple):
                list_parm.append(self.__list_to_parm__(val))
            else:
                list_parm.append(val)
        return list_parm
    
    @property
    def dict(self):
        """
        Return the structure as a dict
        """
        struct_dict = self.__dict__.copy()
        return struct_dict

    def update(self, new):
        """
        Update the structure
        """
        if isinstance(new, MyStruct):
            self.__dict__.update(new.__dict__)
        elif isinstance(new, dict):
            self.__dict__.update(new)
        else:
            raise ValueError("The input must be a MyStruct or dict")
    
    def get_parm(self):
        """
        Return the Paramters as a dict
        """
        struct_dict = self.__dict__.copy()
        remove_keys = []
        for key, value in struct_dict.items():
            if isinstance(value, MyStruct):
                remove_keys.append(key)
            elif isinstance(value, list) or isinstance(value, tuple):
                struct_dict[key] = self.__list_to_parm__(value)
            else:
                struct_dict[key] = value
        for key in remove_keys:
            struct_dict.pop(key, None)
        return struct_dict
    
    def __repr__(self):
        """
        Print the structure
        """
        return f"{self.__dict__}"