# Simple A-Shares Quant System

个人量化投资项目，基于 Python 实现的动量轮动策略量化系统。本项目专注于**行业轮动策略**，提供 Sharpe 和 Sortino 两种因子变体，旨在捕捉行业轮动收益并控制回撤。

## 核心策略算法

本项目实现了两套基于动量的行业轮动策略，使用同一套行业/主题 ETF 资产池。

### 1. 行业轮动 - Sharpe因子 (Return/Volatility)

基于风险调整后动量因子选股，通过相关性矩阵进行分散配置，并附加止损机制控制风险。

*   **选股因子**: **风险调整后动量 (Risk-Adjusted Momentum)**
    *   公式: $Factor = \frac{Return_{N}}{Volatility_{N}}$
    *   其中 $Return_{N}$ 为过去 N 天的累计收益率, $Volatility_{N}$ 为过去 N 天日收益率的标准差。
*   **相关性过滤 (Correlation Filter)**:
    *   计算过去 K 天的资产日收益率相关性矩阵。
    *   **筛选流程**:
        1.  将所有资产按因子值从高到低排序。
        2.  首选因子最高的资产。
        3.  依次考察后续资产，若其与已选资产的相关系数超过阈值，则跳过。
        4.  直到选满 M 只资产。
*   **权重分配**: 等权重持有入选资产。
*   **止损规则**:
    *   若 T 日某持仓资产跌幅超过止损阈值（默认 6%），则 T+1 日信号中排除该资产。
    *   被止损的资产在当期选股中被排除，由其他符合条件的资产替补。
*   **参数配置** (src/config.py):
    *   `SECTOR_M`: 持有资产数量（默认 4）
    *   `SECTOR_N`: 因子计算窗口（默认 25 天）
    *   `SECTOR_K`: 相关性计算窗口（默认 100 天）
    *   `SECTOR_CORR_THRESHOLD`: 相关性阈值（默认 0.9）
    *   `SECTOR_STOP_LOSS_PCT`: 止损阈值（默认 6%）

### 2. 行业轮动 - Sortino因子 (Return/Downside Volatility)

与 Sharpe 因子策略逻辑相同，但使用 Sortino 比率作为选股因子，只惩罚下行波动，不惩罚上行波动。

*   **选股因子**: **Sortino 因子**
    *   公式: $Factor = \frac{Return_{N}}{DownsideVolatility_{N}}$
    *   其中 $DownsideVolatility_{N}$ 仅使用负收益率计算的波动率。
*   **参数配置** (src/config.py):
    *   `SORTINO_M`: 持有资产数量（默认 4）
    *   `SORTINO_N`: 因子计算窗口（默认 25 天）
    *   `SORTINO_K`: 相关性计算窗口（默认 100 天）
    *   `SORTINO_CORR_THRESHOLD`: 相关性阈值（默认 0.9）
    *   `SORTINO_STOP_LOSS_PCT`: 止损阈值（默认 6%）

## 资产池配置

### 行业轮动资产池

| 名称 | 代码 | 说明 |
|------|------|------|
| hs300 | 510300 | 沪深300 |
| zz1000 | 512100 | 中证1000 |
| cyb | 159915 | 创业板 |
| nasdaq | 513100 | 纳指ETF |
| india | 164824 | 印度基金 |
| germany | 513030 | 德国ETF |
| nasdaq_tech | 159509 | 纳指科技ETF |
| free_cash | 159201 | 自由现金流ETF |
| dividend | 510880 | 红利ETF |
| bank | 512800 | 银行ETF |
| bean | 159985 | 豆粕ETF |
| grid | 159326 | 电网设备 |
| liquor | 512690 | 酒ETF |
| gold | 518880 | 黄金ETF |
| communication | 515880 | 通信ETF |
| ai | 159819 | 人工智能ETF |
| satellite | 159206 | 卫星ETF |
| software | 159852 | 软件ETF |
| big_data | 515400 | 大数据ETF |

## 回测引擎特性

*   **事件驱动**: 模拟真实交易时序，T 日收盘生成信号，T+1 日开盘价成交。
*   **成本模拟**: 包含双边交易佣金（默认万分之三）。
*   **数据对齐**: 自动处理不同市场（A股/港股/美股ETF）的交易日历差异，采用前值填充对齐。
*   **资产贡献分析**: 支持查看各资产对组合收益的贡献明细。
*   **股数调整**: 买入股数自动调整为 100 的整数倍。

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 交互式菜单系统

推荐使用交互式菜单系统，支持所有策略的回测、优化和实盘建议：

```bash
python main.py
```

### 运行实盘建议

生成次日持仓建议：

```bash
# 行业轮动 - Sharpe因子 (默认)
python -m src.trading_signal

# 行业轮动 - Sortino因子
python -m src.trading_signal --strategy sortino_rotation
```

### 运行回测

```bash
python -m src.backtest
```

### 数据更新

数据来源于 `akshare`，运行以下命令获取最新 ETF/LOF 日线数据：

```bash
python -m src.data_loader
```

### 参数优化

网格搜索优化策略参数，约束条件为 `|最大回撤| < 年化收益率`，目标为最大化 Sortino 比率：

```bash
python -m src.optimize
```

## 目录结构

```
.
├── main.py                 # 交互式菜单入口
├── src/
│   ├── strategy.py         # 策略核心逻辑 (SectorRotationStrategy, SortinoRotationStrategy)
│   ├── backtest.py         # 回测引擎 (BacktestEngine)
│   ├── config.py           # 资产代码映射与策略参数配置
│   ├── data_loader.py      # 数据加载与更新 (AkShare数据源)
│   ├── trading_signal.py   # 实盘信号生成
│   └── optimize.py         # 参数优化工具 (GridSearchOptimizer)
├── data/                   # ETF 日线数据 (CSV)
├── requirements.txt        # Python 依赖
├── CLAUDE.md              # Claude Code 项目指南
└── README.md
```
