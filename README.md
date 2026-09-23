# A股高潜力股票池系统

基于 AKShare 数据源的 A 股量化选股与持仓跟踪系统。从沪深主板 + 创业板 3500+ 只股票中，通过六大技术维度（均线趋势、MACD 动量、KDJ 位置、布林带空间、量能变化、回调幅度）综合评分筛选 Top 10 高潜力股，每两个月自动轮换票池。

## 核心功能

- **全市场量化选股**：扫描成交活跃的前 200 只股票，计算技术指标并综合评分
- **票池跟踪管理**：记录每期 10 只股票的入场价、当前价、收益率，每两个月轮换
- **买入信号检测**：基于 MACD 金叉、KDJ 金叉、均线突破等多信号共振评分
- **Web 仪表盘**：Flask 服务 + HTML 页面，可视化查看持仓状态、信号、历史档案
- **Trae 移动端交互**：通过 Trae App 远程触发选股、更新行情、查看持仓

## 文件结构

```
├── stock_screener.py          # 量化选股脚本（全市场扫描 + 技术面评分）
├── pool_manager.py            # 票池管理器（初始化/更新价格/换期/状态查询）
├── main.py                    # Flask Web 服务（端口 5000，网页按钮触发操作）
├── generate_index.py          # 生成 index.html 仪表盘页面
├── index.html                 # 票池仪表盘首页（当前状态/买入信号/票池报告/历史/操作指南）
├── stock_pool_history.json    # 票池历史数据（每期存档）
├── latest_analysis.json       # 最新买入信号分析结果
└── stock_screen_results.csv   # 全市场选股结果（完整数据）
```

## 环境依赖

```bash
pip install akshare pandas numpy flask
```

Python 3.8+，AKShare 无需 API Key，直接访问新浪财经公开数据。

## 快速开始

```bash
# 1. 克隆仓库
git clone -b trae/agent-j41Sip https://github.com/pdp111/clone.git
cd clone

# 2. 安装依赖
pip install akshare pandas numpy flask

# 3. 全市场选股（首次运行，约 5-10 分钟）
python3 stock_screener.py

# 4. 初始化票池（第 1 期，取选股结果 Top 10）
python3 pool_manager.py init

# 5. 生成仪表盘页面
python3 generate_index.py

# 6. 启动 Web 服务
python3 main.py
# 浏览器访问 http://127.0.0.1:5000
```

## 命令一览

| 命令 | 说明 | 耗时 |
|------|------|------|
| `python3 stock_screener.py` | 全市场扫描选股，输出 CSV | 5-10 分钟 |
| `python3 pool_manager.py init` | 初始化第 1 期票池（Top 10） | 秒级 |
| `python3 pool_manager.py update` | 更新当前价格 + 检测买入信号 | 10-30 秒 |
| `python3 pool_manager.py new-period` | 生成新一期票池（留前 2 + 补 8） | 5-10 分钟 |
| `python3 pool_manager.py status` | 终端查看当前票池状态 | 秒级 |
| `python3 generate_index.py` | 重新生成 index.html 仪表盘 | 秒级 |
| `python3 main.py` | 启动 Flask Web 服务（端口 5000） | 持续运行 |

## 票池轮换规则

每两个月更新一次，具体逻辑：

1. 老票池按本期涨幅排序，**保留前 2 名**（留存股）
2. 全市场重新筛选，排除上期留池的前 2 名（去重）
3. 补充 **8 只新股**，凑满 10 只
4. 留存股重置入场价为当前价，新股以筛选日收盘价入场

## 技术指标体系

| 指标 | 用途 |
|------|------|
| MA5/MA10/MA20/MA60/MA120 | 均线趋势判断（多头排列加分） |
| MACD (DIF/DEA) | 动量方向（金叉/死叉、零上/零下） |
| KDJ (K/D/J) | 超买超卖判断（K<30 超卖反弹） |
| BOLL (上/中/下轨) | 价格通道位置（中轨下方空间大） |
| RSI (14日) | 强弱指标 |
| 成交量均线 (VOL_MA5/MA20) | 量能变化（量比 >1.5 放量） |

综合评分 = 潜力分 × 0.6 + 技术面分 × 0.4，潜力 ≥ 40% 优先展示。

## Trae 移动端交互

本仓库支持通过 [Trae](https://www.trae.ai) 移动端远程交互操作：

### 交互方式

1. **远程执行命令**：在 Trae App 中直接发送指令，如"更新股票池价格"、"生成新一期票池"，Trae 会在远程沙箱中执行对应 Python 脚本
2. **持仓展示**：发送"查看持仓"指令，Trae 读取 `stock_pool_history.json` 并按加仓提醒格式输出（筛选累计投入接近 35 万元的股票，高亮显示）
3. **加仓提醒**：自动筛选达到 35 万元投入目标的股票，自首次加仓日起保留 3 天提醒
4. **行情分析**：Trae 可调用 AKShare 插件获取实时行情，结合仓库中的技术指标数据进行分析
5. **仓库更新**：本地电脑修改文件后，通过 `git push` 推送到 GitHub，Trae 端 `git pull` 即可同步最新数据

### 使用流程

```
本地电脑 (Mac)                    Trae 移动端
    │                                  │
    │  git push → GitHub 仓库           │
    │                                  │  git pull ← GitHub 仓库
    │                                  │  ↓
    │                                  │  执行 pool_manager.py update
    │                                  │  读取 stock_pool_history.json
    │                                  │  输出加仓提醒 + 汇总统计
    │  ← 查看结果（聊天窗口直接展示） ─┘
```

### 常用 Trae 指令示例

- "查看当前持仓和加仓提醒" → 读取 JSON，输出 35 万加仓名单 + 汇总统计
- "更新行情价格" → 执行 `python3 pool_manager.py update`
- "生成新一期票池" → 执行 `python3 pool_manager.py new-period`
- "分析蓝色光标的技术面" → 调用 AKShare 获取该股实时数据 + 仓库技术指标

## 数据源

- **AKShare**：开源金融数据接口，访问新浪财经公开数据
- **实时行情**：`ak.stock_zh_a_spot()` 全市场 A 股快照
- **历史K线**：`ak.stock_zh_a_daily()` 前复权日线数据
- 无需 API Key，无需注册，完全免费

## 风险提示

本系统基于技术面量化模型生成，仅供研究参考，**不构成任何投资建议**。涨幅潜力为技术面估算值，实际收益受市场环境、政策变化、公司基本面等多重因素影响。股市有风险，入市需谨慎。
