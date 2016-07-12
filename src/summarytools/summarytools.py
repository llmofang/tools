# -*- coding: cp936 -*-
import pandas as pd
import math

def int_to_code(i):
    code = str(int(i))
    if len(code) < 6:
        code = '0' * (6 - len(code)) + code
    return '="' + code + '"'

def changeTime(allTime):
    day = 24*60*60
    hour = 60*60
    min = 60
    if allTime <60:
        if allTime<10:
            return "0%d"%math.ceil(allTime)
        else:
            return "%d"%math.ceil(allTime)
    # elif  allTime > day:
    #     days = divmod(allTime,day)
    #     return "%d天%s"%(int(days[0]),changeTime(days[1]))
    elif allTime > hour:
        hours = divmod(allTime,hour)
        if hours[0]<10:
            return '0%d:%s'%(int(hours[0]),changeTime(hours[1]))
        else:
            return '%d:%s'%(int(hours[0]),changeTime(hours[1]))
    else:
        mins = divmod(allTime,min)
        if mins[0]<10:
            return "0%d:%s"%(int(mins[0]),changeTime(mins[1]))
        else:
            return "%d:%s"%(int(mins[0]),changeTime(mins[1]))


def sec2timeInDay(seconds):
    timestr=changeTime(seconds)
    if len(timestr)==5:
        timestr='00:'+timestr
    if len(timestr)==2:
        timestr='00:00:'+timestr
    return timestr

def price_gap(row):
    if (row['open_num'] > 0) and (row['close_num'] < 0):
        gap = row['close_price'] - row['open_price']
    elif (row['open_num'] < 0) and (row['close_num'] > 0):
        gap = row['open_price'] - row['close_price']
    else:
        gap = 0

    # 扣除手续费
    gap = gap - row['close_price'] * 0.0013 - row['open_price'] * 0.0003
    return gap


def accuracy(row):
    return 'T' if row['price_gap'] > 0 else 'F'


def gap_to_fen(gap):
    # gap转发为分
    gap = int(gap * 100)
    return gap


def amount(row):
    return row['open_price'] * abs(row['open_num']) + row['close_price'] * abs(row['close_num'])


def profit(row):
    num = min(abs(row['open_num']), abs(row['close_num']))
    return num * row['price_gap']


def productivity(row):
    return 2 * 1000 * row['profit'] / row['amount']


def hold_time(row):
    delta = row['close_time'] - row['open_time']
    # minutes = delta.seconds / 60
    # seconds = delta.seconds - minutes * 60
    # return "%d:%d" % (minutes, seconds)
    return sec2timeInDay(delta.seconds)


def format_datetime(dt):
    return "%d:%d:%d" % (int(dt.hour), int(dt.minute), int(dt.second))


def format_float(f):
    return "%.1f" % f



