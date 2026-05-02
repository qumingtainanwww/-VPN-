from flask import Flask, render_template, request, jsonify
import requests
import re
import socket
import json
import concurrent.futures
import os
import random
import threading
import time
import base64
import warnings
import urllib.parse
import pyperclip
import hashlib
import webbrowser
import sys
warnings.filterwarnings('ignore')

app = Flask(__name__)

# 支持 PyInstaller 打包后的路径
if getattr(sys, 'frozen', False):
    # 打包后的路径
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

NODES_DIR = os.path.join(BASE_DIR, 'nodes')
NODES_FILE = os.path.join(NODES_DIR, 'nodes.json')
IP_HISTORY_FILE = os.path.join(NODES_DIR, 'ip_history.json')
LIBRARY_FILE = os.path.join(NODES_DIR, '离线IP库.txt')

# 预编译正则表达式，避免重复编译
PROTOCOLS = {
    "VMess": {"color": "#7b68ee", "pattern": re.compile(r"vmess://", re.IGNORECASE)},
    "VLESS": {"color": "#00d4ff", "pattern": re.compile(r"vless://", re.IGNORECASE)},
    "Shadowsocks": {"color": "#ff6b6b", "pattern": re.compile(r"ss://")},
    "Trojan": {"color": "#00ff88", "pattern": re.compile(r"trojan://", re.IGNORECASE)},
    "Hysteria2": {"color": "#ff9500", "pattern": re.compile(r"hysteria2://", re.IGNORECASE)},
}

_RE_URI_HASH = re.compile(r'#')
_RE_AT_IP_PORT = re.compile(r'@([0-9.]+):([0-9]+)')
_RE_PROTOCOL_START = re.compile(r'^(vmess|vless|ss|trojan|hysteria2)://', re.IGNORECASE)
_RE_PORT_IN_LINE = re.compile(r':([0-9]+)[^0-9]')
_RE_IP_PORT_END = re.compile(r'([0-9.]+):([0-9]+)$')
_RE_IP_DOT_DECIMAL = re.compile(r'^[0-9]+(\.[0-9]+){3}$')
_RE_URL_PROTOCOL = re.compile(r'://([0-9.]+):([0-9]+)')

SOURCES = [
    ('FastNodes All', 'https://gh-proxy.com/https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/everything.txt'),
    ('FastNodes US', 'https://gh-proxy.com/https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/countries/US.txt'),
    ('FreeNodes', 'https://gh-proxy.com/https://raw.githubusercontent.com/free-nodes/v2rayfree/main/v2ray.txt'),
    ('Epodonios', 'https://gh-proxy.com/https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt'),
    ('NiREvil', 'https://gh-proxy.com/https://raw.githubusercontent.com/NiREvil/vless/main/sub/SSTime'),
    ('EbraSha', 'https://gh-proxy.com/https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/main/vmess_configs.txt'),
    ('XrayFree', 'https://gh-proxy.com/https://raw.githubusercontent.com/xrayfree/free-ssr-ss-v2ray-vpn-clash/main/sub/v2ray.txt'),
    ('NodesFree', 'https://gh-proxy.com/https://raw.githubusercontent.com/nodesfree/v2raynode/main/v2ray.txt'),
    ('ClashNode', 'https://clashnode.github.io/uploads/2026/04/0-20260418.txt'),
    ('V2RayClash', 'https://v2rayclashnode.github.io/uploads/2026/03/0-20260328.txt'),
    ('FastNodes VMess', 'https://gh-proxy.com/https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/protocols/vmess.txt'),
    ('FastNodes VLESS', 'https://gh-proxy.com/https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/protocols/vless.txt'),
    ('EbraSha VLESS', 'https://gh-proxy.com/https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/main/vless_configs.txt'),
    ('FastNodes SS', 'https://gh-proxy.com/https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/protocols/ss.txt'),
    ('EbraSha SS', 'https://gh-proxy.com/https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/main/ss_configs.txt'),
    ('FastNodes Trojan', 'https://gh-proxy.com/https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/protocols/trojan.txt'),
    ('EbraSha Trojan', 'https://gh-proxy.com/https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/main/trojan_configs.txt'),
    ('FastNodes H2', 'https://gh-proxy.com/https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/protocols/hysteria2.txt'),
]

COUNTRIES = ["全部", "美国", "加拿大", "英国", "德国", "荷兰", "日本", "新加坡", "香港", "俄罗斯"]

