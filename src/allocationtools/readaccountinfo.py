# -*- coding: cp936 -*-
import pandas as pd
from qpython import qconnection
import numpy as np
import os
def int_to_code(i):
    return '0' * (6 - len(str(i))) + str(i)

def float_to_100int(f):
    return int(f)/100*100

def add2kdb(data):
    q = qconnection.QConnection(host="127.0.0.1", port=5010, pandas=True)
    q.open()
    print(data)
    print(data.dtypes)
    q('upsert', np.string_("account"), data)
    q.close()

if __name__ == "__main__":
    date='20160629'
    pd.options.mode.chained_assignment = None  # default='warn' 关闭警告log
    rootdir = './'+date
    #rootdir = 'D:/github/tools/src/summarytools/bug'
    for parent,dirnames,filenames in os.walk(rootdir):
        fp=None
        for filename in filenames:
            print('reading '+filename)
            pdtemp=pd.read_csv(rootdir+'/'+filename,encoding='gb2312',skiprows=1)
            if fp is not None:
                fp.append(pdtemp)
            else:
                fp=pdtemp

    #fp=pd.read_csv('D:/股票分配表_0628.csv',encoding='gb2312')
    print(fp)
    fp = fp.drop(fp.columns[[1, 3, 4, 5]], axis=1)
    fp = fp.set_index([fp.columns[0], fp.columns[1]])
    fpstack = fp.stack()
    print(fpstack)
    account_tmp = fpstack.reset_index()
    account_tmp = account_tmp.rename(columns={"level_2": "sym", 0: "amount"})
    account_tmp['stockcode'] = account_tmp['stockcode'].map(int_to_code)
    account_tmp['amount'] = account_tmp['amount'].map(float_to_100int)
    account_tmp['amount'] = account_tmp['amount'].astype('int')
    print(account_tmp)
    account_tmp.to_csv('./'+date+'/股票分配_'+date+'_汇总.csv')
    add2kdb(account_tmp)