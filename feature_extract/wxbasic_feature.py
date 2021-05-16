import configparser
from enum import IntEnum
from logging import log
import data_interface
import util
from urllib.parse import unquote_plus
import json
import re
import numpy as np
import traceback
from word_pattern import (
    chatroom_pattern_v1,
    chatroom_pattern_v2,
    phone_pattern
)
import datetime


TIME_FORMAT="%Y-%m-%d %H:%M:%S"
#微信社交信息
#好友计数和朋友圈由于权限没有获取
def parse_sns(key,msg,task_create_time):
    """
    Args:
    key:chatroom string key in data
    msg:main account data

    """
    chatroom_list=[]
    chatroom_pure_list=[]
    qun_repeat=-1
    chatroom_str=""
    qun_similarity_cos=-1
    qun_abnormal=-1
    if key not in msg or (not msg) or msg[key]=="":
        return [
            chatroom_str,qun_repeat,qun_similarity_cos,qun_abnormal
        ]

    chatroom_msg=msg[key]
    chatroom_decode_msg=unquote_plus(chatroom_msg)
    chatroom_decode_json=json.loads(chatroom_decode_msg)
    qun_abnormal=0
    for c in chatroom_decode_json:
        if "name" in c and c["name"] is not None:
            name = c["name"]
            name = util.chatroom_text_deal(name)
            if len(re.findall(chatroom_pattern_v1,name))>0 or len(re.findall(chatroom_pattern_v2,name))>0:
                qun_abnormal+=1
            chatroom_list.append(name)
            if name!="":
                chatroom_pure_list.append(name)
    qun_similarity_cos=util.string_distance(chatroom_pure_list)

    if len(chatroom_pure_list) > 0:
        qun_repeat = 1 - len(set(chatroom_pure_list)) / (len(chatroom_pure_list) + 1e-5)
    chatroom_str="\002".join(chatroom_pure_list)
    return [
        chatroom_str,qun_repeat,qun_similarity_cos,qun_abnormal
    ]


def parse_pay_info(key,msg,task_create_time):
    """
    Args:
    ------
    key:wxpay time key in data
    msg:main account data

    Returns:
    the delta time from add_time and register time to month
    """
    wxpay_register_time=-1
    if key not in msg or (not msg):
        return [wxpay_register_time]

    wxpay_register_str=msg[key]
    try:
        wxpay_register_datetime=datetime.datetime.strptime(wxpay_register_str,TIME_FORMAT)
        wxpay_register_delta=(task_create_time-wxpay_register_datetime)
        wxpay_register_time=(wxpay_register_delta.days+wxpay_register_delta.seconds/(24*60*60))/30.0
    except ValueError:
        wxpay_register_time=-1
    return [wxpay_register_time]


