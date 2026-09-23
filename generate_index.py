#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成整合首页 index.html
所有报告、状态、信号都在一个页面用标签展示
"""

import json
import os
from datetime import datetime

# 修改为当前脚本所在目录，而不是固定的 /workspace
WORKSPACE = os.path.dirname(os.path.abspath(__file__))
POOL_FILE = os.path.join(WORKSPACE, 'stock_pool_history.json')
ANALYSIS_FILE = os.path.join(WORKSPACE, 'latest_analysis.json')
OUTPUT_FILE = os.path.join(WORKSPACE, 'index.html')


def load_data():
    """加载票池和分析数据"""
    pool_data = None
    analysis_data = None

    if os.path.exists(POOL_FILE):
        with open(POOL_FILE, 'r', encoding='utf-8') as f:
            pool_data = json.load(f)

    if os.path.exists(ANALYSIS_FILE):
        with open(ANALYSIS_FILE, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)

    return pool_data, analysis_data


def generate_status_tab(pool_data):
    """生成当前状态标签页内容"""
    if not pool_data or not pool_data.get('pools'):
        return '<p class="empty-tip">暂无票池数据</p>'

    current_pool = pool_data['pools'][-1]
    stocks = current_pool['stocks']
    period = current_pool['period']
    create_date = current_pool['create_date']
    update_date = current_pool.get('update_date', create_date)

    # 计算统计数据
    total_stocks = len(stocks)
    up_count = sum(1 for s in stocks if s['period_return_pct'] > 0)
    down_count = sum(1 for s in stocks if s['period_return_pct'] < 0)
    avg_return = sum(s['period_return_pct'] for s in stocks) / total_stocks if total_stocks > 0 else 0
    avg_potential = sum(s['potential_pct'] for s in stocks) / total_stocks if total_stocks > 0 else 0

    # 按收益率排序
    sorted_by_return = sorted(stocks, key=lambda x: x['period_return_pct'], reverse=True)

    # 生成股票表格行
    rows_html = ''
    for i, s in enumerate(sorted_by_return):
        ret_pct = s['period_return_pct']
        ret_class = 'up' if ret_pct > 0 else 'down' if ret_pct < 0 else 'flat'
        ret_sign = '+' if ret_pct > 0 else ''
        rank_badge = ''
        if i == 0:
            rank_badge = '<span class="rank-badge gold">🥇</span>'
        elif i == 1:
            rank_badge = '<span class="rank-badge silver">🥈</span>'
        elif i == 2:
            rank_badge = '<span class="rank-badge bronze">🥉</span>'

        retained_tag = '<span class="tag retained">留存</span>' if s.get('is_retained') else ''
        new_tag = '<span class="tag new">新进</span>' if not s.get('is_retained') else ''

        # 留存股显示累计涨幅和历史信息
        if s.get('is_retained'):
            ret_label = '累计收益'
            entry_label = f'<span class="entry-original">¥{s["entry_price"]:.2f}</span>'
            prev_ret = ''
            if 'prev_period_return_pct' in s:
                prev_ret = f'<div class="prev-return">上期: {s["prev_period_return_pct"]:+.2f}%</div>'
            retained_count_badge = ''
            if s.get('retained_count', 0) > 0:
                retained_count_badge = f' <span class="tag retained-count">留存{s["retained_count"]}次</span>'
        else:
            ret_label = '本期收益'
            entry_label = f'¥{s["entry_price"]:.2f}'
            prev_ret = ''
            retained_count_badge = ''

        rows_html += f'''
        <tr>
            <td class="rank-col">{rank_badge}{i+1}</td>
            <td class="code-col">{s['code']}</td>
            <td class="name-col">
                <strong>{s['name']}</strong>
                {retained_tag}{new_tag}{retained_count_badge}
                <div class="market-label">{s['market']}</div>
            </td>
            <td class="price-col">¥{s['current_price']:.2f}</td>
            <td class="entry-col">{entry_label}</td>
            <td class="return-col {ret_class}">
                <div class="ret-main">{ret_sign}{ret_pct:.2f}%</div>
                <div class="ret-label">{ret_label}</div>
                {prev_ret}
            </td>
            <td class="potential-col">+{s['potential_pct']}%</td>
            <td class="target-col">¥{s['target_price']:.2f}</td>
            <td class="buy-col">¥{s['buy_price']:.2f}</td>
            <td class="stop-col">¥{s['stop_loss']:.2f}</td>
            <td class="score-col">{s['total_score']:.1f}</td>
        </tr>
        '''

    ret_class = 'up' if avg_return > 0 else 'down' if avg_return < 0 else 'flat'
    ret_sign = '+' if avg_return > 0 else ''

    return f'''
    <div class="tab-content" id="tab-status">
        <!-- 概览卡片 -->
        <div class="overview-grid">
            <div class="stat-card">
                <div class="stat-label">当前期数</div>
                <div class="stat-value">第 {period} 期</div>
                <div class="stat-sub">建仓日：{create_date}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">持仓股票</div>
                <div class="stat-value">{total_stocks} 只</div>
                <div class="stat-sub">涨 {up_count} / 跌 {down_count}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">本期平均收益</div>
                <div class="stat-value {ret_class}">{ret_sign}{avg_return:.2f}%</div>
                <div class="stat-sub">截至 {update_date}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">平均半年潜力</div>
                <div class="stat-value up">+{avg_potential:.0f}%</div>
                <div class="stat-sub">技术面估算</div>
            </div>
        </div>

        <!-- 持仓明细表 -->
        <div class="section-card">
            <div class="section-header">
                <h3>📋 持仓明细（按收益率排序）</h3>
                <span class="update-time">更新时间：{update_date}</span>
            </div>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th class="rank-col">排名</th>
                            <th class="code-col">代码</th>
                            <th class="name-col">名称</th>
                            <th class="price-col">现价</th>
                            <th class="entry-col">入场价</th>
                            <th class="return-col">收益</th>
                            <th class="potential-col">半年潜力</th>
                            <th class="target-col">目标价</th>
                            <th class="buy-col">买入价</th>
                            <th class="stop-col">止损价</th>
                            <th class="score-col">综合分</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- 下一期更新提示 -->
        <div class="notice-card">
            <div class="notice-icon">📅</div>
            <div class="notice-content">
                <strong>下一期更新时间：约 2026年11月下旬</strong>
                <p>票池每两个月更新一次。老票池保留涨幅前2名，补充8只新高潜力股。新股不能是上一期留池的前2名（但可以是之前淘汰的）。</p>
            </div>
        </div>
    </div>
    '''


def generate_signals_tab(analysis_data):
    """生成买入信号标签页内容"""
    if not analysis_data or not isinstance(analysis_data, list) or len(analysis_data) == 0:
        return '<p class="empty-tip">暂无买入信号数据</p>'

    signals = analysis_data
    # 从第一条信号获取更新时间，如果没有则使用当前时间
    update_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    if len(signals) > 0 and 'detect_time' in signals[0]:
        update_time = signals[0]['detect_time']

    # 统计
    strong_count = sum(1 for s in signals if s['signal_score'] >= 50)
    buy_count = sum(1 for s in signals if 30 <= s['signal_score'] < 50)
    watch_count = sum(1 for s in signals if s['signal_score'] < 30)
    avg_score = sum(s['signal_score'] for s in signals) / len(signals) if signals else 0

    # 按信号强度排序
    sorted_signals = sorted(signals, key=lambda x: x['signal_score'], reverse=True)

    rows_html = ''
    for i, s in enumerate(sorted_signals):
        score = s['signal_score']
        if score >= 50:
            level_class = 'strong-buy'
            level_text = '🔴 强烈买入'
        elif score >= 30:
            level_class = 'buy'
            level_text = '🟠 建议买入'
        else:
            level_class = 'watch'
            level_text = '🟡 可关注'

        # 信号列表（格式是 [信号名, 分数, 强度]）
        signal_items = s.get('signals', [])
        signal_badges = ''.join(
            f'<span class="signal-badge">{sig[0]}</span>' for sig in signal_items[:6]
        )

        rows_html += f'''
        <tr>
            <td class="rank-col">{i+1}</td>
            <td class="code-col">{s['code']}</td>
            <td class="name-col">
                <strong>{s['name']}</strong>
                <div class="market-label">{s.get('market', '')}</div>
            </td>
            <td class="price-col">¥{s['current_price']:.2f}</td>
            <td class="score-col">
                <div class="score-ring" style="--score: {score}">
                    <span>{score}</span>
                </div>
            </td>
            <td class="level-col"><span class="signal-level {level_class}">{level_text}</span></td>
            <td class="buy-col">¥{s.get('buy_price', 0):.2f}</td>
            <td class="target-col">¥{s.get('target_price', 0):.2f}</td>
            <td class="signals-col">
                <div class="signal-list">{signal_badges}</div>
            </td>
        </tr>
        '''

    return f'''
    <div class="tab-content" id="tab-signals">
        <!-- 信号概览 -->
        <div class="overview-grid">
            <div class="stat-card">
                <div class="stat-label">🔴 强烈买入</div>
                <div class="stat-value up">{strong_count} 只</div>
                <div class="stat-sub">信号分 ≥ 50</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">🟠 建议买入</div>
                <div class="stat-value warn">{buy_count} 只</div>
                <div class="stat-sub">信号分 30-49</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">🟡 可关注</div>
                <div class="stat-value flat">{watch_count} 只</div>
                <div class="stat-sub">信号分 &lt; 30</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">平均信号强度</div>
                <div class="stat-value">{avg_score:.1f}/100</div>
                <div class="stat-sub">整体偏多</div>
            </div>
        </div>

        <!-- 信号明细表 -->
        <div class="section-card">
            <div class="section-header">
                <h3>📡 买入信号清单（按强度排序）</h3>
                <span class="update-time">检测时间：{update_time}</span>
            </div>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th class="rank-col">排名</th>
                            <th class="code-col">代码</th>
                            <th class="name-col">名称</th>
                            <th class="price-col">现价</th>
                            <th class="score-col">信号分</th>
                            <th class="level-col">操作建议</th>
                            <th class="buy-col">买入价</th>
                            <th class="target-col">目标价</th>
                            <th class="signals-col">触发信号</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- 信号说明 -->
        <div class="notice-card">
            <div class="notice-icon">💡</div>
            <div class="notice-content">
                <strong>买入信号说明</strong>
                <p>信号基于以下技术指标综合评分：MA5金叉MA10、MACD金叉、KDJ金叉、站上60日均线、回踩20日线、量能放大、接近买入价等。信号分越高，技术面共振越强。</p>
                <p class="warn-text">⚠️ 技术信号具有概率属性，不构成投资建议，请结合自身判断决策，严格设置止损。</p>
            </div>
        </div>
    </div>
    '''


def generate_report_tab(pool_data):
    """生成票池报告标签页内容"""
    if not pool_data or not pool_data.get('pools'):
        return '<p class="empty-tip">暂无票池数据</p>'

    current_pool = pool_data['pools'][-1]
    stocks = current_pool['stocks']
    period = current_pool['period']

    # 按综合评分排序
    sorted_stocks = sorted(stocks, key=lambda x: x['total_score'], reverse=True)

    cards_html = ''
    for i, s in enumerate(sorted_stocks):
        ret_pct = s['period_return_pct']
        ret_class = 'up' if ret_pct > 0 else 'down' if ret_pct < 0 else 'flat'
        ret_sign = '+' if ret_pct > 0 else ''

        # Get logic fields with defaults if missing
        potential_logic = s.get('potential_logic', '暂无分析')
        tech_logic = s.get('tech_logic', '暂无技术面分析')

        # 留存股特殊标记
        retained_badge = ''
        retained_info = ''
        if s.get('is_retained'):
            retained_badge = '<span class="retained-badge-card">⭐ 留存股</span>'
            prev_ret_text = ''
            if 'prev_period_return_pct' in s:
                prev_ret_text = f'<div class="retained-history">上期涨幅: {s["prev_period_return_pct"]:+.2f}%</div>'
            retained_count_text = ''
            if s.get('retained_count', 0) > 0:
                retained_count_text = f' · 已留存{s["retained_count"]}期'
            retained_info = f'<div class="retained-info-block"><span class="retained-entry">原始入场价: ¥{s["entry_price"]:.2f}</span>{retained_count_text}</div>{prev_ret_text}'
            ret_label = '累计收益'
        else:
            retained_badge = ''
            retained_info = ''
            ret_label = '本期收益'

        cards_html += f'''
        <div class="stock-card{' retained-card' if s.get('is_retained') else ''}">
            <div class="stock-card-header">
                <div class="stock-rank">#{i+1}</div>
                <div class="stock-title">
                    <h4>{s['name']} {retained_badge}</h4>
                    <span class="stock-code">{s['code']}</span>
                    <span class="market-tag">{s['market']}</span>
                </div>
                <div class="stock-price">
                    <div class="price">¥{s['current_price']:.2f}</div>
                    <div class="change {ret_class}">{ret_sign}{ret_pct:.2f}%</div>
                    <div class="ret-label-card">{ret_label}</div>
                </div>
            </div>
            <div class="stock-card-body">
                {retained_info}
                <div class="info-grid">
                    <div class="info-item">
                        <span class="info-label">综合评分</span>
                        <span class="info-value">{s['total_score']:.1f}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">半年潜力</span>
                        <span class="info-value up">+{s['potential_pct']}%</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">建议买入价</span>
                        <span class="info-value">¥{s['buy_price']:.2f}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">目标价</span>
                        <span class="info-value target">¥{s['target_price']:.2f}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">止损价</span>
                        <span class="info-value down">¥{s['stop_loss']:.2f}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">支撑位</span>
                        <span class="info-value">¥{s['support']:.2f}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">压力位</span>
                        <span class="info-value">¥{s['resistance']:.2f}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">量比</span>
                        <span class="info-value">{s.get('volume_ratio', 0):.2f}</span>
                    </div>
                </div>
                <div class="logic-section">
                    <div class="logic-title">🎯 潜力逻辑</div>
                    <p class="logic-text">{potential_logic}</p>
                </div>
                <div class="logic-section">
                    <div class="logic-title">📊 技术面逻辑</div>
                    <p class="logic-text">{tech_logic}</p>
                </div>
            </div>
        </div>
        '''

    return f'''
    <div class="tab-content" id="tab-report">
        <div class="report-intro">
            <h3>📈 第{period}期高潜力股票池报告</h3>
            <p>从沪深主板+创业板3500+只股票中，基于六大技术维度（均线趋势、MACD动量、KDJ位置、布林带空间、量能变化、回��幅度）综合评分筛选。优先展示半年涨幅潜力≥40%的股票。</p>
        </div>
        <div class="stock-cards-grid">
            {cards_html}
        </div>
    </div>
    '''


def generate_history_tab(pool_data):
    """生成历史记录标签页内容"""
    if not pool_data or not pool_data.get('pools'):
        return '<p class="empty-tip">暂无历史数据</p>'

    pools = pool_data['pools']

    timeline_html = ''
    for pool in reversed(pools):
        stocks = pool['stocks']
        avg_return = sum(s['period_return_pct'] for s in stocks) / len(stocks) if stocks else 0
        ret_class = 'up' if avg_return > 0 else 'down' if avg_return < 0 else 'flat'
        ret_sign = '+' if avg_return > 0 else ''

        # 股票列表
        stock_list_html = ''
        for s in stocks:
            ret = s['period_return_pct']
            rc = 'up' if ret > 0 else 'down' if ret < 0 else 'flat'
            rs = '+' if ret > 0 else ''
            retained = ' <span class="mini-tag retained">留</span>' if s.get('is_retained') else ''
            stock_list_html += f'''
            <div class="history-stock">
                <span class="h-code">{s['code']}</span>
                <span class="h-name">{s['name']}</span>
                <span class="h-return {rc}">{rs}{ret:.2f}%</span>
                {retained}
            </div>
            '''

        retained_count = sum(1 for s in stocks if s.get('is_retained'))
        new_count = len(stocks) - retained_count

        timeline_html += f'''
        <div class="history-item">
            <div class="history-dot"></div>
            <div class="history-card">
                <div class="history-header">
                    <span class="period-badge">第 {pool['period']} 期</span>
                    <span class="history-date">{pool['create_date']}</span>
                    <span class="history-return {ret_class}">{ret_sign}{avg_return:.2f}%</span>
                </div>
                <div class="history-meta">
                    <span>共 {len(stocks)} 只</span>
                    <span>留存 {retained_count} 只</span>
                    <span>新进 {new_count} 只</span>
                </div>
                <div class="history-stocks">
                    {stock_list_html}
                </div>
            </div>
        </div>
        '''

    return f'''
    <div class="tab-content" id="tab-history">
        <div class="history-intro">
            <h3>📜 票池历史档案</h3>
            <p>每两个月更新一次票池。老票池保留涨幅前2名，补充8只新高潜力股。新股不与上一期留池的前2名重复。</p>
        </div>
        <div class="timeline">
            {timeline_html}
        </div>
    </div>
    '''


def generate_ops_tab():
    """生成操作指南标签页内容"""
    return '''
    <div class="tab-content" id="tab-ops">
        <div class="ops-grid">
            <div class="op-card">
                <div class="op-icon">🔄</div>
                <h3>更新当前价格</h3>
                <p>拉取最新行情，更新所有持仓股票的现价和收益率。</p>
                <div class="op-command">
                    <code>python3 pool_manager.py update</code>
                </div>
                <button class="op-btn" onclick="copyCmd('python3 pool_manager.py update')">📋 复制命令</button>
            </div>

            <div class="op-card">
                <div class="op-icon">📡</div>
                <h3>检查买入信号</h3>
                <p>检测当前票池的技术面买入信号，按强度排序展示。</p>
                <div class="op-command">
                    <code>python3 pool_manager.py update</code>
                </div>
                <p class="op-note">（更新价格时自动检测买入信号）</p>
            </div>

            <div class="op-card highlight">
                <div class="op-icon">🆕</div>
                <h3>生成新一期票池</h3>
                <p>从全市场重新筛选高潜力股票，老票池留前2名，补充8只新股。</p>
                <div class="op-command">
                    <code>python3 pool_manager.py new-period</code>
                </div>
                <button class="op-btn primary" onclick="copyCmd('python3 pool_manager.py new-period')">📋 复制命令</button>
                <p class="op-note warn">⚠️ 建议每两个月运行一次</p>
            </div>

            <div class="op-card">
                <div class="op-icon">📊</div>
                <h3>查看当前状态</h3>
                <p>在终端快速查看票池当前状态和持仓收益。</p>
                <div class="op-command">
                    <code>python3 pool_manager.py status</code>
                </div>
                <button class="op-btn" onclick="copyCmd('python3 pool_manager.py status')">📋 复制命令</button>
            </div>

            <div class="op-card">
                <div class="op-icon">🔍</div>
                <h3>重新全市场选股</h3>
                <p>扫描全市场股票，重新筛选高潜力标的（耗时较长）。</p>
                <div class="op-command">
                    <code>python3 stock_screener.py</code>
                </div>
                <button class="op-btn" onclick="copyCmd('python3 stock_screener.py')">📋 复制命令</button>
            </div>

            <div class="op-card">
                <div class="op-icon">🌐</div>
                <h3>刷新本页面</h3>
                <p>每次运行命令后，刷新此页面即可看到最新数据。</p>
                <button class="op-btn" onclick="location.reload()">🔄 刷新页面</button>
            </div>
        </div>

        <div class="section-card">
            <div class="section-header">
                <h3>📁 文件说明</h3>
            </div>
            <div class="file-list">
                <div class="file-item">
                    <span class="file-icon">📄</span>
                    <div class="file-info">
                        <strong>index.html</strong>
                        <p>本页面，票池仪表盘首页（整合所有功能）</p>
                    </div>
                </div>
                <div class="file-item">
                    <span class="file-icon">🐍</span>
                    <div class="file-info">
                        <strong>pool_manager.py</strong>
                        <p>票池管理器（更新价格、生成新一期、状态查询）</p>
                    </div>
                </div>
                <div class="file-item">
                    <span class="file-icon">🐍</span>
                    <div class="file-info">
                        <strong>stock_screener.py</strong>
                        <p>量化选股脚本（全市场扫描+技术面评分）</p>
                    </div>
                </div>
                <div class="file-item">
                    <span class="file-icon">📊</span>
                    <div class="file-info">
                        <strong>stock_pool_history.json</strong>
                        <p>票池历史数据（每期数据存档）</p>
                    </div>
                </div>
                <div class="file-item">
                    <span class="file-icon">📈</span>
                    <div class="file-info">
                        <strong>stock_screen_results.csv</strong>
                        <p>全市场选股结果（197只潜力股完整数据）</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="notice-card">
            <div class="notice-icon">⚠️</div>
            <div class="notice-content">
                <strong>风险提示</strong>
                <p>本系统基于技术面量化模型生成，仅供研究参考，<strong>不构成任何投资建议</strong>。涨幅潜力为技术面估算值，实际收益受市场环境、政策变化、公司基本面等多重因素影响，存在较大不确定性。股市有风险，入市需谨慎。</p>
            </div>
        </div>
    </div>
    '''


def generate_html(pool_data, analysis_data):
    """生成完整的HTML"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    status_tab = generate_status_tab(pool_data)
    signals_tab = generate_signals_tab(analysis_data)
    report_tab = generate_report_tab(pool_data)
    history_tab = generate_history_tab(pool_data)
    ops_tab = generate_ops_tab()

    period = pool_data['pools'][-1]['period'] if pool_data and pool_data.get('pools') else 1

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>股票池仪表盘 - 第{period}期</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    background: #f0f2f5;
    color: #1a1a2e;
    line-height: 1.6;
}}

