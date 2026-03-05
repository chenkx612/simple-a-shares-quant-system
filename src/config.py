# 默认回测参数
START_DATE = '20200101' # 回测开始时间
DATA_DIR = 'data'
COMMISSION_RATE = 0.0003 # 双边佣金万分之三

# 行业轮动策略资产池
SECTOR_ASSET_CODES  = {
    # 宽基
    "hs300": "510300",     # 沪深300 (大盘价值/蓝筹)
    "zz1000": "512100",    # 中证1000 (小盘/高弹性，牛市进攻用)
    "cyb": "159915",       # 创业板 (A股成长风格代表，替代科创/芯片)

    # 跨境
    "nasdaq": "513100",    # 纳指ETF (美股科技，与A股低相关)
    "india": "164824",     # 印度基金 (新兴市场独立行情)
    "germany": "513030",   # 德国ETF (欧洲价值)
    'nasdaq_tech': '159509', # 纳指科技ETF

    # 防御
    'free_cash': '159201', # 自由现金流ETF
    
    # 行业
    "bank": "512800",       # 银行ETF (低波动防御)
    "bean": "159985",      # 豆粕 (农产品，零相关)
    "grid": "159326",       # 电网设备 (具有公用事业属性，与大盘走势往往不同步)
    "liquor": "512690",     # 酒 ETF
    "gold": "518880",      # 黄金ETF
    'chemical': '159870', # 化工ETF
    'communication': '515880', # 通信ETF
    'ai': '159819', # 人工智能ETF
    'satellite': '159206', # 卫星ETF
    'software': '159852', # 软件ETF

    # 备选
    # "dividend": "510880",  # 红利ETF
    # 'dividend1': '512890', # 红利ETF1
    # 'dividend2': '515180', # 红利ETF2
    # 'sp500': '513500', # 标普500
    # 'tourism': '159766',  # 旅游ETF
    # 'japen': '513880', # 日经225ETF
    # 'game': '159869', # 游戏ETF
    # 'chip': '588200', # 芯片ETF
    # 'media': '512980', # 传媒ETF
    # 'rare_earth': '516150', # 稀土ETF
    # 'metals': '512400', # 有色ETF
    # 'military': '512710', # 军工ETF
    # 'industrial_machine': '159667', # 工业母机ETF
    # 'ship': '560710', # 船舶ETF
    # 'semiconductor': '513310', # 半导体ETF
    # 'medicine': '520500', # 创新药ETF
}

# 行业轮动策略参数 (Sharpe因子: Return/Vol)
SECTOR_M = 4  # 持有资产数量
SECTOR_N = 25  # 因子计算窗口 (收益/波动)
SECTOR_K = 100  # 相关性计算窗口
SECTOR_CORR_THRESHOLD = 0.9  # 相关性阈值
SECTOR_STOP_LOSS_PCT = 0.06  # 止损阈值

# Sortino轮动策略参数 (Sortino因子: Return/DownsideVol)
SORTINO_M = 4
SORTINO_N = 25
SORTINO_K = 100
SORTINO_CORR_THRESHOLD = 0.9
SORTINO_STOP_LOSS_PCT = 0.06
