import json
import re
import os
import base64

def extract_ip_from_link(link):
    """从节点链接提取IP"""
    link = link.strip()
    
    # vmess://
    if link.startswith('vmess://'):
        try:
            data = json.loads(base64.b64decode(link.replace('vmess://', '')).decode())
            return data.get('add', '')
        except:
            pass
    
    # vless:// trojan:// ss:// hysteria2:// tuic://
    patterns = [
        (r'vless://[^@]+@([^:]+):', 'vless'),
        (r'trojan://[^@]+@([^:]+):', 'trojan'),
        (r'ss://[^@]+@([^:]+):', 'ss'),
        (r'hysteria2://[^@]+@([^:]+):', 'hysteria2'),
        (r'tuic://[^:]+:[^@]+@([^:]+):', 'tuic'),
    ]
    
    for pattern, proto in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)
    
    # http:// 或 socks5://
    match = re.search(r'(https?|socks5?)://([^:]+):', link)
    if match:
        return match.group(2)
    
    # 纯IP:PORT
    match = re.search(r'^([\d.]+):', link)
    if match:
        return match.group(1)
    
    return None

def parse_clipboard_content(content):
    """解析剪贴板内容"""
    lines = content.strip().split('\n')
    nodes = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 移除注释
        if '#' in line and not line.startswith('#'):
            line = line.split('#')[0].strip()
        
        # 检查是否是节点链接
        if any(line.startswith(p) for p in ['vmess://', 'vless://', 'trojan://', 'ss://', 
                                              'hysteria2://', 'tuic://', 'http://', 'https://',
                                              'socks5://', 'socks://']):
            nodes.append(line)
        # 纯IP:PORT格式
        elif re.match(r'^[\d.]+:\d+$', line):
            nodes.append(line)
    
    return nodes

def extract_proxies(nodes):
    """从节点提取IP和端口"""
    proxies = []
    
    for node in nodes:
        ip = extract_ip_from_link(node)
        
        if not ip:
            continue
        
        # 提取端口
        port_match = re.search(r':(\d+)', node.split('@')[-1] if '@' in node else node)
        if port_match:
            port = int(port_match.group(1))
            proxies.append((ip, port, node))
    
    return proxies

def generate_web3toolbox_config(proxies, output_path):
    """生成Web3Toolbox配置"""
    http_proxies = []
    socks_proxies = []
    
    for ip, port, original_link in proxies:
        # 根据端口判断协议类型
        # HTTP常用端口: 80, 8080, 3128, 8888, 8118, 8123, 8000, 8880, 80, 443
        # SOCKS常用端口: 1080, 10808, 1080, 7890, 7891, 10808
        if port in [80, 8080, 3128, 8888, 8118, 8123, 8000, 8880, 443, 8443, 2096, 2053]:
            proxy_type = 'http'
        else:
            proxy_type = 'socks5'
        
        proxy_str = f"{proxy_type}://{ip}:{port}"
        
        if proxy_type == 'http':
            http_proxies.append(proxy_str)
        else:
            socks_proxies.append(proxy_str)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Web3Toolbox Proxy Configuration\n")
        f.write("# 生成时间: 自动生成\n")
        f.write("# 协议: http:// 或 socks5://\n\n")
        
        if http_proxies:
            f.write(f"# HTTP代理 ({len(http_proxies)}个)\n")
            for p in http_proxies:
                f.write(f"{p}\n")
        
        if socks_proxies:
            f.write(f"\n# SOCKS5代理 ({len(socks_proxies)}个)\n")
            for p in socks_proxies:
                f.write(f"{p}\n")
    
    return http_proxies, socks_proxies

def main():
    print("=" * 60)
    print("  v2rayN 节点导出到 Web3Toolbox")
    print("=" * 60)
    
    # 读取剪贴板
    try:
        import pyperclip
        content = pyperclip.paste()
    except:
        print("无法读取剪贴板，请手动粘贴内容")
        content = input("\n请粘贴v2rayN导出的节点链接:\n")
    
    if not content or len(content.strip()) < 10:
        print("剪贴板内容为空或太短！")
        print("\n使用方法:")
        print("1. 在v2rayN中选择可用的节点")
        print("2. 右键 -> 导出所选服务器为批量URL")
        print("3. 复制URL内容到剪贴板")
        print("4. 运行此脚本")
        return
    
    print(f"\n正在解析剪贴板内容...")
    nodes = parse_clipboard_content(content)
    
    if not nodes:
        print("未找到有效节点！")
        print("请确保剪贴板中包含 vmess:// vless:// trojan:// ss:// 等格式的节点链接")
        return
    
    print(f"找到 {len(nodes)} 个节点")
    
    print("正在提取IP和端口...")
    proxies = extract_proxies(nodes)
    
    if not proxies:
        print("无法提取IP信息！")
        return
    
    print(f"成功提取 {len(proxies)} 个代理")
    
    # 生成配置
    output_dir = r"D:\VPN\免费VPN爬虫\nodes"
    os.makedirs(output_dir, exist_ok=True)
    
    web3_path = os.path.join(output_dir, "web3toolbox_proxies.txt")
    
    print(f"\n正在生成Web3Toolbox配置...")
    http_proxies, socks_proxies = generate_web3toolbox_config(proxies, web3_path)
    
    # 复制到剪贴板
    all_proxies = http_proxies + socks_proxies
    clipboard_content = '\n'.join(all_proxies)
    
    try:
        pyperclip.copy(clipboard_content)
        print("已复制到剪贴板！")
    except:
        pass
    
    print("\n" + "=" * 60)
    print("  完成！")
    print("=" * 60)
    print(f"文件: {web3_path}")
    print(f"HTTP代理: {len(http_proxies)} 个")
    print(f"SOCKS5代理: {len(socks_proxies)} 个")
    print(f"\nWeb3Toolbox使用方法:")
    print("  复制剪贴板内容，在Web3Toolbox中粘贴到代理设置")
    print("\n代理列表 (前10个):")
    print("-" * 40)
    for p in all_proxies[:10]:
        print(f"  {p}")
    if len(all_proxies) > 10:
        print(f"  ... 还有 {len(all_proxies) - 10} 个")

if __name__ == "__main__":
    main()
