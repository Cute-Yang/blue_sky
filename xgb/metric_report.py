import math
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report


class MetricReport():
    def __init__(self, labels, scale=10):
        self.labels = labels
        self.labels_size = len(self.labels)
        self.column_len = 0
        for i in range(self.labels_size):
            if len(self.labels[i]) > self.column_len:
                self.column_len = len(self.labels[i])
        self.column_len += 5

    def append_blank(self, text):
        return str(text) + " " * (self.column_len - len(str(text)))

    def print_cm(self, cm):
        confusion_matrix_str = "confusion_matrix(left labels: y_true, up labels: y_pred):\n"

        confusion_matrix_str += self.append_blank("labels")
        for i in range(self.labels_size):
            confusion_matrix_str += self.append_blank(self.labels[i])
        confusion_matrix_str += "\n" + "-" * (self.labels_size + 1) * self.column_len + "\n"
        for i in range(len(cm)):
            confusion_matrix_str += self.append_blank(self.labels[i])
            for j in range(len(cm[i])):
                confusion_matrix_str += self.append_blank(cm[i][j])
            confusion_matrix_str += "\n" + "-" * (self.labels_size + 1) * self.column_len + "\n"
        confusion_matrix_str += "\n"
        return confusion_matrix_str

    def f1_metric(self, probs, labels,objective="binary:logistic",score=0.5):
        if objective=="binary:logistic":
            pred = [1 if x >= score else 0 for x in probs]
        elif objective=="multi:softmax":  #xgboost 中已经直接返回了对应的索引最大值
            pred=probs
        print(classification_report(labels, pred))
        cm = confusion_matrix(labels, pred)
        confusion_matrix_str = self.print_cm(cm)
        print(confusion_matrix_str)

    def find_score(self, probs, labels):
        min_prob = math.floor(min(probs))
        max_prob = math.ceil(max(probs))
        scale = 1
        if min_prob >= 0 and max_prob <= 1:
            scale = 10
            min_prob = 0
            max_prob *= scale
        print("min_prob {} max_prob {} ".format(min_prob, max_prob))
        for i in range(min_prob, max_prob, 1):
            s = i / scale
            pred = [1 if x > s else 0 for x in probs]
            print("==============================[阈值是%s]=============================" % str(s))
            print(classification_report(labels, pred))
            cm = confusion_matrix(labels, pred)
            confusion_matrix_str = self.print_cm(cm)
            print(confusion_matrix_str)
