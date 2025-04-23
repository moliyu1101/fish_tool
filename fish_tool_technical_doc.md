# 网站镜像钓鱼工具技术文档

## 项目概述

网站镜像钓鱼工具是一个基于Python Flask的应用程序，用于教育和安全研究目的，演示网络钓鱼攻击的技术原理。该工具能够克隆目标网站的页面，捕获用户提交的表单数据，并将用户无缝跳转回原始网站。

## 核心功能

1. **页面镜像钓鱼复制**：输入目标URL后，自动生成视觉与交互高度一致的页面
2. **资源本地化处理**：下载并处理目标网站的CSS、JS、图片等资源文件
3. **表单数据捕获**：修改表单提交逻辑，捕获用户输入的敏感信息
4. **无痕跳转机制**：用户提交后自动跳转回原始站点，降低怀疑概率
5. **安全保护措施**：支持数据加密和管理界面访问控制

## 技术架构

### 前端技术
- HTML5/CSS3/JavaScript
- 响应式设计，适配不同设备

### 后端技术
- **编程语言**：Python 3.x
- **Web框架**：Flask 2.0.1
- **页面解析**：BeautifulSoup4 4.10.0，用于HTML分析和操作
- **HTTP请求**：Requests 2.26.0，处理网络请求
- **数据存储**：JSON文件存储（可扩展为数据库存储）
- **配置管理**：python-dotenv 0.19.0，环境变量配置

## 系统组件

### 1. 站点克隆器 (site_cloner.py)
- **功能**：负责获取目标网站内容并进行本地化处理
- **核心方法**：
  - `clone_site()`: 克隆整个网站
  - `_download_resource()`: 下载资源文件(CSS/JS/图片)
  - `_process_css()`: 处理CSS文件中的URL引用
  - `_make_request()`: 发送HTTP请求，带随机延迟

### 2. 主应用服务 (app.py)
- **功能**：提供Web接口和路由处理
- **主要路由**：
  - `/`: 主页，提供克隆功能界面
  - `/clone`: 处理克隆请求
  - `/view/<site_id>`: 查看克隆页面
  - `/submit/<site_id>`: 处理表单提交
  - `/captured`: 查看捕获的数据
  - `/clear_data`: 清除捕获数据

### 3. 配置管理 (config.py)
- **功能**：加载和管理应用配置
- **配置项**：应用设置、资源下载设置、安全设置

### 4. 启动脚本 (run.py)
- **功能**：提供命令行接口，启动应用服务
- **参数支持**：主机地址、端口、调试模式

## 数据流程

1. **克隆过程**：
   ```
   用户输入URL → 获取页面内容 → 下载资源文件 → 
   修改表单提交目标 → 注入拦截脚本 → 保存处理后的页面
   ```

2. **数据捕获过程**：
   ```
   用户访问克隆页面 → 输入并提交表单 → 
   服务器接收数据 → 保存捕获数据 → 用户跳转至原站点
   ```

## 安全措施

1. **数据保护**：
   - 可选的数据加密存储
   - 敏感字段自动脱敏显示

2. **访问控制**：
   - 管理页面可选的账号密码保护
   - 删除操作需二次确认

3. **反检测机制**：
   - 随机化请求延迟，模拟真实用户行为
   - 自定义User-Agent，避免被目标站点识别

## 系统要求

- Python 3.6+
- 以下Python库:
  - Flask==2.0.1
  - requests==2.26.0
  - beautifulsoup4==4.10.0
  - lxml==4.6.3
  - python-dotenv==0.19.0

## 配置说明

系统通过`.env`文件进行配置，主要配置项包括：

### 基本设置
```
DEBUG=True                    # 调试模式
SECRET_KEY=your_secret_key    # 应用密钥
PORT=5000                     # 服务端口
```

### 资源下载设置
```
DOWNLOAD_RESOURCES=True       # 是否下载资源文件
REQUEST_TIMEOUT=10            # 请求超时时间(秒)
MIN_REQUEST_DELAY=0.5         # 最小请求延迟(秒)
MAX_REQUEST_DELAY=1.5         # 最大请求延迟(秒)
```

