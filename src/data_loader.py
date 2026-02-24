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

def get_sina_symbol(code):
    """
    将纯数字代码转换为 sina 格式 (sh/sz 前缀)
    上海: 5/6 开头 → sh
    深圳: 1/0 开头 → sz
    """
    if code.startswith(('5', '6')):
        return f"sh{code}"
    else:
        return f"sz{code}"


def fetch_all_fund_spot_sina():
    """
    使用 sina 接口获取全市场 ETF/LOF 当日行情
    返回: DataFrame, 以代码为索引（纯数字）, 包含 open/high/low/close/volume
    """
    try:
        etf_df = ak.fund_etf_category_sina("ETF基金")
        lof_df = ak.fund_etf_category_sina("LOF基金")
        combined = pd.concat([etf_df, lof_df], ignore_index=True)

        # 映射列名
        combined = combined.rename(columns={
            "今开": "open",
            "最高": "high",
            "最低": "low",
            "最新价": "close",
            "成交量": "volume",
            "代码": "code"
        })
        # 去除代码前缀 (sh/sz)，转为纯数字格式
        combined["code"] = combined["code"].str.replace(r"^(sh|sz)", "", regex=True)
        combined = combined.set_index("code")
        return combined[["open", "high", "low", "close", "volume"]]
    except Exception as e:
        print(f"Error fetching spot data from sina: {e}")
        return None


def append_spot_to_csv(code, spot_df, trading_date):
    """
    将 spot_df 中指定 code 的当日数据追加到 CSV
    返回: True 成功, False 失败
    """
    if code not in spot_df.index:
        return False

    file_path = os.path.join(DATA_DIR, f"{code}.csv")
    if not os.path.exists(file_path):
        return False  # 没有历史数据，无法增量更新

    existing_df = pd.read_csv(file_path, index_col='date', parse_dates=True)

    # 检查是否已有该日期数据
    if pd.Timestamp(trading_date) in existing_df.index:
        return True  # 已存在，视为成功

    # 构造新行
    row = spot_df.loc[code]
    new_row = pd.DataFrame({
        "open": [row["open"]],
        "high": [row["high"]],
        "low": [row["low"]],
        "close": [row["close"]],
        "volume": [row["volume"]]
    }, index=pd.DatetimeIndex([trading_date], name="date"))

    # 追加并保存
    updated_df = pd.concat([existing_df, new_row]).sort_index()
    updated_df.to_csv(file_path)
    return True


def fetch_data(code, start_date="20160101", end_date=None):
    """
    获取单个ETF/LOF的日线数据 (前复权)
    三级备用机制:
    1. fund_etf_hist_em (东方财富) - 主接口
    2. fund_etf_hist_sina (新浪历史) - 第二备用
    3. fund_etf_category_sina (新浪当日) - 最后备用 (在 update_all_data 中处理)
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    print(f"Fetching {code} from {start_date} to {end_date}...")

    # 方案1: fund_etf_hist_em (主接口)
    try:
        df = ak.fund_etf_hist_em(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
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
        df = df.set_index('date').sort_index()
        return df[["open", "high", "low", "close", "volume"]]
    except Exception as e:
        print(f"fund_etf_hist_em failed for {code}: {e}")

    # 方案2: fund_etf_hist_sina (备用接口)
    try:
        sina_symbol = get_sina_symbol(code)
        df = ak.fund_etf_hist_sina(symbol=sina_symbol)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        # 过滤日期范围
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        df = df[(df.index >= start_dt) & (df.index <= end_dt)]
        return df[["open", "high", "low", "close", "volume"]]
    except Exception as e:
        print(f"fund_etf_hist_sina failed for {code}: {e}")

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

    # 第一轮结束后，如果有失败的资产，尝试备用方案
    if failed_assets:
        print(f"\n尝试使用 sina 备用接口更新 {len(failed_assets)} 个失败资产...")
        spot_df = fetch_all_fund_spot_sina()

        if spot_df is not None:
            still_failed = []

            for name, code in failed_assets:
                if append_spot_to_csv(code, spot_df, latest_trading_date):
                    print(f"Fallback success: {name} ({code})")
                else:
                    print(f"Fallback failed: {name} ({code})")
                    still_failed.append((name, code))

            failed_assets = still_failed

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
