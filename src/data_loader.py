import akshare as ak
import pandas as pd
import os
import time
from datetime import datetime
from .config import ASSET_CODES, DATA_DIR

def fetch_data(code, start_date="20150101", end_date=None):
    """
    获取单个ETF/LOF的日线数据 (前复权)
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
        
    print(f"Fetching {code} from {start_date} to {end_date}...")
    try:
        # 尝试使用 ak.fund_etf_hist_em
        df = ak.fund_etf_hist_em(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        
        #以此重命名列以统一格式
        # 假设返回列包含: 日期, 开盘, 收盘, 最高, 最低, 成交量...
        # akshare返回的列名通常是中文
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
        
        # 这里为了简单，每次全量拉取。
        # 如果数据量大，可以读取现有文件，获取最后日期，然后增量拉取。
        df = fetch_data(code)
        
        if df is not None and not df.empty:
            df.to_csv(file_path)
            print(f"Saved {name} ({code}) to {file_path}")
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
