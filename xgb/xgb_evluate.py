from os import access
from numpy.lib.arraysetops import isin
from numpy.lib.function_base import bartlett
from numpy.lib.npyio import save
import xgboost as xgb
from data_parser import load_feature
from metric_report import MetricReport
import numpy as np

import argparse
parser=argparse.ArgumentParser()

parser.add_argument("--source_file",type=str,default="")
parser.add_argument("--model_file",type=str,default="model/test.model")
# parser.add_argument("--re_fetch",type=bool,default=True)
parser.add_argument("--feature_file",type=str,default="")

args=parser.parse_args()

MODEL_PATH=args.model_file

TEST_DATA_PATH:str=args.source_file
TEST_FEATURE_PATH=args.feature_file
if TEST_DATA_PATH:
    file_prefix=TEST_DATA_PATH.rsplit('/',1)[-1].split('.')[0]
if TEST_FEATURE_PATH:
    file_prefix=TEST_FEATURE_PATH.rsplit('/',1)[-1].split('.')[0]

RE_FETCH=True

LABEL_TYPE=1
LABELS=["no_white","white"]

def save_error_predict(y_true,y_pre,account_df,save_prefix,labels=["no_white","white"]):
    '''
    only save 2 classfication task
    '''
    y_pre=[1 if item>0.5 else 0 for item in y_pre]
    if isinstance(y_pre,list):
        y_pre=np.array(y_pre)
    if isinstance(y_true,list):
        y_true=np.array(y_true)
    diff=y_true-y_pre
    #if y_ture=1 and y_pre=0 diff will be 1
    
    #if y_true=0 and y_pre=1 diff will be -1 

    black_2_white_mask=(diff==-1)
    white_2_black_mask=(diff==1)
    
    save_columns=["main_account_id","wxid"]
    black_2_white=account_df[black_2_white_mask][save_columns]
    white_2_black=account_df[white_2_black_mask][save_columns]
    
    black_2_white.to_csv(
        "error_output/%s_balck_to_white.csv"%save_prefix,
        sep=",",
        index=False
    )

    white_2_black.to_csv(
        "error_output/%s_white_2_black.csv"%save_prefix,
        sep=",",
        index=False
    )


def evaluate(model,data,account_df=None):
    y_true=data.get_label()
    xgb_model=xgb.Booster(model_file=model)
    y_=xgb_model.predict(data)
    mr=MetricReport(
        labels=LABELS
    )
    save_error_predict(
        y_true=y_true,
        y_pre=y_,
        account_df=account_df,
        save_prefix=file_prefix
    )

    mr.f1_metric(y_,y_true)


def predict(model,predict_data):
    pass

if __name__=="__main__":

    test_data_name=TEST_DATA_PATH.rsplit("/",1)[-1].rsplit(".",1)[0]
    test_feature_name="feature/%s.csv"%(test_data_name)
    
    # if not TEST_FEATURE_PATH and TEST_DATA_PATH:
    #     test_writer=open(test_feature_name,mode="w",encoding="utf-8")
    #     print("get feature from source file.....")
    #     parse_file(TEST_DATA_PATH,test_writer)
    #     test_writer.close()
    
    if  TEST_FEATURE_PATH:
        test_feature_name=TEST_FEATURE_PATH
    
    #you should specify one param:file or feature
    elif (not TEST_DATA_PATH) and (not TEST_FEATURE_PATH):
        raise ValueError("please specify valid file path!")

    account_df,test_data,_=load_feature(test_feature_name,split=False)
    evaluate(MODEL_PATH,test_data,account_df)