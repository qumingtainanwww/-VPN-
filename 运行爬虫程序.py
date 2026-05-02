import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'
os.environ['GDK_SCALE'] = '1'
os.environ['GDK_DPI_SCALE'] = '1'

import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip
import threading
import requests
import re
import socket
import concurrent.futures
import json
import base64

BG_COLOR = "#1e1e2e"
FG_COLOR = "#cdd6f4"
ACCENT_COLOR = "#89b4fa"
SUCCESS_COLOR = "#a6e3a1"
WARNING_COLOR = "#f9e2af"
ERROR_COLOR = "#f38ba8"
FRAME_BG = "#313244"
BTN_BG = "#45475a"
BTN_HOVER = "#585b70"

PROTOCOLS = {
    "VMess": {"color": "#7b68ee", "pattern": r"vmess://"},
    "VLESS": {"color": "#00d4ff", "pattern": r"vless://"},
    "Shadowsocks": {"color": "#ff6b6b", "pattern": r"ss://"},
    "Trojan": {"color": "#00ff88", "pattern": r"trojan://"},
    "Hysteria2": {"color": "#ff9500", "pattern": r"hysteria2://"},
}


class IPHistory:
    """IP历史记录管理器"""
    def __init__(self, filename='nodes/ip_history.json'):
        self.filename = filename
        self.history = self.load()
    
    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save(self):
        os.makedirs(os.path.dirname(self.filename) if os.path.dirname(self.filename) else 'nodes', exist_ok=True)
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def add_ip(self, ip):
        self.history[ip] = True
    
    def add_ips(self, ips):
        for ip in ips:
            self.history[ip] = True
    
    def is_seen(self, ip):
        return ip in self.history
    
    def get_count(self):
        return len(self.history)
    
    def clear(self):
        self.history = {}
        if os.path.exists(self.filename):
            os.remove(self.filename)


class ProxyScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("免费节点爬虫 V2.0")
        self.root.geometry("1000x850")
        self.root.configure(bg=BG_COLOR)
        
        self.style_config()
        
        self.sources = [
            # === 聚合源 (多协议) ===
            ('FastNodes All', 'https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/everything.txt'),
            ('FastNodes US', 'https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/countries/US.txt'),
            ('FreeNodes', 'https://raw.githubusercontent.com/free-nodes/v2rayfree/main/v2ray.txt'),
            ('Epodonios', 'https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt'),
            ('NiREvil', 'https://raw.githubusercontent.com/NiREvil/vless/main/sub/SSTime'),
            ('EbraSha', 'https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/main/vmess_configs.txt'),
            ('XrayFree', 'https://raw.githubusercontent.com/xrayfree/free-ssr-ss-v2ray-vpn-clash/main/sub/v2ray.txt'),
            ('NodesFree', 'https://raw.githubusercontent.com/nodesfree/v2raynode/main/v2ray.txt'),
            ('ClashNode', 'https://clashnode.github.io/uploads/2026/04/0-20260418.txt'),
            ('V2RayClash', 'https://v2rayclashnode.github.io/uploads/2026/03/0-20260328.txt'),
            
            # === VMess 专用源 ===
            ('FastNodes VMess', 'https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/protocols/vmess.txt'),
            
            # === VLESS 专用源 ===
            ('FastNodes VLESS', 'https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/protocols/vless.txt'),
            ('EbraSha VLESS', 'https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/main/vless_configs.txt'),
            
            # === Shadowsocks 专用源 ===
            ('FastNodes SS', 'https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/protocols/ss.txt'),
            ('EbraSha SS', 'https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/main/ss_configs.txt'),
            
            # === Trojan 专用源 ===
            ('FastNodes Trojan', 'https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/protocols/trojan.txt'),
            ('EbraSha Trojan', 'https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/main/trojan_configs.txt'),
            
            # === Hysteria2 专用源 ===
            ('FastNodes H2', 'https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/protocols/hysteria2.txt'),
        ]
        
        self.working_nodes = []
        self.country_nodes = {}
        self.protocol_nodes = {}
        self.scraping = False
        self.ip_history = IPHistory()
        
        self.setup_ui()
        self.log(f"📊 历史IP记录: {self.ip_history.get_count()} 个", "info")
    
    def style_config(self):
        try:
            style = ttk.Style()
            style.theme_use('clam')
            style.configure(".", background=BG_COLOR, foreground=FG_COLOR, fieldbackground=FRAME_BG)
            style.configure("TFrame", background=BG_COLOR)
            style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR)
            style.configure("TButton", background=BTN_BG, foreground=FG_COLOR, borderwidth=0)
            style.configure("Horizontal.TProgressbar", background=ACCENT_COLOR, troughcolor=FRAME_BG)
        except:
            pass
    
    def setup_ui(self):
        title = tk.Label(self.root, text="🌐 免费节点爬虫 V2.0", font=("Microsoft YaHei UI", 24, "bold"), 
                        bg=BG_COLOR, fg=ACCENT_COLOR)
        title.pack(pady=(20, 15))
        
        self.create_frame_protocol()
        self.create_frame_scrape()
        self.create_frame_export()
        self.create_frame_log()
    
    def create_frame_protocol(self):
        frame = tk.LabelFrame(self.root, text="🔐 协议筛选 (支持11种协议)", font=("Microsoft YaHei UI", 11, "bold"),
                             bg=FRAME_BG, fg=ACCENT_COLOR, bd=1, relief="flat", padx=15, pady=12)
        frame.pack(fill="x", padx=20, pady=(10, 8))
        
        row1 = tk.Frame(frame, bg=FRAME_BG)
        row1.pack(fill="x")
        row2 = tk.Frame(frame, bg=FRAME_BG)
        row2.pack(fill="x", pady=(8, 0))
        
        self.protocol_btns = {}
        protocols_list = list(PROTOCOLS.keys())
        
        for i, proto in enumerate(protocols_list):
            btn = tk.Button(row1 if i < 6 else row2, text=proto, width=11, font=("Microsoft YaHei UI", 10),
                           bg=BTN_BG, fg=FG_COLOR, bd=0, relief="flat",
                           command=lambda p=proto: self.toggle_protocol(p))
            btn.pack(side="left", padx=4, pady=4)
            self.protocol_btns[proto] = {"btn": btn, "selected": False}
        
        btn_frame = tk.Frame(frame, bg=FRAME_BG)
        btn_frame.pack(side="right", padx=(15, 0))
        
        tk.Button(btn_frame, text="全选", width=7, font=("Microsoft YaHei UI", 10),
                 bg=ACCENT_COLOR, fg="#1e1e2e", bd=0, relief="flat",
                 command=self.select_all_protocols).pack(side="left", padx=3)
        tk.Button(btn_frame, text="清除", width=7, font=("Microsoft YaHei UI", 10),
                 bg=BTN_BG, fg=FG_COLOR, bd=0, relief="flat",
                 command=self.clear_protocols).pack(side="left", padx=3)
    
    def toggle_protocol(self, proto):
        info = self.protocol_btns[proto]
        info["selected"] = not info["selected"]
        if info["selected"]:
            info["btn"].config(bg=PROTOCOLS[proto]["color"], fg="#1e1e2e")
        else:
            info["btn"].config(bg=BTN_BG, fg=FG_COLOR)
    
    def select_all_protocols(self):
        for proto, info in self.protocol_btns.items():
            info["selected"] = True
            info["btn"].config(bg=PROTOCOLS[proto]["color"], fg="#1e1e2e")
    
    def clear_protocols(self):
        for proto, info in self.protocol_btns.items():
            info["selected"] = False
            info["btn"].config(bg=BTN_BG, fg=FG_COLOR)
    
    def create_frame_scrape(self):
        frame = tk.Frame(self.root, bg=FRAME_BG, padx=20, pady=12)
        frame.pack(fill="x", padx=20, pady=(10, 8))
        
        options_frame = tk.Frame(frame, bg=FRAME_BG)
        options_frame.pack(side="left")
        
        tk.Label(options_frame, text="并发:", bg=FRAME_BG, fg=FG_COLOR, font=("Microsoft YaHei UI", 10)).pack(side="left")
        
        self.thread_btns = {}
        for val in ["50", "100", "150", "200"]:
            btn = tk.Button(options_frame, text=val, width=4, font=("Microsoft YaHei UI", 9),
                           bg=BTN_BG, fg=FG_COLOR, bd=0, relief="flat",
                           command=lambda v=val: self.select_thread(v))
            btn.pack(side="left", padx=2)
            self.thread_btns[val] = btn
        
        self.thread_var = tk.StringVar(value="100")
        self.update_thread_btns("100")
        
        tk.Label(options_frame, text=" 源:", bg=FRAME_BG, fg=FG_COLOR, font=("Microsoft YaHei UI", 10)).pack(side="left", padx=(10, 0))
        
        self.source_btns = {}
        for val in ["全", "5", "10", "15", "20"]:
            btn = tk.Button(options_frame, text=val, width=3, font=("Microsoft YaHei UI", 9),
                           bg=BTN_BG, fg=FG_COLOR, bd=0, relief="flat",
                           command=lambda v=val: self.select_source_count(v))
            btn.pack(side="left", padx=2)
            self.source_btns[val] = btn
        
        self.source_count_var = tk.StringVar(value="全")
        self.update_source_btns("全")
        
        self.btn_scrape = tk.Button(frame, text="▶ 开始爬取", command=self.start_scrape_thread,
                                    bg=ACCENT_COLOR, fg="#1e1e2e", font=("Microsoft YaHei UI", 11, "bold"),
                                    width=12, bd=0, padx=12, pady=6)
        self.btn_scrape.pack(side="left", padx=(15, 10))
        
        self.status_label = tk.Label(frame, text="就绪", bg=FRAME_BG, fg="#6c7086", font=("Microsoft YaHei UI", 10))
        self.status_label.pack(side="left", padx=10)
        
        limit_frame = tk.Frame(frame, bg=FRAME_BG)
        limit_frame.pack(side="left", padx=(10, 0))
        
        tk.Label(limit_frame, text="🎯 节点上限", bg=FRAME_BG, fg=ACCENT_COLOR, font=("Microsoft YaHei UI", 9)).pack(side="left", padx=(0, 5))
        
        self.max_nodes_var = tk.StringVar(value="100")
        limit_entry = tk.Entry(limit_frame, textvariable=self.max_nodes_var, width=8, font=("Consolas", 12, "bold"),
                               bg="#252535", fg=SUCCESS_COLOR, bd=1, relief="solid", 
                               highlightthickness=1, highlightcolor=ACCENT_COLOR, highlightbackground="#3a3a4a",
                               justify="center")
        limit_entry.pack(side="left", padx=5)
        
        tk.Label(limit_frame, text="个", bg=FRAME_BG, fg=FG_COLOR, font=("Microsoft YaHei UI", 10)).pack(side="left")
        
        self.progress = ttk.Progressbar(frame, mode='indeterminate', length=150)
        self.progress.pack(side="left", fill="x", expand=True, padx=(15, 5))
    
    def select_thread(self, val):
        self.thread_var.set(val)
        self.update_thread_btns(val)
    
    def select_source_count(self, val):
        self.source_count_var.set(val)
        self.update_source_btns(val)
    
    def update_source_btns(self, selected):
        for val, btn in self.source_btns.items():
            if val == selected:
                btn.config(bg=SUCCESS_COLOR, fg="#1e1e2e")
            else:
                btn.config(bg=BTN_BG, fg=FG_COLOR)
    
    def update_thread_btns(self, selected):
        for val, btn in self.thread_btns.items():
            if val == selected:
                btn.config(bg=ACCENT_COLOR, fg="#1e1e2e")
            else:
                btn.config(bg=BTN_BG, fg=FG_COLOR)
    
    def create_frame_export(self):
        frame = tk.Frame(self.root, bg=FRAME_BG, padx=20, pady=12)
        frame.pack(fill="x", padx=20, pady=8)
        
        tk.Label(frame, text="国家:", bg=FRAME_BG, fg=FG_COLOR, font=("Microsoft YaHei UI", 11)).pack(side="left")
        
        self.country_btns = {}
        country_frame = tk.Frame(frame, bg=FRAME_BG)
        country_frame.pack(side="left", padx=15)
        
        countries = ["全部", "美国", "加拿大", "英国", "德国", "荷兰", "日本", "新加坡", "香港", "俄罗斯"]
        for c in countries:
            btn = tk.Button(country_frame, text=c, width=6, font=("Microsoft YaHei UI", 10),
                           bg=BTN_BG, fg=FG_COLOR, bd=0, relief="flat",
                           command=lambda v=c: self.select_country(v))
            btn.pack(side="left", padx=3)
            self.country_btns[c] = btn
        
        self.country_var = tk.StringVar(value="全部")
        self.update_country_btns("全部")
        
        format_frame = tk.LabelFrame(frame, text="📤 导出格式", font=("Microsoft YaHei UI", 10, "bold"),
                                     bg=FRAME_BG, fg=ACCENT_COLOR, bd=1, relief="flat", padx=10, pady=8)
        format_frame.pack(side="left", padx=(10, 15))
        
        self.export_format_var = tk.StringVar(value="geekez")
        
        btn_geekez = tk.Radiobutton(format_frame, text="🎯 GeekEZ", variable=self.export_format_var, value="geekez",
                              bg=FRAME_BG, fg="#00d4ff", selectcolor="#00d4ff",
                              font=("Microsoft YaHei UI", 10, "bold"), padx=10, pady=5,
                              command=lambda: self.update_format_btns("geekez"))
        btn_geekez.pack(side="left", padx=5)
        
        btn_v2rayn = tk.Radiobutton(format_frame, text="🌐 v2rayN", variable=self.export_format_var, value="v2rayn",
                                  bg=FRAME_BG, fg="#a6e3a1", selectcolor="#a6e3a1",
                                  font=("Microsoft YaHei UI", 10, "bold"), padx=10, pady=5,
                                  command=lambda: self.update_format_btns("v2rayn"))
        btn_v2rayn.pack(side="left", padx=5)
        
        btn_txt = tk.Radiobutton(format_frame, text="📝 TXT", variable=self.export_format_var, value="txt",
                              bg=FRAME_BG, fg=FG_COLOR, selectcolor=ACCENT_COLOR,
                              font=("Microsoft YaHei UI", 10), padx=10, pady=5,
                              command=lambda: self.update_format_btns("txt"))
        btn_txt.pack(side="left", padx=5)
        
        self.format_btns = {"geekez": btn_geekez, "v2rayn": btn_v2rayn, "txt": btn_txt}
        self.update_format_btns("geekez")
        
        self.btn_export = tk.Button(frame, text="📤 导出", command=self.export_with_format,
                                    bg=ACCENT_COLOR, fg="#1e1e2e", font=("Microsoft YaHei UI", 11, "bold"),
                                    width=10, bd=0, padx=10, pady=6)
        self.btn_export.pack(side="left", padx=(15, 8))
        
        self.btn_open = tk.Button(frame, text="📂 打开", command=self.open_export_folder,
                                  bg=WARNING_COLOR, fg="#1e1e2e", font=("Microsoft YaHei UI", 11, "bold"),
                                  width=8, bd=0, padx=8, pady=6)
        self.btn_open.pack(side="left", padx=5)
        
        self.btn_clear_folder = tk.Button(frame, text="🗑️ 清空文件夹", command=self.clear_export_folder,
                                        bg="#e74c3c", fg="#ffffff", font=("Microsoft YaHei UI", 11, "bold"),
                                        width=14, bd=0, padx=12, pady=6)
        self.btn_clear_folder.pack(side="left", padx=8)
        
        self.btn_clear_history = tk.Button(frame, text="清除IP历史", command=self.clear_history,
                                           bg=ERROR_COLOR, fg="#1e1e2e", font=("Microsoft YaHei UI", 11, "bold"),
                                           width=14, bd=0, padx=12, pady=6)
        self.btn_clear_history.pack(side="left", padx=8)
    
    def select_country(self, val):
        self.country_var.set(val)
        self.update_country_btns(val)
    
    def update_format_btns(self, selected):
        format_colors = {
            "geekez": "#00d4ff",
            "v2rayn": "#a6e3a1",
            "txt": ACCENT_COLOR
        }
        for fmt, btn in self.format_btns.items():
            if fmt == selected:
                btn.config(bg=format_colors[fmt], fg="#1e1e2e")
            else:
                if fmt == "geekez":
                    btn.config(bg=BTN_BG, fg="#00d4ff")
                elif fmt == "v2rayn":
                    btn.config(bg=BTN_BG, fg="#a6e3a1")
                else:
                    btn.config(bg=BTN_BG, fg=FG_COLOR)
    
    def update_country_btns(self, selected):
        for c, btn in self.country_btns.items():
            if c == selected:
                btn.config(bg=ACCENT_COLOR, fg="#1e1e2e")
            else:
                btn.config(bg=BTN_BG, fg=FG_COLOR)
    
    def create_frame_log(self):
        frame = tk.LabelFrame(self.root, text="📋 日志", font=("Microsoft YaHei UI", 12, "bold"),
                             bg=FRAME_BG, fg=FG_COLOR, bd=1, relief="flat", padx=15, pady=12)
        frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        
        self.log_text = tk.Text(frame, width=85, bg="#11111b", fg=FG_COLOR,
                                font=("Consolas", 12), bd=0, padx=12, pady=10)
        self.log_text.pack(side="left", fill="both", expand=True)
        self.log_text.tag_config("info", foreground=ACCENT_COLOR)
        self.log_text.tag_config("success", foreground=SUCCESS_COLOR)
        self.log_text.tag_config("warning", foreground=WARNING_COLOR)
        
        scroll = tk.Scrollbar(frame, bg=FRAME_BG, width=12)
        scroll.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scroll.set)
        scroll.config(command=self.log_text.yview)
    
    def log(self, msg, tag="info"):
        self.log_text.insert("end", msg + "\n", tag)
        self.log_text.see("end")
        self.root.update_idletasks()
    
    def start_scrape_thread(self):
        if self.scraping:
            return
        
        selected = [p for p, info in self.protocol_btns.items() if info["selected"]]
        if not selected:
            messagebox.showwarning("提示", "请至少选择一个协议类型!")
            return
        
        self.scraping = True
        self.btn_scrape.config(state="disabled", bg=BTN_BG)
        self.progress.start(10)
        
        thread = threading.Thread(target=self.scrape_worker, args=(selected,), daemon=True)
        thread.start()
    
    def fetch(self, url):
        try:
            r = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code == 200:
                nodes = []
                seen = set()
                for line in r.text.strip().split('\n'):
                    line = line.strip()
                    if not line or line in seen:
                        continue
                    seen.add(line)
                    
                    for proto, info in PROTOCOLS.items():
                        if re.search(info["pattern"], line, re.IGNORECASE):
                            nodes.append(line)
                            break
                return nodes
        except:
            pass
        return []
    
    def extract_ip(self, node):
        match = re.search(r'@([0-9.]+):', node)
        if match:
            return match.group(1)
        return None
    
    def get_ip_port(self, node):
        match = re.search(r'@([0-9.]+):([0-9]+)', node)
        if match:
            return match.group(1), int(match.group(2))
        match = re.search(r'://([0-9.]+):([0-9]+)', node)
        if match:
            return match.group(1), int(match.group(2))
        match = re.search(r'([0-9.]+):([0-9]+)$', node)
        if match:
            return match.group(1), int(match.group(2))
        return None, None
    
    def get_country(self, ip):
        try:
            r = requests.get(f'http://ip-api.com/json/{ip}?fields=countryCode', timeout=2)
            return r.json().get('countryCode', '')
        except:
            return ''
    
    def test_node(self, node):
        ip, port = self.get_ip_port(node)
        if not ip or port is None:
            return None, ''
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((ip, port))
            sock.close()
            country = self.get_country(ip)
            return node, country
        except:
            pass
        
        if node.lower().startswith('http://') or node.lower().startswith('socks'):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((ip, port))
                sock.close()
                return node, 'PROXY'
            except:
                pass
        
        return None, ''
    
    def scrape_worker(self, selected_protocols):
        threads = self.thread_var.get()
        count_str = self.source_count_var.get()
        
        self.log("=" * 50, "info")
        self.log(f"🚀 开始爬取 (协议: {', '.join(selected_protocols)})...", "info")
        
        import random
        
        if count_str == "全部":
            sources_to_fetch = self.sources
            self.log(f"📊 使用全部 {len(self.sources)} 个数据源", "info")
        else:
            count = int(count_str)
            
            proto_keywords = {
                "VMess": ["vmess", "v2ray", "v2"],
                "VLESS": ["vless"],
                "Shadowsocks": ["ss", "shadowsock"],
                "Trojan": ["trojan"],
                "Hysteria2": ["h2", "hysteria", "hy2"],
            }
            
            preferred = []
            for name, url in self.sources:
                name_lower = name.lower()
                for proto in selected_protocols:
                    keywords = proto_keywords.get(proto, [])
                    if any(k in name_lower for k in keywords):
                        preferred.append((name, url))
                        break
            
            other = [(n, u) for n, u in self.sources if (n, u) not in preferred]
            
            if len(preferred) >= count:
                sources_to_fetch = random.sample(preferred, count)
            elif len(preferred) + len(other) <= count:
                sources_to_fetch = self.sources
            else:
                need_more = count - len(preferred)
                sources_to_fetch = preferred + random.sample(other, min(need_more, len(other)))
            
            self.log(f"🎲 随机选择 {len(sources_to_fetch)} 个数据源 (优先: {len(preferred)})", "info")
        
        self.log(f"📥 开始并行获取 {len(sources_to_fetch)} 个数据源...", "info")
        
        source_results = {}
        def fetch_source(args):
            name, url = args
            nodes = self.fetch(url)
            return name, nodes
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(fetch_source, (name, url)): name for name, url in sources_to_fetch}
            completed = 0
            for future in concurrent.futures.as_completed(futures):
                name, nodes = future.result()
                source_results[name] = nodes
                completed += 1
                self.log(f"   [{completed}/{len(sources_to_fetch)}] {name}: {len(nodes)} 个节点", "success")
        
        all_nodes = []
        for name, nodes in source_results.items():
            all_nodes.extend(nodes)
        
        all_nodes = list(set(all_nodes))
        
        filtered = []
        skipped_count = 0
        for node in all_nodes:
            ip = self.extract_ip(node)
            if ip and self.ip_history.is_seen(ip):
                skipped_count += 1
                continue
            for proto in selected_protocols:
                if re.search(PROTOCOLS[proto]["pattern"], node, re.IGNORECASE):
                    filtered.append(node)
                    break
        all_nodes = filtered
        
        if skipped_count > 0:
            self.log(f"📊 筛选后: {len(all_nodes)} 个节点 (跳过 {skipped_count} 个已存在IP)", "info")
        else:
            self.log(f"📊 筛选后: {len(all_nodes)} 个节点", "info")
        self.log(f"🧪 测试连接 (并行 {threads} 线程)...", "warning")
        
        self.working_nodes = []
        self.country_nodes = {}
        self.protocol_nodes = {p: [] for p in selected_protocols}
        
        try:
            max_nodes = int(self.max_nodes_var.get())
        except:
            max_nodes = 100
        
        self.log(f"🎯 目标: 获取 {max_nodes} 个可用节点后停止", "info")
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=int(threads)) as executor:
                futures = {executor.submit(self.test_node, n): n for n in all_nodes}
                completed = 0
                for future in concurrent.futures.as_completed(futures):
                    completed += 1
                    node, country = future.result()
                    if node:
                        self.working_nodes.append(node)
                        if country not in self.country_nodes:
                            self.country_nodes[country] = []
                        self.country_nodes[country].append(node)
                        
                        for proto in selected_protocols:
                            if re.search(PROTOCOLS[proto]["pattern"], node, re.IGNORECASE):
                                self.protocol_nodes[proto].append(node)
                        
                        if len(self.working_nodes) >= max_nodes:
                            self.log(f"\n🎉 已达到目标 {max_nodes} 个节点，停止测试!", "success")
                            for f in futures:
                                f.cancel()
                            break
                    
                    if completed % 100 == 0 or len(self.working_nodes) >= max_nodes:
                        self.log(f"   已测试 {completed} 个, 可用: {len(self.working_nodes)}", "info")
        except Exception as e:
            self.log(f"❌ 错误: {e}", "error")
        
        country_map = {'US': '美国', 'CA': '加拿大', 'GB': '英国', 'DE': '德国', 
                       'NL': '荷兰', 'JP': '日本', 'SG': '新加坡', 'HK': '香港', 'RU': '俄罗斯'}
        
        self.log("\n" + "=" * 50, "info")
        self.log(f"✅ 完成! 共找到 {len(self.working_nodes)} 个可用节点", "success")
        
        self.log("\n📍 国家分布:", "info")
        for c in sorted(self.country_nodes.keys()):
            name = country_map.get(c, c)
            self.log(f"   {name}: {len(self.country_nodes[c])}", "info")
        
        self.log("\n🔐 协议分布:", "info")
        for proto in selected_protocols:
            self.log(f"   {proto}: {len(self.protocol_nodes[proto])}", "info")
        
        new_ips = []
        for node in self.working_nodes:
            ip = self.extract_ip(node)
            if ip:
                new_ips.append(ip)
        
        if new_ips:
            self.ip_history.add_ips(new_ips)
            self.ip_history.save()
            self.log(f"\n💾 新增 {len(new_ips)} 个IP到历史记录", "success")
            self.log(f"📊 历史IP总数: {self.ip_history.get_count()} 个", "info")
        
        self.scraping = False
        self.progress.stop()
        self.btn_scrape.config(state="normal", bg=ACCENT_COLOR)
        self.status_label.config(text=f"可用: {len(self.working_nodes)} 个节点")
    
    def export_nodes(self):
        if not self.working_nodes:
            messagebox.showwarning("警告", "请先运行爬虫!")
            return
        
        selected_country = self.country_var.get()
        selected_protocols = [p for p, info in self.protocol_btns.items() if info["selected"]]
        
        country_map = {"美国": "US", "加拿大": "CA", "英国": "GB", "德国": "DE",
                       "荷兰": "NL", "日本": "JP", "新加坡": "SG", "香港": "HK", "俄罗斯": "RU"}
        reverse_map = {"US": "美国", "CA": "加拿大", "GB": "英国", "DE": "德国",
                       "NL": "荷兰", "JP": "日本", "SG": "新加坡", "HK": "香港", "RU": "俄罗斯"}
        
        os.makedirs('nodes', exist_ok=True)
        
        if selected_country == "全部":
            nodes = self.working_nodes
        else:
            c = country_map.get(selected_country)
            nodes = self.country_nodes.get(c, [])
        
        if selected_protocols:
            filtered = []
            for node in nodes:
                for proto in selected_protocols:
                    if re.search(PROTOCOLS[proto]["pattern"], node, re.IGNORECASE):
                        filtered.append(node)
                        break
            nodes = filtered
        
        if not nodes:
            messagebox.showwarning("警告", "没有符合条件的节点")
            return
        
        new_ips = []
        for node in nodes:
            ip = self.extract_ip(node)
            if ip and not self.ip_history.is_seen(ip):
                new_ips.append(ip)
                self.ip_history.add_ip(ip)
        
        if new_ips:
            self.ip_history.save()
        
        proto_str = "_".join(selected_protocols[:2]) if selected_protocols else "全部"
        filename = f'nodes/{selected_country}_{proto_str}.txt'
        
        with open(filename, 'w', encoding='utf-8') as f:
            for n in nodes:
                node_only = n.split('#')[0]
                f.write(node_only + '\n')
        
        self.log(f"✅ 已导出 {len(nodes)} 个节点到 {filename}", "success")
        if new_ips:
            self.log(f"💾 新增 {len(new_ips)} 个IP到历史记录", "success")
        messagebox.showinfo("完成", f"已导出 {len(nodes)} 个节点")
    
    def open_export_folder(self):
        folder = os.path.abspath('nodes')
        os.makedirs(folder, exist_ok=True)
        os.startfile(folder)
    
    def clear_history(self):
        if self.scraping:
            messagebox.showwarning("警告", "爬取中无法清除历史记录")
            return
        result = messagebox.askyesno("确认", f"确定要清除所有历史IP记录吗?\n当前历史记录: {self.ip_history.get_count()} 个IP")
        if result:
            self.ip_history.clear()
            self.log("✅ 已清除所有历史IP记录", "success")
            messagebox.showinfo("完成", "历史记录已清除")
    
    def clear_export_folder(self):
        folder = os.path.abspath('nodes')
        if not os.path.exists(folder):
            messagebox.showinfo("提示", "文件夹为空")
            return
        files = os.listdir(folder)
        if not files:
            messagebox.showinfo("提示", "文件夹为空")
            return
        result = messagebox.askyesno("确认", f"确定要清空 nodes 文件夹吗?\n将删除 {len(files)} 个文件")
        if result:
            for f in files:
                try:
                    os.remove(os.path.join(folder, f))
                except:
                    pass
            self.log(f"✅ 已清空 nodes 文件夹 ({len(files)} 个文件)", "success")
            messagebox.showinfo("完成", f"已删除 {len(files)} 个文件")
    
    def export_all_formats(self):
        if not self.working_nodes:
            messagebox.showwarning("警告", "请先运行爬虫获取节点!")
            return
        
        selected_country = self.country_var.get()
        selected_protocols = [p for p, info in self.protocol_btns.items() if info["selected"]]
        
        country_map = {"美国": "US", "加拿大": "CA", "英国": "GB", "德国": "DE",
                       "荷兰": "NL", "日本": "JP", "新加坡": "SG", "香港": "HK", "俄罗斯": "RU"}
        
        if selected_country == "全部":
            nodes = self.working_nodes
        else:
            c = country_map.get(selected_country)
            nodes = self.country_nodes.get(c, [])
        
        if selected_protocols:
            filtered = []
            for node in nodes:
                for proto in selected_protocols:
                    if re.search(PROTOCOLS[proto]["pattern"], node, re.IGNORECASE):
                        filtered.append(node)
                        break
            nodes = filtered
        
        if not nodes:
            messagebox.showwarning("警告", "没有符合条件的节点")
            return
        
        proto_str = "_".join(selected_protocols) if selected_protocols else "全部"
        
        self.log(f"\n📋 转换节点格式...", "info")
        
        import_lines = []
        detailed_lines = []
        
        for node in nodes:
            node_only = node.split('#')[0]
            
            node_proto = None
            if node_only.startswith('http://') or node_only.startswith('https://'):
                node_proto = 'HTTP'
            elif node_only.startswith('socks5://') or node_only.startswith('socks4://') or node_only.startswith('socks://'):
                node_proto = 'SOCKS'
            elif node_only.startswith('vmess://'):
                node_proto = 'VMess'
            elif node_only.startswith('vless://'):
                node_proto = 'VLESS'
            elif node_only.startswith('trojan://'):
                node_proto = 'Trojan'
            elif node_only.startswith('ss://'):
                node_proto = 'Shadowsocks'
            elif node_only.startswith('hysteria2://'):
                node_proto = 'Hysteria2'
            elif node_only.startswith('tuic://'):
                node_proto = 'TUIC'
            
            if node_proto not in selected_protocols:
                continue
            
            if node_only.startswith('http://') or node_only.startswith('https://'):
                import_lines.append(node_only)
                match = re.search(r'(https?)://(?:([^:]+):([^@]+)@)?([^:]+):(\d+)', node_only)
                if match:
                    proto, user, pwd, ip, port = match.groups()
                    user = user or ""
                    pwd = pwd or ""
                    detailed_lines.append(f"[HTTP]\n协议: {proto.upper()}\n地址: {ip}\n端口: {port}\n用户名: {user}\n密码: {pwd}\n完整链接: {node_only}\n")
                else:
                    detailed_lines.append(f"[HTTP]\n完整链接: {node_only}\n")
            
            elif node_only.startswith('socks5://') or node_only.startswith('socks4://') or node_only.startswith('socks://'):
                import_lines.append(node_only)
                match = re.search(r'socks[45]?://(?:([^:]+):([^@]+)@)?([^:]+):(\d+)', node_only)
                if match:
                    user, pwd, ip, port = match.groups()
                    user = user or ""
                    pwd = pwd or ""
                    detailed_lines.append(f"[SOCKS]\n地址: {ip}\n端口: {port}\n用户名: {user}\n密码: {pwd}\n完整链接: {node_only}\n")
            
            elif node_only.startswith('vmess://'):
                import_lines.append(node_only)
                try:
                    data = json.loads(base64.b64decode(node_only.replace('vmess://', '')).decode())
                    detailed_lines.append(f"[VMess]\n地址: {data.get('add')}\n端口: {data.get('port')}\nID: {data.get('id')}\nUUID: {data.get('id')}\nAlterID: {data.get('aid')}\n网络: {data.get('net')}\n协议: {data.get('tls') or 'none'}\n完整链接: {node_only}\n")
                except:
                    detailed_lines.append(f"[VMess]\n完整链接: {node_only}\n")
            
            elif node_only.startswith('vless://'):
                import_lines.append(node_only)
                match = re.search(r'vless://([^@]+)@([^:]+):(\d+)', node_only)
                if match:
                    uuid, ip, port = match.groups()
                    detailed_lines.append(f"[VLESS]\n地址: {ip}\n端口: {port}\nUUID: {uuid}\n完整链接: {node_only}\n")
            
            elif node_only.startswith('trojan://'):
                import_lines.append(node_only)
                match = re.search(r'trojan://([^@]+)@([^:]+):(\d+)', node_only)
                if match:
                    pwd, ip, port = match.groups()
                    detailed_lines.append(f"[Trojan]\n地址: {ip}\n端口: {port}\n密码: {pwd}\n完整链接: {node_only}\n")
            
            elif node_only.startswith('ss://'):
                import_lines.append(node_only)
                match = re.search(r'ss://([A-Za-z0-9+/=]+)@([^:]+):(\d+)', node_only)
                if match:
                    cipher_pwd = match.group(1)
                    ip, port = match.group(2), match.group(3)
                    try:
                        decoded = base64.b64decode(cipher_pwd).decode()
                        if ':' in decoded:
                            cipher, pwd = decoded.split(':', 1)
                            detailed_lines.append(f"[Shadowsocks]\n地址: {ip}\n端口: {port}\n加密: {cipher}\n密码: {pwd}\n完整链接: {node_only}\n")
                        else:
                            detailed_lines.append(f"[Shadowsocks]\n地址: {ip}\n端口: {port}\n密码: {decoded}\n完整链接: {node_only}\n")
                    except:
                        detailed_lines.append(f"[Shadowsocks]\n地址: {ip}\n端口: {port}\n完整链接: {node_only}\n")
            
            elif node_only.startswith('hysteria2://'):
                import_lines.append(node_only)
                match = re.search(r'hysteria2://([^@]+)@([^:]+):(\d+)', node_only)
                if match:
                    pwd, ip, port = match.groups()
                    detailed_lines.append(f"[Hysteria2]\n地址: {ip}\n端口: {port}\n密码: {pwd}\n完整链接: {node_only}\n")
            
            elif node_only.startswith('tuic://'):
                import_lines.append(node_only)
                match = re.search(r'tuic://([^:]+):([^@]+)@([^:]+):(\d+)', node_only)
                if match:
                    uuid, pwd, ip, port = match.groups()
                    detailed_lines.append(f"[TUIC]\n地址: {ip}\n端口: {port}\nUUID: {uuid}\n密码: {pwd}\n完整链接: {node_only}\n")
            
            elif re.match(r'^[\d.]+:\d+$', node_only):
                ip, port = node_only.rsplit(':', 1)
                import_lines.append(f"socks5://{ip}:{port}#HTTP-{ip}")
                detailed_lines.append(f"[HTTP/SOCKS]\n地址: {ip}\n端口: {port}\n协议: HTTP/SOCKS5\n完整链接: socks5://{ip}:{port}\n")
        
        new_ips = []
        for node in import_lines:
            ip = self.extract_ip(node)
            if ip and not self.ip_history.is_seen(ip):
                new_ips.append(ip)
                self.ip_history.add_ip(ip)
        
        if new_ips:
            self.ip_history.save()
        
        plain_content = '\n'.join(import_lines)
        pyperclip.copy(plain_content)
        
        os.makedirs('nodes', exist_ok=True)
        
        link_filename = f'nodes/{selected_country}_{proto_str}.txt'
        with open(link_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(import_lines))
        
        detail_filename = f'nodes/{selected_country}_{proto_str}_详情.txt'
        with open(detail_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(detailed_lines))
        
        self.log(f"  ✅ {len(import_lines)} 个节点已复制", "success")
        self.log(f"  📄 链接: {link_filename}", "success")
        self.log(f"  📄 详情: {detail_filename}", "success")
        if new_ips:
            self.log(f"  💾 新增 {len(new_ips)} 个IP到历史记录", "success")
        self.log(f"  📊 历史IP总数: {self.ip_history.get_count()} 个", "info")
        self.log(f"  💡 导入: 服务器 → 从剪贴板导入批量URL", "info")
        self.log(f"  ⚠️ 失败则: 订阅 → 添加订阅 → 粘贴URL", "warning")
        messagebox.showinfo("完成", f"剪贴板: {len(import_lines)} 个节点\n链接: {link_filename}\n详情: {detail_filename}\n历史IP: {self.ip_history.get_count()} 个")
    
    def export_v2rayn_json(self):
        if not self.working_nodes:
            messagebox.showwarning("警告", "请先运行爬虫获取节点!")
            return
        
        selected_country = self.country_var.get()
        selected_protocols = [p for p, info in self.protocol_btns.items() if info["selected"]]
        
        country_map = {"美国": "US", "加拿大": "CA", "英国": "GB", "德国": "DE",
                       "荷兰": "NL", "日本": "JP", "新加坡": "SG", "香港": "HK", "俄罗斯": "RU"}
        
        if selected_country == "全部":
            nodes = self.working_nodes
        else:
            c = country_map.get(selected_country)
            nodes = self.country_nodes.get(c, [])
        
        if not nodes:
            messagebox.showwarning("警告", "没有可用节点")
            return
        
        if selected_protocols:
            filtered = []
            for node in nodes:
                for proto in selected_protocols:
                    if re.search(PROTOCOLS[proto]["pattern"], node, re.IGNORECASE):
                        filtered.append(node)
                        break
            nodes = filtered
        
        if not nodes:
            messagebox.showwarning("警告", "没有符合条件的节点")
            return
        
        self.log("\n生成v2rayN兼容节点...", "info")
        
        valid_urls = []
        detailed_lines = []
        
        for node in nodes:
            node_only = node.split('#')[0]
            
            node_proto = None
            if node_only.startswith('http://') or node_only.startswith('https://'):
                node_proto = 'HTTP'
            elif node_only.startswith('socks5://') or node_only.startswith('socks4://') or node_only.startswith('socks://'):
                node_proto = 'SOCKS'
            elif node_only.startswith('vmess://'):
                node_proto = 'VMess'
            elif node_only.startswith('vless://'):
                node_proto = 'VLESS'
            elif node_only.startswith('trojan://'):
                node_proto = 'Trojan'
            elif node_only.startswith('ss://'):
                node_proto = 'Shadowsocks'
            elif node_only.startswith('hysteria2://'):
                node_proto = 'Hysteria2'
            elif node_only.startswith('tuic://'):
                node_proto = 'TUIC'
            
            if node_proto not in selected_protocols:
                continue
            
            if node_only.startswith('http://') or node_only.startswith('https://'):
                valid_urls.append(node_only)
                match = re.search(r'(https?)://(?:([^:]+):([^@]+)@)?([^:]+):(\d+)', node_only)
                if match:
                    proto, user, pwd, ip, port = match.groups()
                    user = user or ""
                    pwd = pwd or ""
                    detailed_lines.append(f"[HTTP]\n协议: {proto.upper()}\n地址: {ip}\n端口: {port}\n用户名: {user}\n密码: {pwd}\n完整链接: {node_only}\n")
                else:
                    detailed_lines.append(f"[HTTP]\n完整链接: {node_only}\n")
            
            elif node_only.startswith('socks5://') or node_only.startswith('socks4://') or node_only.startswith('socks://'):
                valid_urls.append(node_only)
                match = re.search(r'socks[45]?://(?:([^:]+):([^@]+)@)?([^:]+):(\d+)', node_only)
                if match:
                    user, pwd, ip, port = match.groups()
                    user = user or ""
                    pwd = pwd or ""
                    detailed_lines.append(f"[SOCKS]\n地址: {ip}\n端口: {port}\n用户名: {user}\n密码: {pwd}\n完整链接: {node_only}\n")
            
            elif node_only.startswith('vmess://'):
                valid_urls.append(node_only)
                try:
                    data = json.loads(base64.b64decode(node_only.replace('vmess://', '')).decode())
                    detailed_lines.append(f"[VMess]\n地址: {data.get('add')}\n端口: {data.get('port')}\nID: {data.get('id')}\nUUID: {data.get('id')}\nAlterID: {data.get('aid')}\n网络: {data.get('net')}\n协议: {data.get('tls') or 'none'}\n完整链接: {node_only}\n")
                except:
                    detailed_lines.append(f"[VMess]\n完整链接: {node_only}\n")
            
            elif node_only.startswith('vless://'):
                valid_urls.append(node_only)
                match = re.search(r'vless://([^@]+)@([^:]+):(\d+)', node_only)
                if match:
                    uuid, ip, port = match.groups()
                    detailed_lines.append(f"[VLESS]\n地址: {ip}\n端口: {port}\nUUID: {uuid}\n完整链接: {node_only}\n")
            
            elif node_only.startswith('trojan://'):
                valid_urls.append(node_only)
                match = re.search(r'trojan://([^@]+)@([^:]+):(\d+)', node_only)
                if match:
                    pwd, ip, port = match.groups()
                    detailed_lines.append(f"[Trojan]\n地址: {ip}\n端口: {port}\n密码: {pwd}\n完整链接: {node_only}\n")
            
            elif node_only.startswith('ss://'):
                valid_urls.append(node_only)
                match = re.search(r'ss://([A-Za-z0-9+/=]+)@([^:]+):(\d+)', node_only)
                if match:
                    cipher_pwd = match.group(1)
                    ip, port = match.group(2), match.group(3)
                    try:
                        decoded = base64.b64decode(cipher_pwd).decode()
                        if ':' in decoded:
                            cipher, pwd = decoded.split(':', 1)
                            detailed_lines.append(f"[Shadowsocks]\n地址: {ip}\n端口: {port}\n加密: {cipher}\n密码: {pwd}\n完整链接: {node_only}\n")
                        else:
                            detailed_lines.append(f"[Shadowsocks]\n地址: {ip}\n端口: {port}\n密码: {decoded}\n完整链接: {node_only}\n")
                    except:
                        detailed_lines.append(f"[Shadowsocks]\n地址: {ip}\n端口: {port}\n完整链接: {node_only}\n")
            
            elif node_only.startswith('hysteria2://'):
                valid_urls.append(node_only)
                match = re.search(r'hysteria2://([^@]+)@([^:]+):(\d+)', node_only)
                if match:
                    pwd, ip, port = match.groups()
                    detailed_lines.append(f"[Hysteria2]\n地址: {ip}\n端口: {port}\n密码: {pwd}\n完整链接: {node_only}\n")
            
            elif node_only.startswith('tuic://'):
                valid_urls.append(node_only)
                match = re.search(r'tuic://([^:]+):([^@]+)@([^:]+):(\d+)', node_only)
                if match:
                    uuid, pwd, ip, port = match.groups()
                    detailed_lines.append(f"[TUIC]\n地址: {ip}\n端口: {port}\nUUID: {uuid}\n密码: {pwd}\n完整链接: {node_only}\n")
            
            elif re.match(r'^[\d.]+:\d+$', node_only):
                ip, port = node_only.rsplit(':', 1)
                valid_urls.append(f"socks5://{node_only}")
                detailed_lines.append(f"[HTTP/SOCKS]\n地址: {ip}\n端口: {port}\n协议: HTTP/SOCKS5\n完整链接: socks5://{ip}:{port}\n")
        
        if not valid_urls:
            messagebox.showwarning("警告", "没有v2rayN支持的协议节点\n(仅支持: VMess/VLESS/Trojan/SS/Hysteria2/HTTP/SOCKS)")
            return
        
        content = '\n'.join(valid_urls)
        pyperclip.copy(content)
        
        os.makedirs('nodes', exist_ok=True)
        link_filename = 'nodes/全部_链接.txt'
        detail_filename = 'nodes/全部_详情.txt'
        
        with open(link_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(valid_urls))
        
        with open(detail_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(detailed_lines))
        
        self.log(f"  ✅ {len(valid_urls)} 个节点已复制到剪贴板", "success")
        self.log(f"  📄 链接: {link_filename}", "success")
        self.log(f"  📄 详情: {detail_filename}", "success")
        self.log("  💡 导入: v2rayN → 服务器 → 从剪贴板导入批量URL", "info")
        messagebox.showinfo("完成", f"剪贴板: {len(valid_urls)} 个节点\n链接: {link_filename}\n详情: {detail_filename}")
    
    def node_to_v2ray_outbound(self, node):
        try:
            node_only = node.split('#')[0]
            
            if node_only.startswith('vmess://'):
                node_str = node_only.replace('vmess://', '')
                try:
                    decoded = base64.b64decode(node_str).decode()
                    data = json.loads(decoded)
                    return {
                        "tag": f"VMess-{data.get('add', '')[:8]}",
                        "protocol": "vmess",
                        "settings": {"vless": [], "vmess": [{
                            "address": data.get('add', ''),
                            "port": int(data.get('port', 0)),
                            "id": data.get('id', ''),
                            "alterId": int(data.get('aid', 0)),
                            "security": "auto"
                        }]},
                        "streamSettings": {"network": data.get('net', 'tcp')}
                    }
                except:
                    return None
            
            elif node_only.startswith('vless://'):
                node_str = node_only.replace('vless://', '')
                uuid = node_str.split('@')[0]
                rest = node_str.split('@')[1]
                ip = rest.split(':')[0]
                port = rest.split(':')[1].split('?')[0]
                params = rest.split('?')[1] if '?' in rest else ''
                
                ob = {
                    "tag": f"VLESS-{ip[:8]}",
                    "protocol": "vless",
                    "settings": {"vless": [{
                        "address": ip,
                        "port": int(port),
                        "id": uuid,
                        "flow": "",
                        "encryption": "none"
                    }]},
                    "streamSettings": {"network": "tcp"}
                }
                
                if 'ws' in params:
                    ob["streamSettings"]["network"] = "ws"
                    m = re.search(r'path=([^&]+)', params)
                    if m:
                        ob["streamSettings"]["wsSettings"] = {"path": m.group(1)}
                if 'tls' in params or 'reality' in params:
                    ob["streamSettings"]["security"] = "tls"
                    m = re.search(r'sni=([^&]+)', params)
                    if m:
                        ob["streamSettings"]["tlsSettings"] = {"serverName": m.group(1)}
                
                return ob
            
            elif node_only.startswith('trojan://'):
                node_str = node_only.replace('trojan://', '')
                password = node_str.split('@')[0]
                rest = node_str.split('@')[1]
                ip = rest.split(':')[0]
                port = rest.split(':')[1].split('?')[0]
                params = rest.split('?')[1] if '?' in rest else ''
                
                ob = {
                    "tag": f"Trojan-{ip[:8]}",
                    "protocol": "trojan",
                    "settings": {"trojan": [{
                        "address": ip,
                        "port": int(port),
                        "password": password
                    }]}
                }
                
                if 'sni=' in params:
                    m = re.search(r'sni=([^&]+)', params)
                    if m:
                        ob["streamSettings"] = {"security": "tls", "tlsSettings": {"serverName": m.group(1)}}
                
                return ob
            
            elif node_only.startswith('ss://'):
                node_str = node_only.replace('ss://', '')
                if '@' in node_str:
                    auth = node_str.split('@')[0]
                    rest = node_str.split('@')[1]
                    ip = rest.split(':')[0]
                    port = rest.split(':')[1].split('?')[0]
                    try:
                        decoded = base64.b64decode(auth).decode()
                        cipher = decoded.split(':')[0]
                        password = decoded.split(':')[1]
                        return {
                            "tag": f"SS-{ip[:8]}",
                            "protocol": "shadowsocks",
                            "settings": {"shadowsocks": [{
                                "address": ip,
                                "port": int(port),
                                "method": cipher,
                                "password": password
                            }]}
                        }
                    except:
                        pass
            
            elif node_only.startswith('hysteria2://') or node_only.startswith('hysteria://'):
                node_str = node_only.replace('hysteria2://', '').replace('hysteria://', '')
                if '@' in node_str:
                    password = node_str.split('@')[0]
                    rest = node_str.split('@')[1]
                    ip = rest.split(':')[0]
                    port = rest.split(':')[1].split('?')[0]
                    return {
                        "tag": f"Hysteria2-{ip[:8]}",
                        "protocol": "hysteria2",
                        "settings": {"hysteria2": [{
                            "address": ip,
                            "port": int(port),
                            "password": password
                        }]}
                    }
            
            elif node_only.startswith('socks://') or node_only.startswith('socks4://') or node_only.startswith('socks5://'):
                node_str = re.sub(r'^socks[45]?://', '', node_only)
                if '@' in node_str:
                    auth = node_str.split('@')[0]
                    rest = node_str.split('@')[1]
                    ip_port = rest.split(':')
                    if len(ip_port) >= 2:
                        ip = ip_port[0]
                        port = ip_port[1]
                        return {
                            "tag": f"SOCKS-{ip[:8]}",
                            "protocol": "socks",
                            "settings": {"socks": [{
                                "address": ip,
                                "port": int(port),
                                "users": [{"user": auth.split(':')[0], "pass": auth.split(':')[1] if ':' in auth else ""}]
                            }]}
                        }
                else:
                    ip_port = node_str.split(':')
                    if len(ip_port) >= 2:
                        ip = ip_port[0]
                        port = ip_port[1]
                        return {
                            "tag": f"SOCKS-{ip[:8]}",
                            "protocol": "socks",
                            "settings": {"socks": [{"address": ip, "port": int(port)}]}
                        }
            
            elif node_only.startswith('http://') or node_only.startswith('https://'):
                m = re.search(r'(https?)://([^:]+):(\d+)', node_only)
                if m:
                    return {
                        "tag": f"HTTP-{m.group(2)[:8]}",
                        "protocol": "http",
                        "settings": {"http": [{
                            "address": m.group(2),
                            "port": int(m.group(3))
                        }]}
                    }
            
        except Exception as e:
            self.log(f"  ⚠️ 转换失败: {str(e)[:50]}", "warning")
        return None
    
    def get_clash_content(self, nodes):
        proxies = []
        for node in nodes:
            p = self.node_to_clash(node)
            if p:
                proxies.append(p)
        
        lines = ['port: 7890', 'socks-port: 7891', 'allow-lan: true', 
                 'mode: rule', 'external-controller: 127.0.0.1:9090', 'proxies:']
        for p in proxies:
            for line in self.format_clash_proxy(p):
                lines.append(line)
        lines.extend(['proxy-groups:', '  - name: "Manual"', '    type: select', '    proxies:'])
        for p in proxies[:50]:
            lines.append(f'      - {p.get("name", "unknown")}')
        lines.append('rules:')
        lines.append('  - MATCH,Manual')
        return '\n'.join(lines)
    
    def save_as_txt(self, nodes, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            for n in nodes:
                node_only = n.split('#')[0]
                f.write(node_only + '\n')
    
    def save_as_base64(self, nodes, filename):
        content = '\n'.join([n.split('#')[0] for n in nodes])
        encoded = base64.b64encode(content.encode('utf-8')).decode('ascii')
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(encoded)
    
    def save_as_clash(self, nodes, filename):
        proxies = []
        for node in nodes:
            p = self.node_to_clash(node)
            if p:
                proxies.append(p)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('port: 7890\n')
            f.write('socks-port: 7891\n')
            f.write('allow-lan: true\n')
            f.write('mode: rule\n')
            f.write('external-controller: 127.0.0.1:9090\n')
            f.write('proxies:\n')
            for p in proxies:
                for line in self.format_clash_proxy(p):
                    f.write(line + '\n')
            f.write('proxy-groups:\n')
            f.write('  - name: "Manual"\n')
            f.write('    type: select\n')
            f.write('    proxies:\n')
            for p in proxies[:50]:
                f.write(f'      - {p.get("name", "unknown")}\n')
            f.write('rules:\n')
            f.write('  - MATCH,Manual\n')
    
    def format_clash_proxy(self, p):
        lines = [f'  - name: "{p.get("name", "unknown")}"']
        lines.append(f'    type: {p.get("type", "vless")}')
        lines.append(f'    server: {p.get("server", "")}')
        lines.append(f'    port: {p.get("port", 0)}')
        
        ptype = p.get("type", "")
        if ptype == "vless":
            lines.append(f'    uuid: {p.get("uuid", "")}')
            if p.get("network") == "ws":
                lines.append(f'    ws-opts:')
                lines.append(f'      path: {p.get("path", "/")}')
            if p.get("tls"):
                lines.append(f'    tls: true')
                if p.get("sni"):
                    lines.append(f'    sni: {p.get("sni", "")}')
        elif ptype == "trojan":
            lines.append(f'    password: {p.get("password", "")}')
            if p.get("sni"):
                lines.append(f'    sni: {p.get("sni", "")}')
        elif ptype == "ss":
            lines.append(f'    cipher: {p.get("cipher", "aes-256-gcm")}')
            lines.append(f'    password: {p.get("password", "")}')
        elif ptype == "vmess":
            lines.append(f'    uuid: {p.get("uuid", "")}')
            lines.append(f'    alterId: {p.get("alterId", 0)}')
            lines.append(f'    cipher: auto')
        
        return lines
    
    def save_as_singbox(self, nodes, filename):
        outbounds = []
        for node in nodes:
            ob = self.node_to_singbox(node)
            if ob:
                outbounds.append(ob)
        
        config = {
            "log": {"level": "info"},
            "inbounds": [{
                "type": "socks",
                "listen": "127.0.0.1",
                "port": 1080,
                "protocol": "socks",
                "settings": {"auth": "noauth"}
            }],
            "outbounds": outbounds
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def save_as_mihomo(self, nodes, filename):
        proxies = []
        for node in nodes:
            p = self.node_to_clash(node)
            if p:
                proxies.append(p)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('port: 7890\n')
            f.write('socks-port: 7891\n')
            f.write('allow-lan: true\n')
            f.write('mode: rule\n')
            f.write('external-controller: 127.0.0.1:9090\n')
            f.write('proxies:\n')
            for p in proxies:
                for line in self.format_clash_proxy(p):
                    f.write(line + '\n')
            f.write('proxy-groups:\n')
            f.write('  - name: "Auto"\n')
            f.write('    type: url-test\n')
            f.write('    use:\n')
            f.write('      - selected\n')
            f.write('    url: "http://www.gstatic.com/generate_204"\n')
            f.write('    interval: 300\n')
            f.write('  - name: "Manual"\n')
            f.write('    type: select\n')
            f.write('    proxies:\n')
            for p in proxies[:50]:
                f.write(f'      - {p.get("name", "unknown")}\n')
            f.write('proxy-providers:\n')
            f.write('  selected:\n')
            f.write('    type: http\n')
            f.write('    url: ""\n')
            f.write('    path: ./providers/proxies.yaml\n')
            f.write('    interval: 3600\n')
            f.write('rules:\n')
            f.write('  - MATCH,Manual\n')
    
    def node_to_clash(self, node):
        try:
            node_only = node.split('#')[0]
            
            if node_only.startswith('vless://'):
                node_str = node_only.replace('vless://', '')
                uuid = node_str.split('@')[0]
                rest = node_str.split('@')[1]
                ip = rest.split(':')[0]
                port = rest.split(':')[1].split('?')[0]
                params = rest.split('?')[1] if '?' in rest else ''
                
                p = {'name': f'VLESS-{ip[:8]}', 'type': 'vless', 'server': ip, 'port': int(port), 'uuid': uuid}
                if 'ws' in params: p['network'] = 'ws'
                if 'tls' in params: p['tls'] = True
                if 'reality' in params: p['reality'] = True
                if 'sni=' in params:
                    m = re.search(r'sni=([^&]+)', params)
                    if m: p['sni'] = m.group(1)
                if 'path=' in params:
                    m = re.search(r'path=([^&]+)', params)
                    if m: p['path'] = m.group(1)
                if 'fp=' in params:
                    m = re.search(r'fp=([^&]+)', params)
                    if m: p['fingerprint'] = m.group(1)
                return p
            
            elif node_only.startswith('trojan://'):
                node_str = node_only.replace('trojan://', '')
                password = node_str.split('@')[0]
                rest = node_str.split('@')[1]
                ip = rest.split(':')[0]
                port = rest.split(':')[1].split('?')[0]
                return {'name': f'Trojan-{ip[:8]}', 'type': 'trojan', 'server': ip, 'port': int(port), 'password': password}
            
            elif node_only.startswith('ss://'):
                node_str = node_only.replace('ss://', '')
                if '@' in node_str:
                    auth = node_str.split('@')[0]
                    rest = node_str.split('@')[1]
                    ip = rest.split(':')[0]
                    port = rest.split(':')[1].split('?')[0]
                    try:
                        decoded = base64.b64decode(auth).decode()
                        cipher = decoded.split(':')[0]
                        password = decoded.split(':')[1]
                        return {'name': f'SS-{ip[:8]}', 'type': 'ss', 'server': ip, 'port': int(port), 'cipher': cipher, 'password': password}
                    except:
                        pass
            
            elif node_only.startswith('vmess://'):
                node_str = node_only.replace('vmess://', '')
                try:
                    decoded = json.loads(base64.b64decode(node_str).decode())
                    return {
                        'name': decoded.get('ps', 'VMess'),
                        'type': 'vmess',
                        'server': decoded.get('add', ''),
                        'port': int(decoded.get('port', 0)),
                        'uuid': decoded.get('id', ''),
                        'alterId': int(decoded.get('aid', 0)),
                    }
                except:
                    pass
        except:
            pass
        return None
    
    def node_to_singbox(self, node):
        try:
            node_only = node.split('#')[0]
            
            if node_only.startswith('vless://'):
                node_str = node_only.replace('vless://', '')
                uuid = node_str.split('@')[0]
                rest = node_str.split('@')[1]
                ip = rest.split(':')[0]
                port = rest.split(':')[1].split('?')[0]
                params = rest.split('?')[1] if '?' in rest else ''
                
                ob = {
                    "tag": f"VLESS-{ip[:8]}",
                    "type": "vless",
                    "server": ip,
                    "port": int(port),
                    "uuid": uuid,
                    "flow": "",
                    "tls": {"enabled": False}
                }
                if 'ws' in params:
                    m = re.search(r'path=([^&]+)', params)
                    ob["transport"] = {"type": "ws", "path": m.group(1) if m else "/"}
                if 'tls' in params or 'reality' in params:
                    ob["tls"]["enabled"] = True
                    if 'sni=' in params:
                        m = re.search(r'sni=([^&]+)', params)
                        if m: ob["tls"]["server_name"] = m.group(1)
                return ob
            
            elif node_only.startswith('trojan://'):
                node_str = node_only.replace('trojan://', '')
                password = node_str.split('@')[0]
                rest = node_str.split('@')[1]
                ip = rest.split(':')[0]
                port = rest.split(':')[1].split('?')[0]
                return {
                    "tag": f"Trojan-{ip[:8]}",
                    "type": "trojan",
                    "server": ip,
                    "port": int(port),
                    "password": password
                }
            
            elif node_only.startswith('ss://'):
                node_str = node_only.replace('ss://', '')
                if '@' in node_str:
                    auth = node_str.split('@')[0]
                    rest = node_str.split('@')[1]
                    ip = rest.split(':')[0]
                    port = rest.split(':')[1].split('?')[0]
                    try:
                        decoded = base64.b64decode(auth).decode()
                        cipher = decoded.split(':')[0]
                        password = decoded.split(':')[1]
                        return {
                            "tag": f"SS-{ip[:8]}",
                            "type": "shadowsocks",
                            "server": ip,
                            "port": int(port),
                            "method": cipher,
                            "password": password
                        }
                    except:
                        pass
        except:
            pass
        return None

    def export_with_format(self):
        export_format = self.export_format_var.get()
        
        if export_format == "txt":
            self.export_all_formats()
            return
        
        if not self.working_nodes:
            messagebox.showwarning("警告", "请先运行爬虫获取节点!")
            return
        
        selected_country = self.country_var.get()
        selected_protocols = [p for p, info in self.protocol_btns.items() if info["selected"]]
        
        country_map = {"美国": "US", "加拿大": "CA", "英国": "GB", "德国": "DE",
                       "荷兰": "NL", "日本": "JP", "新加坡": "SG", "香港": "HK", "俄罗斯": "RU"}
        
        if selected_country == "全部":
            nodes = self.working_nodes
        else:
            c = country_map.get(selected_country)
            nodes = self.country_nodes.get(c, [])
        
        if selected_protocols:
            filtered = []
            for node in nodes:
                for proto in selected_protocols:
                    if re.search(PROTOCOLS[proto]["pattern"], node, re.IGNORECASE):
                        filtered.append(node)
                        break
            nodes = filtered
        
        if not nodes:
            messagebox.showwarning("警告", "没有符合条件的节点")
            return
        
        if export_format == "geekez":
            self.export_geekez_format(nodes, selected_country)
        elif export_format == "v2rayn":
            self.export_v2rayn_format(nodes, selected_country)
    
    def export_geekez_format(self, nodes, selected_country):
        valid_nodes = []
        for node in nodes:
            node_only = node.split('#')[0]
            if node_only.startswith(('vless://', 'vmess://', 'trojan://', 'ss://', 'hysteria2://', 'tuic://')):
                valid_nodes.append(node_only)
        
        if not valid_nodes:
            messagebox.showwarning("警告", "没有GeekEZ支持的节点\n(仅支持: VLESS/VMess/Trojan/SS/Hysteria2/TUIC)")
            return
        
        content = '\n'.join(valid_nodes)
        pyperclip.copy(content)
        
        os.makedirs('nodes', exist_ok=True)
        
        selected_protocols = [p for p, info in self.protocol_btns.items() if info["selected"]]
        proto_str = "_".join(selected_protocols) if selected_protocols else "全部"
        filename = f'nodes/{selected_country}_{proto_str}_GeekEZ.txt'
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.log(f"\n📋 GeekEZ 格式导出...", "info")
        self.log(f"  ✅ {len(valid_nodes)} 个节点已复制", "success")
        self.log(f"  📄 文件: {filename}", "success")
        self.log(f"  💡 使用: GeekEZ → 点击+ → 粘贴链接", "info")
        messagebox.showinfo("完成", f"剪贴板: {len(valid_nodes)} 个节点\n文件: {filename}\n\n使用方法:\nGeekEZ → 点击+ → 粘贴链接")
    
    def export_v2rayn_format(self, nodes, selected_country):
        outbounds = []
        
        for node in nodes:
            node_only = node.split('#')[0]
            ob = self.node_to_v2ray_outbound(node_only)
            if ob:
                outbounds.append(ob)
        
        if not outbounds:
            messagebox.showwarning("警告", "没有可转换的节点")
            return
        
        config = {
            "log": {"level": "warning"},
            "inbounds": [{
                "tag": "socks-in",
                "protocol": "socks",
                "port": 10808,
                "listen": "0.0.0.0",
                "settings": {"auth": "noauth"}
            }, {
                "tag": "http-in",
                "protocol": "http",
                "port": 10809,
                "listen": "0.0.0.0",
                "settings": {"auth": "noauth"}
            }],
            "outbounds": outbounds,
            "routing": {
                "domainStrategy": "IPIfNonMatch",
                "rules": [{
                    "type": "field",
                    "outboundTag": "direct",
                    "protocol": ["bittorrent"]
                }]
            }
        }
        
        os.makedirs('nodes', exist_ok=True)
        
        selected_protocols = [p for p, info in self.protocol_btns.items() if info["selected"]]
        proto_str = "_".join(selected_protocols) if selected_protocols else "全部"
        filename = f'nodes/{selected_country}_{proto_str}_v2rayN.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        self.log(f"\n📋 v2rayN 格式导出...", "info")
        self.log(f"  ✅ {len(outbounds)} 个节点已转换", "success")
        self.log(f"  📄 文件: {filename}", "success")
        self.log(f"  💡 使用: v2rayN → 导入客户端配置", "info")
        messagebox.showinfo("完成", f"节点: {len(outbounds)} 个\n文件: {filename}\n\n使用方法:\nv2rayN → 导入 → 客户端配置")


def main():
    try:
        root = tk.Tk()
        app = ProxyScraperGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")

if __name__ == "__main__":
    main()
