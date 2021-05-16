#!/usr/bin/env python
# -*- coding: utf-8 -*-
import configparser

import pandas as pd
import xgboost as xgb


class Parser(object):
    def __init__(self, feature_type):
        self.feature_type = feature_type
        # precise_rough 1是精标,2是粗标
        self.perfix_feature_names = [
            "main_account_id","wxid"
        ]
        self.feature_config = self.get_features()

    def load_enum_dict(self, feature_all, enum_idex):
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
        for idex in enum_idex:
            feature_name = feature_all[idex]
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
        print("enum_conf", enum_conf)
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

    def load_features(self, feature_file):
        if self.feature_type == "v1":
            return self.load_features_v1(feature_file)

    def get_feature_v1(self):
        cnf = configparser.ConfigParser()
        cnf.read("feature_cfg.conf")
        feature_extracted = self.load_feature_cfg(cnf)

        feature_remove = []
        print("feature_remove", len(feature_remove))

        feature_all = self.perfix_feature_names + feature_extracted
        all_idex = list(range(len(feature_all)))
        feature_all_idex = dict(zip(feature_all, all_idex))
        print("feature_all_idex", feature_all_idex)
        print("all_names", len(feature_all))

        text_fields = ['rs', 'label', 'precise_rough', 'type', 'task_id',
                       'account', 'rtx', 'time', 'interface',
                       'interrupt_max_1d', 'reminder_max_1d',
                       'interrupt_latest_1d', 'reminder_latest_1d',
                       'interrupt_1d', 'reminder_1d', 'interrupt_1w',
                       'reminder_1w', 'income_max_pattern',
                       'outcome_max_pattern', 'wx_big_head_url',
                       'history_phones',
                       'latest_devicename', 'gamble_room']
        text_idex = [feature_all_idex[f] for f in text_fields]
        print("text_idex", [feature_all[i] for i in text_idex])

        enum_fields = ['is_interrupt_target', 'is_reminder_target',
                       'wxsafe_buspay',
                       'ban_in_1m', 'fraudtype', 'fraudlevel', 'predictlabel',
                       'wxsafe_gender', 'wxsafe_regcountry',
                       'blockevillevel', 'is_bind_phone', 'android_most',
                       'iphone_most', 'windows_most',
                       'unknow_bank_phone', 'risklevel', 'textexp',
                       'opponent_distribution', 'expresult', 'gamble_type',
                       'gamble_room_level', 'gamble_msg_level',
                       'gamble_hb_level', 'is_gamble_organizer',
                       'gamble_main_type', 'gamble_detail_type',
                       'gamble_user_type', 'gamble_black_level', 'mchid_flag',
                       'f2f_flag', 'card_flag', 'zsm_flag', 'room_flag',
                       'hb_flag', 'transfer_flag', 'mobile_flag',
                       'zsm_day_gamble_level', 'zsm_week_gamble_level',
                       'zsm_month_gamble_level', 'account_exp',
                       'bank_card_exp', 'related_punish']
        enum_idex = [feature_all_idex[f] for f in enum_fields]
        enum_conf, enum_columns = self.load_enum_dict(feature_all, enum_idex)
        print("enum_idex", len(enum_idex))

        numerical_idex = [i for i in all_idex if
                          i not in text_idex and i not in enum_idex]
        print("numerical_idex", [feature_all[i] for i in numerical_idex])
        print("numerical_idex", len(numerical_idex))

        feature_selected = [feature_all[i] for i in
                            numerical_idex] + enum_columns

        feature_config = {
            "feature_all": feature_all,
            "feature_extracted": feature_extracted,
            "feature_selected": feature_selected,
            "numerical_idex": numerical_idex,
            "text_idex": text_idex,
            "enum_idex": enum_idex,
            "enum_conf": enum_conf,
            "enum_columns": enum_columns,

        }

        return feature_config

    def deal_numerical_feature(self, feature_fields):
        all_idex = list(
            range(len(self.feature_config["feature_extracted"]) + 7))
        type = feature_fields[0]
        task_id = feature_fields[1]
        account = feature_fields[2]
        rs = int(feature_fields[3])
        values = [
            float(feature_fields[i])
            for i in all_idex if i in self.feature_config["numerical_idex"]]
        data_list_temp = values
        return data_list_temp

    def deal_enum_feature(self, feature_fields):
        new_feature_fields = []
        for idex in self.feature_config["enum_idex"]:
            feature_name = self.feature_config["feature_all"][idex]
            if feature_name not in self.feature_config["enum_conf"]:
                raise ValueError(
                    "枚举特征{}({})没有找到配置".format(feature_name, idex))
            values_dict = self.feature_config["enum_conf"][feature_name][
                "values_dict"]
            values_size = self.feature_config["enum_conf"][feature_name][
                "values_size"]
            default = self.feature_config["enum_conf"][feature_name][
                "default"]
            value = feature_fields[idex]
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

    def load_features_v1(self, feature_file):
        reader = open(feature_file, encoding="utf-8")
        data_list = []
        while True:
            line = reader.readline().strip()
            if not line:
                break
            fields = line.split('\001')
            if len(fields) != len(self.feature_config['feature_all']):
                print("{} {}".format(fields[:3], len(fields)))
                continue
            data_list_temp = fields[:6] + fields[7:9]
            numerical_value = [float(fields[i]) for i in range(len(fields)) if
                               i in self.feature_config["numerical_idex"]]
            enum_value = self.deal_enum_feature(fields)

            data_list_temp += numerical_value
            data_list_temp += enum_value
            data_list.append(data_list_temp)

        numerical_column = [self.feature_config['feature_all'][i] for i in
                            self.feature_config["numerical_idex"]]
        feature_df = pd.DataFrame(
            data_list,
            columns=[
                        'type', 'task_id', 'account', 'rs', 'rtx', 'time',
                        'label', 'precise_rough'
                    ] + numerical_column + self.feature_config["enum_columns"]
        )
        feature_df["rs"] = feature_df["rs"].apply(int)
        print("feature_df {}".format(len(feature_df)))
        return feature_df

    def df_2_dmatrix(self, df):
        x = df[self.feature_config['feature_selected']]
        y = df["rs"].values - 1
        dmatrix = xgb.DMatrix(x, label=y)
        return dmatrix, x, y
