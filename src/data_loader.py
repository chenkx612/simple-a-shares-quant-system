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

def update_all_data(force_full=False):
    """
    更新所有配置资产的数据并保存到本地
    :param force_full: 是否强制全量更新。
                       True: 忽略本地文件，从 20160101 重新拉取所有数据。
                       False: 尝试增量更新。如果本地文件不存在，则全量拉取。
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    for name, code in ASSET_CODES.items():
        file_path = os.path.join(DATA_DIR, f"{code}.csv")
        
        # 默认起始日期
        default_start_date = "20160101"
        
        if force_full:
            print(f"Full update for {name} ({code})...")
            df = fetch_data(code, start_date=default_start_date)
            if df is not None and not df.empty:
                df.to_csv(file_path)
                print(f"Saved {name} ({code}) to {file_path}")
            else:
                 print(f"Failed to fetch data for {name} ({code})")
        else:
            # 增量更新模式
            if os.path.exists(file_path):
                try:
                    existing_df = pd.read_csv(file_path, index_col='date', parse_dates=True)
                    if not existing_df.empty:
                        last_date = existing_df.index.max()
                        start_date_str = last_date.strftime("%Y%m%d")
                        print(f"Incremental update for {name} ({code}) from {start_date_str}...")
                        
                        new_df = fetch_data(code, start_date=start_date_str)
                        
                        if new_df is not None and not new_df.empty:
                            # 过滤掉已经存在的日期
                            new_df = new_df[new_df.index > last_date]
                            
                            if not new_df.empty:
                                df = pd.concat([existing_df, new_df])
                                df = df[~df.index.duplicated(keep='last')]
                                df = df.sort_index()
                                df.to_csv(file_path)
                                print(f"Updated {name} ({code}). Added {len(new_df)} records.")
                            else:
                                print(f"No new records for {name} ({code}).")
                        else:
                             print(f"No new data fetched for {name} ({code}).")
                    else:
                        # 文件为空，全量
                        print(f"File empty for {name} ({code}). Full update...")
                        df = fetch_data(code, start_date=default_start_date)
                        if df is not None:
                            df.to_csv(file_path)
                            print(f"Saved {name} ({code}) to {file_path}")
                except Exception as e:
                    print(f"Error reading {file_path}: {e}. Fallback to full update.")
                    df = fetch_data(code, start_date=default_start_date)
                    if df is not None:
                        df.to_csv(file_path)
                        print(f"Saved {name} ({code}) to {file_path}")
            else:
                # 文件不存在，全量
                print(f"File not found for {name} ({code}). Full update...")
                df = fetch_data(code, start_date=default_start_date)
                if df is not None:
                    df.to_csv(file_path)
                    print(f"Saved {name} ({code}) to {file_path}")
        
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
