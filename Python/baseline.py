# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import datetime
import pandas as pd
import gbdt_lr_train 

# 1. 类目列表特征
listItem = ['item_category_list','item_property_list']

# 2. 类别特征
singleIntItem = ['item_id','item_city_id','item_price_level','item_sales_level','item_collected_level','item_pv_level','item_brand_id']
singleIntUser = ['user_gender_id','user_age_level','user_occupation_id','user_star_level']
singleIntContext = ['context_page_id']
singleIntShop = ['shop_id','shop_review_num_level','shop_star_level']
singleIntFeature = singleIntItem + singleIntUser + singleIntContext + singleIntShop

# 3. 连续型特征
singleDoubleShop = ['shop_review_positive_rate','shop_score_service','shop_score_delivery','shop_score_description']
singleDoubleShopDispersed = ['shop_review_positive_rate_dispersed','shop_score_service_dispersed','shop_score_delivery_dispersed','shop_score_description_dispersed']

# 4. ID列表
idList = ['instance_id','item_id','user_id','context_id','shop_id' ]

# 5. 目前还未用到的特征
unsureList = ['predict_category_property']

# 5 train label标记
label = ['isTrain', 'is_trade']

# time
timeFeature = ['context_timestamp','time','time_real']

def convert_time(data):
    data['time'] = pd.to_datetime(data.context_timestamp, unit='s')
    # 对时间进行偏移 +8h
    data['time_real'] = data['time'].apply(lambda x: x + datetime.timedelta(hours=8))
    data['day'] = data['time_real'].apply(lambda x: int(str(x)[8:10]))
    data['hour'] = data['time_real'].apply(lambda x: int(str(x)[11:13]))
    # user_id join day
    user_query_day = data.groupby(['user_id', 'day']).size(
    ).reset_index().rename(columns={0: 'user_query_day'})
    data = pd.merge(data, user_query_day, 'left', on=['user_id', 'day'])
    # user_id join day hour
    user_query_day_hour = data.groupby(['user_id', 'day', 'hour']).size().reset_index().rename(
        columns={0: 'user_query_day_hour'})
    data = pd.merge(data, user_query_day_hour, 'left',
                    on=['user_id', 'day', 'hour'])

    return data

def base_process(data):

    data['len_item_category'] = data['item_category_list'].map(lambda x: len(str(x).split(';')))
    data['len_item_property'] = data['item_property_list'].map(lambda x: len(str(x).split(';')))    
    data['len_predict_category_property'] = data['predict_category_property'].map(lambda x: len(str(x).split(';')))
    print("  =========> Part 1!") 
    
    # one-hot
    #singleIntFeatureList = singleIntFeature + ['instance_id']
    
    # join 
    data = data.assign(A = data.user_gender_id.astype('str') + '&' + data.user_age_level.astype('str'))
    #data = data.assign(B = data.user_age_level.astype('str') + '&' + data.hour.astype('str'))
    
    # id 类型
    singleIntFeature = ['user_gender_id','user_occupation_id','A']
    singleIntFeatureList = singleIntFeature + ['instance_id','isTrain']
    category = data.loc[:,singleIntFeatureList]
    category.loc[:,singleIntFeature] = category.loc[:,singleIntFeature].astype('str')
    dfCategory = pd.get_dummies(category)
    
    # 因为测试集与训练集中 有3个instance_id重复出现
    train = pd.merge(data[data['isTrain'] == 1], dfCategory[dfCategory['isTrain'] == 1], on='instance_id')
    test = pd.merge(data[data['isTrain'] == 0], dfCategory[dfCategory['isTrain'] == 0], on='instance_id')
    data = pd.concat([train,test])
    data['isTrain'] = data['isTrain_x']
    del data['isTrain_x']
    del data['isTrain_y']
    print("  =========> Part 2!") 

    '''
    # 分箱 + one-hot
    for x in singleDoubleShop:            
        ser = data[x]            
        cats = pd.qcut(ser[ser != -1], 10, labels=[1,2,3,4])
        ser = pd.concat([cats, ser[ser == -1]]).astype('int')
        data[x+'_dispersed'] = ser
    
    singleDoubleShopDispersedList = singleDoubleShopDispersed + ['instance_id']
    category = data.loc[:,singleDoubleShopDispersedList]
    category.loc[:,singleDoubleShopDispersed] = category.loc[:,singleDoubleShopDispersed].astype('str')
    dfCategory = pd.get_dummies(category)
    data = pd.merge(data,dfCategory,on='instance_id')
    print("  =========> Part 3!") 
    '''
    
    return data 

