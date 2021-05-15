import util
import data_interface

def parse_bg_judge(msg:str):
    '''
    Args:
    ------
    msg:str
    '''
    # 恶意封号等级
    blockevilevel = -1
    # 设备
    # 封号等级 设备被举报等级
    deviceblockrate, deviceexposerate = -1, -1
    # 证件被投诉等级 证件被举报等级
    cardblockrate, cardexposerate = -1, -1
    # 赌博风险等级
    risklevel = -1
    # 文本是否有异常
    textexp = -1
    # 异地支付高风险
    opponent_distribution = -1
    # 高危场景交易
    expresult = -1
    add_msg_json=util.load_json(msg)
    wxsafe_cheat = add_msg_json.get("wxsafe_reported_cheatevidence")
    if wxsafe_cheat:
        # this way can avoid return None value
        blockevilevel = wxsafe_cheat.setdefault("blockevillevel", -1)
        deviceblockrate = wxsafe_cheat.setdefault("deviceblockrate", -1)
        deviceexposerate = wxsafe_cheat.setdefault("deviceexposerate", -1)
        cardblockrate = wxsafe_cheat.setdefault("cardblockrate", -1)
        cardexposerate = wxsafe_cheat.setdefault("cardexposerate", -1)

    text_abnormal_info = add_msg_json.get("textAbnormalInfo")
    if text_abnormal_info:
        textexp = text_abnormal_info.setdefault("textExp", -1)

    opponent_abnormal_info = add_msg_json.get("tradeAbnormalInfo")
    if opponent_abnormal_info:
        opponent_distribution = opponent_abnormal_info.setdefault(
            "opponentDistribution", -1)

    gamble_risk_abnormal_info = add_msg_json.get("gambleRiskAbnormalInfo")
    if gamble_risk_abnormal_info:
        risklevel = gamble_risk_abnormal_info.setdefault("risklevel", -1)

    danger_abnoraml_info = add_msg_json.get("dangerAbnormalInfo")
    if danger_abnoraml_info:
        expresult = danger_abnoraml_info.setdefault("expResult", -1)

    return [
        blockevilevel, deviceblockrate, deviceexposerate, cardblockrate,
        cardexposerate, risklevel, textexp, opponent_distribution, expresult
    ]

def parse_line():
    deal_msg=main_account_data["add_msg"]
    output=parse_bg_judge(deal_msg)
    print(deal_msg)

if __name__ == "__main__":
    # data_file = "/home/sun/桌面/account_model/data/2021-05-08#2021-05-08.txt"
    data_file="C:/Users/sunyyao/Desktop/NanGuo/xgb_model/data/2021-05-12#2021-05-12.txt"
    data_wraper = data_interface.DataWraper(
        src=data_file
    )
    data_gen = data_wraper.wrap_batch_data()
    # skip None
    next(data_gen)
    for main_account_data,_ in data_gen:
        add_msg=main_account_data["add_msg"]
        output=parse_bg_judge(add_msg)
        print(output)