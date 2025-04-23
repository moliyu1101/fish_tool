import os
from dotenv import load_dotenv

# 加载.env文件中的配置
load_dotenv()

# 应用配置
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key_for_dev_only')
PORT = int(os.getenv('PORT', 5000))

# 资源下载设置
DOWNLOAD_RESOURCES = os.getenv('DOWNLOAD_RESOURCES', 'True').lower() == 'true'
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 10))
MIN_REQUEST_DELAY = float(os.getenv('MIN_REQUEST_DELAY', 0.5))
MAX_REQUEST_DELAY = float(os.getenv('MAX_REQUEST_DELAY', 1.5))

# 安全设置
ENCRYPT_CAPTURED_DATA = os.getenv('ENCRYPT_CAPTURED_DATA', 'False').lower() == 'true'
ENABLE_AUTH = os.getenv('ENABLE_AUTH', 'False').lower() == 'true'
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123') 