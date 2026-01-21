import akshare as ak
import pandas as pd
import os
import time
from datetime import datetime
from .config import ASSET_CODES, DATA_DIR

def fetch_data(code, start_date="20160101", end_date=None):
    """
    获取单个ETF/LOF的日线数据 (前复权)
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
        
    print(f"Fetching {code} from {start_date} to {end_date}...")
    try:
        # 尝试使用 ak.fund_etf_hist_em
        df = ak.fund_etf_hist_em(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        
        # 重命名列以统一格式
        rename_map = {
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
        }
        df = df.rename(columns=rename_map)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        df = df.sort_index()
        return df
    except Exception as e:
        print(f"Error fetching {code}: {e}")
        return None

def update_all_data():
    """
    更新所有配置资产的数据并保存到本地
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    for name, code in ASSET_CODES.items():
        file_path = os.path.join(DATA_DIR, f"{code}.csv")
        
        start_date = "20160101"
        existing_df = None
        
        # 尝试读取现有数据以进行增量更新
        if os.path.exists(file_path):
            try:
                existing_df = pd.read_csv(file_path, index_col='date', parse_dates=True)
                if not existing_df.empty:
                    last_date = existing_df.index.max()
                    # 从最后一天开始拉取，以便校验复权因子是否变化
                    start_date = last_date.strftime("%Y%m%d")
            except Exception as e:
                print(f"Error reading existing file for {code}: {e}, will fetch full data.")
                existing_df = None

        new_df = fetch_data(code, start_date=start_date)
        
        if new_df is not None and not new_df.empty:
            df = None
            if existing_df is not None:
                # 检查是否发生复权（比较 last_date 的收盘价）
                is_adjusted = False
                if last_date in new_df.index:
                    old_close = existing_df.loc[last_date, 'close']
                    new_close = new_df.loc[last_date, 'close']
                    
                    # 处理可能返回 Series 的情况
                    if isinstance(old_close, pd.Series): old_close = old_close.iloc[0]
                    if isinstance(new_close, pd.Series): new_close = new_close.iloc[0]
                    
                    # 如果价格差异超过 0.01，认为发生了复权变化
                    if abs(old_close - new_close) > 0.01:
                        is_adjusted = True
                        print(f"Adjusted factor changed for {name} ({code}). Triggering full update.")
                else:
                    # 如果新拉取的数据里没有 start_date，保险起见全量更新
                    is_adjusted = True
                    print(f"Data discontinuity for {name} ({code}). Triggering full update.")
                
                if is_adjusted:
                    # 全量更新
                    df = fetch_data(code, start_date="20160101")
                else:
                    # 增量合并
                    df = pd.concat([existing_df, new_df])
            else:
                df = new_df
                
            if df is not None:
                # 去重（保留最新的）
                df = df[~df.index.duplicated(keep='last')]
                df = df.sort_index()
                df.to_csv(file_path)
                print(f"Saved {name} ({code}) to {file_path}")
        elif existing_df is not None:
             print(f"No new data found for {name} ({code}).")
        else:
            print(f"Failed to fetch data for {name} ({code})")
        
        # 避免请求过快
        time.sleep(0.5)

def load_all_data():
    """
    从本地加载所有数据
    返回: dict {asset_key: dataframe}
    """
    data_map = {}
    for name, code in ASSET_CODES.items():
        file_path = os.path.join(DATA_DIR, f"{code}.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, index_col='date', parse_dates=True)
            data_map[name] = df
        else:
            print(f"Warning: Data file for {name} ({code}) not found.")
    return data_map

if __name__ == "__main__":
    update_all_data()
