from flask import Flask, jsonify, request, send_from_directory
import subprocess
import json
import os
import sys
from datetime import datetime

app = Flask(__name__, static_url_path='', static_folder='.')

# 存储运行日志
operation_log = []

def run_command(cmd):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        return {
            'success': result.returncode == 0,
            'output': result.stdout + '\n' + result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': '命令执行超时（5分钟）',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'output': f'执行异常: {str(e)}',
            'returncode': -2
        }

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/operation', methods=['POST'])
def run_operation():
    data = request.get_json()
    op_type = data.get('type')
    
    cmd_map = {
        'update': 'python3 pool_manager.py update',
        'new-period': 'python3 pool_manager.py new-period',
        'status': 'python3 pool_manager.py status',
        'screen': 'python3 stock_screener.py'
    }
    
    if op_type not in cmd_map:
        return jsonify({'success': False, 'output': '未知操作类型'})
    
    cmd = cmd_map[op_type]
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    operation_log.append(f"[{timestamp}] 开始执行: {cmd}")
    
    result = run_command(cmd)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if result['success']:
        operation_log.append(f"[{timestamp}] 执行成功 ✓")
    else:
        operation_log.append(f"[{timestamp}] 执行失败 ✗ 退出码: {result['returncode']}")
    
    operation_log.append("--- 输出开始 ---")
    operation_log.extend(result['output'].splitlines())
    operation_log.append("--- 输出结束 ---")
    operation_log.append("")
    
    # 保持日志只保留最近1000行
    if len(operation_log) > 1000:
        operation_log[:] = operation_log[-1000:]
    
    return jsonify({
        'success': result['success'],
        'output': result['output'],
        'log': '\n'.join(operation_log)
    })

@app.route('/api/log')
def get_log():
    return jsonify({'log': '\n'.join(operation_log)})

@app.route('/api/reload')
def reload_html():
    """重新读取最新的index.html"""
    # 这个接口只是告诉前端可以刷新了
    return jsonify({'success': True})

@app.route('/api/pool')
def get_pool_data():
    """获取最新股票池数据"""
    pool_file = 'stock_pool.json'
    screener_file = 'screener_result.json'
    
    result = {
        'pool': None,
        'screener': None,
        'success': False
    }
    
    if os.path.exists(pool_file):
        try:
            with open(pool_file, 'r', encoding='utf-8') as f:
                result['pool'] = json.load(f)
            result['success'] = True
        except Exception as e:
            result['pool'] = f"读取失败: {str(e)}"
    else:
        result['pool'] = "暂无股票池数据，请先执行更新操作"
    
    if os.path.exists(screener_file):
        try:
            with open(screener_file, 'r', encoding='utf-8') as f:
                result['screener'] = json.load(f)
            result['success'] = True
        except Exception as e:
            result['screener'] = f"读取失败: {str(e)}"
    else:
        result['screener'] = "暂无筛选结果，请先执行选股操作"
    
    return jsonify(result)

if __name__ == '__main__':
    print("🚀 股票池仪表盘服务启动中...")
    print("📱 访问地址: http://127.0.0.1:5000")
    print("⚙️  现在可以直接在网页上点击按钮执行操作了！")
    app.run(host='0.0.0.0', port=5000, debug=True)
