from logging import log
import configparser
from urllib import parse
from urllib.parse import unquote_plus
import data_interface
import json
import re
import util
from collections import defaultdict,Counter
import time
import datetime
import traceback
from rule import complaint_type_lookup,complaint_transfer

TIME_FORMAT="%Y-%m-%d %H:%M:%S"

from word_pattern import(
    greeting_pattern,
    reporter_redpacket_pattern,
    reporter_transfer_pattern,
    be_reported_redpacket_pattern,
    be_reported_transfer_pattern,
    gamble_evidence_pattern,
    cashback_evidence_pattern,
    cashout_evidence_pattern,
    exchange_evidence_pattern,
    porn_evidence_pattern,
    porn_proof_pattern,
    third_party_pay_pattern,
    pull_back_pattern
)

#同设备关联
DEVICE_SPEAD=2
#同身份关联
BINDCARD_SPEAD=1


def face_2_face_pay(string):
    if string.find("pay:") != -1 and string.find("recv:") != -1:
        return True
    return False


def find_number(org):
    number_pattern_1="\D*\d+\.*\d*\D*"
    number_pattern_2="[一,二,三,四,五,六,七,八,九]"
    if re.match(number_pattern_1,org):
        return True
    else:
        if len(re.findall(number_pattern_2,org))>0:
            return True
    return False


def count_pick_max(list_to_count):
    cnt = 0
    max_pattern = ""
    max_pattern_cnt = 0
    if len(list_to_count) > 0:
        cnt = len(list_to_count)
        counter = Counter(list_to_count)
        t = counter.most_common(1)
        max_pattern = t[0][0]
        max_pattern_cnt = t[0][1]
    return cnt, max_pattern, max_pattern_cnt

def income_outcome_text(key,msg):
    """
    Args:
    -----
    key:income text and outcome text key,default is greeting text
    msg:main_account_data
    """
    incomegreeting, outcomegreeting = [], []
    income_number, outcome_number = 0, 0
    income_cnt,outcome_cnt=0,0
    income_number_pct,outcome_number_pct=0,0
    income_face_2_face_cnt, outcome_face_2_face_cnt = 0, 0
    income_face_2_face_pct,outcome_face_2_face_pct=0,0
    income_pattern_list, outcome_pattern_list = [], []
    #出入账文本中数值占比
    income_number_rate,outcome_number_rate=0,0
    #出入账文本异常的数量，这里匹配色情和赌博
    income_abnormal,outcome_abnormal=0,0
    income_max_pattern_cnt,outcome_max_pattern_cnt=0,0
    income_max_pattern_pct,outcome_max_pattern_pct=0,0
    income_max_pattern,outcome_max_pattern="",""
    if key in msg and msg[key]:
        greeting_text=unquote_plus(msg[key])
        greeting_text=json.loads(greeting_text)
        incomegreeting=greeting_text["income_text"]
        outcomegreeting=greeting_text["outcome_text"]
        for t in incomegreeting:
            t=util.greeting_text_deal(t)
            if find_number(t):
                income_number += 1
            if face_2_face_pay(t):
                income_face_2_face_cnt += 1
            income_number_rate+=util.greeting_text_number_rate(t)
            if len(re.findall(greeting_pattern,t)):
                income_abnormal+=1
        
            income_pattern = re.sub("\d+", "$", t)
            income_pattern_list.append(income_pattern)

        for t in outcomegreeting:
            t=util.greeting_text_deal(t)
            if find_number(t):
                outcome_number += 1
            if face_2_face_pay(t):
                outcome_face_2_face_cnt += 1
            outcome_number_rate+=util.greeting_text_number_rate(t)
            if len(re.findall(greeting_pattern,t))>0:
                outcome_abnormal+=1
            outcome_pattern = re.sub("\d+", "$", t)
            outcome_pattern_list.append(outcome_pattern)
        
        income_cnt = len(incomegreeting)
        income_pattern_cnt, income_max_pattern, income_max_pattern_cnt = \
        count_pick_max(income_pattern_list)

        if income_cnt < 5:
            # income_pattern_cnt = 0
            income_number = 0
            income_face_2_face_cnt = 0
            income_max_pattern_cnt = 0
        if income_max_pattern_cnt == 1:
            income_max_pattern_cnt = 0
        income_number_pct = income_number / (income_cnt + 1e-5)
        income_face_2_face_pct = income_face_2_face_cnt / (income_cnt + 1e-5)
        income_max_pattern_pct = income_max_pattern_cnt / (income_cnt + 1e-5)

        outcome_cnt = len(outcomegreeting)
        outcome_pattern_cnt, outcome_max_pattern, outcome_max_pattern_cnt = \
            count_pick_max(outcome_pattern_list)

        if outcome_cnt < 5:
            # outcome_pattern_cnt = 0
            outcome_number = 0
            outcome_face_2_face_cnt = 0
            outcome_max_pattern_cnt = 0
        if outcome_max_pattern_cnt == 1:
            outcome_max_pattern_cnt = 0
        outcome_number_pct = outcome_number / (outcome_cnt + 1e-5)
        outcome_face_2_face_pct = outcome_face_2_face_cnt / (outcome_cnt + 1e-5)
        outcome_max_pattern_pct = outcome_max_pattern_cnt / (outcome_cnt + 1e-5)
    return [
        income_number, income_number_pct, income_cnt, outcome_number,
        outcome_number_pct, outcome_cnt,
        income_face_2_face_pct, outcome_face_2_face_pct,
        income_max_pattern_pct, outcome_max_pattern_pct,
        income_max_pattern_cnt, income_max_pattern,
        outcome_max_pattern_cnt, outcome_max_pattern,
        income_number_rate,outcome_number_rate,
        income_abnormal,outcome_abnormal
    ]


