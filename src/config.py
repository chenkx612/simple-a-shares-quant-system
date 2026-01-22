# 资产配置代码映射

ASSET_CODES = {
    # 大涨组合
    "kc50": "588000",      # 科创50
    "hstech": "513130",    # 恒生科技
    "nasdaq": "513100",    # 纳指ETF

    # 慢牛组合
    "hs300": "510300",     # 沪深300
    "nikkei": "513520",    # 日经ETF
    "sp500": "513500",     # 标普500

    # 慢熊组合
    "bond30": "511090",    # 30年国债
    "dividend": "510880",  # 红利ETF
    "usdbond": "501300",   # 海富通美元债LOF

    # 恐慌组合
    "gold": "518880",      # 黄金ETF
    "cash": "511990",      # 华宝添益 (货币ETF)
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
