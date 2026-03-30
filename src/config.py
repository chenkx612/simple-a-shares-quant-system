# 默认回测参数
START_DATE = '20230301' # 回测开始时间
DATA_DIR = 'data'
COMMISSION_RATE = 0.0003 # 双边佣金万分之三

# 行业轮动策略资产池
SECTOR_ASSET_CODES  = {
    # 宽基
    "cyb": "159915",       # 创业板 (A股成长风格代表，替代科创/芯片)
    'hs_tech': '513130',   # 恒生科技ETF

    # 跨境
    "nasdaq": "513100",      # 纳指ETF
    'nas_tech': '159509',    # 纳指科技ETF
    "india": "164824",       # 印度基金

    # 防御
    'fcash': '159201',       # 自由现金流ETF
    
    # 行业
    "bank": "512800",          # 银行ETF
    "bean": "159985",          # 豆粕 (农产品，零相关)
    "grid": "159326",          # 电网设备 (具有公用事业属性，与大盘走势往往不同步)
    "gold": "518880",          # 黄金ETF
    'telecom': '515880',       # 通信ETF
    'ai': '159819',            # 人工智能ETF
    'satellite': '159206',     # 卫星ETF
    'software': '159852',      # 软件ETF
    'big_data': '515400',      # 大数据ETF
    'hksec': '513090',         # 香港证券ETF
    'sp_oil_gas': '159518',    # 标普油气ETF

    # 备选
    # 'semiconductor': '159516', # 半导体设备ETF
    # 'metals': '516650', # 有色金属ETF
    # 'food': '159698', # 粮食ETF
    # 'hk_medicine': '159570', # 港股通创新药ETF
    # 'medicine': '159992', # 创新药ETF
    # 'rare_metal': '562800', # 稀有金属ETF
    # 'coal': '515220', # 煤炭ETF
    # 'battery': '159755', # 电池ETF
    # 'tourism': '159766',  # 旅游ETF
    # 'hk_consumer': '513070', # 港股通消费ETF
    # '30y_bond': '511090', # 30年国债ETF
    # 'pv': '515790', # 光伏ETF
    # "liquor": "512690",        # 酒 ETF
    # 'cyb50': '159949', # 创业板50ETF
    # 'energy_chemical': '159981', # 能源化工ETF
    # 'insurance': '512070', # 证券保险ETF
    # "dividend": "510880",  # 红利ETF
    # 'infrastructure': '516970', # 基建ETF
    # 'chemical': '159870', # 化工ETF
    # 'sp500': '513500', # 标普500
    # 'japen': '513880', # 日经225ETF
    # 'game': '159869', # 游戏ETF
    # 'chip': '588200', # 芯片ETF
    # 'media': '512980', # 传媒ETF
    # 'rare_earth': '516150', # 稀土ETF
    # 'military': '512710', # 军工ETF
    # 'industrial_machine': '159667', # 工业母机ETF
    # 'semiconductor': '513310', # 半导体ETF
    # 'fishing': '159865', # 养殖ETF
    # 'internet': '513050', # 中概互联网ETF
    # 'kcb': '159781', # 科创创业ETF
}

# 行业轮动策略参数 (Sharpe因子: Return/Vol)
SECTOR_M = 5  # 持有资产数量
SECTOR_N = 20  # 因子计算窗口 (收益/波动)
SECTOR_K = 100  # 相关性计算窗口
SECTOR_CORR_THRESHOLD = 0.9  # 相关性阈值
SECTOR_STOP_LOSS_PCT = 0.1  # 止损阈值

# Sortino轮动策略参数 (Sortino因子: Return/DownsideVol)
SORTINO_M = 4
SORTINO_N = 25
SORTINO_K = 100
SORTINO_CORR_THRESHOLD = 0.9
SORTINO_STOP_LOSS_PCT = 0.06

# 因子下限轮动策略参数 (板块轮动 + 因子下限过滤)
FACTOR_THRESHOLD_M = 5
FACTOR_THRESHOLD_N = 25
FACTOR_THRESHOLD_LOWER_BOUND = 0.0  # 因子下限，低于此值的资产不买入
FACTOR_THRESHOLD_K = 100
FACTOR_THRESHOLD_CORR_THRESHOLD = 0.9
FACTOR_THRESHOLD_STOP_LOSS_PCT = 0.1