def self_acc_evidence(main_account_data,key):
    self_acc_trans_cnt, self_acc_pic_cnt, self_acc_sens_cnt, \
    self_acc_words_per_sen, self_acc_expose_cnt = 0, 0, 0, 0, 0

    #举报该账号的账号数量
    self_acc_expose_by_account=0
    
    self_acc_trans_set,self_acc_pic_set,self_acc_sens_set=set(),set(),set()
    self_complaint_key_set=defaultdict(set)
    if key in main_account_data:
        complaint_msg=main_account_data[key]
        complaint_list=json.loads(
            unquote_plus(complaint_msg)
        )

        for complaint in complaint_list:
            if "evidence" in complaint:
                evidence=complaint["evidence"]
                evidence=evidence.split("|")
                self_acc_pic_set.update(evidence)

            if "trans_id" in complaint:
                trans_id=complaint["trans_id"]
                trans_id=trans_id.split("|")
                self_acc_trans_set.update(trans_id)
            
            if "msg_txt" in complaint:
                msg_txt=complaint["msg_txt"]
                be_reported_sentence_list=[]
                for m in msg_txt.split("|"):
                    if m.startswith("被举报人:"):
                        self_acc_sens_set.add(m)
            if "wxid" in complaint:
                exposetime=complaint["exposetime"]
                #有可能不是时间辍
                if not isinstance(exposetime, int):
                    timestamp=time.mktime(
                        time.strptime(exposetime,"%Y-%m-%d %H:%M:%S")
                    )
                    timestamp=int(timestamp)
                from_wxid=complaint["wxid"]
                self_complaint_key_set[from_wxid].add(
                    "{}#{}".format(from_wxid,timestamp)
                )
        def _stat_complaint(complaint_record):
            stat_res=0
            for _,value in complaint_record.items():
                stat_res+=len(value)
            return stat_res
        
        self_acc_pic_cnt=len(self_acc_pic_set)
        self_acc_trans_cnt=len(self_acc_trans_set)
        self_acc_sens_cnt=len(self_acc_sens_set)
        self_acc_sens_per_compliant=len(self_acc_sens_set)/(len(complaint_list)+1e-5)
        self_acc_expose_cnt=_stat_complaint(self_complaint_key_set)
        self_acc_expose_by_account=len(self_complaint_key_set)
        return [
            self_acc_expose_cnt, self_acc_trans_cnt, self_acc_pic_cnt,
            self_acc_sens_cnt,self_acc_sens_per_compliant,
            self_acc_expose_cnt,self_acc_expose_by_account
        ]

def spread_feature(spread_account_data,key="related_type"):
    same_device_account_number=0
    same_idcard_account_number=0
    spread_all_acc_cnt=0
    for account_data in spread_account_data:
        related_type=account_data[key]
        if related_type==DEVICE_SPEAD:
            same_device_account_number+=1
        elif related_type==BINDCARD_SPEAD:
            same_idcard_account_number+=1
        spread_all_acc_cnt+=1

    return [
        spread_all_acc_cnt,
        same_device_account_number,
        same_idcard_account_number
    ]

