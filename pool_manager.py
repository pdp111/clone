#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
票池跟踪与更新系统
功能：
1. 记录每期票池数据
2. 计算持仓涨幅
3. 每两个月更新票池（留前2名 + 补8只新股）
4. 去重规则：新股不能是上期留池的前2名
"""

import json
import pandas as pd
from datetime import datetime
import os

POOL_FILE = './stock_pool_history.json'
SCREEN_FILE = './stock_screen_results.csv'

# 确保工作目录存在
os.makedirs('./data', exist_ok=True)

def init_pool():
    """初始化票池（第1期）"""
    df = pd.read_csv(SCREEN_FILE, dtype={'代码': str})
    df['代码'] = df['代码'].apply(lambda x: x.zfill(6))
    
    top10 = df.head(10)
    
    pool_data = {
        "version": "1.0",
        "pools": [
            {
                "period": 1,
                "create_date": datetime.now().strftime('%Y-%m-%d'),
                "update_date": datetime.now().strftime('%Y-%m-%d'),
                "stocks": [],
                "retained_from_prev": [],
                "new_stocks": []
            }
        ]
    }
    
    for _, row in top10.iterrows():
        stock = {
            "code": row['代码'],
            "name": row['名称'],
            "market": row['市场'],
            "entry_price": row['最新价'],
            "current_price": row['最新价'],
            "entry_date": datetime.now().strftime('%Y-%m-%d'),
            "potential_pct": row['估算半年涨幅潜力%'],
            "tech_score": row['技术面评分'],
            "total_score": row['综合评分'],
            "buy_price": row['建议买入价'],
            "target_price": row['目标价(半年)'],
            "stop_loss": row['止损价'],
            "support": row['支撑位'],
            "resistance": row['压力位'],
            "change_pct_20d": row['20日涨幅%'],
            "volume_ratio": row['量比'],
            "potential_logic": row['潜力逻辑'],
            "tech_logic": row['技术面逻辑'],
            "is_retained": False,  # 是否为上期留存
            "period_return_pct": 0.0,  # 本期收益率
        }
        pool_data["pools"][0]["stocks"].append(stock)
        pool_data["pools"][0]["new_stocks"].append(row['代码'])
    
    with open(POOL_FILE, 'w', encoding='utf-8') as f:
        json.dump(pool_data, f, ensure_ascii=False, indent=2)
    
    print(f"初始票池已创建，共 {len(top10)} 只股票")
    return pool_data

def load_pool():
    """加载票池数据"""
    if not os.path.exists(POOL_FILE):
        return None
    with open(POOL_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_pool(pool_data):
    """保存票池数据"""
    with open(POOL_FILE, 'w', encoding='utf-8') as f:
        json.dump(pool_data, f, ensure_ascii=False, indent=2)

def update_current_prices(pool_data):
    """更新当前价格（使用AKShare）"""
    import akshare as ak
    import warnings
    warnings.filterwarnings('ignore')
    
    current_pool = pool_data["pools"][-1]
    codes = [s["code"] for s in current_pool["stocks"]]
    
    try:
        # 获取实时行情
        df = ak.stock_zh_a_spot()
        df['pure_code'] = df['代码'].str.extract(r'(\d{6})')
        
        for stock in current_pool["stocks"]:
            match = df[df['pure_code'] == stock["code"]]
            if len(match) > 0:
                new_price = float(match.iloc[0]['最新价'])
                stock["current_price"] = new_price
                stock["period_return_pct"] = round(
                    (new_price - stock["entry_price"]) / stock["entry_price"] * 100, 2
                )
        
        current_pool["update_date"] = datetime.now().strftime('%Y-%m-%d')
        save_pool(pool_data)
        print(f"价格已更新，共更新 {len(codes)} 只股票")
        return True
    except Exception as e:
        print(f"更新价格失败: {e}")
        return False

def generate_new_pool(pool_data):
    """生成新一期票池
    规则：
    1. 老票池按本期涨幅排序，留前2名
    2. 从全市场重新筛选，排除上期留池的前2名
    3. 补充8只新股，凑满10只
    """
    import akshare as ak
    import numpy as np
    import time
    import warnings
    warnings.filterwarnings('ignore')
    
    current_pool = pool_data["pools"][-1]
    current_period = current_pool["period"]
    
    # 1. 计算上期每只股票的涨幅，排序取前2名
    sorted_stocks = sorted(current_pool["stocks"], 
                          key=lambda x: x["period_return_pct"], 
                          reverse=True)
    top2 = sorted_stocks[:2]
    top2_codes = [s["code"] for s in top2]
    
    print(f"\n上期票池涨幅排名前2:")
    for i, s in enumerate(top2):
        print(f"  {i+1}. {s['name']}({s['code']}): {s['period_return_pct']}%")
    
    # 2. 重新筛选全市场
    print("\n开始重新筛选全市场高潜力股票...")
    
    # 获取股票列表
    df = ak.stock_zh_a_spot()
    df['code'] = df['代码'].str.extract(r'(\d{6})')
    
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
    df = df[~df['名称'].str.contains('ST|退', na=False)]
    df = df.sort_values('成交额', ascending=False)
    candidates = df.head(200)
    
    # 计算每只股票的评分
    results = []
    count = 0
    
    for _, row in candidates.iterrows():
        count += 1
        full_code = row['代码']
        code = row['code']
        name = row['名称']
        market = row['市场']
        
        # 排除上期留池的前2名（去重规则）
        if code in top2_codes:
            continue
        
        if count % 40 == 0:
            print(f"  已筛选 {count}/{len(candidates)} 只...")
        
        try:
            # 获取历史行情
            end_date = pd.Timestamp.now().strftime('%Y%m%d')
            start_date = (pd.Timestamp.now() - pd.Timedelta(days=500)).strftime('%Y%m%d')
            hist = ak.stock_zh_a_daily(symbol=full_code, start_date=start_date, 
                                       end_date=end_date, adjust="qfq")
            
            if hist is None or len(hist) < 60:
                continue
            
            hist = hist.sort_values('date').reset_index(drop=True)
            hist = hist.rename(columns={
                'date': '日期', 'open': '开盘', 'high': '最高',
                'low': '最低', 'close': '收盘', 'volume': '成交量', 'amount': '成交额'
            })
            
            close = hist['收盘']
            high = hist['最高']
            low = hist['最低']
            volume = hist['成交量']
            
            # 计算技术指标
            ma5 = close.rolling(5).mean()
            ma10 = close.rolling(10).mean()
            ma20 = close.rolling(20).mean()
            ma60 = close.rolling(60).mean()
            
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            dif = ema12 - ema26
            dea = dif.ewm(span=9, adjust=False).mean()
            
            low_list = low.rolling(9, min_periods=1).min()
            high_list = high.rolling(9, min_periods=1).max()
            rsv = (close - low_list) / (high_list - low_list) * 100
            rsv = rsv.fillna(50)
            k = rsv.ewm(com=2, adjust=False).mean()
            d_val = k.ewm(com=2, adjust=False).mean()
            
            boll_mid = close.rolling(20).mean()
            boll_std = close.rolling(20).std()
            boll_up = boll_mid + 2 * boll_std
            boll_low = boll_mid - 2 * boll_std
            
            vol_ma20 = volume.rolling(20).mean()
            
            latest_close = close.iloc[-1]
            latest_dif = dif.iloc[-1]
            latest_dea = dea.iloc[-1]
            latest_k = k.iloc[-1]
            latest_ma60 = ma60.iloc[-1]
            latest_boll_up = boll_up.iloc[-1]
            latest_boll_mid = boll_mid.iloc[-1]
            latest_vol = volume.iloc[-1]
            latest_vol_ma20 = vol_ma20.iloc[-1]
            
            # 估算潜力
            potential = 0
            if latest_close < latest_ma60 * 1.05:
                potential += 20
            elif latest_close < latest_ma60 * 1.15:
                potential += 15
            else:
                potential += 8
            
            if latest_close < latest_boll_mid:
                potential += 15
            elif latest_close < latest_boll_up:
                potential += 10
            else:
                potential += 5
            
            if latest_dif > latest_dea and latest_dif < 0:
                potential += 25
            elif latest_dif > latest_dea and latest_dif > 0:
                potential += 18
            elif latest_dif < latest_dea and latest_dif > 0:
                potential += 10
            else:
                potential += 5
            
            if len(hist) >= 60:
                high_60 = hist.iloc[-60:]['最高'].max()
                drawdown = (high_60 - latest_close) / high_60 * 100
                if drawdown > 30:
                    potential += 20
                elif drawdown > 20:
                    potential += 15
                elif drawdown > 10:
                    potential += 10
                else:
                    potential += 5
            
            vol_ratio = latest_vol / latest_vol_ma20 if latest_vol_ma20 > 0 else 1
            if vol_ratio > 2:
                potential += 10
            elif vol_ratio > 1.5:
                potential += 8
            elif vol_ratio > 1:
                potential += 5
            else:
                potential += 3
            
            if latest_k < 30:
                potential += 10
            elif latest_k < 50:
                potential += 7
            elif latest_k < 70:
                potential += 5
            else:
                potential += 2
            
            # 技术面评分
            tech_score = 0
            latest_ma5 = ma5.iloc[-1]
            latest_ma10 = ma10.iloc[-1]
            latest_ma20 = ma20.iloc[-1]
            
            if latest_ma5 > latest_ma10 > latest_ma20 > latest_ma60:
                tech_score += 25
            elif latest_ma5 > latest_ma10 > latest_ma20:
                tech_score += 18
            elif latest_close > latest_ma60:
                tech_score += 10
            
            if latest_dif > latest_dea:
                tech_score += 15
            
            if latest_k > d_val.iloc[-1] and latest_k < 70:
                tech_score += 10
            
            if vol_ratio > 1.5:
                tech_score += 10
            
            if len(hist) >= 20:
                high_20 = hist.iloc[-20:-1]['最高'].max()
                if latest_close > high_20:
                    tech_score += 10
            
            total_score = round(potential * 0.6 + tech_score * 0.4, 1)
            
            results.append({
                'code': code,
                'name': name,
                'market': market,
                'latest_price': round(latest_close, 2),
                'potential_pct': potential,
                'tech_score': tech_score,
                'total_score': total_score,
                'ma20': round(latest_ma20, 2),
                'boll_up': round(latest_boll_up, 2),
                'boll_low': round(boll_low.iloc[-1], 2),
                'vol_ratio': round(vol_ratio, 2),
            })
            
        except Exception as e:
            continue
        
        time.sleep(0.1)
    
    # 排序
    results_df = pd.DataFrame(results)
    results_df['优先等级'] = results_df['potential_pct'].apply(lambda x: 1 if x >= 40 else 2)
    results_df = results_df.sort_values(['优先等级', 'total_score'], ascending=[True, False]).reset_index(drop=True)
    
    # 取前8只新股
    new_stocks = results_df.head(8)
    print(f"\n筛选出 {len(results)} 只候选股，选取前8只入池")
    
    # 3. 构建新票池（2只留存 + 8只新股 = 10只）
    new_pool = {
        "period": current_period + 1,
        "create_date": datetime.now().strftime('%Y-%m-%d'),
        "update_date": datetime.now().strftime('%Y-%m-%d'),
        "stocks": [],
        "retained_from_prev": top2_codes,
        "new_stocks": new_stocks['code'].tolist()
    }
    
    # 添加留存股（保留原始入场价和累计涨幅，不从头计算）
    for s in top2:
        retained_stock = s.copy()
        retained_stock["is_retained"] = True
        # 保留原始入场价，不重置为当前价
        # entry_price 保持原值不变
        # period_return_pct 保持原值不变（上期的累计涨幅带过来）
        # entry_date 保持原值不变（原始入场日期）
        # 记录上期涨幅，便于展示
        retained_stock["prev_period_return_pct"] = s["period_return_pct"]
        # 记录留存期数（第几次被留存）
        retained_stock["retained_count"] = s.get("retained_count", 0) + 1
        new_pool["stocks"].append(retained_stock)
    
    # 添加新股
    for _, row in new_stocks.iterrows():
        stock = {
            "code": row['code'],
            "name": row['name'],
            "market": row['market'],
            "entry_price": row['latest_price'],
            "current_price": row['latest_price'],
            "entry_date": datetime.now().strftime('%Y-%m-%d'),
            "potential_pct": row['potential_pct'],
            "tech_score": row['tech_score'],
            "total_score": row['total_score'],
            "buy_price": round(row['ma20'] * 0.98, 2),
            "target_price": round(row['latest_price'] * (1 + row['potential_pct']/100), 2),
            "stop_loss": round(min(row['ma20'], row['boll_low']) * 0.97, 2),
            "support": round(min(row['ma20'], row['boll_low']), 2),
            "resistance": round(row['boll_up'], 2),
            "is_retained": False,
            "period_return_pct": 0.0,
        }
        new_pool["stocks"].append(stock)
    
    # 添加到历史
    pool_data["pools"].append(new_pool)
    save_pool(pool_data)
    
    print(f"\n第 {current_period + 1} 期票池已生成：")
    print(f"  上期留存: {len(top2)} 只 (涨幅前2)")
    for i, s in enumerate(top2):
        print(f"    留存{i+1}: {s['name']}({s['code']}) "
              f"入场价:{s['entry_price']} 现价:{s['current_price']} "
              f"累计涨幅:{s['period_return_pct']:+.2f}%")
    print(f"  新进股票: {len(new_stocks)} 只")
    print(f"  合计: {len(new_pool['stocks'])} 只")
    
    return pool_data

def get_pool_summary():
    """获取票池摘要"""
    pool_data = load_pool()
    if not pool_data:
        return None
    
    current = pool_data["pools"][-1]
    print(f"\n{'='*60}")
    print(f"第 {current['period']} 期票池（{current['create_date']}）")
    print(f"{'='*60}")
    
    total_return = 0
    for i, s in enumerate(current["stocks"]):
        if s["is_retained"]:
            tag = "⭐留存"
            entry_info = f"入场:{s['entry_price']}(原始)"
            ret_info = f"累计收益:{s['period_return_pct']:+.2f}%"
            if "prev_period_return_pct" in s:
                ret_info += f" (上期:{s['prev_period_return_pct']:+.2f}%)"
        else:
            tag = "  新股"
            entry_info = f"入场:{s['entry_price']}"
            ret_info = f"收益:{s['period_return_pct']:+.2f}%"
        print(f"{tag} {i+1:2d}. {s['name']}({s['code']}) "
              f"现价:{s['current_price']} {entry_info} {ret_info}")
        total_return += s["period_return_pct"]
    
    avg_return = total_return / len(current["stocks"])
    print(f"\n平均收益: {avg_return:+.2f}%")
    
    return pool_data

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 pool_manager.py init       - 初始化票池")
        print("  python3 pool_manager.py update     - 更新当前价格")
        print("  python3 pool_manager.py new-period - 生成新一期票池")
        print("  python3 pool_manager.py status     - 查看当前票池状态")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'init':
        init_pool()
    elif cmd == 'update':
        pool = load_pool()
        if pool:
            update_current_prices(pool)
            get_pool_summary()
    elif cmd == 'new-period':
        pool = load_pool()
        if pool:
            generate_new_pool(pool)
    elif cmd == 'status':
        get_pool_summary()
    else:
        print(f"未知命令: {cmd}")