EXPORT_FORMATS = ["geekez", "v2rayn", "txt"]

working_nodes = []  # 当前工作节点（兼容旧逻辑）
local_nodes = []   # 本地获取节点
scraped_nodes = [] # 网络获取节点
ip_history = {}
protocol_nodes = {}
country_nodes = {}
logs = []

# 线程锁保护全局变量
_data_lock = threading.Lock()

def _get_ip_hash(node):
    """获取节点URI哈希（线程安全）"""
    node_clean = _RE_URI_HASH.split(node)[0]
    return hashlib.md5(node_clean.encode('utf-8')).hexdigest()

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def add_log(msg, level="info"):
    logs.append({"msg": msg, "level": level, "time": time.strftime("%H:%M:%S")})
    if len(logs) > 100:
        logs.pop(0)

def save_nodes():
    with _data_lock:
        os.makedirs(NODES_DIR, exist_ok=True)
        with open(NODES_FILE, 'w', encoding='utf-8') as f:
            json.dump(working_nodes, f, ensure_ascii=False)

def load_nodes():
    global working_nodes
    with _data_lock:
        if os.path.exists(NODES_FILE):
            try:
                with open(NODES_FILE, 'r', encoding='utf-8') as f:
                    working_nodes = json.load(f)
            except:
                working_nodes = []
        else:
            working_nodes = []

