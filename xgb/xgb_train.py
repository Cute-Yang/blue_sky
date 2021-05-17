from data_parser import Parser
import xgboost as xgb
import numpy as np
from metric_report import MetricReport
import argparse

parser=argparse.ArgumentParser()
parser.add_argument("--task_type",type=int,default=1)
parser.add_argument("--feature_file",type=str,default="data/feature_v1.csv")
args=parser.parse_args()

task_type=args.task_type
feature_file=args.feature_file
# task_type=3  #can be 1 2 3
parser=Parser()
feature_df, dtrain, dtest = parser.load_features(feature_file,label_type=task_type)
if task_type==1:
    LABELS = ["no_white","white"]

elif task_type==2:
    LABELS=["white","gray","black"]

elif task_type==3:
    LABELS=["white","light_gray","heavy_gray","light_black","heavy_black"]

#模型训练部分解耦


# 自定义损失函数,希望能够缓解正负样本不平衡的问题,logistic版本的focal_loss
def focal_loss(p, dtrain,gamma=1,alpha=0.5):
    y = dtrain.get_label()
    p = 1.0 / (1.0 + np.exp(-p))#转换成为向量
    grad = p * (1 - p) * (alpha * gamma * y * (1 - p) ** gamma * np.log(p) / (1 - p) - alpha * y * (
        1 - p) ** gamma / p - gamma * p ** gamma * (1 - alpha) * (1 - y) * np.log(1 - p) / p + p ** gamma * (
        1 - alpha) * (1 - y) / (1 - p))
    hess = p * (1 - p) * (p * (1 - p) * (
        -alpha * gamma ** 2 * y * (1 - p) ** gamma * np.log(p) / (1 - p) ** 2 + alpha * gamma * y * (
            1 - p) ** gamma * np.log(p) / (1 - p) ** 2 + 2 * alpha * gamma * y * (1 - p) ** gamma / (
            p * (1 - p)) + alpha * y * (1 - p) ** gamma / p ** 2 - gamma ** 2 * p ** gamma * (
            1 - alpha) * (1 - y) * np.log(1 - p) / p ** 2 + 2 * gamma * p ** gamma * (1 - alpha) * (
            1 - y) / (p * (1 - p)) + gamma * p ** gamma * (1 - alpha) * (1 - y) * np.log(
            1 - p) / p ** 2 + p ** gamma * (1 - alpha) * (1 - y) / (1 - p) ** 2) - p * (
        alpha * gamma * y * (1 - p) ** gamma * np.log(p) / (1 - p) - alpha * y * (
            1 - p) ** gamma / p - gamma * p ** gamma * (1 - alpha) * (1 - y) * np.log(
            1 - p) / p + p ** gamma * (1 - alpha) * (1 - y) / (1 - p)) + (1 - p) * (
        alpha * gamma * y * (1 - p) ** gamma * np.log(p) / (1 - p) - alpha * y * (
            1 - p) ** gamma / p - gamma * p ** gamma * (1 - alpha) * (1 - y) * np.log(
            1 - p) / p + p ** gamma * (1 - alpha) * (1 - y) / (1 - p)))
    return grad, hess


#对于xgboost 需要返回梯度和hess矩阵
#用于调整gamma参数和alpha参数
#alpha参数取值跟正负样本比例有关
#这里0表示no_white 1表示white
#这个alpha作用在1标签上,具体取值根据正负样本的比例而定
focal_obj=lambda p,dtrain:focal_loss(p,dtrain,2,0.25)

def predict(xgb_model, X):
    output = xgb_model.predict(X)
    return output

def train(task_typ):
    '''
    class_number:number of classfication,if 2,use logistic,else:use softmax
    '''
    class_number=len(LABELS)
    if class_number==2:
        objective="binary:logistic"

    elif class_number>2:
        objective="multi:softmax"
    
    if class_number==2:
        train_params = {
            "objective": objective,
            "eta": 0.01,
            "max_depth": 6,
            "colsample_bytree": 0.6,
            "min_child_weight": 3,
            "eval_metric": ["auc"],
            "nthread": 20,
            "num_parallel_tree": 10,
            "eval_set": [(dtest, "test set")]
            # "num_class":class_number
        }


        model = xgb.train(
            params=train_params,
            dtrain=dtrain,
            num_boost_round=2000,
            evals=[(dtrain, "train_set"), (dtest, "test_set")],
            early_stopping_rounds=500,
            obj=focal_obj
        )

    elif class_number>2:
        train_params = {
            "objective": objective,
            "eta": 0.01,
            "max_depth": 6,
            "colsample_bytree": 0.6,
            "min_child_weight": 3,
            "eval_metric": ["auc"],
            "nthread": 20,
            "num_parallel_tree": 10,
            "eval_set": [(dtest, "test set")],
            "num_class":class_number
        }


        model = xgb.train(
            params=train_params,
            dtrain=dtrain,
            num_boost_round=2000,
            evals=[(dtrain, "train_set"), (dtest, "test_set")],
            early_stopping_rounds=500,
    )
    mr=MetricReport(labels=LABELS)

    model_name="xgb_classfication_%s.model"%class_number
    model.save_model("model/%s"%model_name)    
    probs=predict(model,dtest)
    mr.f1_metric(probs,dtest.get_label(),objective)
if __name__ == "__main__":
    train(task_type)


'''
grad:
p*(1 - p)*(alpha*gamma*y*(1 - p)**gamma*log(p)/(1 - p) - alpha*y*(1 - p)**gamma/p - gamma*p**gamma*(1 - alpha)*(1 - y)*log(1 - p)/p + p**gamma*(1 - alpha)*(1 - y)/(1 - p))
hess:
p*(1 - p)*(p*(1 - p)*(-alpha*gamma**2*y*(1 - p)**gamma*log(p)/(1 - p)**2 + alpha*gamma*y*(1 - p)**gamma*log(p)/(1 - p)**2 + 2*alpha*gamma*y*(1 - p)**gamma/(p*(1 - p)) + alpha*y*(1 - p)**gamma/p**2 - gamma**2*p**gamma*(1 - alpha)*(1 - y)*log(1 - p)/p**2 + 2*gamma*p**gamma*(1 - alpha)*(1 - y)/(p*(1 - p)) + gamma*p**gamma*(1 - alpha)*(1 - y)*log(1 - p)/p**2 + p**gamma*(1 - alpha)*(1 - y)/(1 - p)**2) - p*(alpha*gamma*y*(1 - p)**gamma*log(p)/(1 - p) - alpha*y*(1 - p)**gamma/p - gamma*p**gamma*(1 - alpha)*(1 - y)*log(1 - p)/p + p**gamma*(1 - alpha)*(1 - y)/(1 - p)) + (1 - p)*(alpha*gamma*y*(1 - p)**gamma*log(p)/(1 - p) - alpha*y*(1 - p)**gamma/p - gamma*p**gamma*(1 - alpha)*(1 - y)*log(1 - p)/p + p**gamma*(1 - alpha)*(1 - y)/(1 - p)))
'''