def measure(file_in, file_out):
    entrust_df = pd.read_csv(file_in,encoding='gb2312')
    entrust_df=entrust_df.dropna(how='all')
    if not entrust_df.columns.values[0]=='时间':
        print('error 文件抬头错误 '+file_in)
        raise SystemExit
    entrust_df = entrust_df.rename(columns={entrust_df.columns[0]: "time", entrust_df.columns[1]: "entrust_no",
                                            entrust_df.columns[2]: "code", entrust_df.columns[3]: "stock_name",
                                            entrust_df.columns[4]: "price", entrust_df.columns[5]: "num",
                                            entrust_df.columns[6]: "deal_price", entrust_df.columns[7]: "deal_num",
                                            entrust_df.columns[8]: "withdraw", entrust_df.columns[9]: "status"})

    entrust_df = entrust_df[entrust_df['deal_num'] != 0]
    entrust_df[entrust_df.columns[0]] = pd.to_datetime(entrust_df[entrust_df.columns[0]])
    entrust_df = entrust_df.sort_values(by=['time'], ascending=True)

    entrust_pair_df = pd.DataFrame(columns=['stock_name', 'code', 'open_time', 'open_price', 'open_num',
                                            'close_time', 'close_price', 'close_num'])

    for i, row in entrust_df.iterrows():
        unfinished = entrust_pair_df[(entrust_pair_df['stock_name'] == row.stock_name) & (entrust_pair_df['close_price'] == 0) &
                                     (entrust_pair_df['open_num'] * row.deal_num < 0)]
        if len(unfinished) == 0:
            entrust_pair_df.loc[len(entrust_pair_df)] = [row.stock_name, row.code, row.time, row.deal_price,
                                                         row.deal_num, row.time, 0, 0]
        else:
            for j, unfinished_row in unfinished.iterrows():
                if abs(entrust_df.loc[i, "deal_num"]) >= 100:
                    unfinished.loc[j, "close_time"] = row.time
                    unfinished.loc[j, "close_price"] = row.deal_price
                    if abs(unfinished_row.open_num) > abs(entrust_df.loc[i, "deal_num"]):
                        entrust_pair_df.loc[len(entrust_pair_df)] = [unfinished_row.stock_name, unfinished_row.code,
                                                                     unfinished_row.open_time,
                                                                     unfinished_row.open_price,
                                                                     unfinished_row.open_num + entrust_df.loc[
                                                                         i, "deal_num"],
                                                                     unfinished_row.open_time, 0, 0]
                        unfinished.loc[j, "open_num"] = - entrust_df.loc[i, "deal_num"]
                        unfinished.loc[j, "close_num"] = entrust_df.loc[i, "deal_num"]
                        entrust_df.loc[i, "deal_num"] = 0
                    else:
                        unfinished.loc[j, "close_num"] = - unfinished_row.open_num
                        entrust_df.loc[i, "deal_num"] = entrust_df.loc[i, "deal_num"] - unfinished.loc[j, "close_num"]
                else:
                    break
            if abs(entrust_df.loc[i, "deal_num"]) >= 100:
                entrust_pair_df.loc[len(entrust_pair_df)] = [row.stock_name, row.code, row.time, row.deal_price,
                                                             entrust_df.loc[i, "deal_num"], row.time, 0, 0]
        entrust_pair_df.update(unfinished)

    entrust_pair_df['code'] = entrust_pair_df['code'].map(int_to_code)
    entrust_pair_df['hold_time'] = entrust_pair_df.apply(hold_time, axis=1)
    # format datetime
    entrust_pair_df['open_time'] = entrust_pair_df['open_time'].map(format_datetime)
    entrust_pair_df['close_time'] = entrust_pair_df['close_time'].map(format_datetime)

    entrust_pair_df['accuracy'] = 0
    entrust_pair_df['price_gap'] = entrust_pair_df.apply(price_gap, axis=1)
    entrust_pair_df['accuracy'] = entrust_pair_df.apply(accuracy, axis=1)
    entrust_pair_df['profit'] = entrust_pair_df.apply(profit, axis=1)
    entrust_pair_df['price_gap'] = entrust_pair_df['price_gap'].map(gap_to_fen)
    entrust_pair_df['amount'] = entrust_pair_df.apply(amount, axis=1)

    entrust_pair_df['productivity'] = entrust_pair_df.apply(productivity, axis=1)
    sum_profit = entrust_pair_df['profit'].sum()
    sum_amount = entrust_pair_df['amount'].sum()
    win = entrust_pair_df[entrust_pair_df['accuracy'] == 'T']
    gain_ration = win['accuracy'].count() * 1.0 / entrust_pair_df['accuracy'].count()
    length = len(entrust_pair_df)
    entrust_pair_df.loc[length, 'stock_name'] = '汇总'
    entrust_pair_df.loc[length, 'profit'] = sum_profit
    entrust_pair_df.loc[length, 'amount'] = sum_amount
    entrust_pair_df.loc[length, 'accuracy'] = '%.2f' % (gain_ration * 100)
    entrust_pair_df.loc[length, 'productivity'] = 1000 * 2 * sum_profit / sum_amount

    entrust_pair_df['profit'] = entrust_pair_df['profit'].map(format_float)
    entrust_pair_df['amount'] = entrust_pair_df['amount'].map(format_float)
    entrust_pair_df['productivity'] = entrust_pair_df['productivity'].map(format_float)

    zh_df = entrust_pair_df.rename(columns={'stock_name': '股票名称', 'code': '股票代码', 'open_time': '开仓时间',
                                            'open_price': '开仓价格', 'open_num': '开仓数量', 'close_time': '平仓时间',
                                            'close_price': '平仓价格', 'close_num': '平仓数量', 'hold_time': '持仓时间',
                                            'accuracy': '正确率', 'price_gap': '价差', 'profit': '盈利', 'amount': '成交额',
                                            'productivity': '利用率'})

    zh_df.to_csv(file_out, index=False)
    data= entrust_pair_df[-1:].values[0]
    return [float(data[9]),float(data[11]),float(data[12]),float(data[13])]


