#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高潜力股票筛选器 - 使用新浪数据源
筛选范围：沪市主板(600/601/603/605)、深市主板(000/001)、创业板(300/301)
筛选维度：动量、量能、技术突破
"""

import akshare as ak
import pandas as pd
import numpy as np
import time
import warnings
warnings.filterwarnings('ignore')

# 确保工作目录存在
os.makedirs('/workspace', exist_ok=True)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)

def get_stock_list():
    """获取A股股票列表（新浪数据源），筛选主板和创业板"""
    try:
        df = ak.stock_zh_a_spot()
        print(f"获取到 {len(df)} 只A股")
        
        # 提取纯代码（去掉sh/sz/bj前缀）
        df['code'] = df['代码'].str.extract(r'(\d{6})')
        
        # 筛选主板和创业板
        def get_market(code):
            if code.startswith('60'):
                return '沪市主板'
            elif code.startswith('000') or code.startswith('001'):
                return '深市主板'
            elif code.startswith('300') or code.startswith('301'):
                return '创业板'
            else:
                return '其他'
        
        df['市场'] = df['code'].apply(get_market)
        df = df[df['市场'].isin(['沪市主板', '深市主板', '创业板'])]
        print(f"筛选后主板+创业板共 {len(df)} 只")
        
        # 排除ST、*ST、退市股
        df = df[~df['名称'].str.contains('ST|退', na=False)]
        print(f"排除ST后退市股后共 {len(df)} 只")
        
        return df.reset_index(drop=True)
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_stock_history(full_code, days=500):
    """获取个股历史行情（新浪数据源）
    full_code: sh600519 或 sz000001 格式
    """
    try:
        end_date = pd.Timestamp.now().strftime('%Y%m%d')
        start_date = (pd.Timestamp.now() - pd.Timedelta(days=days)).strftime('%Y%m%d')
        df = ak.stock_zh_a_daily(symbol=full_code, start_date=start_date, 
                                 end_date=end_date, adjust="qfq")
        if df is None or len(df) == 0:
            return None
        df = df.sort_values('date').reset_index(drop=True)
        # 重命名列以匹配后续计算
        df = df.rename(columns={
            'date': '日期',
            'open': '开盘',
            'high': '最高',
            'low': '最低',
            'close': '收盘',
            'volume': '成交量',
            'amount': '成交额',
        })
        return df
    except Exception as e:
        return None

def calc_technical_indicators(df):
    """计算技术指标"""
    if df is None or len(df) < 60:
        return None
    
    close = df['收盘']
    high = df['最高']
    low = df['最低']
    volume = df['成交量']
    
    # 均线
    df['MA5'] = close.rolling(5).mean()
    df['MA10'] = close.rolling(10).mean()
    df['MA20'] = close.rolling(20).mean()
    df['MA60'] = close.rolling(60).mean()
    df['MA120'] = close.rolling(120).mean() if len(df) >= 120 else df['MA60']
    
    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df['DIF'] = ema12 - ema26
    df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
    df['MACD'] = 2 * (df['DIF'] - df['DEA'])
    
    # KDJ
    low_list = low.rolling(9, min_periods=1).min()
    high_list = high.rolling(9, min_periods=1).max()
    rsv = (close - low_list) / (high_list - low_list) * 100
    rsv = rsv.fillna(50)
    df['K'] = rsv.ewm(com=2, adjust=False).mean()
    df['D'] = df['K'].ewm(com=2, adjust=False).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    
    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI'] = df['RSI'].fillna(50)
    
    # 布林带
    df['BOLL_MID'] = close.rolling(20).mean()
    df['BOLL_STD'] = close.rolling(20).std()
    df['BOLL_UP'] = df['BOLL_MID'] + 2 * df['BOLL_STD']
    df['BOLL_LOW'] = df['BOLL_MID'] - 2 * df['BOLL_STD']
    
    # 成交量均线
    df['VOL_MA5'] = volume.rolling(5).mean()
    df['VOL_MA20'] = volume.rolling(20).mean()
    
    # 涨幅
    df['涨跌幅'] = close.pct_change() * 100
    
    return df

def estimate_growth_potential(hist):
    """估算未来半年涨幅潜力
    基于技术面、动量、突破信号综合评估
    """
    if hist is None or len(hist) < 60:
        return 0, "数据不足"
    
    latest = hist.iloc[-1]
    close = latest['收盘']
    ma60 = latest['MA60']
    
    potential = 0
    reasons = []
    
    # 1. 基于均线空间估算 (20%)
    if close < ma60 * 1.05:
        potential += 20
        reasons.append("靠近60日线，突破后空间大")
    elif close < ma60 * 1.15:
        potential += 15
        reasons.append("略高于60日线")
    else:
        potential += 8
        reasons.append("已远离60日线")
    
    # 2. 基于布林带位置 (15%)
    boll_up = latest['BOLL_UP']
    boll_mid = latest['BOLL_MID']
    if close < boll_mid:
        potential += 15
        reasons.append("布林中轨下方，回归空间大")
    elif close < boll_up:
        potential += 10
        reasons.append("布林中上部，仍有空间")
    else:
        potential += 5
        reasons.append("布林上轨附近")
    
    # 3. 基于动量趋势 (25%)
    dif = latest['DIF']
    dea = latest['DEA']
    if dif > dea and dif < 0:
        potential += 25
        reasons.append("MACD底部金叉，反弹动能强")
    elif dif > dea and dif > 0:
        potential += 18
        reasons.append("MACD零上金叉，趋势延续")
    elif dif < dea and dif > 0:
        potential += 10
        reasons.append("MACD零上死叉，回调中")
    else:
        potential += 5
        reasons.append("MACD空头")
    
    # 4. 基于近期回调幅度 (20%)
    if len(hist) >= 60:
        high_60 = hist.iloc[-60:]['最高'].max()
        drawdown = (high_60 - close) / high_60 * 100
        if drawdown > 30:
            potential += 20
            reasons.append(f"较60日高点回调{drawdown:.0f}%，超跌反弹")
        elif drawdown > 20:
            potential += 15
            reasons.append(f"较60日高点回调{drawdown:.0f}%，回调充分")
        elif drawdown > 10:
            potential += 10
            reasons.append(f"较60日高点回调{drawdown:.0f}%")
        else:
            potential += 5
            reasons.append(f"接近60日高点")
    
    # 5. 基于量能变化 (10%)
    vol_ratio = latest['成交量'] / latest['VOL_MA20'] if latest['VOL_MA20'] > 0 else 1
    if vol_ratio > 2:
        potential += 10
        reasons.append("放量启动")
    elif vol_ratio > 1.5:
        potential += 8
        reasons.append("量能放大")
    elif vol_ratio > 1:
        potential += 5
        reasons.append("量能温和")
    else:
        potential += 3
        reasons.append("缩量")
    
    # 6. KDJ位置 (10%)
    k = latest['K']
    if k < 30:
        potential += 10
        reasons.append("KDJ超卖，反弹在即")
    elif k < 50:
        potential += 7
        reasons.append("KDJ中低位")
    elif k < 70:
        potential += 5
        reasons.append("KDJ中位偏多")
    else:
        potential += 2
        reasons.append("KDJ超买")
    
    return potential, "；".join(reasons)

def score_stock(full_code, code, name, market):
    """对单只股票进行综合评分和潜力评估"""
    hist = get_stock_history(full_code, days=500)
    if hist is None or len(hist) < 60:
        return None
    
    hist = calc_technical_indicators(hist)
    if hist is None:
        return None
    
    latest = hist.iloc[-1]
    close = latest['收盘']
    
    # 估算涨幅潜力
    potential, potential_reasons = estimate_growth_potential(hist)
    
    # 技术面评分
    tech_score = 0
    tech_reasons = []
    
    # 趋势
    ma5 = latest['MA5']
    ma10 = latest['MA10']
    ma20 = latest['MA20']
    ma60 = latest['MA60']
    
    if ma5 > ma10 > ma20 > ma60:
        tech_score += 25
        tech_reasons.append("完美多头")
    elif ma5 > ma10 > ma20:
        tech_score += 18
        tech_reasons.append("短期多头")
    elif close > ma60:
        tech_score += 10
        tech_reasons.append("站上60日线")
    
    # MACD
    if latest['DIF'] > latest['DEA']:
        tech_score += 15
        tech_reasons.append("MACD金叉")
    
    # KDJ
    if latest['K'] > latest['D'] and latest['K'] < 70:
        tech_score += 10
        tech_reasons.append("KDJ金叉未超买")
    
    # 量比
    vol_ratio = latest['成交量'] / latest['VOL_MA20'] if latest['VOL_MA20'] > 0 else 1
    if vol_ratio > 1.5:
        tech_score += 10
        tech_reasons.append(f"量比{vol_ratio:.1f}")
    
    # 20日涨幅
    if len(hist) >= 20:
        price_20 = hist.iloc[-20]['收盘']
        change_20 = (close - price_20) / price_20 * 100
    else:
        change_20 = 0
    
    # 突破20日新高
    if len(hist) >= 20:
        high_20 = hist.iloc[-20:-1]['最高'].max()
        if close > high_20:
            tech_score += 10
            tech_reasons.append("突破20日新高")
    
    # 支撑压力位
    support = round(min(ma20, ma60, latest['BOLL_LOW']), 2)
    resistance = round(latest['BOLL_UP'], 2)
    
    # 买卖点建议
    buy_point = round(ma20 * 0.98, 2)  # 回踩20日线附近
    sell_target = round(close * (1 + potential/100), 2)
    stop_loss = round(support * 0.97, 2)  # 跌破支撑位止损
    
    return {
        '代码': code,
        '名称': name,
        '市场': market,
        '最新价': round(close, 2),
        '估算半年涨幅潜力%': round(potential, 1),
        '技术面评分': tech_score,
        '综合评分': round(potential * 0.6 + tech_score * 0.4, 1),
        '潜力逻辑': potential_reasons,
        '技术面逻辑': '；'.join(tech_reasons),
        'MA5': round(ma5, 2),
        'MA10': round(ma10, 2),
        'MA20': round(ma20, 2),
        'MA60': round(ma60, 2),
        'MACD_DIF': round(latest['DIF'], 3),
        'MACD_DEA': round(latest['DEA'], 3),
        'KDJ_K': round(latest['K'], 2),
        'KDJ_D': round(latest['D'], 2),
        'RSI': round(latest['RSI'], 2),
        '量比': round(vol_ratio, 2),
        '20日涨幅%': round(change_20, 2),
        '布林上轨': round(latest['BOLL_UP'], 2),
        '布林中轨': round(latest['BOLL_MID'], 2),
        '布林下轨': round(latest['BOLL_LOW'], 2),
        '支撑位': support,
        '压力位': resistance,
        '建议买入价': buy_point,
        '目标价(半年)': sell_target,
        '止损价': stop_loss,
    }

def main():
    print("=" * 70)
    print("高潜力股票筛选器 - 主板+创业板")
    print("数据源: 新浪财经 | 分析方法: 技术面+动量综合评分")
    print("=" * 70)
    
    # 获取股票列表
    stock_df = get_stock_list()
    if stock_df is None:
        print("获取股票列表失败")
        return
    
    # 按成交额排序，取前200只成交活跃股进行技术面分析
    stock_df = stock_df.sort_values('成交额', ascending=False)
    candidates = stock_df.head(200)
    
    print(f"\n开始分析前 {len(candidates)} 只成交活跃股票...")
    
    results = []
    count = 0
    errors = 0
    
    for _, row in candidates.iterrows():
        count += 1
        full_code = row['代码']  # sh600519 格式
        code = row['code']
        name = row['名称']
        market = row['市场']
        
        if count % 20 == 0:
            print(f"  已分析 {count}/{len(candidates)} 只... (成功:{len(results)} 失败:{errors})")
        
        try:
            result = score_stock(full_code, code, name, market)
            if result:
                results.append(result)
            else:
                errors += 1
        except Exception as e:
            errors += 1
            continue
        
        # 控制请求频率，避免被限流
        time.sleep(0.1)
    
    print(f"\n分析完成: 成功 {len(results)} 只，失败 {errors} 只")
    
    if len(results) == 0:
        print("无有效结果")
        return
    
    # 转为DataFrame
    results_df = pd.DataFrame(results)
    
    # 排序规则：
    # 1. 优先显示涨幅潜力>=40%的
    # 2. 其余按综合评分排序
    results_df['优先等级'] = results_df['估算半年涨幅潜力%'].apply(lambda x: 1 if x >= 40 else 2)
    results_df = results_df.sort_values(['优先等级', '综合评分'], ascending=[True, False]).reset_index(drop=True)
    
    # 保存完整结果
    results_df.to_csv('/workspace/stock_screen_results.csv', index=False, encoding='utf-8-sig')
    print(f"\n完整结果已保存到 /workspace/stock_screen_results.csv")
    
    # 显示TOP 15
    print("\n" + "=" * 100)
    print("TOP 15 高潜力股票（40%+涨幅潜力优先，其余按综合评分排序）")
    print("=" * 100)
    display_cols = ['代码', '名称', '市场', '最新价', '估算半年涨幅潜力%', '综合评分', 
                    '20日涨幅%', '量比', '建议买入价', '目标价(半年)', '止损价']
    print(results_df[display_cols].head(15).to_string(index=False))
    
    # 显示40%以上的
    high_potential = results_df[results_df['估算半年涨幅潜力%'] >= 40]
    print(f"\n\n⭐ 涨幅潜力≥40%的股票共 {len(high_potential)} 只:")
    if len(high_potential) > 0:
        print(high_potential[display_cols].to_string(index=False))
    
    return results_df

if __name__ == '__main__':
    main()
