import pandas as pd
import os
import numpy as np
import random
import math 
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score,f1_score,recall_score
from sklearn.model_selection import KFold, RepeatedKFold, RepeatedStratifiedKFold
from sklearn.utils import resample
from sklearn.svm import LinearSVC
from collections import Counter,defaultdict
from sklearn.linear_model import LogisticRegression

def convert_surgery(x): 
    if (x == "mastectomy"): 
        return 1 
    if (x == "breast preserving"): 
        return 2 
    if (x == 'NA'):  
        return 0 
    raise Exception("bad surgery") 

def convert_posOutcome(x):
    if (x == '2'):
        return 1
    return int(x)

def read_treat_dataset(path="./"):
    return pd.read_csv(os.path.join(path, 'bmc15mldata1.csv'), converters=dict(surgery = convert_surgery, posOutcome = convert_posOutcome))

def read_full_dataset(path = "example15bmc"):
    datasets_fn = ["study_12093_GPL96_all-bmc15.csv.xz",
    "study_1379_GPL1223_all-bmc15.csv.xz",
    "study_16391_GPL570_all-bmc15.csv.xz",
    "study_16446_GPL570_all-bmc15.csv.xz",
    "study_17705_GPL96_JBI_Tissue_BC_Tamoxifen-bmc15.csv.xz",
    "study_17705_GPL96_MDACC_Tissue_BC_Tamoxifen-bmc15.csv.xz",
    "study_19615_GPL570_all-bmc15.csv.xz",
    "study_20181_GPL96_all-bmc15.csv.xz",
    "study_20194_GPL96_all-bmc15.csv.xz",
    "study_2034_GPL96_all-bmc15.csv.xz",
    "study_22226_GPL1708_all-bmc15.csv.xz",
    "study_22358_GPL5325_all-bmc15.csv.xz",
    "study_25055_GPL96_MDACC_M-bmc15.csv.xz",
    "study_25065_GPL96_MDACC-bmc15.csv.xz",
    "study_25065_GPL96_USO-bmc15.csv.xz",
    "study_32646_GPL570_all-bmc15.csv.xz",
    "study_9893_GPL5049_all-bmc15.csv.xz"]

    datasets = [pd.read_csv(os.path.join(path,d)) for d in datasets_fn]
    join_dataset = pd.concat(datasets, sort=False, ignore_index=True)
    
    treat_dataset = read_treat_dataset()
    return pd.merge(treat_dataset, join_dataset)

def read_oleg_dataset():
    join_dataset = pd.read_csv("ex15bmcMerged.csv")
    treat_dataset = read_treat_dataset()
    return pd.merge(treat_dataset, join_dataset)

def prepare_dataset(full_dataset, study):
    study_dataset = full_dataset.loc[full_dataset['study'] == study]
    X = study_dataset.drop(columns=['study', 'patient_ID','pCR', 'RFS', 'DFS', 'posOutcome', 'hormone','surgery', 'chemo']).to_numpy(dtype = np.float)
    y_posOutcome = study_dataset['posOutcome'].to_numpy(dtype = np.float)
    return X, y_posOutcome

def prepare_datasets(full_dataset, studies):
    Xys = [prepare_dataset(full_dataset, study ) for study in studies] 
    Xs, ys = zip(*Xys)
    return np.concatenate(Xs), np.concatenate(ys)

def _get_shuffled_study_list(full_dataset):
    all_studies = list(set(full_dataset['study']))
    random.shuffle(all_studies)
    return all_studies

def study_fold(full_dataset, shuffled_study_list, nval):
    return prepare_datasets(full_dataset, shuffled_study_list[nval:]), prepare_datasets(full_dataset, shuffled_study_list[:nval])



def calc_results_for_fold(X, y, train_index, test_index):        
    X_train, X_test = X[train_index], X[test_index]
    y_train, y_test = y[train_index], y[test_index]
    
    clf = XGBClassifier()
    clf.fit(X_train,y_train)
    
#    y_pred_prob = clf.predict_proba(X_test)[:,1]
    y_pred      = clf.predict(X_test)
    
    acc = np.mean(y_test == y_pred)
    recall_0 =  recall_score(y_test, y_pred, pos_label=0)
    recall_1 =  recall_score(y_test, y_pred, pos_label=1)
    
    return acc, recall_0, recall_1

