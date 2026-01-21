# 个人量化投资项目

基于 Python 实现的简单动量轮动策略量化系统。

## 功能特性

1.  **数据获取**: 使用 `akshare` 获取 ETF/LOF 日线数据。
2.  **策略回测**: 实现基于 n 天收益率的动量轮动策略。
3.  **参数优化**: 遍历不同的回顾窗口 n，寻找最优参数。
4.  **实盘建议**: 每日收盘后，根据最新数据生成次日持仓建议。
5.  **防止未来函数**: 信号基于 T 日收盘数据生成，用于 T+1 日开盘建仓。

## 策略逻辑

将市场分为四种情形，根据过去 n 天收益率最高的组合进行轮动：

-   **大涨 (Bull Surge)**: 科创50 (30%) + 恒生科技 (30%) + 纳指ETF (40%)
-   **慢牛 (Slow Bull)**: 沪深300 (40%) + 日经ETF (20%) + 标普500 (40%)
-   **慢熊 (Slow Bear)**: 30年国债 (30%) + 红利ETF (30%) + 美元债LOF (40%)
-   **恐慌 (Panic)**: 黄金ETF (40%) + 货币ETF (60%)

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

运行主程序：

```bash
python main.py
```

或者直接运行各个模块：

-   **获取实盘建议**: `python -m src.trading_signal`
-   **运行回测**: `python -m src.backtest`
-   **参数优化**: `python -m src.optimize`
-   **更新数据**: `python -m src.data_loader`

## 目录结构

```
.
├── README.md           # 项目说明
├── requirements.txt    # 依赖列表
├── main.py             # 主入口脚本
├── check_codes.py      # ETF代码检查工具
├── data/               # 数据存储目录
└── src/                # 源代码目录
    ├── __init__.py
    ├── config.py       # 配置文件 (资产代码、组合权重、回测参数)
    ├── data_loader.py  # 数据获取模块
    ├── backtest.py     # 回测引擎
    ├── optimize.py     # 参数优化模块
    └── trading_signal.py # 实盘信号生成
```
