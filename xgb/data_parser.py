#!/usr/bin/env python
# -*- coding: utf-8 -*-
import configparser
from sklearn.model_selection import train_test_split
import pandas as pd
import xgboost as xgb
import os
import util
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s]: %(message)s"
)

class Parser(object):
    def __init__(self, feature_type="v1"):
        self.feature_type = feature_type
        # precise_rough 1是精标,2是粗标
        self.perfix_feature_names = [
            "main_account_id","wxid","quality"
        ]
        self.feature_config = self.get_features()

    def load_enum_dict(self, feature_all, enum_index):
        enum_conf = {
            "fraudtype": {"values": ['0', '8']},
            "fraudlevel": {"values": ["0", "1", "2", "3", "4"]},
            "predictlabel": {"values": ['0', '7']},
            "wxsafe_gender": {
                "values": ["0", "1", "2"],
                "default": "1"
            },
            "wxsafe_regcountry": {
                "values": ['CN', 'OTHERS'],
                "default": "OTHERS"
            },
            "blockevillevel": {
                "values": ['-1', '0', '1', '2', '3'],
                "default": "-1"
            },
            "is_bind_phone": {
                "values": ['0', '1'],
                "default": "1"
            },
            "android_most": {
                "values": ['0', '1'],
                "default": "1"
            },
            "is_demestic_phone":{
                "values":["0","1"],
                "default":"1"
            },
            "is_demestic_idcard":{
                "values":["0","1"],
                "default":"1"
            },
            "logout":{
                "values":["0","1"],
                "default":"0"
            },
            "sex":{
                "values":["-1","0","1"],
                "default":"1"
            },
            "wxsafe_buspay":{
                "values":["-1","0","1"],
                "default":"0"
            },
            "risklevel": {"values": ['-1', '1', '2', '3'], },
            "textexp": {"values": ['-1', '0', '1'], },
            "opponent_distribution": {"values": ['-1', '1', '2', '3'], },
            "expresult": {"values": ['-1', '0', '1'], },
            "gamble_type": {"values": ['0', '1', '2', '3', '4'], },
            "gamble_room_level": {"values": ['0', '1', '2', '3', '4'], },
            "gamble_msg_level": {
                "values": ['0', '1', '2', '3', '4', '5', '6'], },
            "gamble_hb_level": {
                "values": ['0', '1', '2', '3', '4', '5', '6'], },
            "gamble_main_type": {
                "values": ['0', '1', '2', '3', '4', '5', '6', '7'], },
            "gamble_detail_type": {"values": ['0', '1', '2', '3', '4'], },
            "gamble_user_type": {"values": ['0', '1', '2'], },
            "gamble_black_level": {"values": ['0', '1', '2', '3'], },
            "zsm_day_gamble_level": {"values": ['0', '3']},
            "zsm_week_gamble_level": {"values": ['0', '3']},
            "zsm_month_gamble_level": {"values": ['0', '3']},
            "account_exp": {"values": ['-1', '0', '1']},
            "bank_card_exp": {"values": ['-1', '0']},
            "related_punish": {"values": ['-1', '0']},
        }
        enum_columns = []
        for index in enum_index:
            feature_name = feature_all[index]
            if feature_name not in enum_conf:
                enum_conf[feature_name] = {
                    "values": ["0", "1"],
                    "default": "0",
                    "values_dict": dict(zip(["0", "1"], [0, 1])),
                    "values_size": 2
                }
            else:
                values = enum_conf[feature_name]["values"]
                if "default" not in enum_conf[feature_name]:
                    enum_conf[feature_name]["default"] = \
                        enum_conf[feature_name]["values"][0]
                if "values_dict" not in enum_conf[feature_name]:
                    enum_conf[feature_name]["values_dict"] = dict(
                        zip(values, range(len(values))))
                if "values_size" not in enum_conf[feature_name]:
                    enum_conf[feature_name]["values_size"] = len(values)

            if enum_conf[feature_name]["values_size"] == 2:
                enum_columns.append(feature_name)
            else:
                enum_columns.extend([feature_name + "_" + str(x) for x in enum_conf[feature_name]["values"]])
        # print("enum_conf", enum_conf)
        return enum_conf, enum_columns

    def load_feature_cfg(self, cnf):
        feature_extracters = cnf.get('feature_modules', 'extracter_names')
        feature_extracters = feature_extracters.split(',')
        print("extracter", feature_extracters)

        all_feature_names = []
        for name in feature_extracters:
            feature_names = cnf.get(name, "feature_names")
            feature_names = feature_names.split(',')
            feature_names = [x.strip() for x in feature_names]
            all_feature_names.extend(feature_names)

        return all_feature_names

    def get_features(self):
        if self.feature_type == "v1":
            return self.get_feature_v1()


    def get_feature_v1(self,conf_file="feature_extract/feature_cfg.conf"):
        cnf = configparser.ConfigParser()
        cnf.read(conf_file)
        feature_extracted = self.load_feature_cfg(cnf)

        feature_remove = []
        print("feature_remove", len(feature_remove))

        feature_all = self.perfix_feature_names + feature_extracted
        all_index = list(range(len(feature_all)))
        feature_all_index = dict(zip(feature_all, all_index))
        # print("feature_all_index", feature_all_index)
        # print("all_names", len(feature_all))

        text_fields = [
                       "main_account_id","wxid","quality","chatroom_str",
                       'interrupt_max_1d', 'reminder_max_1d',
                       'interrupt_latest_1d', 'reminder_latest_1d',
                       'interrupt_1d', 'reminder_1d', 'interrupt_1w',
                       'reminder_1w', 'income_max_pattern',"signature","nickname",
                       'outcome_max_pattern','latest_devicename'
                    ]
        text_index = [feature_all_index[f] for f in text_fields]
        print("text_index", [feature_all[i] for i in text_index])

        enum_fields = ['is_interrupt_target', 'is_reminder_target',
                       'wxsafe_buspay','ban_in_1m', 
                       'blockevilevel', 'is_bind_phone', 'android_most',
                       'iphone_most', 'windows_most',
                       'risklevel', 'textexp',
                       'opponent_distribution', 'expresult',
                       "sex","is_demestic_phone","is_demestic_idcard","logout",
                ]
        enum_index = [feature_all_index[f] for f in enum_fields]
        enum_conf, enum_columns = self.load_enum_dict(feature_all, enum_index)
        print("enum_index", len(enum_index))

        numerical_index = [i for i in all_index if
                          i not in text_index and i not in enum_index]
        sb=[feature_all[item] for item in numerical_index]
        util.logging.info(sb)
        # print("numerical_index", [feature_all[i] for i in numerical_index])
        print("numerical_index", len(numerical_index))

        feature_selected = [feature_all[i] for i in
                            numerical_index] + enum_columns

        feature_config = {
            "feature_all": feature_all,
            "feature_extracted": feature_extracted,
            "feature_selected": feature_selected,
            "numerical_index": numerical_index,
            "text_index": text_index,
            "enum_index": enum_index,
            "enum_conf": enum_conf,
            "enum_columns": enum_columns,

        }

        return feature_config

    def deal_enum_feature(self, feature_fields):
        feature_fields=self.feature_config["feature_all"]
        new_feature_fields = []
        for index in self.feature_config["enum_index"]:
            feature_name = self.feature_config["feature_all"][index]
            if feature_name not in self.feature_config["enum_conf"]:
                raise ValueError(
                    "枚举特征{}({})没有找到配置".format(feature_name, index))
            values_dict = self.feature_config["enum_conf"][feature_name][
                "values_dict"]
            values_size = self.feature_config["enum_conf"][feature_name][
                "values_size"]
            default = self.feature_config["enum_conf"][feature_name][
                "default"]
            value = feature_fields[index]
            if values_size == 2:
                if value not in values_dict:
                    new_value = values_dict[default]
                elif values_dict[value] == 0:
                    new_value = 0
                else:
                    new_value = 1
                new_feature_fields.append(new_value)
            else:
                new_value = [0] * \
                            self.feature_config["enum_conf"][feature_name][
                                "values_size"]
                if value in values_dict:
                    new_value[values_dict[value]] = 1
                else:
                    new_value[values_dict[default]] = 1
                new_feature_fields.extend(new_value)
        return new_feature_fields


    def load_features(self,feature_file,label_type=1,split=True):
        """
        Args:
        feature_file:source feature file,type string
        label_type:here we design 3 kind label,int,can be 1 ,2,3 
        """
        quality_map={
            "white":0,
            "light_gray":1,
            "heavy_gray":2,
            "light_black":3,
            "heavy_black":4 
        }

        #直接根据标签编码,编码后的结果对应上面的映射表
        label_func_v1=lambda quality:quality_map[quality]

        #white分为一类，其余分成一类   1代表white 0代表非white
        label_func_v2=lambda quality:int(quality=="white")

        #按照三类处理 white 0 gray 1 black 2
        def func_v3(quality:str):
            if quality=="white":
                return 0
            elif quality=="light_gray" or quality=="heavy_gray":
                return 1
            else:
                return 2
        label_func_v3=lambda quality:func_v3(quality)

        reader=open(feature_file,mode="r",encoding="utf-8")
        data_list=[]
        for line in reader:
            line_split=line.strip().split('\001')
            if len(line_split)!=len(self.feature_config["feature_all"]):
                print("%s:data_size not match field name"%(line_split[0]))
                print(len(line_split),len(self.feature_config["feature_all"]))
                continue
    
            data=line_split[:3]
            # for item in self.feature_config["numerical_index"]:
            #     print(self.feature_config["feature_all"][item],":",line_split[item])
            numberical_value=[float(line_split[item]) for item in self.feature_config["numerical_index"]]

            enum_value=self.deal_enum_feature(self.feature_config["feature_all"])
            
            data=data+numberical_value
            data=data+enum_value
            data_list.append(data)
            
        numberical_columns=[self.feature_config["feature_all"][item] for item in self.feature_config["numerical_index"]]

        headers=["main_account_id","wxid","quality"]+numberical_columns+self.feature_config["enum_columns"]
        feature_df=pd.DataFrame(
            data_list,
            columns=headers
        )

        #暂且按照两类处理
        if label_type==1:
            feature_df["quality"]=feature_df["quality"].apply(label_func_v2)
        
        #对应分成三类
        elif label_type==2:
            feature_df["quality"]=feature_df["quality"].apply(label_func_v3)
        
        #对应分成五类
        elif label_type==3:
            feature_df["quality"]=feature_df["quality"].apply(label_func_v1)

        rows,cols=feature_df.shape
        util.logging.info("feature shape:rows {} x cols {}".format(rows,cols))

        selected_feature=self.feature_config["feature_selected"]
        x_all=feature_df[selected_feature]

        y_all=feature_df["quality"]
        account_name=["main_account_id","wxid"]
        if split:
            x_train,x_test,y_train,y_test=train_test_split(x_all,y_all,test_size=0.1,random_state=6)
            train_dis=y_train.value_counts()
            test_dis=y_test.value_counts()
            util.logging.info("训练数据:%s"%dict(train_dis))
            util.logging.info("验证数据:%s"%dict(test_dis))
            #转换成xgboost需要的数据格式
            dataset_train=xgb.DMatrix(x_train,label=y_train)
            dataset_test=xgb.DMatrix(x_test,label=y_test)
        else:
            dataset_train=xgb.DMatrix(x_all,label=y_all)
            all_dis=y_all.value_counts()
            print("evaluate data:",dict(all_dis))
            dataset_test=None #保证返回值是相等长度的
        account_name=["main_account_id","wxid"]
        account_df=feature_df[account_name]

        return account_df,dataset_train,dataset_test

