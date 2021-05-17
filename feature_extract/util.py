import json
from urllib.parse import unquote_plus
import logging
import re
import datetime
from math import exp, sqrt


TIME_FORMAT="%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s]: %(message)s"
)


def load_json(msg:str):
    """
    load deal msg

    Args:
    -----
    msg:string

    Returns:
    wxsafe:map
    """
    try:
        wxsafe=json.loads(msg)
        for key,value in wxsafe.items():
            if value:
                value=unquote_plus(value)
                value=json.loads(value)
            wxsafe[key]=value
    except:
        logging.error("error occured when load json msg!",exc_info=True)
        return {}
    else:
        return wxsafe
        
def text_deal(text:str):
    """
    remove the space
    """
    text = text.replace('\r', '')
    text = text.replace('\n', '')
    text = text.replace('\001', '')
    text=text.replace("🐮","牛").replace("🀄️","牌").replace("niu","牛")
    return text


def chatroom_text_deal(text:str):
    #去除非可见字符
    #替换常见表情符号
    text=text.replace("🐮","牛").replace("🀄️","牌")
    text=re.sub(
        pattern="[^\u4e00-\u9fa5,^0-9,^a-z,^A-Z]",
        repl="",
        string=text
    )
    text=re.sub(
        pattern="[一,二,三,四,五,六,七,八,九,十,0-9][年级,年][一,二,三,四,五,六,七,八,九,十,0-9][班级,班]",
        repl="班级",
        string=text
    )

    text=re.sub(
        pattern="\d?群",
        repl="",
        string=text
    )
    return text

def string_distance(string_list):
    """
    compute the cos value of strings
    """
    def _cos(v1,v2):
        assert len(v1)==len(v2),"vector should have same lenght"
        n=len(v1)
        multi=0
        v1_square=0
        v2_square=0
        for idx in range(n):
            multi+=v1[idx]*v2[idx]
            v1_square+=v1[idx]**2
            v2_square+=v2[idx]**2
        cos_value=multi/(sqrt(v1_square)*sqrt(v2_square)+1e-5)
        return cos_value

    union_char=set()
    for string in string_list:
        string_set=set(string)
        union_char=union_char|string_set
    vector_size=len(union_char)
    char_idx_map=dict(
        zip(union_char,range(vector_size))
    )
    vector_list=[]
    for string in string_list:
        vector=[0 for _ in range(vector_size)]
        for _,char in enumerate(string):
            if char in union_char:
                idx=char_idx_map[char]
                vector[idx]+=1
        vector_list.append(vector)
    n=len(vector_list)
    cos_list=[]
    for row in range(n-1):
        for col in range(row+1,n):
            v1=vector_list[row]
            v2=vector_list[col]
            cos_value=_cos(v1,v2)
            cos_list.append(cos_value)
    distance_sum=sum(cos_list)
    #如果群之间没有任何相似性，那么求和也不会影响，反而求平均会将其稀释
    return distance_sum
    
def string_distance_test():
    s=["僵尸粉检测群","僵尸粉检测","三年级二班","三年二班"]
    string_distance(s)

string_distance_test()


def gamble_pattern_detect(org):
    cnt = 0
    pattern = re.findall(
        r"[1-9|一|二|三|四|五|六|七|八|九|十][^1-9|一|二|三|四|五|六|七|八|九|十]",
        org)
    if not pattern:
        for p in pattern:
            p_re = re.findall(
                r"[1|2|3|4|5|6|7|8|9|一|二|三|四|五|六|七|八|九|十][元|毛]", p
            )
            if p_re:
                cnt += 1
    return cnt

def greeting_text_deal(text):
    text=text.replace("🐮","牛").replace("🀄️","牌").replace("niu","牛")
    text=text.upper()
    return text

def greeting_text_number_rate(text)->float:
    digit_pattern=r"\d"
    digit_list=re.findall(digit_pattern,text)
    digit_rate=len(digit_list)/(len(text)+1e-5)
    return digit_rate


def multi_unquote(msg,max_retry=3):
    while max_retry>0:
        try:
            msg=unquote_plus(msg)
            decode_msg=json.loads(msg)
            return True,decode_msg
        except json.decoder.JSONDecodeError:
            max_retry-=1
    return False,""

def decode_exposetime(exposetime):
    if isinstance(exposetime,int):
        res=datetime.datetime.fromtimestamp(exposetime)
        time_str=datetime.datetime.strftime(res,TIME_FORMAT)
        return True,res,time_str
    elif isinstance(exposetime,str):
        res=datetime.datetime.strptime(exposetime,TIME_FORMAT)
        return True,res,exposetime
    else:
        return False,""
