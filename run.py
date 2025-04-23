from app import app
import config
import os
import uuid
import argparse

def main():
    parser = argparse.ArgumentParser(description='网站镜像工具 - 仅用于教育目的')
    parser.add_argument('--host', default='127.0.0.1', help='主机地址 (默认: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=config.PORT, help=f'端口 (默认: {config.PORT})')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    args = parser.parse_args()
    
    # 如果没有.env文件，生成一个基本的配置
    if not os.path.exists('.env'):
        try:
            with open('.env.example', 'r') as example_file:
                example_content = example_file.read()
                
            with open('.env', 'w') as env_file:
                # 替换示例中的密钥为随机生成的密钥
                env_content = example_content.replace('your_secret_key_here', uuid.uuid4().hex)
                env_file.write(env_content)
                
            print('[*] 已创建新的.env配置文件')
        except:
            print('[!] 无法创建.env文件，请手动从.env.example复制')
    
    # 提示信息
    print('================================================')
    print('  网站镜像工具 v1.0')
    print('  仅用于教育目的和安全研究')
    print('================================================')
    print(f'[*] 服务运行在: http://{args.host}:{args.port}')
    print('[*] 按 Ctrl+C 停止服务')
    print('================================================')
    
    # 运行应用
    app.run(host=args.host, port=args.port, debug=args.debug or config.DEBUG)

if __name__ == '__main__':
    main() 