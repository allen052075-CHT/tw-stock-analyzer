# logic.py
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_stock_data(stock_id, token=None):
    """從 FinMind 抓取數據並計算河流圖數據"""
    try:
        # 設定抓取 5 年數據
        days = 365 * 5
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        url = "https://api.finmindtrade.com/api/v4/data"
        
        # 1. 抓股價
        params_price = {
            "dataset": "TaiwanStockPrice",
            "data_id": stock_id,
            "start_date": start_date,
            "token": token
        }
        res_price = requests.get(url, params=params_price)
        df_price = pd.DataFrame(res_price.json()['data'])
        
        # 2. 抓本益比
        params_per = {
            "dataset": "TaiwanStockPER",
            "data_id": stock_id,
            "start_date": start_date,
            "token": token
        }
        res_per = requests.get(url, params=params_per)
        df_per = pd.DataFrame(res_per.json()['data'])
        
        if df_price.empty or df_per.empty:
            return None

        # 整理數據
        df_price['date'] = pd.to_datetime(df_price['date'])
        df_per['date'] = pd.to_datetime(df_per['date'])
        
        # 合併
        df = pd.merge(df_price[['date', 'close_price']], 
                      df_per[['date', 'PER', 'PBR']], 
                      on='date', how='inner')
        
        # 計算 EPS (Price / PER)
        df['eps'] = df.apply(lambda x: x['close_price'] / x['PER'] if x['PER'] > 0 else 0, axis=1)
        
        return df
    except Exception as e:
        print(f"Error: {e}")
        return None

def calculate_river(df):
    """計算河流圖的統計數據"""
    window = 240 * 3  # 3年滾動平均
    
    df['pe_mean'] = df['PER'].rolling(window=window, min_periods=200).mean()
    df['pe_std'] = df['PER'].rolling(window=window, min_periods=200).std()
    
    # 計算各個位階的價格
    eps = df['eps']
    mean = df['pe_mean']
    std = df['pe_std']
    
    df['river_high_2sd'] = eps * (mean + 2 * std)
    df['river_high_1sd'] = eps * (mean + 1 * std)
    df['river_mean']     = eps * mean
    df['river_low_1sd']  = eps * (mean - 1 * std)
    df['river_low_2sd']  = eps * (mean - 2 * std)
    
    return df