/* 顶部导航 */
.header {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: white;
    padding: 20px 30px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    position: sticky;
    top: 0;
    z-index: 100;
}}

.header-content {{
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 15px;
}}

.header h1 {{
    font-size: 22px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 10px;
}}

.header h1 .emoji {{ font-size: 26px; }}

.header-sub {{
    font-size: 13px;
    opacity: 0.8;
}}

.header-time {{
    font-size: 12px;
    opacity: 0.7;
}}

/* 标签导航 */
.tabs {{
    background: white;
    border-bottom: 1px solid #e8e8e8;
    position: sticky;
    top: 72px;
    z-index: 99;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}}

.tabs-inner {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 30px;
    display: flex;
    gap: 0;
    overflow-x: auto;
}}

.tab-btn {{
    padding: 14px 24px;
    border: none;
    background: none;
    font-size: 14px;
    cursor: pointer;
    color: #666;
    border-bottom: 3px solid transparent;
    transition: all 0.2s;
    white-space: nowrap;
    font-weight: 500;
}}

.tab-btn:hover {{
    color: #1890ff;
    background: #f0f7ff;
}}

.tab-btn.active {{
    color: #1890ff;
    border-bottom-color: #1890ff;
    font-weight: 600;
}}

.tab-btn .tab-icon {{ margin-right: 6px; }}