def evidence_feature(account_data,key,task_create_time):
    #赌博
    gamble_account_number,gamble_in_evidence=0,0
    #返现
    cashback_account_number,cashback_in_evidence=0,0
    #套现
    cashout_account_number,cashout_in_evidence=0,0
    #汇兑
    exchange_account_number,exchange_in_evidence=0,0
    #色情
    porn_account_number,porn_in_evidence=0,0
    #支付宝
    alipay_account_number,alipay_cnt=0,0
    
    #投诉方向,相同方向的投诉人数
    complaint_direction,complaint_direction_number=-1,0
    #举证中有订单的次数
    trans_account_number=0
    #举证中有图片的次数
    pic_account_number=0
    
    trans_account_pct=0
    pic_account_pct=0
    
    reporter_money_cnt,reporter_money_pct=0,0
    be_reported_money_cnt,be_reported_money_pct=0,0

    complaint_sens_pct=0
    trans_account_set,pic_account_set=set(),set()

    #evidence record block 
    gamble_evidence_block=defaultdict(set)
    cashback_evidence_block=defaultdict(set)
    cashout_evidence_block=defaultdict(set)
    exchange_evidence_block=defaultdict(set)
    porn_evidence_block=defaultdict(set)
    alipay_evidence_block=defaultdict(set)
    
    gamble_proof_account,gamble_in_proof=0,0
    porn_proof_account,porn_in_proof=0,0
    pull_back_proof_account,pull_back_in_proof=0,0


    #proof record block
    gamble_proof_block=defaultdict(set)
    porn_proof_block=defaultdict(set)
    pull_back_block=defaultdict(set)
    
    #被投诉的账号数量
    complaint_account_number=0

    #投诉的账号数量
    from_complaint_account_number=0
    from_complaint_account_set=set()

    #投诉的记录的数量
    complaint_number=0
    complaint_set=set()

    #it means main_account_data,we should wrap it to a list,syntax
    if isinstance(account_data,dict):
        account_data=[account_data]
        
    trans_total_number,pic_total_number=0,0
    trans_per_acc,pic_per_acc=0,0
    trans_set,pic_set,sens_set=set(),set(),set()
    reporter_transfer_set,be_reported_transfer_set=set(),set()
    reporter_redpacket_set,be_reported_redpacket_set=set(),set()
    
    complaint_direction_block=defaultdict(list)
    datetime_6m=task_create_time-datetime.timedelta(days=30*6)
    for data in account_data:
        complaint_msg=data["complaint_msg"]
        complaint_account_number+=1
        if complaint_msg=="":
            continue
        to_wxid=data["account"]
        _status,complaint_list=util.multi_unquote(complaint_msg)
        if not _status:
            util.logging.info("json decode failed.....")
            continue
        # complaint_account_number+=1
        for complaint in complaint_list:
            if "wxid" not in complaint:
                util.logging.info("found a invalid compliant item,miss wxid....")
                continue
            from_wxid=complaint["wxid"]

            if "exposetime" in complaint:
                exposetime=complaint["exposetime"]
                _status,complaint_time,time_str=util.decode_exposetime(exposetime)
                if (complaint_time < datetime_6m) or (complaint_time>task_create_time):
                    task_create_time_str=datetime.datetime.strftime(task_create_time,TIME_FORMAT)
                    util.logging.info("Meet invlalid time %s and %s"%(time_str,task_create_time_str))
                    continue
                if not _status:
                    util.logging.error("failed to decode expose time:%s"%exposetime)

                from_wxid=complaint["wxid"]
                complaint_set.add(
                    "{}#{}".format(from_wxid,time_str)
                )
    
            from_complaint_account_set.add(from_wxid)
            complaint_sub_type = int(complaint.get("complaint_sub_type"))
            complaint_main_type = int(complaint.get("complaint_type"))
            complaint_src = complaint.get("src")
            complaint_type = complaint_transfer(
                src=complaint_src,
                complaint_sub_type=complaint_sub_type,
                complaint_type=complaint_main_type
            )
            complaint_type = complaint_type_lookup[complaint_type]
            if complaint_type:
                complaint_direction_block[from_wxid].append(complaint_type)
            if "evidence" in complaint:
                evidence=complaint["evidence"]
                try:
                    evidence=evidence.split("|")
                except:
                    if not isinstance(evidence, list):
                        util.logging.error("unknown evidence data format not str or list")
                        evidence=[]
                    # else:
                    #     util.logging.info("meet evidence data format list...")
                pic_set.update(evidence)
                pic_account_set.add(from_wxid)

            if "trans_id" in complaint:
                trans_id=complaint["trans_id"]
                trans_id=trans_id.split("|")
                trans_set.update(trans_id)
                trans_account_set.add(from_wxid)

            if "msg_txt" in complaint:
                msg_txt=complaint["msg_txt"]
                msg_txt=util.text_deal(msg_txt)
                # be_reported_sentence_list=set()
                for m in msg_txt.split("|"):
                    if m.startswith("被举报人:"):
                        sens_set.add(m)
                #add gamble record from msg text
                if len(re.findall(gamble_evidence_pattern,msg_txt))>0:
                    # print(msg_txt)
                    gamble_evidence_block[to_wxid].add(from_wxid)
                
                #add cashback record from msg text
                if len(re.findall(cashback_evidence_pattern,msg_txt))>0:
                    cashback_evidence_block[to_wxid].add(from_wxid)

                #add cashout record from msg text
                if len(re.findall(cashout_evidence_pattern,msg_txt)):
                    cashback_evidence_block[to_wxid].add(from_wxid)

                #add exchange record from msg text
                if len(re.findall(exchange_evidence_pattern,msg_txt))>0:
                    exchange_evidence_block[to_wxid].add(from_wxid)
                
                #add porn record from msg text
                if len(re.findall(porn_evidence_pattern,msg_txt))>0:
                    porn_evidence_block[to_wxid].add(from_wxid)
                
                if len(re.findall(third_party_pay_pattern,msg_txt))>0:
                    alipay_evidence_block[to_wxid].add(from_wxid)
    
                #add gamble record from proof
                #红包
                reporter_transfer_find=re.findall(reporter_transfer_pattern,msg_txt)
                reporter_transfer_set.update(reporter_transfer_find)

                #转账
                reporter_redpacket_find=re.findall(reporter_redpacket_pattern, msg_txt)
                reporter_redpacket_set.update(reporter_redpacket_find)

                be_reported_transfer_find=re.findall(be_reported_transfer_pattern,msg_txt)
                be_reported_transfer_set.update(be_reported_transfer_find)
                
                be_reported_redpacket_find=re.findall(be_reported_redpacket_pattern, msg_txt)
                be_reported_redpacket_set.update(be_reported_redpacket_find)

            if "proof" in complaint:
                proof=complaint["proof"]
                #add gamble record from proof
                if len(re.findall(gamble_evidence_pattern,proof))>0:
                    gamble_proof_block[to_wxid].add(from_wxid)

                #add porn record from proof
                if len(re.findall(porn_proof_pattern,proof))>0:
                    porn_proof_block[to_wxid].add(from_wxid)

                #add pull back record from proof
                if len(re.findall(pull_back_pattern,proof))>0:
                    pull_back_block[to_wxid].add(from_wxid)

            
                

        #this function is just for interanl function,so we define it in this block
        def _stat_complaint_block(block):
            to_complaint_num=len(block)
            from_complaint_num=0
            for _,value in block.items():
                from_complaint_num+=len(value)
            return to_complaint_num,from_complaint_num
        def _stat_complaint_type(block):
            temp=[]
            t,n=-1,0
            for key,value in block.items():
                if value:
                    value_count=Counter(value)
                    most_complaint=value_count.most_common(1)[0]
                    temp.append(most_complaint)
            if temp:
                temp_count=Counter(temp)
                t,n=temp_count.most_common(1)[0]
            return t,n

        complaint_direction,complaint_direction_number=_stat_complaint_block(complaint_direction_block)
        complaint_number=len(complaint_set)
        
        from_complaint_account_number=len(from_complaint_account_set)

        #msg text pattern result
        gamble_account_number,gamble_in_evidence=_stat_complaint_block(gamble_evidence_block)
        porn_account_number,porn_in_evidence=_stat_complaint_block(porn_evidence_block)
        cashback_account_number,cashback_in_evidence=_stat_complaint_block(cashback_evidence_block)
        cashout_account_number,cashout_in_evidence=_stat_complaint_block(cashout_evidence_block)
        exchange_account_number,exchange_in_evidence=_stat_complaint_block(exchange_evidence_block)
        porn_account_number,porn_in_evidence=_stat_complaint_block(porn_evidence_block)
        alipay_account_number,alipay_cnt=_stat_complaint_block(alipay_evidence_block)
        
        #proof text pattern result
        gamble_proof_account,gamble_in_proof=_stat_complaint_block(gamble_proof_block)
        porn_proof_account,porn_in_proof=_stat_complaint_block(porn_proof_block)
        pull_back_proof_account,pull_back_in_proof=_stat_complaint_block(pull_back_block)

        #举报人转账，发红包次数 平均次数
        reporter_money_cnt=len(reporter_redpacket_set)+len(reporter_transfer_set)
        reporter_money_pct=reporter_money_cnt/(from_complaint_account_number+1e-5)
        
        #被举报人转账,收红包次数,平均次数
        be_reported_money_cnt=len(be_reported_redpacket_set) + len(be_reported_transfer_set)
        be_reported_money_pct=be_reported_money_cnt/(from_complaint_account_number+1e-5)

        #被举报人说话句数
        complaint_sens_pct=len(sens_set)/(complaint_number+1e-5)


        #举报中订单数量 平均订单数量
        #所有订单数量
        trans_total_number=len(trans_set)
        #平均订单数量
        trans_per_acc=trans_total_number/(from_complaint_account_number+1e-5)
        
        #投诉中有订单的账号数量
        trans_account_number=len(trans_account_set)
        
        #投诉中有订单数量的账号占比
        trans_account_pct=trans_account_number/(from_complaint_account_number+1e-5)


        #举报中图片数量  平均图片数量
        #所有图片数量
        pic_total_number=len(pic_set)
        
        #平均图片数量
        pic_per_acc=pic_total_number/(from_complaint_account_number+1e-5)
        # print(pic_total_number,from_complaint_account_number)
        
        #投诉中有图片的账号数量
        pic_account_number=len(pic_account_set)

        #投诉中有图片的账号数量占比
        pic_account_pct=pic_account_number/(from_complaint_account_number+1e-5)

    return [
        trans_per_acc,trans_total_number,trans_account_number,trans_account_pct,
        pic_per_acc,pic_total_number,pic_account_number,pic_account_pct,
        gamble_in_evidence,gamble_account_number,cashback_in_evidence,cashback_account_number,
        cashout_in_evidence,cashout_account_number,exchange_in_evidence,exchange_account_number,
        porn_in_evidence,porn_account_number,alipay_cnt,alipay_account_number,
        gamble_proof_account,gamble_in_proof,porn_proof_account,porn_in_proof,
        pull_back_proof_account,pull_back_in_proof,
        reporter_money_cnt,reporter_money_pct,
        be_reported_money_cnt,be_reported_money_pct,
        complaint_account_number,from_complaint_account_number,complaint_number,
        complaint_sens_pct,
        complaint_direction,complaint_direction_number
    ]

