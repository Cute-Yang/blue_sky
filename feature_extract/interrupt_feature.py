import data_interface
import datetime
import os
import traceback
import util
from collections import Counter


TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

def banhis_def(banhis,task_create_time):
    """
    Args:
    ------
    banhis:list of ban history 
    task_create_time:add time

    Returns:
    -----
    ban_1_1m:whether ban in latest 1 month
    ban_reason_abnormal:if the reason has sex or gamble
    """
    ban_in_1m = 0
    ban_reason_abnormal=0
    for item in banhis:
        if "bantime" in item and "processtype" in item:
            processtype = item["processtype"]
            bantime = item["bantime"]
            # bantime = bantime.replace('+', ' ')
            bantime_datetime = datetime.datetime.strptime(
                bantime, "%Y-%m-%d %H:%M:%S"
            )
            if bantime_datetime > task_create_time:
                continue
            if processtype != "封号":
                continue
            ban_reason=item["banreason"]
            if "色情" in ban_reason or "代练" in ban_reason or "盗号" in ban_reason or "赌博" in ban_reason:
                ban_reason_abnormal=1
            ban_in_1m = 1
    return ban_in_1m,ban_reason_abnormal


def parse_wxsafe_block_data(msg: str, task_create_time,content_key: str = "blockmessage"):
    # 提醒拦截策略的次数
    reminder_cnt_1d, reminder_cnt_1w, interrupt_cnt_1d, \
        interrupt_cnt_1w = -1, -1, -1, -1
    # 提醒拦截策略
    interrupt_max_1d, reminder_max_1d, interrupt_latest_1d, \
        reminder_latest_1d = "", "", "", ""
    # 是否拦截命中方,是否提醒命中方
    is_interrupt_target, is_reminder_target, wxsafe_buspay = -1, -1, -1
    # 一天内、一周内的提醒拦截策略
    interrupt_1d, reminder_1d, interrupt_1w, reminder_1w = "", "", "", ""
    ban_in_1m = 0
    ban_reason_abnormal=0

    default_rs = [
        reminder_cnt_1d, reminder_cnt_1w, interrupt_cnt_1d,
        interrupt_cnt_1w, interrupt_max_1d, reminder_max_1d,
        interrupt_latest_1d, reminder_latest_1d, is_reminder_target,
        is_interrupt_target, interrupt_1d, reminder_1d, interrupt_1w,
        reminder_1w, wxsafe_buspay,
        ban_in_1m,ban_reason_abnormal
    ]
    if not msg:
        return default_rs

    wxsafe = util.load_json(msg)

    if not wxsafe:
        return default_rs

    block_message = wxsafe.get(content_key)
    if not block_message:
        return default_rs
    print(block_message)

    last_1d = task_create_time - datetime.timedelta(days=1)
    last_1w = task_create_time - datetime.timedelta(weeks=1)

    reminder_cnt_1d, reminder_cnt_1w, interrupt_cnt_1d, \
        interrupt_cnt_1w = 0, 0, 0, 0
    is_interrupt_target, is_reminder_target, wxsafe_buspay = 0, 0, 0

    def _time_statis(time_list):
        cnt = 0
        max_pay_scene = ""
        if len(time_list) > 0:
            cnt = len(time_list)
            time_list_counter = Counter(time_list)
            max_pay_scene = time_list_counter.most_common(1)
        return cnt, max_pay_scene

    reminder_cnt_1d, reminder_cnt_1w, interrupt_cnt_1d, \
        interrupt_cnt_1w = 0, 0, 0, 0
    interrupt_1d_list, reminder_1d_list = [], []
    interrupt_1w_list, reminder_1w_list = [], []

    def _blockmessage_def():
        is_interrupt_target, is_reminder_target, wxsafe_buspay = 0, 0, 0
        for item in block_message:
            item_time = item["time"]
            time_datetime = datetime.datetime.fromtimestamp(item_time)
            if time_datetime > task_create_time:
                continue
            channel = item["channel"]
            scene = item["scene"]
            type = item["type"]
            strageid = item["strageid"]
            matchrule = item["matchrule"]
            ruledescription = item["ruledescription"]
            if ruledescription.find("商业支付") != -1:
                wxsafe_buspay = 1
            ruletype = item["ruletype"]
            interrupttype = item["interrupttype"]
            # interrupttype:1-付款方, 2-收款方
            strategy_target = 0
            if (interrupttype == 1 and type == "付款(1)") or (
                    interrupttype == 2 and type == "收款(2)"):
                strategy_target = 1
            pay_scene = (
                scene, type, strageid, matchrule, ruledescription, ruletype,
                strategy_target)
            if channel == "提醒(1)":
                if strategy_target:
                    is_reminder_target = 1
                if time_datetime > last_1d:
                    reminder_1d_list.append(pay_scene)
                if time_datetime > last_1w:
                    reminder_1w_list.append(pay_scene)
            elif channel == "拦截(0)":
                if strategy_target:
                    is_interrupt_target = 1
                if time_datetime > last_1d:
                    interrupt_1d_list.append(pay_scene)
                if time_datetime > last_1w:
                    interrupt_1w_list.append(pay_scene)
        return wxsafe_buspay, is_reminder_target, is_interrupt_target
    is_interrupt_target, is_reminder_target, wxsafe_buspay = _blockmessage_def()
    interrupt_cnt_1d, interrupt_max_1d = _time_statis(interrupt_1d_list)
    interrupt_cnt_1w, interrupt_max_1w = _time_statis(interrupt_1w_list)
    reminder_cnt_1d, reminder_max_1d = _time_statis(reminder_1d_list)
    reminder_cnt_1w, reminder_max_1w = _time_statis(reminder_1w_list)
    interrupt_1d = '|'.join(
        [','.join([str(y) for y in x]) for x in interrupt_1d_list])
    interrupt_1w = '|'.join(
        [','.join([str(y) for y in x]) for x in interrupt_1w_list])
    reminder_1d = '|'.join(
        [','.join([str(y) for y in x]) for x in reminder_1d_list])
    reminder_1w = '|'.join(
        [','.join([str(y) for y in x]) for x in reminder_1w_list])

    #封号记录
    if "txt110" in wxsafe:
        ban_his=wxsafe["txt110"]
        ban_in_1m,ban_reason_abnormal=banhis_def(
            ban_his=ban_his,
            task_create_time=task_create_time
        )
        
    return [
        reminder_cnt_1d, reminder_cnt_1w, interrupt_cnt_1d,
        interrupt_cnt_1w, interrupt_max_1d, reminder_max_1d,
        interrupt_latest_1d, reminder_latest_1d, is_reminder_target,
        is_interrupt_target, interrupt_1d, reminder_1d, interrupt_1w,
        reminder_1w, wxsafe_buspay,
        ban_in_1m,ban_reason_abnormal
    ]

def paser_line(main_account_data):
    deal_msg=main_account_data["deal_msg"]
    add_time = main_account_data["add_time"]
    util.logging.info(add_time)
    task_create_time = datetime.datetime.strptime(add_time, TIME_FORMAT)
    output=parse_wxsafe_block_data(
        msg=deal_msg,
        task_create_time=task_create_time,
        content_key="blockmessage"
    )


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
        deal_msg=main_account_data["deal_msg"]
        add_time = main_account_data["add_time"]
        util.logging.info(add_time)
        task_create_time = datetime.datetime.strptime(add_time, TIME_FORMAT)
        output=parse_wxsafe_block_data(
            msg=deal_msg,
            task_create_time=task_create_time,
            content_key="blockmessage"
        )
        print(output)