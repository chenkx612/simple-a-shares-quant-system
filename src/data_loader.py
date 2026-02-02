import akshare as ak
import pandas as pd
import os
import time
from datetime import datetime, timedelta
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
        
        # 如果最近交易日是今天，且现在还没收盘（< 16:00），则认为今天的数据还没准备好
        if latest_date == today and now.hour < 16:
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

def update_all_data(force_full=False, assets_to_update=None):
    """
    更新所有配置资产的数据并保存到本地
    :param force_full: 是否强制全量更新。
                       True: 忽略本地文件，从 20160101 重新拉取所有数据。
                       False: 尝试增量更新。如果本地文件不存在，则全量拉取。
    :param assets_to_update: 指定要更新的资产列表 (name, code) 元组。为 None 时更新所有资产。
    :return: 更新失败的资产列表 [(name, code), ...]
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    today = datetime.now().date()
    failed_assets = []

    # 确定要更新的资产
    if assets_to_update is None:
        assets_to_update = list(ASSET_CODES.items())

    for name, code in assets_to_update:
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
                failed_assets.append((name, code))
        else:
            # 增量更新模式
            if os.path.exists(file_path):
                try:
                    existing_df = pd.read_csv(file_path, index_col='date', parse_dates=True)
                    if not existing_df.empty:
                        last_date = existing_df.index.max()

                        # 只有当本地数据已经是今天时才跳过
                        # 不再依赖交易日历API，避免因API延迟导致漏更新
                        if last_date.date() >= today:
                            print(f"Skipping {name} ({code}): Already up to date ({last_date.date()})")
                            continue

                        start_date_obj = last_date + timedelta(days=1)
                        start_date_str = start_date_obj.strftime("%Y%m%d")
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
                        elif new_df is None:
                            # 接口报错
                            print(f"Failed to fetch data for {name} ({code}).")
                            failed_assets.append((name, code))
                        else:
                            # 返回空数据，正常情况
                            print(f"No new data for {name} ({code}).")
                    else:
                        # 文件为空，全量
                        print(f"File empty for {name} ({code}). Full update...")
                        df = fetch_data(code, start_date=default_start_date)
                        if df is not None and not df.empty:
                            df.to_csv(file_path)
                            print(f"Saved {name} ({code}) to {file_path}")
                        else:
                            print(f"Failed to fetch data for {name} ({code})")
                            failed_assets.append((name, code))
                except Exception as e:
                    print(f"Error reading {file_path}: {e}. Fallback to full update.")
                    df = fetch_data(code, start_date=default_start_date)
                    if df is not None and not df.empty:
                        df.to_csv(file_path)
                        print(f"Saved {name} ({code}) to {file_path}")
                    else:
                        print(f"Failed to fetch data for {name} ({code})")
                        failed_assets.append((name, code))
            else:
                # 文件不存在，全量
                print(f"File not found for {name} ({code}). Full update...")
                df = fetch_data(code, start_date=default_start_date)
                if df is not None and not df.empty:
                    df.to_csv(file_path)
                    print(f"Saved {name} ({code}) to {file_path}")
                else:
                    print(f"Failed to fetch data for {name} ({code})")
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