def parse_device(key,msg,task_create_time):
    """
    Args:
    -----
    key:the key string of msg
    msg:main account data

    Returns:
    -----
    loging device msg
    """
    ipad_device_cnt, iphone_device_cnt, windows_device_cnt, \
    mac_device_cnt, android_device_cnt = 0, 0, 0, 0, 0
    ipad_login_cnt, iphone_login_cnt, windows_login_cnt, \
    mac_login_cnt, android_login_cnt = 0, 0, 0, 0, 0
    latest_devicename = ""
    latest_devicename_datetime = None
    last_30d = task_create_time - datetime.timedelta(days=30)
    change_device_cnt = 0
    android_most, iphone_most, windows_most = 0, 0, 0
    iphone_pct, android_pct, windows_pct, ipad_pct, mac_pct = 0, 0, 0, 0, 0
    
    default_rs = [
        latest_devicename, android_most, iphone_most, windows_most,
        iphone_pct, android_pct, windows_pct,ipad_pct,mac_pct, change_device_cnt
    ]

    if key not in msg or (not msg) or msg[key]=="":
        return default_rs
    
    logindev_msg=msg[key]
    logindev_decode_msg=unquote_plus(logindev_msg)
    device_json=json.loads(logindev_decode_msg)
    for item in device_json:
        devicetype = item["devicetype"].lower()
        devicename = item["devicename"].lower()
        devicetype = util.text_deal(devicetype)
        logincnt = item["logincnt"]
        firstlogintime = item["firstlogintime"]
        firstlogintime_datetime = datetime.datetime.fromtimestamp(
            firstlogintime)
        lastlogintime = item["lastlogintime"]
        lastlogintime_datetime = datetime.datetime.fromtimestamp(
            lastlogintime)
        if latest_devicename_datetime is None \
                or lastlogintime_datetime > latest_devicename_datetime:
            latest_devicename_datetime = lastlogintime_datetime
            latest_devicename = devicename

        if lastlogintime_datetime < last_30d:
            if devicetype.find("windows") == -1 and devicetype.find(
                    "mac") == -1:
                change_device_cnt += 1

        if devicetype.find("ipad") != -1:
            ipad_device_cnt += 1
            ipad_login_cnt += logincnt
        elif devicetype.find("iphone") != -1:
            iphone_device_cnt += 1
            iphone_login_cnt += logincnt
        elif devicetype.find("mac") != -1:
            mac_device_cnt += 1
            mac_login_cnt += logincnt
        elif devicetype.find("windows") != -1:
            windows_device_cnt += 1
            windows_login_cnt += logincnt
        elif devicetype.find("android") != -1:
            android_device_cnt += 1
            android_login_cnt += logincnt

    device_type_login_cnt = np.sum(
        [ipad_login_cnt, iphone_login_cnt, mac_login_cnt, windows_login_cnt,
         android_login_cnt])
    max_device_type_login_cnt = np.max(
        [ipad_login_cnt, iphone_login_cnt, mac_login_cnt, windows_login_cnt,
         android_login_cnt])
    android_most = 1 if android_login_cnt >= max_device_type_login_cnt else 0
    iphone_most = 1 if iphone_login_cnt >= max_device_type_login_cnt else 0
    windows_most = 1 if windows_login_cnt >= max_device_type_login_cnt else 0
    iphone_pct = iphone_login_cnt / (device_type_login_cnt + 1e-5)
    android_pct = android_login_cnt / (device_type_login_cnt + 1e-5)
    windows_pct = windows_login_cnt / (device_type_login_cnt + 1e-5)
    ipad_pct = ipad_login_cnt / (device_type_login_cnt + 1e-5)
    mac_pct = mac_login_cnt / (device_type_login_cnt + 1e-5)

    return [latest_devicename, android_most, iphone_most, windows_most,
            iphone_pct, android_pct, windows_pct, ipad_pct,
            mac_pct, change_device_cnt]

def parse_wxinfo(msg,task_create_time):
    """
    Args:
    -----
    msg:main account data
    spread_msg:spread account data

    """
    opentime_to_now = -1
    signature = ""
    nickname = ""
    sale_in_wxp = 0
    business_in_wxp = 0
    illegal_solicit_in_wxp = 0
    gamble_in_wxp = 0
    gamble_pattern_in_wxp = 0
    is_demestic_phone=0
    is_demestic_idcard=0
    logout=0
    age=0
    sex=0

    sex_map={
        "":-1,
        "男":0,
        "女":1
    }
    
    if not msg:
        return [
            opentime_to_now, sale_in_wxp,business_in_wxp, illegal_solicit_in_wxp, 
            gamble_in_wxp,gamble_pattern_in_wxp
        ]
    if "opentime" in msg:
        opentime=msg["opentime"]
        if opentime:
            opentime_datetime=datetime.datetime.strptime(opentime,TIME_FORMAT)
            opentime_to_now=(task_create_time-opentime_datetime)
            opentime_to_now=(opentime_to_now.days+opentime_to_now.seconds/(24*30*30))/30.
    
    #绑定的手机号是否国内
    if "phone" in msg:
        phone=msg["phone"]
        if re.match(phone_pattern,phone):
            is_demestic_phone=1
    
    #是否国内身份正
    id_card=msg["idcard"]
    if len(id_card)==18:
        is_demestic_idcard=1
    
    #是否注销
    if id_card=="":
        logout=1
    #性别
    if "sex" in msg:
        sex=msg["sex"]
        if sex=="":
            if len(id_card)==18:
                flag=int(id_card[16])
                if flag%2==0:
                    sex=0
                else:
                    sex=1
        else:
            sex=sex_map[sex]
    #年龄
    if "age" in msg:
        age_str=msg["age"]
        if age_str!="":
            age=int(age_str)

    if "signature" in msg:
        signature=unquote_plus(msg["signature"])
        signature=util.text_deal(signature)
    
    if "nickname" in msg:
        nickname=unquote_plus(msg["nickname"])
        nickname=util.text_deal(nickname)

    sale_in_wxp += len(
        re.findall(r"快手号|直播|商品|运费|不退不换|退换|客服|招代理|支持一件代发|备用微信|批发", nickname))
    sale_in_wxp += len(
        re.findall(r"快手号|直播|商品|运费|不退不换|退换|客服|招代理|支持一件代发|备用微信|批发", signature))

    business_in_wxp += len(re.findall(r"维修中心|顺风快递", nickname))
    business_in_wxp += len(re.findall(r"维修中心|顺风快递", signature))

    illegal_solicit_in_wxp += len(
        re.findall(r"希望小学|募捐|捐赠|捐助|希望工程", signature))
    illegal_solicit_in_wxp += len(re.findall(r"希望小学|募捐|捐赠|捐助|希望工程", nickname))

    gamble_in_wxp += len(
        re.findall(r"菠菜|厅主|猪蹄|埋雷|上分|下分|房费|特码|僵尸粉检测", nickname))
    gamble_in_wxp += len(
        re.findall(r"菠菜|厅主|猪蹄|埋雷|上分|下分|房费|特码|僵尸粉检测", signature))

    gamble_pattern_in_wxp += util.gamble_pattern_detect(nickname)

    return [
            opentime_to_now, sale_in_wxp, business_in_wxp,
            illegal_solicit_in_wxp, gamble_in_wxp,
            gamble_pattern_in_wxp, nickname, signature,
            sex,age,is_demestic_phone,is_demestic_idcard,logout
        ]
