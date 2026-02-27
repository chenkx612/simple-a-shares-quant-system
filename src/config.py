# 资产配置代码映射
ASSET_CODES = {
    # --- 核心宽基 (基石) ---                                                                                                                               
    "sz50": "510050",         # 上证50                                                                                                                      
    "zz500": "510500",        # 中证500                                                                                                                     
    "zz1000": "512100",       # 中证1000                                                                                                                    
    "cyb": "159915",          # 创业板                                                                                                                      
    "kcg50": "588000",        # 科创50                                                                                                                      
                                                                                                                                                            
    # --- 跨境资产 (低相关性来源；均为沪深上市ETF/QDII ETF) ---                                                                                             
    "nasdaq": "513100",       # 纳指100                                                                                                                     
    "sp500": "513500",        # 标普500                                                                                                                     
    "hangseng": "159920",     # 恒生指数                                                                                                                    
    "hangseng_tech": "513180",# 恒生科技                                                                                                                    
    "germany": "513030",      # 德国                                                                                                                        
                                                                                                                                                            
    # --- 防御与避险 (控制回撤的关键) ---                                                                                                                   
    "dividend": "510880",     # 红利                                                                                                                        
                                                                                                                                                            
    # --- 进攻/弹性 (风险偏好上行、牛市与反弹阶段) ---                                                                                                      
    "securities": "512880",   # 证券(高弹性)                                                                                                                
    "new_energy_vehicle": "515030",  # 新能源车                                                                                                             
                                                                                                                                                            
    # --- 稳健成长/内需 (震荡与结构行情常用) ---                                                                                                            
    "consumer": "159928",     # 消费                                                                                                                        
    "liquor": "512690",       # 酒                                                                                                                          
    "medicine": "512170",     # 医药                                                                                                                        
                                                                                                                                                            
    # --- 周期/通胀 (资源品、补库存、通胀预期阶段) ---                                                                                                      
    "metals": "512400",       # 有色金属                                                                                                                    
    "energy": "159930",       # 能源(抗通胀/周期)                                                                                                           
                                                                                                                                                            
    # --- 事件/主题 (独立行情来源) ---                                                                                                                      
    "military": "512660",     # 军工                                                                                                                        
                                                                                                                                                            
    # --- 卫星资产 (尽量低相关) ---                                                                                                                         
    "gold": "518880",         # 黄金                                                                                                                        
    "bean": "159985",         # 豆粕                                                                                                                        
    "grid": "159326",         # 电网设备/电力设备链条(你原始设定保留)                                                                                       
                                                                                                                                                            
    # --- 利率/现金类 (熊市/去杠杆/风险厌恶时的“避风港”) ---                                                                                                
    "cash": "511990",         # 货币ETF/交易型货基(现金替代)                                                                                                
    "bond_10y": "511260",     # 10年国债ETF(你原始设定保留)                                                                                                 
    "convertible": "511380",  # 可转债ETF(股债混合属性)                                                                                                     
}

# 默认回测参数
START_DATE = "20200101" # 回测开始时间
DATA_DIR = "data"
COMMISSION_RATE = 0.0003 # 双边佣金万分之三

# 止损轮动策略参数
STOP_LOSS_M = 5  # 持有资产数量
STOP_LOSS_N = 25  # 因子计算窗口 (收益/波动)
STOP_LOSS_K = 100  # 相关性计算窗口
STOP_LOSS_CORR_THRESHOLD = 0.9  # 相关性阈值
STOP_LOSS_PCT = 0.1  # 止损阈值

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
    # 'tourism': '159766',  # 旅游ETF
    # 'japen': '513880', # 日经225ETF
    # 'game': '159869', # 游戏ETF
    # 'chip': '588200', # 芯片ETF
    # 'media': '512980', # 传媒ETF
    # 'rare_earth': '516150', # 稀土ETF
    # 'metals': '560860', # 有色ETF
    # 'semiconductor': '512480', # 半导体ETF
    # 'nasdaq_tech': '159509', # 纳指科技ETF
    # 'military': '512660', # 军工ETF
}

# 行业轮动策略参数（初始值与止损轮动相同）
SECTOR_M = 4  # 持有资产数量
SECTOR_N = 25  # 因子计算窗口 (收益/波动)
SECTOR_K = 100  # 相关性计算窗口
SECTOR_CORR_THRESHOLD = 0.9  # 相关性阈值
SECTOR_STOP_LOSS_PCT = 0.06  # 止损阈值

# 因子下限轮动策略参数
FACTOR_FLOOR_M = 5  # 持有资产数量
FACTOR_FLOOR_N = 25  # 因子计算窗口 (收益/波动)
FACTOR_FLOOR_K = 100  # 相关性计算窗口
FACTOR_FLOOR_CORR_THRESHOLD = 0.9  # 相关性阈值
FACTOR_FLOOR_STOP_LOSS_PCT = 0.1  # 止损阈值
FACTOR_FLOOR_THRESHOLD = -1.9  # 因子下限