def parse_line(main_account_data,spread_account_data,task_create_time):
    output=[]
    try:
        greeting_output=income_outcome_text(
            key="greeting_text",
            msg=main_account_data
        )
        output.extend(greeting_output)

        self_account_feature=evidence_feature(
            main_account_data, 
            key="complaint_msg",
            task_create_time=task_create_time
        )
        output.extend(self_account_feature)

        spread_account_feature=evidence_feature(
            spread_account_data,
            key="complaint_msg",
            task_create_time=task_create_time
        )
        output.extend(spread_account_feature)

        #统计扩散账号数量的
        spread_feature_output=spread_feature(
            spread_account_data=spread_account_data,
            key="related_type"
        )
        output.extend(spread_feature_output)

    except:
        traceback.print_exc()
    
    finally:
        return output

def test():
    # data_file = "/home/sun/桌面/account_model/data/2021-05-08#2021-05-08.txt"
    data_file="C:/Users/sunyyao/Desktop/NanGuo/xgb_model/data/2021-05-12#2021-05-12.txt"
    cnf = configparser.ConfigParser()
    cnf.read("feature_extract/feature_cfg.conf")
    perfix_feature_names = cnf.get('prefix_feature', 'feature_names')
    perfix_feature_names = perfix_feature_names.split(',')
    perfix_feature_names = [x.strip() for x in perfix_feature_names]
    print("perfix_feature_names", perfix_feature_names)
    feature_names = cnf.get('evidence_feature', 'feature_names')
    feature_names=feature_names.split(",")
    feature_names=[x.strip() for x in feature_names]

    data_wraper = data_interface.DataWraper(
        src=data_file
    )
    data_gen = data_wraper.wrap_batch_data()
    # skip None
    next(data_gen)
    for main_account_data,spread_account_data in data_gen:
        deal_msg=main_account_data["deal_msg"]
        add_time = main_account_data["add_time"]
        task_create_time = datetime.datetime.strptime(add_time, TIME_FORMAT)
        evidence_feature=parse_line(
            main_account_data,
            spread_account_data,
            task_create_time=task_create_time
        )
        assert len(evidence_feature)==len(feature_names),"not match,feature_names is:%d but return is :%d"%(len(feature_names),len(evidence_feature))
        print(
            list(
                zip(feature_names,evidence_feature)
            )
        )
if __name__=="__main__":
    test()