# AGENTS.md - NodeCollector

## 项目概述
多协议节点 URI 采集与格式化工具（VMess/VLESS/Shadowsocks/Trojan/Hysteria2）。支持从公开源采集、本地库导入、格式转换导出。

## 运行入口
- **Tkinter GUI 版**: `python 运行爬虫程序.py`（需要 PyQt6, tkinter）
- **Flask Web 版**: `python 网页版NodeCollector.py`（自动打开浏览器，默认 http://127.0.0.1:5000）

## 依赖安装
```bash
pip install -r requirements.txt
npm install  # 仅 playwright（可选）
```

## 关键配置
- **config.json**: 爬虫目标站点配置（start_url, selector, pattern, password, script）
- **离线IP库.txt**: 本地节点库（nodes/ 目录，被 .gitignore 忽略）

## 架构要点
- `运行爬虫程序.py`: Tkinter GUI，支持协议筛选、并发爬取、IP 历史去重、导出
- `网页版NodeCollector.py`: Flask + 多线程，提供 Web UI，支持本地库导入/加载
- `导出到Web3Toolbox.py`: 节点格式转换工具
- `NodeScrapy/`: Scrapy 框架目录（scrapy.cfg 配置了默认设置）
- `templates/`, `static/`: Flask Web 版前端资源

## 数据流向
1. 爬取/导入 → 节点列表（内存）
2. IP 去重 → `nodes/ip_history.json`（运行时生成）
3. 导出 → `nodes/*.txt`（按国家_协议格式命名）

## 重要约定
- **节点 URI 格式**: `协议://base64编码或明文@IP:端口`，URI 中 `#` 后为备注，导出时去除
- **IP 历史**: 用 `hashlib.md5(node_uri)` 去重，保存在 `nodes/ip_history.json`
- **国家识别**: 测试节点时调用 `http://ip-api.com/json/{ip}?fields=countryCode`
- **GitHub 代理**: Flask 版使用 `gh-proxy.com` 代理 GitHub raw 内容
- **并发控制**: GUI 版支持 50/100/150/200 线程，Web 版默认 50

## 注意事项
- `nodes/` 目录被 gitignore，不包含在版本控制中
- 无标准测试套件，主要逻辑通过 GUI/Web 交互验证
- 配置文件中的 `up_date` 需要手动更新（如 `2026-04-18`）
- 协议正则模式在代码中硬编码（PROTOCOLS 字典）
- IP 历史记录可能在多次运行间累积，可用"清除IP历史"按钮重置

## 导出格式
- **GeekEZ**: 剪贴板导入格式
- **v2rayN**: 兼容 v2rayN 的 JSON 配置
- **TXT**: 纯节点 URI 列表

## 相关文档
- README.md: 免责声明、数据源订阅列表
- OPTIMIZATION_SUMMARY.md, VERIFICATION_REPORT.md: 优化与验证报告（如有）