def group_summary(group):
    group.loc[-1,'brokerage']='汇总'
    group.loc[-1,'accuracy']=group['accuracy'].sum()
    group.loc[-1,'profit']=group['profit'].sum()
    group.loc[-1,'amount']=group['amount'].sum()
    group.loc[-1,'productivity']=group['productivity'].sum()
    group=group.rename(columns={'brokerage':'券商','account':'账户','user':'交易员','date':'日期','format':'格式','accuracy':'正确率','profit':'盈利','amount':'成交额','productivity': '利用率'})
    del group['格式']
    return group


import os
import os.path
if __name__ == "__main__":

    #xxx = measure('./原始记录/0523/刘一奇_20160523.csv', './统计/0523/刘一奇_20160523.csv')
    #print(xxx)
    pd.options.mode.chained_assignment = None  # default='warn' 关闭警告log
    rootdir = 'D:/github/tools/src/summarytools/20160524'
    #rootdir = 'D:/github/tools/src/summarytools/bug'
    summarydir='/汇总'
    print('————个人统计—————')
    for parent,dirnames,filenames in os.walk(rootdir):

        if  parent==rootdir:
            fileInfoArr=[]
            date=None
            if not os.path.exists(rootdir+summarydir):
                    os.makedirs(rootdir+summarydir)
            for filename in filenames:
                print('converting  '+filename)
                fullFileName=os.path.join(parent,filename)
                filenameArr=filename.split('_')
                if not len(filenameArr)==4:
                    print('error 文件名格式错误   '+filename)
                    raise SystemExit

                fileInfo=filenameArr[:-1]+filenameArr[-1].split('.')
                date=fileInfo[-2]
                #print(filenameArr)
                rtdata=measure(fullFileName,rootdir+summarydir+'/'+filename)
                fileInfo.extend(rtdata)
                fileInfoArr.append(fileInfo)
            print('————账户汇总—————')
            gatherDF=pd.DataFrame(fileInfoArr,columns=['brokerage','account','user','date','format','accuracy','profit','amount','productivity'])
            gatherDFgyAccount=gatherDF.groupby(['account'])
            accoutsummary=None
            for name,group in gatherDFgyAccount:
                group=group_summary(group)
                group.to_csv(rootdir+summarydir+'/'+name+'_'+date+'_账户汇总.csv',index=False)
                if accoutsummary is None:
                    accoutsummary=group
                else:
                    accoutsummary=accoutsummary.append(group)

            accoutsummary.to_csv(rootdir+summarydir+'/'+date+'_账户汇总.csv',index=False)
            #个人分开汇总
            # gatherDFgyUser=gatherDF.groupby(['user'])``
            # for name,group in gatherDFgyUser:
            #     group=group_summary(group)
            #     group.to_csv(rootdir+'/process/'+name+'_汇总.csv',index=False)
            print('————个人汇总—————')
            gatherDF=gatherDF.sort_values(by='profit')
            gatherDF=gatherDF.rename(columns={'brokerage':'券商','account':'账户','user':'交易员','date':'日期','format':'格式','accuracy':'正确率','profit':'盈利','amount':'成交额','productivity': '利用率'})
            del gatherDF['格式']
            gatherDF.to_csv(rootdir+summarydir+'/'+date+'_个人汇总.csv',index=False)
    print('————执行完成—————')


                