def parse_account_nickname(main_account_data,spread_account_data):
    """
    cacl the similarity between nickname
    Args:
    -----
    main_account_data: main account data
    spread_account_data:spread account data

    Returns:
    account_nickname_similarity:similarity of nickanmes,float
    """
    main_account_nickname=main_account_data["nickname"]
    main_account_nickname=unquote_plus(main_account_nickname)
    account_nickname=[unquote_plus(account_data["nickname"]) for account_data in spread_account_data]
    account_nickname.append(main_account_nickname)
    account_nickname_similarity=util.string_distance(account_nickname)
    return [account_nickname_similarity]


def parse_line(main_account_data,spread_account_data,task_create_time):
    try:
        output=[]
        #微信社交信息
        sns_output=parse_sns(
            key="group_msg",
            msg=main_account_data,
            task_create_time=task_create_time
        )
        
        #微信登录设备
        device_output=parse_device(
            key="logindev_msg",
            msg=main_account_data,
            task_create_time=task_create_time
        )

        #微信支付信息
        pay_info_output=parse_pay_info(
            key="wxpay_register_time",
            msg=main_account_data,
            task_create_time=task_create_time
        )
        wxinfo_output=parse_wxinfo(
            msg=main_account_data,
            task_create_time=task_create_time
        )

        #账号之间昵称的相似度,cos
        nickname_similarity_output=parse_account_nickname(
            main_account_data=main_account_data,
            spread_account_data=spread_account_data
        )

        output.extend(sns_output)
        output.extend(device_output)
        output.extend(pay_info_output)
        output.extend(wxinfo_output)
        output.extend(nickname_similarity_output)
        return output
    except:
        traceback.print_exc()
        return []

if __name__ == "__main__":
    data_file = "/home/sun/桌面/account_model/data/2021-05-08#2021-05-08.txt"
    cnf = configparser.ConfigParser()
    cnf.read("feature_extract/feature_cfg.conf")
    perfix_feature_names = cnf.get('prefix_feature', 'feature_names')
    perfix_feature_names = perfix_feature_names.split(',')
    perfix_feature_names = [x.strip() for x in perfix_feature_names]
    print("perfix_feature_names", perfix_feature_names)
    feature_names = cnf.get('wxbasic_feature', 'feature_names')
    feature_names=feature_names.split(",")
    feature_names=[x.strip() for x in feature_names]
    # data_file="C:/Users/sunyyao/Desktop/NanGuo/xgb_model/data/2021-05-12#2021-05-12.txt"
    data_wraper = data_interface.DataWraper(
        src=data_file
    )
    data_gen = data_wraper.wrap_batch_data()
    # skip None
    next(data_gen)
    for main_account_data,spread_account_data in data_gen:
        add_time=main_account_data["add_time"]
        task_create_time=datetime.datetime.strptime(add_time,TIME_FORMAT)
        wxbasic_feature=parse_line(
            main_account_data=main_account_data,
            spread_account_data=spread_account_data,
            task_create_time=task_create_time,
        )
        assert len(wxbasic_feature)==len(feature_names),"not match,feature_names is:%d but return is :%d"%(len(feature_names),len(wxbasic_feature))
        print(
            list(
                zip(feature_names,wxbasic_feature)
            )
        )
        