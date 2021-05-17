def complaint_transfer(src:str,complaint_sub_type:str,complaint_type):
    '''
    Args:
        src:投诉来源
        complaint_sub_type:投诉子类
        complaint_type:投诉大类
    Return:
        new_compalint_type:返回其中文映射
    '''
    id_2_name = {
        200 :"色情诈骗",
        201 :"收款不发货",
        202 :"金融诈骗",
        203: "兼职诈骗",
        204: "返利诈骗",
        205: "仿冒诈骗",
        206: "盗号诈骗",
        207: "其他诈骗",
        208: "交友诈骗",
        0: "用户未填写",
        101: "兼职诈骗",
        102: "返利诈骗",
        103: "收款不发货",
        104: "仿冒诈骗",
        105: "交友诈骗",
        106: "虚假投资理财",
        107: "金融诈骗",
        108: "游戏相关",
        109: "色情诈骗",
        110: "赌博诈骗",
        199: "其他诈骗",
        18: "收款不发货",
        19: "仿冒诈骗",
        25: "其他欺诈",
        27: "金融诈骗",
        28: "兼职诈骗",
        29: "免费送诈骗",
        65: "肺炎疫情相关",
        66: "虚假投资理财",
        67: "返利诈骗",
        68: "游戏相关",
        69: "交友诈骗",
        70: "赌博诈骗",

    }

    new_complaint_type = ""
    if complaint_sub_type in id_2_name:
        new_complaint_type = id_2_name[complaint_sub_type]
    elif src == "110" and complaint_type == 2:
        new_complaint_type = "欺诈"
    elif src == "sns_pay" and complaint_type == 1:
        new_complaint_type = "欺诈"
    elif src == "sns_pay" and complaint_type == 2:
        new_complaint_type = "不满意商家服务"
    elif src == "sns_pay" and complaint_type == 99:
        new_complaint_type = "其他"
    elif src == "sns_chat" and complaint_type == 2:
        new_complaint_type = "欺诈"
    elif src == "sns_chat" and complaint_type == 1:
        new_complaint_type = "色情"
    elif src == "sns_chat" and complaint_type == 4:
        new_complaint_type = "广告骚扰"
    elif src == "sns_chat" and complaint_type == 8:
        new_complaint_type = "侵权"
    elif src == "sns_chat" and complaint_type == 16:
        new_complaint_type = "反动"
    elif src == "sns_chat" and complaint_type == 32:
        new_complaint_type = "赌博"
    elif src == "sns_chat" and complaint_type == 64:
        new_complaint_type = "钓鱼"
    elif src == "sns_chat" and complaint_type == 128:
        new_complaint_type = "谣言"
    elif src == "sns_chat" and complaint_type == 256:
        new_complaint_type = "暴恐"
    elif src == "sns_chat" and complaint_type == 512:
        new_complaint_type = "售假"
    elif src == "sns_chat" and complaint_type == 1024:
        new_complaint_type = "诱导"
    elif src == "sns_chat" and complaint_type == 2048:
        new_complaint_type = "违法"
    elif src == "sns_chat" and complaint_type == 4096:
        new_complaint_type = "政治谣言"
    elif src == "sns_chat" and complaint_type == 8192:
        new_complaint_type = "仿冒"
    elif src == "sns_chat" and complaint_type == 16384:
        new_complaint_type = "盗号"
    else:
        new_complaint_type = src + "，" + str(complaint_type)

    return new_complaint_type


complaint_type_collection=[
    "色情诈骗",
    "收款不发货",
    "金融诈骗",
    "兼职诈骗",
    "返利诈骗",
    "仿冒诈骗",
    "盗号诈骗",
    "其他诈骗",
    "交友诈骗",
    "兼职诈骗",
    "收款不发货",
    "虚假投资理财",
    "游戏相关",
    "赌博诈骗",
    "其他欺诈",
    "免费送诈骗",
    "肺炎疫情相关",
    "欺诈",
    "色情",
    "其他",
    "广告骚扰",
    "侵权",
    "反动",
    "赌博",
    "钓鱼",
    "谣言",
    "暴恐",
    "售假",
    "诱导",
    "违法",
    "政治谣言",
    "仿冒",
    "盗号",
    "不满意商家服务",
    "用户未填写",
]

size=len(complaint_type_collection)
index=list(range(size))
complaint_type_lookup=dict(zip(complaint_type_collection,index))