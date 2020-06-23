import pandas as pd
import os
import numpy as np
import random
import math 
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score,f1_score,recall_score
from sklearn.model_selection import KFold, RepeatedKFold, RepeatedStratifiedKFold, StratifiedKFold
from collections import Counter,defaultdict
from funs_balance import random_upsample_balance
from sklearn import svm
from sklearn.linear_model import LogisticRegression
from funs_common import *
import sys
from sklearn.preprocessing import OneHotEncoder



def read_coincide_types_dataset(path="./"):
    dataset = pd.read_csv(os.path.join(path, 'coincideTypes.csv'))
    treat_dataset = read_treat_dataset()
    return pd.merge(treat_dataset, dataset)

def drop_na(d, field):
    return d.loc[d[field].notna()]

def read_pam_types_cat_dataset():    
    coincide_types_dataset = read_coincide_types_dataset()
    print(list(coincide_types_dataset))
    keep = coincide_types_dataset[["patient_ID", "study", 'pCR', 'RFS', 'DFS','radio','surgery','chemo','hormone', 'posOutcome']]
    return pd.concat([keep, pd.get_dummies(coincide_types_dataset["pam_name"])], axis=1) 
    

def calc_results_simple(X_train, X_test, y_train, y_test, clf):
    clf.fit(X_train,y_train)
    y_pred  = clf.predict(X_test)
    acc = np.mean(y_test == y_pred)
    
#    y_pred_prob = clf.predict_proba(X_test)[:,1]
#    assert clf.classes_[1] == 1
#    recall_0 =  recall_score(y_test, y_pred, pos_label=0)
#    recall_1 =  recall_score(y_test, y_pred, pos_label=1)    
#    auc = roc_auc_score(y_test, y_pred_prob)
    
    return (acc,)

def calc_results_simple_fold(X, y, train_index, test_index, clf):
    X_train, X_test = X[train_index], X[test_index]
    y_train, y_test = y[train_index], y[test_index]
    return calc_results_simple(X_train, X_test, y_train, y_test, clf)

def y_to_int(y):
    ydict = {s:i for i,s in (enumerate(set(y)))}
    return np.array([ydict[yi] for yi in y])
                
def print_rez_for_mike_dataset(mike_dataset):
    notrea_dataset =drop_trea(mike_dataset)

    X,y     = prepare_full_dataset(notrea_dataset, y_field = 'study')

    y = y_to_int(y)
    #    print(X_full.shape, X_notrea.shape)

    kf = StratifiedKFold(n_splits=5, shuffle=True)
    print_order = ["notrea_xgboost", "notrea_svm", "notrea_logi"]
    max_len_order = max(map(len,print_order))
    
    rez = defaultdict(list)
    for i, (train_index, test_index) in enumerate(kf.split(X, y)):
        print("split ", i)
        rez["notrea_xgboost"].append(calc_results_simple_fold(X, y, train_index, test_index, XGBClassifier()))
        rez["notrea_svm"].append(   calc_results_simple_fold(X, y, train_index, test_index, svm.SVC()))
        rez["notrea_logi"].append(   calc_results_simple_fold(X, y, train_index, test_index, LogisticRegression(max_iter=10000)))
        
        for order in print_order:
            print(order, " "*(max_len_order - len(order)), ": ", list_to_4g_str(rez[order][-1]))
        print ("")
        sys.stdout.flush()
        
    for order in print_order:
        print("==> ", order, " "*(max_len_order - len(order)), ": ", list_to_4g_str(np.mean(rez[order], axis=0)))
    

print("==> original mike dataset:")
print_rez_for_mike_dataset(read_mike_dataset())

print("")
print("")
print("==> combat dataset:")
print_rez_for_mike_dataset(read_combat_dataset())