def save_ip_history():
    with _data_lock:
        os.makedirs(NODES_DIR, exist_ok=True)
        with open(IP_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(ip_history, f, ensure_ascii=False, indent=2)

def load_ip_history():
    global ip_history
    with _data_lock:
        if os.path.exists(IP_HISTORY_FILE):
            try:
                with open(IP_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    ip_history = json.load(f)
            except:
                ip_history = {}
        else:
            ip_history = {}

def _decode_vmess(node):
    """尝试解码VMess节点，返回config字典或None"""
    if not node.startswith('vmess://'):
        return None
    try:
        b64 = node.replace('vmess://', '')
        b64 = b64.replace('-', '+').replace('_', '/')
        pad = 4 - len(b64) % 4
        if pad != 4:
            b64 += '=' * pad
        b64 = ''.join(c for c in b64 if ord(c) < 128)
        decoded = base64.b64decode(b64, validate=True).decode('utf-8', errors='ignore')
        return json.loads(decoded)
    except:
        return None

def extract_ip(node):
    config = _decode_vmess(node)
    if config:
        return config.get('add', '')
    match = _RE_AT_IP_PORT.search(node)
    if match:
        return match.group(1)
    match = _RE_URL_PROTOCOL.search(node)
    if match:
        return match.group(1)
    return None

def extract_port(node):
    config = _decode_vmess(node)
    if config:
        return config.get('port', None)
    match = _RE_PORT_IN_LINE.search(node.split('#')[0])
    if match:
        return match.group(1)
    return None

def get_ip_port(node):
    if node.startswith('vmess://'):
        try:
            b64 = node.replace('vmess://', '')
            b64 = b64.replace('-', '+').replace('_', '/')
            pad = 4 - len(b64) % 4
            if pad != 4:
                b64 += '=' * pad
            decoded = base64.b64decode(b64, validate=True).decode('utf-8')
            config = json.loads(decoded)
            return config.get('add', ''), config.get('port', None)
        except:
            pass
    match = _RE_AT_IP_PORT.search(node)
    if match:
        return match.group(1), int(match.group(2))
    match = _RE_URL_PROTOCOL.search(node)
    if match:
        return match.group(1), int(match.group(2))
    match = _RE_IP_PORT_END.search(node)
    if match:
        return match.group(1), int(match.group(2))
    return None, None

def get_country(ip):
    try:
        r = requests.get(f'http://ip-api.com/json/{ip}?fields=countryCode', timeout=2, headers=HEADERS)
        return r.json().get('countryCode', '')
    except:
        return ''

def test_node(node):
    """验证节点格式"""
    ip, port = get_ip_port(node)
    if not ip or not port:
        return None, ''
    parts = ip.split('.')
    if len(parts) != 4 or any(not p.isdigit() for p in parts):
        return None, ''
    return node, ''

def fetch(url, timeout=10):
    try:
        add_log(f"正在获取: {url[:60]}...", "info")
        r = requests.get(url, timeout=(5, timeout), allow_redirects=True, verify=False, headers=HEADERS)
        if r.status_code == 200:
            nodes = []
            seen = set()
            for line in r.text.strip().split('\n'):
                line = line.strip()
                if not line or line in seen:
                    continue
                seen.add(line)
                line_lower = line.lower()
                try:
                    from urllib.parse import unquote
                    line = unquote(line)
                except:
                    pass
                if _RE_PROTOCOL_START.search(line_lower):
                    nodes.append(line)
            add_log(f"获取成功: {len(nodes)} 个节点", "success")
            return nodes
        else:
            add_log(f"HTTP {r.status_code}: {url[:50]}", "warning")
    except Exception as e:
        add_log(f"获取失败 {url[:50]}: {str(e)[:50]}", "error")
    return []

def filter_by_protocol(nodes, selected_protocols):
    filtered = []
    for node in nodes:
        for proto in selected_protocols:
            if PROTOCOLS[proto]["pattern"].search(node):
                filtered.append(node)
                break
    return filtered

@app.route('/')
def index():
    load_ip_history()
    global working_nodes
    working_nodes = []
    if os.path.exists(NODES_FILE):
        os.remove(NODES_FILE)
    return render_template('index.html', protocols=PROTOCOLS, sources=SOURCES, ip_count=len(ip_history), 
                     countries=COUNTRIES, formats=EXPORT_FORMATS, node_count=len(working_nodes))

@app.route('/api/test1')
def test1():
    url = 'https://gh-proxy.com/https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/everything.txt'
    nodes = fetch(url)
    return jsonify({'count': len(nodes)})

scrape_status = {'running': False, 'progress': 0, 'total': 0, 'valid': 0, 'finished': False, 'stage': ''}

@app.route('/api/logs')
def get_logs():
    return jsonify({'logs': logs, 'status': scrape_status})

@app.route('/api/progress')
def get_progress():
    return jsonify(scrape_status)

@app.route('/api/scrape', methods=['POST'])
def scrape():
    if not request.is_json:
        return jsonify({'error': '需要JSON格式'}), 400
    data = request.get_json()
    selected_protocols = data.get('protocols', [])
    threads = int(data.get('threads', 50))
    max_nodes = int(data.get('max_nodes', 100))
    source_count = data.get('source_count', '全')
    selected_country = data.get('country', '全部')
    country_map = {'全部': '全部', 'all': '全部', '美国': '美国', 'US': '美国'}
    selected_country = country_map.get(selected_country, selected_country)
    
    if scrape_status.get('running'):
        return jsonify({'error': '爬取中'})
    
    if not selected_protocols:
        return jsonify({'error': '请选择协议'})
    
    scrape_status['running'] = True
    scrape_status['stage'] = '初始化'
    scrape_status['progress'] = 0
    scrape_status['total'] = 0
    scrape_status['valid'] = 0
    scrape_status['finished'] = False
    
    thread = threading.Thread(target=scrape_in_background, args=(selected_protocols, threads, max_nodes, source_count, selected_country), daemon=True)
    thread.start()
    
    return jsonify({'started': True, 'message': '开始爬取'})

def scrape_in_background(selected_protocols, threads, max_nodes, source_count, selected_country):
    global working_nodes, ip_history, protocol_nodes, country_nodes, scrape_status
    
    try:
        add_log(f"开始爬取 (协议: {', '.join(selected_protocols)})", "info")
        with _data_lock:
            scrape_status['stage'] = '加载历史'
        load_ip_history()
        with _data_lock:
            scrape_status['stage'] = '准备数据源'
        add_log(f"IP历史记录: {len(ip_history)} 个", "info")
    except Exception as e:
        add_log(f"初始化错误: {str(e)}", "error")
        with _data_lock:
            scrape_status['running'] = False
            scrape_status['stage'] = '错误'
        return
    
    try:
        if source_count == "全" or source_count == "all":
            sources_to_fetch = SOURCES
        else:
            count = int(source_count)
            proto_keywords = {
                "VMess": ["vmess", "v2ray", "v2"],
                "VLESS": ["vless"],
                "Shadowsocks": ["ss", "shadowsock"],
                "Trojan": ["trojan"],
                "Hysteria2": ["h2", "hysteria", "hy2"],
            }
            preferred = []
            for name, url in SOURCES:
                name_lower = name.lower()
                for proto in selected_protocols:
                    keywords = proto_keywords.get(proto, [])
                    if any(k in name_lower for k in keywords):
                        preferred.append((name, url))
                        break
            other = [(n, u) for n, u in SOURCES if (n, u) not in preferred]
            if len(preferred) >= count:
                sources_to_fetch = random.sample(preferred, count)
            elif len(preferred) + len(other) <= count:
                sources_to_fetch = SOURCES
            else:
                need_more = count - len(preferred)
                sources_to_fetch = preferred + random.sample(other, min(need_more, len(other)))
        
        add_log(f"使用 {len(sources_to_fetch)} 个数据源", "info")
    except Exception as e:
        add_log(f"错误: {str(e)}", "error")
        with _data_lock:
            scrape_status['running'] = False
            scrape_status['stage'] = '错误'
        return
    
    source_results = {}
    def fetch_source(args):
        name, url = args
        nodes = fetch(url)
        return name, nodes
    
    add_log("开始并行获取数据源...", "warning")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_source, (name, url)): name for name, url in sources_to_fetch}
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            name, nodes = future.result()
            source_results[name] = nodes
            completed += 1
            add_log(f"  [{completed}/{len(sources_to_fetch)}] {name}: {len(nodes)} 个节点", "success")
    
    all_nodes = []
    for name, nodes in source_results.items():
        all_nodes.extend(nodes)
    all_nodes = list(set(all_nodes))
    
    skipped_count = 0
    filtered = []
    node_hash_map = {}  # 保存节点的哈希，检测有效后再记录历史
    for node in all_nodes:
        node_clean = _RE_URI_HASH.split(node)[0]
        uri_hash = _get_ip_hash(node)
        if uri_hash in ip_history:
            skipped_count += 1
            continue
        for proto in selected_protocols:
            if PROTOCOLS[proto]["pattern"].search(node):
                filtered.append(node)
                node_hash_map[node] = uri_hash
                break
    all_nodes = filtered
    
    add_log(f"筛选后: {len(all_nodes)} 个节点 (跳过 {skipped_count} 个已存在IP)", "info")
    # 安全地显示样例
    if all_nodes:
        sample = all_nodes[0][:50]
    else:
        sample = '无'
    add_log(f"协议: {selected_protocols}, 节点协议检测样例: {sample}", "info")
    add_log(f"开始处理...", "warning")
    
    scrape_status['stage'] = '检测节点'
    scrape_status['total'] = len(all_nodes)
    
    # 网络获取的节点存入 scraped_nodes，不影响本地获取
    global scraped_nodes
    scraped_nodes = []
    working_nodes = []
    country_nodes = {}
    protocol_nodes = {p: [] for p in selected_protocols}
    
    try:
        add_log(f"并发检测 {len(all_nodes)} 个节点 (线程: {threads})...", "info")
        checked = 0
        valid_count = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(test_node, n): n for n in all_nodes}
            for future in concurrent.futures.as_completed(futures):
                checked += 1
                scrape_status['progress'] = checked
                scrape_status['valid'] = valid_count
                if checked % 30 == 0:
                    add_log(f"进度: {checked}/{len(all_nodes)} (有效:{valid_count})", "info")
                node, country = future.result()
                if node:
                    working_nodes.append(node)
                    scraped_nodes.append(node)
                    valid_count += 1
                    if node in node_hash_map:
                        ip_history[node_hash_map[node]] = True
                    if country not in country_nodes:
                        country_nodes[country] = []
                    country_nodes[country].append(node)
                    for proto in selected_protocols:
                        if PROTOCOLS[proto]["pattern"].search(node):
                            protocol_nodes[proto].append(node)
                            break
                    if len(working_nodes) >= max_nodes:
                        add_log(f"达到目标 {max_nodes} 个 (检测{checked})", "success")
                        for f in futures:
                            f.cancel()
                        break
    except Exception as e:
        add_log(f"错误: {str(e)}", "error")
    
    save_ip_history()
    save_nodes()
    add_log(f"完成: {len(working_nodes)} 个可用节点", "success")
    
    scrape_status['running'] = False
    scrape_status['finished'] = True
    scrape_status['progress'] = scrape_status['total']
    scrape_status['valid'] = len(working_nodes)
    scrape_status['ip_count'] = len(ip_history)
    scrape_status['stage'] = '完成'

