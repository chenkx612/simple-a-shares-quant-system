# 资产配置代码映射
ASSET_CODES = {
    "kc50": "588000",      # 科创50
    "hstech": "513130",    # 恒生科技
    "nasdaq": "513100",    # 纳指ETF
    "hs300": "510300",     # 沪深300
    "nikkei": "513520",    # 日经ETF
    "sp500": "513500",     # 标普500
    "bond30": "511090",    # 30年国债
    "dividend": "510880",  # 红利ETF
    "usdbond": "501300",   # 海富通美元债LOF
    "gold": "518880",      # 黄金ETF
    "cash": "511990",      # 华宝添益 (货币ETF)
    # "zz500": "510500",     # 中证500
    # "zz1000": "512100",    # 中证1000（若可接受波动）
    # "commodity": "510170", # 大宗商品ETF
    # "hs_dividend": "513820", # 恒生高股息
    # "hs_index": "159920",    # 恒生ETF（宽基）
    # "bond5": "511010",       # 5年国债
    # "bond10": "511260",      # 10年国债
}

# 组合权重配置
PORTFOLIOS = {
    "bull_surge": { # 大涨
        "name": "大涨 (Bull Surge)",
        "assets": {"kc50": 0.3, "hstech": 0.3, "nasdaq": 0.4}
    },
    "slow_bull": { # 慢牛
        "name": "慢牛 (Slow Bull)",
        "assets": {"hs300": 0.4, "nikkei": 0.2, "sp500": 0.4}
    },
    "slow_bear": { # 慢熊
        "name": "慢熊 (Slow Bear)",
        "assets": {"bond30": 0.3, "dividend": 0.3, "usdbond": 0.4}
    },
    "panic": { # 恐慌
        "name": "恐慌 (Panic)",
        "assets": {"gold": 0.4, "cash": 0.6}
    }
}

# 默认回测参数
DEFAULT_N = 20 # 经过优化，20天表现最好
START_DATE = "20200101" # 回测开始时间
DATA_DIR = "data"
COMMISSION_RATE = 0.0003 # 双边佣金万分之三

# 智能轮动策略参数
SMART_M = 3 # 持有资产数量
SMART_N = 30 # 因子计算窗口 (收益/波动)
SMART_K = 100 # 相关性计算窗口 
CORR_THRESHOLD = 0.9 # 相关性阈值