### 安全设置
```
ENCRYPT_CAPTURED_DATA=False   # 是否加密捕获数据
ENABLE_AUTH=False             # 是否启用认证
ADMIN_USERNAME=admin          # 管理员用户名
ADMIN_PASSWORD=admin123       # 管理员密码
```

## 使用指南

### 安装
```bash
# 克隆仓库
git clone [仓库地址]
cd [项目目录]

# 安装依赖
pip install -r requirements.txt

# 配置环境
cp .env.example .env
# 编辑.env文件进行个性化配置
```

### 启动服务
```bash
python run.py                       # 默认配置启动
python run.py --host 0.0.0.0        # 允许外部访问
python run.py --port 8080           # 自定义端口
python run.py --debug               # 启用调试模式
```

### 使用流程
1. 访问 `http://[主机地址]:[端口]`
2. 输入目标网站URL并点击"开始克隆"
3. 等待克隆完成，获取克隆页面链接
4. 访问克隆页面，测试表单捕获功能
5. 访问 `/captured` 路径查看捕获的数据

## 模块详解

### 1. 站点克隆模块
```python
# 核心逻辑
site_id = site_cloner.clone_site(target_url)
```
- 请求目标URL并获取HTML内容
- 解析HTML结构，处理资源引用
- 替换表单提交目标为本地服务器
- 注入表单拦截脚本，添加加载动画

### 2. 表单捕获模块
```python
# 表单数据捕获
@app.route('/submit/<site_id>', methods=['POST'])
def submit_form(site_id):
    form_data = request.form.to_dict()
    # 保存捕获数据
```
- 接收表单POST请求
- 记录提交时间、IP地址、用户代理
- 保存表单字段值
- 根据配置进行加密处理
- 将用户重定向至原始站点

### 3. 管理页面模块
```python
@app.route('/captured')
@login_required
def view_captured():
    # 获取并显示捕获数据
```
- 列出所有捕获的数据记录
- 对敏感字段进行脱敏处理
- 提供数据清除功能

## 扩展与定制

### 1. 数据存储扩展
当前版本使用JSON文件存储数据，可扩展为数据库存储：
```python
# 示例：添加SQLAlchemy支持
from flask_sqlalchemy import SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///captured_data.db'
db = SQLAlchemy(app)

class CapturedData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String(80))
    # 其他字段...
```

### 2. 克隆能力增强
可以增强以支持复杂的现代网站：
```python
# 示例：使用Puppeteer/Selenium获取动态渲染内容
from selenium import webdriver

def get_dynamic_content(url):
    driver = webdriver.Chrome()
    driver.get(url)
    # 等待动态内容加载
    time.sleep(3)
    content = driver.page_source
    driver.quit()
    return content
```

## 安全注意事项

- 仅用于教育和授权测试环境
- 未经授权使用可能违反相关法律法规
- 捕获数据应妥善保管并在测试后及时删除
- 避免在生产环境使用，以防安全风险

## 项目结构
```
/
├── app.py                  # 主应用服务
├── site_cloner.py          # 站点克隆工具
├── config.py               # 配置管理
├── run.py                  # 启动脚本
├── requirements.txt        # 依赖列表
├── .env.example            # 配置示例
├── .env                    # 配置文件
├── templates/              # HTML模板
│   ├── index.html          # 主页模板
│   ├── login.html          # 登录页模板
│   ├── captured.html       # 数据查看模板
│   └── cloned_sites/       # 克隆页面存储
├── static/                 # 静态资源
│   └── cloned_sites/       # 克隆资源存储
└── captured_data/          # 捕获数据存储
```

## 技术实现细节

1. **表单劫持技术**：通过修改表单的`action`属性，将提交目标指向本地服务器
2. **资源本地化**：处理相对路径和绝对路径，确保资源正确加载
3. **表单拦截**：注入JavaScript脚本，在表单提交时显示加载动画
4. **跳转机制**：用户表单提交后延迟1-2秒跳转回原站点，模拟服务器处理时间
5. **数据捕获**：按照表单字段名智能识别敏感信息，并根据配置进行处理

---

*此文档仅用于教育目的。使用本工具进行实际网络钓鱼攻击可能违反法律法规，请在合法的授权环境中使用。* 