/* 主内容区 */
.main {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 24px 30px;
}}

.tab-content {{ display: none; }}
.tab-content.active {{ display: block; animation: fadeIn 0.3s ease; }}

@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

/* 概览卡片 */
.overview-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
}}

.stat-card {{
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    transition: transform 0.2s, box-shadow 0.2s;
}}

.stat-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}}

.stat-label {{
    font-size: 13px;
    color: #888;
    margin-bottom: 8px;
}}

.stat-value {{
    font-size: 26px;
    font-weight: 700;
    margin-bottom: 4px;
}}

.stat-value.up {{ color: #f5222d; }}
.stat-value.down {{ color: #52c41a; }}
.stat-value.warn {{ color: #fa8c16; }}
.stat-value.flat {{ color: #8c8c8c; }}

.stat-sub {{
    font-size: 12px;
    color: #aaa;
}}

/* 区块卡片 */
.section-card {{
    background: white;
    border-radius: 12px;
    margin-bottom: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    overflow: hidden;
}}

.section-header {{
    padding: 18px 24px;
    border-bottom: 1px solid #f0f0f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
}}

.section-header h3 {{
    font-size: 16px;
    font-weight: 600;
}}

.update-time {{
    font-size: 12px;
    color: #999;
}}

/* 表格 */
.table-wrapper {{
    overflow-x: auto;
}}

.data-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}}

.data-table th {{
    background: #fafafa;
    padding: 12px 14px;
    text-align: left;
    font-weight: 600;
    color: #555;
    border-bottom: 1px solid #f0f0f0;
    white-space: nowrap;
    position: sticky;
    top: 0;
}}

.data-table td {{
    padding: 12px 14px;
    border-bottom: 1px solid #f5f5f5;
}}

.data-table tbody tr:hover {{
    background: #f9f9f9;
}}

.data-table .up {{ color: #f5222d; font-weight: 600; }}
.data-table .down {{ color: #52c41a; font-weight: 600; }}
.data-table .flat {{ color: #8c8c8c; }}

.rank-col {{ width: 60px; text-align: center; }}
.code-col {{ width: 80px; font-family: monospace; }}
.name-col {{ min-width: 140px; }}
.price-col, .return-col, .potential-col, .target-col, .buy-col, .stop-col, .score-col {{
    text-align: right;
    white-space: nowrap;
}}

.market-label {{
    font-size: 11px;
    color: #999;
    margin-top: 2px;
}}

/* 标签 */
.tag {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    margin-left: 6px;
    vertical-align: middle;
}}

.tag.new {{ background: #e6f7ff; color: #1890ff; }}
.tag.retained {{ background: #fff7e6; color: #fa8c16; }}
.tag.retained-count {{ background: #fff0f6; color: #eb2f96; font-size: 10px; }}

/* 留存股样式 */
.entry-original {{
    color: #722ed1;
    font-weight: 600;
}}
.ret-main {{
    font-weight: 700;
}}
.ret-label {{
    font-size: 10px;
    color: #999;
}}
.prev-return {{
    font-size: 10px;
    color: #888;
    margin-top: 2px;
}}

/* 排名徽章 */
.rank-badge {{
    display: inline-block;
    margin-right: 4px;
    font-size: 14px;
}}

/* 信号分圆环 */
.score-ring {{
    --score: 50;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: conic-gradient(
        #f5222d calc(var(--score) * 1%),
        #e8e8e8 0
    );
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}}

.score-ring::before {{
    content: '';
    position: absolute;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: white;
}}

.score-ring span {{
    position: relative;
    font-size: 12px;
    font-weight: 700;
    color: #333;
}}

/* 信号等级 */
.signal-level {{
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;
}}

.signal-level.strong-buy {{ background: #fff1f0; color: #f5222d; }}
.signal-level.buy {{ background: #fff7e6; color: #fa8c16; }}
.signal-level.watch {{ background: #feffe6; color: #a0d911; }}

/* 信号徽章列表 */
.signal-list {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    max-width: 250px;
}}

.signal-badge {{
    background: #f0f5ff;
    color: #2f54eb;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    white-space: nowrap;
}}

/* 通知卡片 */
.notice-card {{
    background: linear-gradient(135deg, #e6f7ff 0%, #f0f5ff 100%);
    border-radius: 12px;
    padding: 20px 24px;
    display: flex;
    gap: 16px;
    align-items: flex-start;
    margin-bottom: 24px;
}}

.notice-icon {{
    font-size: 32px;
    flex-shrink: 0;
}}

.notice-content strong {{
    display: block;
    margin-bottom: 6px;
    font-size: 15px;
}}

.notice-content p {{
    font-size: 13px;
    color: #555;
    line-height: 1.7;
}}

.warn-text {{ color: #f5222d !important; font-weight: 500; }}

/* 报告页 - 股票卡片网格 */
.report-intro {{
    background: white;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}}

.report-intro h3 {{
    font-size: 18px;
    margin-bottom: 8px;
}}

.report-intro p {{
    font-size: 14px;
    color: #666;
}}

.stock-cards-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 20px;
}}

.stock-card {{
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
}}

.stock-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.1);
}}

/* 留存股卡片样式 */
.stock-card.retained-card {{
    border: 2px solid #fa8c16;
    background: linear-gradient(135deg, #fffbe6 0%, #ffffff 30%);
}}
.retained-badge-card {{
    font-size: 12px;
    background: linear-gradient(135deg, #fa8c16, #faad14);
    color: white;
    padding: 2px 8px;
    border-radius: 10px;
    vertical-align: middle;
    margin-left: 6px;
}}
.retained-info-block {{
    background: #fff7e6;
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 12px;
    font-size: 12px;
}}
.retained-entry {{
    color: #722ed1;
    font-weight: 600;
}}
.retained-history {{
    font-size: 11px;
    color: #888;
    margin-top: 4px;
}}
.ret-label-card {{
    font-size: 11px;
    color: #999;
}}

.stock-card-header {{
    padding: 16px 20px;
    background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
    border-bottom: 1px solid #f0f0f0;
    display: flex;
    align-items: center;
    gap: 12px;
}}

.stock-rank {{
    font-size: 20px;
    font-weight: 800;
    color: #1890ff;
    min-width: 40px;
}}

.stock-title {{
    flex: 1;
}}

.stock-title h4 {{
    font-size: 16px;
    margin-bottom: 4px;
}}

.stock-code {{
    font-family: monospace;
    color: #888;
    font-size: 13px;
    margin-right: 8px;
}}

.market-tag {{
    font-size: 11px;
    color: #1890ff;
    background: #e6f7ff;
    padding: 2px 6px;
    border-radius: 4px;
}}

.stock-price {{
    text-align: right;
}}

.stock-price .price {{
    font-size: 20px;
    font-weight: 700;
}}

.stock-price .change {{
    font-size: 13px;
    font-weight: 600;
}}

.stock-card-body {{
    padding: 16px 20px;
}}

.info-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 16px;
}}

.info-item {{
    text-align: center;
}}

.info-label {{
    display: block;
    font-size: 11px;
    color: #999;
    margin-bottom: 4px;
}}

.info-value {{
    font-size: 14px;
    font-weight: 600;
}}

.info-value.up {{ color: #f5222d; }}
.info-value.down {{ color: #52c41a; }}
.info-value.target {{ color: #722ed1; }}

.logic-section {{
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px dashed #f0f0f0;
}}

.logic-title {{
    font-size: 12px;
    font-weight: 600;
    color: #555;
    margin-bottom: 6px;
}}

.logic-text {{
    font-size: 12px;
    color: #666;
    line-height: 1.6;
}}

/* 历史时间线 */
.history-intro {{
    background: white;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}}

.timeline {{
    position: relative;
    padding-left: 30px;
}}

.timeline::before {{
    content: '';
    position: absolute;
    left: 10px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #e8e8e8;
}}

.history-item {{
    position: relative;
    margin-bottom: 20px;
}}

.history-dot {{
    position: absolute;
    left: -25px;
    top: 20px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #1890ff;
    border: 3px solid white;
    box-shadow: 0 0 0 2px #1890ff;
}}

.history-card {{
    background: white;
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}}

.history-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
}}

.period-badge {{
    background: linear-gradient(135deg, #1890ff, #096dd9);
    color: white;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 13px;
    font-weight: 600;
}}

.history-date {{
    font-size: 13px;
    color: #888;
}}

.history-return {{
    margin-left: auto;
    font-size: 16px;
    font-weight: 700;
}}

.history-return.up {{ color: #f5222d; }}
.history-return.down {{ color: #52c41a; }}

.history-meta {{
    display: flex;
    gap: 16px;
    font-size: 12px;
    color: #999;
    margin-bottom: 12px;
}}

.history-stocks {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 8px;
}}

.history-stock {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    background: #fafafa;
    border-radius: 6px;
    font-size: 12px;
}}

.h-code {{
    font-family: monospace;
    color: #888;
}}

.h-name {{
    flex: 1;
    font-weight: 500;
}}

.h-return.up {{ color: #f5222d; font-weight: 600; }}
.h-return.down {{ color: #52c41a; font-weight: 600; }}

.mini-tag {{
    font-size: 10px;
    padding: 1px 5px;
    border-radius: 3px;
}}

.mini-tag.retained {{
    background: #fff7e6;
    color: #fa8c16;
}}

/* 操作指南 */
.ops-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
    margin-bottom: 24px;
}}

.op-card {{
    background: white;
    border-radius: 12px;
    padding: 24px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    transition: transform 0.2s;
}}

.op-card:hover {{
    transform: translateY(-2px);
}}

.op-card.highlight {{
    border: 2px solid #1890ff;
    background: linear-gradient(135deg, #f0f7ff 0%, white 100%);
}}

.op-icon {{
    font-size: 40px;
    margin-bottom: 12px;
}}

.op-card h3 {{
    font-size: 16px;
    margin-bottom: 8px;
}}

.op-card p {{
    font-size: 13px;
    color: #666;
    margin-bottom: 14px;
}}

.op-command {{
    background: #1a1a2e;
    color: #4ade80;
    padding: 10px 14px;
    border-radius: 8px;
    font-family: monospace;
    font-size: 12px;
    margin-bottom: 12px;
    text-align: left;
    overflow-x: auto;
}}

.op-btn {{
    width: 100%;
    padding: 10px;
    border: 1px solid #d9d9d9;
    background: white;
    border-radius: 8px;
    cursor: pointer;
    font-size: 13px;
    transition: all 0.2s;
}}

.op-btn:hover {{
    border-color: #1890ff;
    color: #1890ff;
    background: #f0f7ff;
}}

.op-btn.primary {{
    background: #1890ff;
    color: white;
    border-color: #1890ff;
}}

.op-btn.primary:hover {{
    background: #40a9ff;
    color: white;
}}

.op-note {{
    margin-top: 10px !important;
    font-size: 11px !important;
    color: #999 !important;
}}

.op-note.warn {{ color: #fa8c16 !important; }}

/* 文件列表 */
.file-list {{
    padding: 8px 24px 20px;
}}

.file-item {{
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 0;
    border-bottom: 1px solid #f5f5f5;
}}

.file-item:last-child {{ border-bottom: none; }}

.file-icon {{
    font-size: 28px;
    width: 40px;
    text-align: center;
}}

.file-info strong {{
    display: block;
    font-size: 14px;
    margin-bottom: 2px;
}}

.file-info p {{
    font-size: 12px;
    color: #888;
}}

/* 空状态 */
.empty-tip {{
    text-align: center;
    padding: 60px 20px;
    color: #999;
    font-size: 14px;
}}

/* 复制提示 */
.copy-toast {{
    position: fixed;
    top: 100px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0,0,0,0.8);
    color: white;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    z-index: 9999;
    opacity: 0;
    transition: opacity 0.3s;
    pointer-events: none;
}}

.copy-toast.show {{
    opacity: 1;
}}

/* 响应式 */
@media (max-width: 768px) {{
    .header {{ padding: 15px 20px; }}
    .header h1 {{ font-size: 18px; }}
    .tabs-inner {{ padding: 0 15px; }}
    .tab-btn {{ padding: 12px 16px; font-size: 13px; }}
    .main {{ padding: 16px; }}
    .overview-grid {{ grid-template-columns: repeat(2, 1fr); gap: 10px; }}
    .stat-card {{ padding: 14px; }}
    .stat-value {{ font-size: 20px; }}
    .info-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .stock-cards-grid {{ grid-template-columns: 1fr; }}
    .ops-grid {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>

<div class="header">
    <div class="header-content">
        <div>
            <h1><span class="emoji">📈</span> 股票池仪表盘</h1>
            <div class="header-sub">第 {period} 期 · 沪深主板+创业板 · 半年潜力40%+优先</div>
        </div>
        <div class="header-time">生成时间：{current_time}</div>
    </div>
</div>

<div class="tabs">
    <div class="tabs-inner">
        <button class="tab-btn active" onclick="switchTab('status', this)">
            <span class="tab-icon">📊</span>当前状态
        </button>
        <button class="tab-btn" onclick="switchTab('signals', this)">
            <span class="tab-icon">🔴</span>买入信号
        </button>
        <button class="tab-btn" onclick="switchTab('report', this)">
            <span class="tab-icon">📈</span>票池报告
        </button>
        <button class="tab-btn" onclick="switchTab('history', this)">
            <span class="tab-icon">📜</span>历史记录
        </button>
        <button class="tab-btn" onclick="switchTab('ops', this)">
            <span class="tab-icon">⚙️</span>操作指南
        </button>
    </div>
</div>

<div class="main">
    {status_tab}
    {signals_tab}
    {report_tab}
    {history_tab}
    {ops_tab}
</div>

<div class="copy-toast" id="copyToast">✅ 已复制到剪贴板</div>

<script>
function switchTab(tabId, btn) {{
    // 隐藏所有标签内容
    document.querySelectorAll('.tab-content').forEach(el => {{
        el.classList.remove('active');
    }});
    // 显示选中的
    document.getElementById('tab-' + tabId).classList.add('active');
    // 更新按钮状态
    document.querySelectorAll('.tab-btn').forEach(b => {{
        b.classList.remove('active');
    }});
    btn.classList.add('active');
    // 保存到 localStorage
    localStorage.setItem('lastTab', tabId);
}}

// 恢复上次选中的标签
document.addEventListener('DOMContentLoaded', function() {{
    var lastTab = localStorage.getItem('lastTab');
    if (lastTab) {{
        var btns = document.querySelectorAll('.tab-btn');
        var tabMap = {{'status': 0, 'signals': 1, 'report': 2, 'history': 3, 'ops': 4}};
        if (tabMap[lastTab] !== undefined) {{
            btns[tabMap[lastTab]].click();
        }}
    }}
}});

function copyCmd(cmd) {{
    navigator.clipboard.writeText(cmd).then(function() {{
        var toast = document.getElementById('copyToast');
        toast.classList.add('show');
        setTimeout(function() {{
            toast.classList.remove('show');
        }}, 1500);
    }}).catch(function() {{
        // 降级方案
        var textarea = document.createElement('textarea');
        textarea.value = cmd;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        var toast = document.getElementById('copyToast');
        toast.classList.add('show');
        setTimeout(function() {{
            toast.classList.remove('show');
        }}, 1500);
    }});
}}
</script>

</body>
</html>'''

    return html


def main():
    """主函数：生成 index.html"""
    pool_data, analysis_data = load_data()

    if not pool_data:
        print("错误：未找到票池数据，请先运行 stock_screener.py 或 pool_manager.py")
        return

    html = generate_html(pool_data, analysis_data)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ index.html 已生成：{OUTPUT_FILE}")
    print(f"   票池期数：第 {pool_data['pools'][-1]['period']} 期")
    print(f"   股票数量：{len(pool_data['pools'][-1]['stocks'])} 只")


if __name__ == '__main__':
    main()