class BiasPredictor:
    def fit(self, _, y_train):
        self.rezult = Counter(y_train).most_common(1)[0][0]
    def predict(self, X_test):
        return np.zeros(len(X_test)) + self.rezult

class BiasPredictor2:
    def fit(self, X_train, y_train):
        self.c = Counter(zip(X_train[:,0], y_train))
#        for t in [0,1]:
#            N0 = c[(t,0)]
#            N1 = c[(t,1)]
#            print(t, N0, N1, N0 / (N1 + N0), N1 / (N1 + N0))
#        exit(0)
#        self.rezult = Counter(y_train).most_common(1)[0][0]
    def predict(self, X_test):
        y_test = np.zeros(X_test.shape[0])
        
        for i,t in enumerate(X_test[:,0]):
            print(t)
            N0 = self.c[(t,0)]
            N1 = self.c[(t,1)]
            P0 = N0/(N0 + N1)
            y_test[i] = int(P0 < 0.5)
            print("P0", P0, y_test[i])
            
        return y_test

    
#def bias_predictor(y_train, test_size):
#    return np.zeros(test_size) + Counter(y_train).most_common(0)[0][0]



def calc_results_for_fold(X, y, train_index, test_index, classifer = 'xgboost'):        
    X_train, X_test = X[train_index], X[test_index]
    y_train, y_test = y[train_index], y[test_index]
        
    if (classifer == "xgboost"):
#        clf = XGBClassifier(max_depth=4)
        clf = LogisticRegression()
#        clf = LinearSVC()
    elif (classifer == "bias"):
        clf = BiasPredictor2() 
    else:
        raise Exception("bad classifer")
    clf.fit(X_train,y_train)    
    y_pred  = clf.predict(X_test)
#    print(y_test)
#    print(y_pred)
    acc = np.mean(y_test == y_pred)
    recall_0 =  recall_score(y_test, y_pred, pos_label=0)
    recall_1 =  recall_score(y_test, y_pred, pos_label=1)
    
    return acc, recall_0, recall_1

def count_to_str(y):
    c = Counter(y)
    return "count_01=%i/%i"%(c[0], c[1])

def simple_balance(X,y):
    Xsplit = defaultdict(list)
    for Xi,yi in zip(X,y):
        Xsplit[yi].append(Xi)
    
    max_len = max(len(Xyi) for _, Xyi in Xsplit.items())
    
    for yi,Xyi in list(Xsplit.items()):
        add_Xyi = random.choices(Xyi, k = max_len - len(Xyi) + 4)
        Xsplit[yi] = Xyi + add_Xyi 
    
    X_rez = []
    y_rez = []
    for yi, Xyi in Xsplit.items():
        X_rez = X_rez + Xyi
        y_rez = y_rez + [yi] * len(Xyi)
    return np.array(X_rez),np.array(y_rez)

treat_dataset = read_treat_dataset()


all_studies = list(set(treat_dataset['study']))

for study in ["study_9893_GPL5049_all-bmc15"]:
#for study in sorted(all_studies):
        
    X_trea, y_full = prepare_dataset(treat_dataset, study)
    X_trea, y_full = simple_balance(X_trea, y_full)
    print("==>", study, count_to_str(y_full))
    kf = RepeatedStratifiedKFold(n_splits=5, n_repeats=100)
    rez_trea = []
    rez_bias = []
    for i, (train_index, test_index) in enumerate(kf.split(X_trea, y_full)):
        y_train, y_test = y_full[train_index], y_full[test_index]
        
        rez_trea.append(calc_results_for_fold(X_trea, y_full, train_index, test_index))
        rez_bias.append(calc_results_for_fold(X_trea, y_full, train_index, test_index, "bias"))
        print("split: ", i, "train: ", count_to_str(y_train), "  test:", count_to_str(y_test))
        print("trea: ", *rez_trea[-1])
        print("bias: ", *rez_bias[-1])
        print("")
    print("==> mean trea:", *np.mean(rez_trea, axis=0))
    print("==> mean bias:", *np.mean(rez_bias, axis=0))
    print("")
    print("")