@app.route('/api/export', methods=['POST'])
def export_nodes():
    data = request.get_json()
    country = data.get('country', '全部')
    fmt = data.get('format', 'geekez')
    selected_protocols = data.get('protocols', [])
    source = data.get('source', 'current')
    
    if source == 'local':
        nodes_to_export = local_nodes
    elif source == 'scraped':
        nodes_to_export = scraped_nodes
    else:
        nodes_to_export = working_nodes
    if country in country_nodes:
        nodes_to_export = country_nodes[country]
    
    if selected_protocols:
        filtered = []
        for node in nodes_to_export:
            for proto in selected_protocols:
                if PROTOCOLS[proto]["pattern"].search(node):
                    filtered.append(node)
                    break
        nodes_to_export = filtered
    
    lines = []
    for node in nodes_to_export:
        node = node.split('#')[0]
        if '%25' in node or '%2525' in node:
            continue
        lines.append(node)
    
    if fmt == 'geekez' or fmt == 'v2rayn':
        content = '\n'.join(lines)
    elif fmt == 'txt':
        content = '\n'.join(lines)
    else:
        content = '\n'.join(lines)
    
    country_map = {"全部": "all", "美国": "US", "加拿大": "CA", "英国": "GB", "德国": "DE",
               "荷兰": "NL", "日本": "JP", "新加坡": "SG", "香港": "HK", "俄罗斯": "RU"}
    c = country_map.get(country, "all")
    proto_str = "_".join(selected_protocols[:2]) if selected_protocols else "all"
    
    filename = f'{c}_{proto_str}.txt'
    filepath = os.path.join(NODES_DIR, filename)
    os.makedirs(NODES_DIR, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    sample_ips = [extract_ip(n) for n in nodes_to_export[:5]]
    add_log(f"导出 {len(nodes_to_export)} 个节点到 {filename}，样例IP: {sample_ips}", "info")
    return jsonify({'count': len(nodes_to_export), 'content': content[:500], 'format': fmt, 'filename': filename})

@app.route('/api/copy', methods=['POST'])
def copy_to_clipboard():
    global working_nodes
    load_nodes()
    try:
        content = '\n'.join([n.split('#')[0] for n in working_nodes])
        pyperclip.copy(content)
        return jsonify({'success': True, 'count': len(working_nodes)})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    global ip_history
    ip_history = {}
    if os.path.exists(IP_HISTORY_FILE):
        os.remove(IP_HISTORY_FILE)
    add_log("IP历史已清空", "success")
    return jsonify({'success': True})

@app.route('/api/open_folder', methods=['POST'])
def open_folder():
    os.makedirs(NODES_DIR, exist_ok=True)
    os.startfile(NODES_DIR)
    return jsonify({'success': True})

@app.route('/api/clear_folder', methods=['POST'])
def clear_folder():
    os.makedirs(NODES_DIR, exist_ok=True)
    count = 0
    for f in os.listdir(NODES_DIR):
        path = os.path.join(NODES_DIR, f)
        if os.path.isfile(path):
            os.remove(path)
            count += 1
    add_log(f"已清空 {count} 个文件", "success")
    return jsonify({'success': True, 'count': count})

@app.route('/api/import_local', methods=['POST'])
def import_local():
    global working_nodes, ip_history
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'})
    file = request.files['file']
    if not file.filename.endswith('.txt'):
        return jsonify({'error': '请上传.txt文件'})
    try:
        protocols_param = request.form.get('protocols', 'vmess,vless,ss,trojan,hysteria2')
        selected_protocols = [p.strip().lower() + '://' for p in protocols_param.split(',') if p.strip()]
        if not selected_protocols:
            selected_protocols = ['vmess://', 'vless://', 'ss://', 'trojan://', 'hysteria2://']
        
        content = file.read().decode('utf-8', errors='ignore')
        lines = [l.strip() for l in content.split('\n') if l.strip()]
  
        filtered = []
        for line in lines:
            proto = next((p for p in selected_protocols if line.lower().startswith(p)), None)
            if proto:
                node_uri = line.split('#')[0]
                filtered.append(node_uri)
  
        add_log(f"导入 {len(filtered)} 个节点（无历史过滤）", "info")
        
        working_nodes.clear()
        working_nodes.extend(filtered)
        
        os.makedirs(NODES_DIR, exist_ok=True)
        with open(LIBRARY_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(filtered))
        add_log(f"已保存到 {LIBRARY_FILE}", "info")
        
        proto_count = {}
        for line in working_nodes:
            proto = next((p for p in selected_protocols if line.lower().startswith(p)), None)
            if proto:
                key = proto.replace('://', '').upper()
                proto_count[key] = proto_count.get(key, 0) + 1
        total_valid = len(working_nodes)
  
        proto_detail = ', '.join([f"{k}:{v}" for k, v in proto_count.items()])
        filename = file.filename
        msg = f"导入 {filename}: {total_valid} 个节点 ({proto_detail})"
        add_log(msg, "success")
        return jsonify({
            'count': total_valid,
            'filename': filename,
            'protocols': proto_count,
            'error': None
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/load_library', methods=['POST'])
def load_library():
    global working_nodes, ip_history
    try:
        if not os.path.exists(LIBRARY_FILE):
            if working_nodes:
                os.makedirs(NODES_DIR, exist_ok=True)
                with open(LIBRARY_FILE, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(working_nodes))
                add_log(f"自动从内存创建离线IP库: {len(working_nodes)} 个节点", "info")
            else:
                return jsonify({'error': 'nodes/离线IP库.txt 不存在，请先使用"导入本地库"功能导入节点'})
        
        data = request.get_json(silent=True) or {}
        protocols_param = data.get('protocols', 'vmess,vless,ss,trojan,hysteria2')
        max_nodes = int(data.get('max_nodes', '30'))
        selected_protocols = [p.strip().lower() + '://' for p in protocols_param.split(',') if p.strip()]
        if not selected_protocols:
            selected_protocols = ['vmess://', 'vless://', 'ss://', 'trojan://', 'hysteria2://']
        
        add_log(f"正在读取离线IP库...", "info")
        
        with open(LIBRARY_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        add_log(f"离线库总行数: {len(lines)}", "info")
        
        protocol_filtered = []
        for line in lines:
            proto = next((p for p in selected_protocols if line.lower().startswith(p)), None)
            if proto:
                node_uri = line.split('#')[0]
                protocol_filtered.append(node_uri)
        
        add_log(f"协议筛选后: {len(protocol_filtered)} 个节点", "info")
        
        load_ip_history()
        add_log(f"加载历史记录: {len(ip_history)} 条", "info")
        
        filtered = []
        skipped_count = 0
        for node_uri in protocol_filtered:
            uri_hash = hashlib.md5(node_uri.encode('utf-8')).hexdigest()
            if uri_hash in ip_history:
                skipped_count += 1
                continue
            filtered.append(node_uri)
        
        add_log(f"历史过滤后: 新增 {len(filtered)} 个，跳过 {skipped_count} 个", "info")
        
        random.shuffle(filtered)
        add_log(f"已打乱节点顺序，避免重复获取", "info")
        
        if len(filtered) > max_nodes:
            filtered = filtered[:max_nodes]
            add_log(f"截断到上限: {max_nodes} 个", "info")
        
        global local_nodes
        local_nodes = filtered[:]
        working_nodes.clear()
        working_nodes.extend(filtered)
        add_log(f"本地获取节点: {len(local_nodes)} 个", "info")
        
        added_count = 0
        for node_uri in working_nodes:
            uri_hash = hashlib.md5(node_uri.encode('utf-8')).hexdigest()
            if uri_hash not in ip_history:
                ip_history[uri_hash] = True
                added_count += 1
        
        save_ip_history()
        add_log(f"保存历史记录: {len(ip_history)} 条", "info")
        
        proto_count = {}
        for line in working_nodes:
            proto = next((p for p in selected_protocols if line.lower().startswith(p)), None)
            if proto:
                key = proto.replace('://', '').upper()
                proto_count[key] = proto_count.get(key, 0) + 1
        total_valid = len(working_nodes)
        
        proto_detail = ', '.join([f"{k}:{v}" for k, v in proto_count.items()])
        msg = f"本地获取完成: 新增 {total_valid} 个节点，跳过 {skipped_count} 个历史节点 ({proto_detail})"
        add_log(msg, "success")
        return jsonify({
            'count': total_valid,
            'skipped': skipped_count,
            'protocols': proto_count,
            'error': None
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    """关闭服务"""
    import sys
    add_log("正在关闭服务...", "warning")
    # 使用线程延迟关闭，让响应先返回
    def delayed_shutdown():
        import time
        time.sleep(1)
        os._exit(0)
    threading.Thread(target=delayed_shutdown, daemon=True).start()
    return jsonify({'success': True, 'message': '服务正在关闭'})

if __name__ == '__main__':
    os.makedirs(NODES_DIR, exist_ok=True)
    # 自动打开浏览器
    url = 'http://127.0.0.1:5000'
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host='127.0.0.1', port=5000, debug=False)
