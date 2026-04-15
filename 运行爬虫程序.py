import sys
sys.stdout.reconfigure(encoding='utf-8')

import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
import re
import socket
import ssl
import concurrent.futures
import os

BG_COLOR = "#1e1e2e"
FG_COLOR = "#cdd6f4"
ACCENT_COLOR = "#89b4fa"
SUCCESS_COLOR = "#a6e3a1"
WARNING_COLOR = "#f9e2af"
ERROR_COLOR = "#f38ba8"
FRAME_BG = "#313244"
BTN_BG = "#45475a"
BTN_HOVER = "#585b70"

class ProxyScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("免费节点爬虫 - VPN Proxy Scraper")
        self.root.geometry("800x600")
        self.root.configure(bg=BG_COLOR)
        
        self.style_config()
        
        self.sources = [
            ('FastNodes US', 'https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/countries/US.txt'),
            ('FastNodes All', 'https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/everything.txt'),
            ('FastNodes VLESS', 'https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/protocols/vless.txt'),
            ('FastNodes Trojan', 'https://raw.githubusercontent.com/rtwo2/FastNodes/main/sub/protocols/trojan.txt'),
            ('Epodonios', 'https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt'),
            ('NiREvil', 'https://raw.githubusercontent.com/NiREvil/vless/main/sub/SSTime'),
            ('FreeNodes', 'https://raw.githubusercontent.com/Barabama/FreeNodes/main/nodes/yudou66.txt'),
            ('CloudflareIP', 'https://raw.githubusercontent.com/gslege/CloudflareIP/main/Vless.txt'),
        ]
        
        self.working_nodes = []
        self.country_nodes = {}
        self.scraping = False
        
        self.setup_ui()
    
    def style_config(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(".", background=BG_COLOR, foreground=FG_COLOR, fieldbackground=FRAME_BG)
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR)
        style.configure("TButton", background=BTN_BG, foreground=FG_COLOR, borderwidth=0)
        style.configure("TCombobox", fieldbackground=BTN_BG, background=BTN_BG, foreground=FG_COLOR)
        style.map("TCombobox", background=[("active", BTN_HOVER)])
        style.configure("Horizontal.TProgressbar", background=ACCENT_COLOR, troughcolor=FRAME_BG)
    
    def setup_ui(self):
        title = tk.Label(self.root, text="🌐 免费节点爬虫", font=("Segoe UI", 22, "bold"), 
                        bg=BG_COLOR, fg=ACCENT_COLOR)
        title.pack(pady=(15, 10))
        
        self.create_frame_scrape()
        self.create_frame_export()
        self.create_frame_log()
    
    def create_frame_scrape(self):
        frame = tk.Frame(self.root, bg=FRAME_BG, padx=15, pady=10)
        frame.pack(fill="x", padx=15, pady=(10, 5))
        
        tk.Label(frame, text="并行线程:", bg=FRAME_BG, fg=FG_COLOR, font=("Segoe UI", 10)).pack(side="left")
        
        self.thread_btns = {}
        thread_frame = tk.Frame(frame, bg=FRAME_BG)
        thread_frame.pack(side="left", padx=10)
        
        for val in ["50", "100", "150", "200"]:
            btn = tk.Button(thread_frame, text=val, width=4, font=("Segoe UI", 9),
                           bg=BTN_BG, fg=FG_COLOR, bd=0, relief="flat",
                           command=lambda v=val: self.select_thread(v))
            btn.pack(side="left", padx=2)
            self.thread_btns[val] = btn
        
        self.thread_var = tk.StringVar(value="100")
        self.update_thread_btns("100")
        
        self.btn_scrape = tk.Button(frame, text="▶ 开始爬取", command=self.start_scrape_thread,
                                    bg=ACCENT_COLOR, fg="#1e1e2e", font=("Segoe UI", 10, "bold"),
                                    width=12, bd=0, padx=10, pady=5)
        self.btn_scrape.pack(side="left", padx=(20, 10))
        
        self.status_label = tk.Label(frame, text="点击开始爬取", bg=FRAME_BG, fg="#6c7086", font=("Segoe UI", 9))
        self.status_label.pack(side="left", padx=10)
        
        self.progress = ttk.Progressbar(frame, mode='indeterminate', length=200)
        self.progress.pack(side="left", fill="x", expand=True, padx=(10, 5))
    
    def select_thread(self, val):
        self.thread_var.set(val)
        self.update_thread_btns(val)
    
    def update_thread_btns(self, selected):
        for val, btn in self.thread_btns.items():
            if val == selected:
                btn.config(bg=ACCENT_COLOR, fg="#1e1e2e")
            else:
                btn.config(bg=BTN_BG, fg=FG_COLOR)
    
    def create_frame_export(self):
        frame = tk.Frame(self.root, bg=FRAME_BG, padx=15, pady=10)
        frame.pack(fill="x", padx=15, pady=5)
        
        tk.Label(frame, text="选择国家:", bg=FRAME_BG, fg=FG_COLOR, font=("Segoe UI", 10)).pack(side="left")
        
        self.country_btns = {}
        country_frame = tk.Frame(frame, bg=FRAME_BG)
        country_frame.pack(side="left", padx=10)
        
        countries = ["全部", "美国", "加拿大", "英国", "德国", "荷兰", "日本", "新加坡", "香港"]
        for c in countries:
            btn = tk.Button(country_frame, text=c, width=4, font=("Segoe UI", 9),
                           bg=BTN_BG, fg=FG_COLOR, bd=0, relief="flat",
                           command=lambda v=c: self.select_country(v))
            btn.pack(side="left", padx=2)
            self.country_btns[c] = btn
        
        self.country_var = tk.StringVar(value="全部")
        self.update_country_btns("全部")
        
        self.btn_export = tk.Button(frame, text="💾 导出节点", command=self.export_nodes,
                                    bg=SUCCESS_COLOR, fg="#1e1e2e", font=("Segoe UI", 10, "bold"),
                                    width=12, bd=0, padx=10, pady=5)
        self.btn_export.pack(side="left", padx=(15, 5))
        
        self.btn_open = tk.Button(frame, text="📁 打开文件夹", command=self.open_export_folder,
                                  bg=WARNING_COLOR, fg="#1e1e2e", font=("Segoe UI", 10, "bold"),
                                  width=12, bd=0, padx=10, pady=5)
        self.btn_open.pack(side="left", padx=10)
        
        self.btn_delete = tk.Button(frame, text="🗑️ 删除文件", command=self.delete_all_nodes,
                                    bg=ERROR_COLOR, fg="#1e1e2e", font=("Segoe UI", 10, "bold"),
                                    width=12, bd=0, padx=10, pady=5)
        self.btn_delete.pack(side="left", padx=10)
    
    def select_country(self, val):
        self.country_var.set(val)
        self.update_country_btns(val)
    
    def update_country_btns(self, selected):
        for c, btn in self.country_btns.items():
            if c == selected:
                btn.config(bg=ACCENT_COLOR, fg="#1e1e2e")
            else:
                btn.config(bg=BTN_BG, fg=FG_COLOR)
    
    def create_frame_log(self):
        frame = tk.LabelFrame(self.root, text="📋 日志", font=("Segoe UI", 11, "bold"),
                             bg=FRAME_BG, fg=FG_COLOR, bd=1, relief="flat", padx=10, pady=10)
        frame.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        
        self.log_text = tk.Text(frame, width=70, bg="#11111b", fg=FG_COLOR,
                                font=("Consolas", 10), bd=0, padx=10, pady=8)
        self.log_text.pack(side="left", fill="both", expand=True)
        self.log_text.tag_config("info", foreground=ACCENT_COLOR)
        self.log_text.tag_config("success", foreground=SUCCESS_COLOR)
        self.log_text.tag_config("warning", foreground=WARNING_COLOR)
        
        scroll = tk.Scrollbar(frame, bg=FRAME_BG, width=10)
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
        self.scraping = True
        self.btn_scrape.config(state="disabled", bg=BTN_BG)
        self.progress.start(10)
        
        thread = threading.Thread(target=self.scrape_worker, daemon=True)
        thread.start()
    
    def fetch(self, url):
        try:
            r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code == 200:
                nodes = []
                for line in r.text.strip().split('\n'):
                    line = line.strip()
                    if line.startswith(('vmess://', 'vless://', 'trojan://', 'ss://')):
                        nodes.append(line)
                return nodes
        except:
            pass
        return []
    
    def get_ip_port(self, node):
        match = re.search(r'@([0-9.]+):([0-9]+)', node)
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
            return None, ''
    
    def scrape_worker(self):
        threads = self.thread_var.get()
        
        self.log("=" * 40, "info")
        self.log("🚀 开始爬取节点...", "info")
        
        all_nodes = []
        for name, url in self.sources:
            self.log(f"📥 获取 {name}...", "info")
            nodes = self.fetch(url)
            self.log(f"   → 获取到 {len(nodes)} 个节点", "success")
            all_nodes.extend(nodes)
        
        all_nodes = list(set(all_nodes))
        self.log(f"📊 总计: {len(all_nodes)} 个节点\n", "info")
        
        self.log(f"🧪 测试连接 (并行 {threads} 线程)...", "warning")
        self.working_nodes = []
        self.country_nodes = {}
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=int(threads)) as executor:
                futures = {executor.submit(self.test_node, n): n for n in all_nodes[:3000]}
                completed = 0
                for future in concurrent.futures.as_completed(futures):
                    completed += 1
                    node, country = future.result()
                    if node:
                        self.working_nodes.append(node)
                        if country not in self.country_nodes:
                            self.country_nodes[country] = []
                        self.country_nodes[country].append(node)
                    
                    if completed % 100 == 0:
                        self.log(f"   已测试 {completed} 个, 可用: {len(self.working_nodes)}", "info")
        except Exception as e:
            self.log(f"❌ 错误: {e}", "error")
        
        self.log(f"\n✅ 完成! 共找到 {len(self.working_nodes)} 个可用节点", "success")
        
        country_map = {'US': '美国', 'CA': '加拿大', 'GB': '英国', 'DE': '德国', 
                       'NL': '荷兰', 'JP': '日本', 'SG': '新加坡', 'HK': '香港', 'RU': '俄罗斯'}
        
        self.log("\n📍 国家分布:", "info")
        for c in sorted(self.country_nodes.keys()):
            name = country_map.get(c, c)
            self.log(f"   {name}: {len(self.country_nodes[c])}", "info")
        
        self.scraping = False
        self.progress.stop()
        self.btn_scrape.config(state="normal", bg=ACCENT_COLOR)
        self.status_label.config(text=f"可用: {len(self.working_nodes)} 个节点")
    
    def export_nodes(self):
        if not self.working_nodes:
            messagebox.showwarning("警告", "请先运行爬虫!")
            return
        
        selected = self.country_var.get()
        country_map = {"美国": "US", "加拿大": "CA", "英国": "GB", "德国": "DE",
                      "荷兰": "NL", "日本": "JP", "新加坡": "SG", "香港": "HK",
                      "美国": "US", "加拿大": "CA", "英国": "GB", "德国": "DE",
                      "荷兰": "NL", "日本": "JP", "新加坡": "SG", "香港": "HK"}
        
        reverse_map = {"US": "美国", "CA": "加拿大", "GB": "英国", "DE": "德国",
                       "NL": "荷兰", "JP": "日本", "SG": "新加坡", "HK": "香港", "RU": "俄罗斯"}
        
        os.makedirs('nodes', exist_ok=True)
        
        if selected == "全部":
            for c, nodes in self.country_nodes.items():
                cn_name = reverse_map.get(c, c)
                yaml_file = f'nodes/{cn_name}.yaml'
                txt_file = f'nodes/{cn_name}.txt'
                self.save_nodes_yaml(nodes, yaml_file)
                self.save_nodes(nodes, txt_file)
            self.save_nodes_yaml(self.working_nodes, 'nodes/全部.yaml')
            self.save_nodes(self.working_nodes, 'nodes/全部.txt')
            self.log("✅ 已导出所有国家节点 (YAML + TXT)", "success")
            messagebox.showinfo("完成", "已导出 YAML 和 TXT 格式\nTXT文件可直接复制")
        else:
            c = country_map.get(selected)
            if c and c in self.country_nodes:
                yaml_file = f'nodes/{selected}.yaml'
                txt_file = f'nodes/{selected}.txt'
                self.save_nodes_yaml(self.country_nodes[c], yaml_file)
                self.save_nodes(self.country_nodes[c], txt_file)
                self.log(f"✅ 已导出 {selected} 节点 (YAML + TXT)", "success")
                messagebox.showinfo("完成", f"已导出 {selected} 节点\nTXT文件可直接复制")
            else:
                messagebox.showwarning("警告", f"没有 {selected} 的节点")
    
    def save_nodes(self, nodes, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            for n in nodes:
                node_only = n.split('#')[0]
                f.write(node_only + '\n')
    
    def save_nodes_yaml(self, nodes, filename):
        proxies = []
        for node in nodes:
            p = self.link_to_proxy(node)
            if p:
                proxies.append(p)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('proxies:\n')
            for p in proxies:
                f.write(f"  - name: {p.get('name', 'unknown')}\n")
                f.write(f"    type: {p.get('type', 'vless')}\n")
                f.write(f"    server: {p.get('server', '')}\n")
                f.write(f"    port: {p.get('port', 0)}\n")
                for k, v in p.items():
                    if k not in ['name', 'type', 'server', 'port']:
                        f.write(f"    {k}: {v}\n")
    
    def link_to_proxy(self, node):
        try:
            node_only = node.split('#')[0]
            
            if node_only.startswith('vless://'):
                node_str = node_only.replace('vless://', '')
                uuid = node_str.split('@')[0]
                rest = node_str.split('@')[1]
                ip = rest.split(':')[0]
                port = rest.split(':')[1].split('?')[0]
                params = rest.split('?')[1] if '?' in rest else ''
                
                p = {
                    'name': f'VLESS-{ip}',
                    'type': 'vless',
                    'server': ip,
                    'port': int(port),
                    'uuid': uuid,
                    'alterId': 0,
                    'security': 'auto',
                    'network': 'tcp'
                }
                
                if 'ws' in params:
                    p['network'] = 'ws'
                if 'tls' in params:
                    p['security'] = 'tls'
                if 'reality' in params:
                    p['security'] = 'reality'
                if 'sni=' in params:
                    sni = re.search(r'sni=([^&]+)', params)
                    if sni:
                        p['sni'] = sni.group(1)
                if 'path=' in params:
                    path = re.search(r'path=([^&]+)', params)
                    if path:
                        p['path'] = path.group(1)
                if 'fp=' in params:
                    fp = re.search(r'fp=([^&]+)', params)
                    if fp:
                        p['fingerprint'] = fp.group(1)
                if 'pbk=' in params:
                    pbk = re.search(r'pbk=([^&]+)', params)
                    if pbk:
                        p['publicKey'] = pbk.group(1)
                if 'sid=' in params:
                    sid = re.search(r'sid=([^&]+)', params)
                    if sid:
                        p['shortId'] = sid.group(1)
                
                return p
            
            elif node_only.startswith('trojan://'):
                node_str = node_only.replace('trojan://', '')
                password = node_str.split('@')[0]
                rest = node_str.split('@')[1]
                ip = rest.split(':')[0]
                port = rest.split(':')[1].split('?')[0]
                params = rest.split('?')[1] if '?' in rest else ''
                
                p = {
                    'name': f'Trojan-{ip}',
                    'type': 'trojan',
                    'server': ip,
                    'port': int(port),
                    'password': password,
                    'sni': ''
                }
                
                if 'sni=' in params:
                    sni = re.search(r'sni=([^&]+)', params)
                    if sni:
                        p['sni'] = sni.group(1)
                
                return p
            
            elif node_only.startswith('ss://'):
                node_str = node_only.replace('ss://', '')
                auth = node_str.split('@')[0]
                rest = node_str.split('@')[1]
                ip = rest.split(':')[0]
                port = rest.split(':')[1].split('?')[0]
                
                import base64
                decoded = base64.b64decode(auth).decode()
                cipher = decoded.split(':')[0]
                password = decoded.split(':')[1]
                
                return {
                    'name': f'SS-{ip}',
                    'type': 'ss',
                    'server': ip,
                    'port': int(port),
                    'cipher': cipher,
                    'password': password
                }
        except:
            pass
        return None
    
    def delete_all_nodes(self):
        folder = os.path.abspath('nodes')
        if not os.path.exists(folder):
            messagebox.showinfo("提示", "没有需要删除的文件")
            return
        
        files = os.listdir(folder)
        if not files:
            messagebox.showinfo("提示", "没有需要删除的文件")
            return
        
        result = messagebox.askyesno("确认", f"确定要删除 nodes 文件夹中的 {len(files)} 个文件吗?")
        if result:
            import shutil
            shutil.rmtree(folder)
            os.makedirs(folder, exist_ok=True)
            self.log("✅ 已删除所有导出文件", "success")
            messagebox.showinfo("完成", "已删除所有文件")
    
    def open_export_folder(self):
        folder = os.path.abspath('nodes')
        os.makedirs(folder, exist_ok=True)
        os.startfile(folder)

def main():
    root = tk.Tk()
    app = ProxyScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