def main(onlineFlag):
    
    path = '../Data/'
    #'item_id','user_gender_id','shop_id','user_occupation_id','item_city_id','item_brand_id',
    gbdt_features = ['item_sales_level','item_collected_level', 'item_pv_level', 'context_page_id','item_price_level',
                     'user_age_level', 'user_star_level', 'user_query_day', 'user_query_day_hour',
                     'hour', 'shop_review_num_level', 'shop_star_level','shop_review_positive_rate', 
                     'shop_score_service', 'shop_score_delivery', 'shop_score_description','len_item_category','len_item_property',
                     'len_predict_category_property','cvr','shop_cvr']#,'shop_last_day_cvr','last_day_cvr'
    
    # init lr feature
    UselessFeature = idList + singleDoubleShopDispersed + singleDoubleShop + singleIntFeature + listItem + unsureList + timeFeature + label + gbdt_features + ['isTrain_x', 'isTrain_y','A']
    
    target = ['is_trade']
    
    if onlineFlag == True:
        
        # load train
        train = pd.read_csv(path + 'round1_ijcai_18_train_20180301.txt', sep=' ')
        train.drop_duplicates(subset='instance_id')
        train['isTrain'] = 1
        
        # load test
        test = pd.read_csv('../data/round1_ijcai_18_test_a_20180301.txt', sep=' ')
        test['isTrain'] = 0
        
        print('Load data success!')
        # concat and process
        data = pd.concat([train,test])
        data = convert_time(data)
        data = base_process(data)
        print('Pre-process success!')
        
        lr_features=[x for x in data.columns if x not in UselessFeature] + ['hour']
        print(lr_features)
        
        # load history data
        item_history_cvr = pd.read_csv(path + 'features/item_id_history.csv')
        shop_history_cvr = pd.read_csv(path + 'features/shop_id_history.csv')
        print('Load history data success!')
        
        
        # merge data with history data
        trainData = pd.merge(data[data['isTrain'] == 1], item_history_cvr[item_history_cvr['isTrain'] == 1], on='instance_id')
        trainData = pd.merge(trainData[trainData['isTrain_y'] == 1], shop_history_cvr[shop_history_cvr['isTrain'] == 1], on='instance_id')
        
        testData = pd.merge(data[data['isTrain'] == 0], item_history_cvr[item_history_cvr['isTrain'] == 0], on='instance_id')
        testData = pd.merge(testData[testData['isTrain_y'] == 0], shop_history_cvr[shop_history_cvr['isTrain'] == 0], on='instance_id')
        print(len(testData))
        print('Merge history data success!')
        
        gbdt_lr_train.gbdt_lr_train(trainData,testData,gbdt_features,lr_features,target,'with_history_cvr',True)
        
    else:
        
        # load train
        data = pd.read_csv(path + 'round1_ijcai_18_train_20180301.txt', sep=' ')
        data['isTrain'] = 1
        print('Load data success!')
        
        # process data
        data.drop_duplicates(subset='instance_id')
        data = convert_time(data)
        data = base_process(data)
        print('Pre-process success!')
        
        # load history data
        item_history_cvr = pd.read_csv(path + 'features/item_id_history.csv')
        shop_history_cvr = pd.read_csv(path + 'features/shop_id_history.csv')
        print('Load history data success!') 
        
        # merge data with history data
        data = pd.merge(data, item_history_cvr[item_history_cvr['isTrain'] == 1], on='instance_id')
        data = pd.merge(data, shop_history_cvr[shop_history_cvr['isTrain'] == 1], on='instance_id')
        print('Merge history data success!')  
        
        lr_features=[x for x in data.columns if x not in UselessFeature] + ['hour']
        print(lr_features)
        
        # split train and validate data
        train = data.loc[data.day < 24]  # 18,19,20,21,22,23
        test = data.loc[data.day == 24]  # 暂时先使用第24天作为验证集
        
        # train
        gbdt_lr_train.gbdt_lr_train(train,test,gbdt_features,lr_features,target,'',False)
            

if __name__ == "__main__":
    
    online = True # 这里用来标记是 线下验证 还是 在线提交
    main(online)
        

