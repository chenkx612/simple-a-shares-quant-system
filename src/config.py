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
    # # --- 全球市场补位 ---
    # "india": "164824",      # 印度基金LOF (长期趋势极其稳定)
    # "germany": "513030",    # 德国ETF (欧洲核心)
    # "france": "513080",     # 法国ETF (欧洲互补)
    # "se_asia": "513730",    # 东南亚科技 (新兴市场动量)
    # # --- A股风格与细分行业 ---
    # "zz1000": "512100",     # 中证1000 (小盘股，行情启动时弹性极高)
    # "chip": "159995",       # 芯片ETF (高波动、强进攻)
    # "energy": "159930",     # 能源ETF (与科技股负相关，抗通胀)
    # "bank": "512800",       # 银行ETF (低波动防御)
    # # --- 另类资产 (低相关性) ---
    # "soymeal": "159985",    # 豆粕ETF (农产品动量，受股市影响极小)
    # "oil": "162411",        # 华宝油气 (挂钩标普石油天然气上游)
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

# 止损轮动策略参数
STOP_LOSS_M = 3  # 持有资产数量
STOP_LOSS_N = 30  # 因子计算窗口 (收益/波动)
STOP_LOSS_K = 100  # 相关性计算窗口
STOP_LOSS_CORR_THRESHOLD = 0.9  # 相关性阈值
STOP_LOSS_PCT = 0.07  # 止损阈值
