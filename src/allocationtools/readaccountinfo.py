# -*- coding: cp936 -*-
import pandas as pd
from qpython import qconnection
import numpy as np
import os
def int_to_code(i):
    return '0' * (6 - len(str(int(i)))) + str(int(i))

def float_to_100int(f):
    return int(f)/100*100

def add2kdb(data):
    q = qconnection.QConnection(host="139.224.9.75", port=52800, pandas=True)
    #q = qconnection.QConnection(host="127.0.0.1", port=5010, pandas=True)
    q.open()
    print(data)
    q('upsert', np.string_("account"), data)
    q.close()

if __name__ == "__main__":
    date='20160711'
    pd.options.mode.chained_assignment = None  # default='warn' 关闭警告log
    rootdir = './'+date+'/'
    summarydir='汇总'
    fp=None

    if(os.path.isdir(rootdir)):
        if not os.path.exists(rootdir+summarydir):
            os.makedirs(rootdir+summarydir)
        for parent,dirnames,filenames in os.walk(rootdir):
            if  parent==rootdir:
                for filename in filenames:
                    print('reading '+filename)
                    pdtemp=pd.read_csv(rootdir+filename,encoding='gb2312',skiprows=1)
                    pdtemp=(pdtemp.dropna(how='all')).T.dropna(how='all').T
                    if fp is not None:
                        fp=fp.append(pdtemp)
                    else:
                        fp=pdtemp
    else:
        fp=pd.read_csv(rootdir,encoding='gb2312',skiprows=1)
        fp=(fp.dropna(how='all')).T.dropna(how='all').T
    #print(fp)
    fp = fp.drop(labels=['stockname','available_num','allocated_num','unalocated_num'],axis=1)
    fp = fp.set_index(keys=["accountname","stockcode"])
    fpstack = fp.stack()
    account_tmp = fpstack.reset_index()
    account_tmp = account_tmp.rename(columns={"level_2": "sym", 0: "amount"})
    account_tmp['stockcode'] = account_tmp['stockcode'].map(int_to_code)
    account_tmp['amount'] = account_tmp['amount'].map(float_to_100int)
    account_tmp['amount'] = account_tmp['amount'].astype('int')
    if(os.path.isdir(rootdir)):
        account_tmp.to_csv('./'+date+'/汇总/股票分配_'+date+'_汇总.csv',index=False)
        acc=account_tmp[['accountname','stockcode','sym']].duplicated()
        if(acc[acc==True].index.values.size!=0):
            print('重复数据编号：',acc[acc==True].index.values)
            exit()
    add2kdb(account_tmp)