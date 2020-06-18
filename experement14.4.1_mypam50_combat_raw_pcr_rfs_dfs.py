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


def full_dataset2pam50_raw_dataset(full_dataset, path = "./"):
    pam50centroids = pd.read_csv(os.path.join(path, 'pam50centroids.csv'))
    types = list(pam50centroids)
    types.remove("geneSymbol")
    centroids = defaultdict(list)
    all_present_fields = set(full_dataset)
    for _, row_full in full_dataset.iterrows():
        centroids["patient_ID"].append(row_full["patient_ID"])
        for t in types:
            to_sum = [row_full[row_pam50c["geneSymbol"]] * row_pam50c[t] for _,row_pam50c in pam50centroids.iterrows() if row_pam50c[t] in all_present_fields]
            centroids[t].append(np.nansum(to_sum))
    
            
    centroids_pd =  pd.DataFrame(centroids)
    keep = ["patient_ID", "study", 'pCR', 'RFS', 'DFS','radio','surgery','chemo','hormone', 'posOutcome']
    return pd.merge(full_dataset[keep], centroids_pd)
    

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
    
    y_pred_prob = clf.predict_proba(X_test)[:,1]
    assert clf.classes_[1] == 1
    recall_0 =  recall_score(y_test, y_pred, pos_label=0)
    recall_1 =  recall_score(y_test, y_pred, pos_label=1)    
    auc = roc_auc_score(y_test, y_pred_prob)
    
    return acc, recall_0, recall_1, auc

def calc_results_simple_fold(X, y, train_index, test_index, clf):
    X_train, X_test = X[train_index], X[test_index]
    y_train, y_test = y[train_index], y[test_index]
    return calc_results_simple(X_train, X_test, y_train, y_test, clf)

def print_results_for_field(dataset, field):
    
    dataset = drop_na(dataset, field)
    notrea_dataset =drop_trea(dataset)


    X_full, y_full = prepare_full_dataset(dataset, y_field = field)
    X_notrea,_     = prepare_full_dataset(notrea_dataset, y_field = field)

    print(X_full.shape, X_notrea.shape)

    kf = StratifiedKFold(n_splits=5, shuffle=True)
    print_order = ["full_xgboost", "full_logi", "notrea_xgboost", "notrea_logi"]
    max_len_order = max(map(len,print_order))
    
    rez = defaultdict(list)
    for i, (train_index, test_index) in enumerate(kf.split(X_full, y_full)):
        print("split ", i)
        rez["full_xgboost"].append(calc_results_simple_fold(X_full, y_full, train_index, test_index, XGBClassifier()))
        rez["full_logi"].append(   calc_results_simple_fold(X_full, y_full, train_index, test_index, LogisticRegression(max_iter=1000)))
        rez["notrea_xgboost"].append(calc_results_simple_fold(X_notrea, y_full, train_index, test_index, XGBClassifier()))
        rez["notrea_logi"].append(   calc_results_simple_fold(X_notrea, y_full, train_index, test_index, LogisticRegression(max_iter=1000)))
        
        for order in print_order:
            print(order, " "*(max_len_order - len(order)), ": ", list_to_4g_str(rez[order][-1]))
        print ("")
    
    for order in print_order:
        print("==> ", order, " "*(max_len_order - len(order)), ": ", list_to_4g_str(np.mean(rez[order], axis=0)))
                
mike_dataset = read_combat_dataset()

pam_dataset = full_dataset2pam50_raw_dataset(mike_dataset)

print("==> pCR")
print_results_for_field(pam_dataset, "pCR")
print("")
print("")

print("==> RFS")
print_results_for_field(pam_dataset, "RFS")
print("")
print("")

print("==> DFS")
print_results_for_field(pam_dataset, "DFS")
print("")
print("")

print("==> posOutcome")
print_results_for_field(pam_dataset, "posOutcome")
print("")
print("")


