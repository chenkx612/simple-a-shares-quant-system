import akshare as ak
import pandas as pd
import os
import time
from datetime import datetime
from .config import ASSET_CODES, SECTOR_ASSET_CODES, DATA_DIR

_TRADE_DATES_CACHE = None


def get_all_asset_codes():
    """
    合并所有资产池的代码，避免重复
    返回: dict {asset_key: code}
    """
    all_codes = {}
    all_codes.update(ASSET_CODES)
    all_codes.update(SECTOR_ASSET_CODES)
    return all_codes

def get_latest_valid_trading_date():
    """
    获取最近一个可获取完整数据的交易日
    """
    global _TRADE_DATES_CACHE
    try:
        if _TRADE_DATES_CACHE is None:
             trade_df = ak.tool_trade_date_hist_sina()
             _TRADE_DATES_CACHE = pd.to_datetime(trade_df['trade_date']).dt.date.tolist()
        
        trade_dates = _TRADE_DATES_CACHE
        if not trade_dates:
            return None
            
        now = datetime.now()
        today = now.date()
        
        # 找到 <= today 的交易日
        valid_dates = [d for d in trade_dates if d <= today]
        if not valid_dates:
            return None
        
        latest_date = valid_dates[-1]
        
        # 如果最近交易日是今天，且现在还没收盘（< 15:00），则认为今天的数据还没准备好
        if latest_date == today and now.hour < 15:
            if len(valid_dates) > 1:
                return valid_dates[-2]
            else:
                return None
                
        return latest_date
    except Exception as e:
        print(f"Warning: Failed to fetch trade dates: {e}")
        return None

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

def update_all_data(assets_to_update=None):
    """
    更新所有配置资产的数据并保存到本地
    逻辑：如果本地数据已是最新则跳过，否则全量拉取覆盖
    :param assets_to_update: 指定要更新的资产列表 (name, code) 元组。为 None 时更新所有资产。
    :return: 更新失败的资产列表 [(name, code), ...]
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # 获取最近有效交易日（考虑非交易日和盘中情况）
    latest_trading_date = get_latest_valid_trading_date()
    if latest_trading_date is None:
        print("Warning: Could not determine latest trading date, using today's date")
        latest_trading_date = datetime.now().date()

    failed_assets = []
    default_start_date = "20160101"

    # 确定要更新的资产
    if assets_to_update is None:
        assets_to_update = list(ASSET_CODES.items())

    for name, code in assets_to_update:
        file_path = os.path.join(DATA_DIR, f"{code}.csv")

        # 检查是否需要更新：本地数据最后日期 >= 最近有效交易日则跳过
        if os.path.exists(file_path):
            try:
                existing_df = pd.read_csv(file_path, index_col='date', parse_dates=True)
                if not existing_df.empty:
                    last_date = existing_df.index.max()
                    if last_date.date() >= latest_trading_date:
                        print(f"Skipping {name} ({code}): Already up to date ({last_date.date()})")
                        continue
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

        # 全量拉取
        print(f"Fetching {name} ({code})...")
        df = fetch_data(code, start_date=default_start_date)
        if df is not None and not df.empty:
            df.to_csv(file_path)
            print(f"Saved {name} ({code})")
        else:
            print(f"Failed to fetch {name} ({code})")
            failed_assets.append((name, code))

        # 避免请求过快
        time.sleep(0.5)

    return failed_assets


def load_all_data(asset_codes=None):
    """
    从本地加载数据
    :param asset_codes: 要加载的资产字典 {name: code}。为 None 时加载默认资产池 (ASSET_CODES)。
    返回: dict {asset_key: dataframe}
    """
    if asset_codes is None:
        asset_codes = ASSET_CODES

    data_map = {}
    for name, code in asset_codes.items():
        file_path = os.path.join(DATA_DIR, f"{code}.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, index_col='date', parse_dates=True)
            data_map[name] = df
        else:
            print(f"Warning: Data file for {name} ({code}) not found.")
    return data_map

if __name__ == "__main__":
    update_all_data()
