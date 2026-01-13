#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetworkToolPro - 专业网络工具集
基于PyQt5的现代化网络诊断工具
功能：Ping, Traceroute, 端口扫描, 速度测试, HTTP测试, DNS查询, 局域网扫描, Whois查询, 子网计算
作者：LYP
GitHub：https://github.com/lyp0746
邮箱：1610369302@qq.com
版本：2.0.0
"""  

import sys  
import socket  
import platform  
import subprocess  
import time  
import re  
import json  
import ipaddress  
from datetime import datetime  
from typing import List, Tuple, Optional  
from urllib.parse import urlparse  

from PyQt5.QtWidgets import (  
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,  
    QTabWidget, QLabel, QLineEdit, QPushButton, QTextEdit, QSpinBox,  
    QComboBox, QProgressBar, QGroupBox, QGridLayout, QMessageBox,  
    QSplitter, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,  
    QStatusBar, QAction, QMenu, QFileDialog, QDoubleSpinBox, QFrame  
)  
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer  
from PyQt5.QtGui import QFont, QColor, QTextCursor, QIcon  

import requests  


class WorkerThread(QThread):  
    """通用工作线程"""  
    output_signal = pyqtSignal(str)  
    progress_signal = pyqtSignal(int)  
    finished_signal = pyqtSignal(object)  
    error_signal = pyqtSignal(str)  
    
    def __init__(self, func, *args, **kwargs):  
        super().__init__()  
        self.func = func  
        self.args = args  
        self.kwargs = kwargs  
        self.is_running = True  
        
    def run(self):  
        try:  
            result = self.func(*self.args, **self.kwargs)  
            self.finished_signal.emit(result)  
        except Exception as e:  
            self.error_signal.emit(str(e))  
            
    def stop(self):  
        self.is_running = False  


class PingWorker(QThread):  
    """Ping工作线程"""  
    output_signal = pyqtSignal(str)  
    stats_signal = pyqtSignal(dict)  
    finished_signal = pyqtSignal()  
    
    def __init__(self, host, count, timeout, interval):  
        super().__init__()  
        self.host = host  
        self.count = count  
        self.timeout = timeout  
        self.interval = interval  
        self.is_running = True  
        
    def run(self):  
        stats = {  
            'sent': 0,  
            'received': 0,  
            'lost': 0,  
            'min': float('inf'),  
            'max': 0,  
            'avg': 0,  
            'times': []  
        }  
        
        self.output_signal.emit(f"正在 Ping {self.host} [持续 {self.count} 次]...\n")  
        self.output_signal.emit(f"超时时间: {self.timeout}秒, 间隔: {self.interval}秒\n")  
        self.output_signal.emit("-" * 70 + "\n")  
        
        system = platform.system().lower()  
        
        for i in range(self.count):  
            if not self.is_running:  
                break  
                
            try:  
                stats['sent'] += 1  
                
                if system == "windows":  
                    cmd = ["ping", "-n", "1", "-w", str(int(self.timeout * 1000)), self.host]  
                else:  
                    cmd = ["ping", "-c", "1", "-W", str(int(self.timeout)), self.host]  
                
                start_time = time.time()  
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout + 1)  
                elapsed = (time.time() - start_time) * 1000  
                
                if result.returncode == 0:  
                    stats['received'] += 1  
                    stats['times'].append(elapsed)  
                    stats['min'] = min(stats['min'], elapsed)  
                    stats['max'] = max(stats['max'], elapsed)  
                    
                    # 解析TTL  
                    ttl_match = re.search(r'ttl=(\d+)', result.stdout.lower())  
                    ttl = ttl_match.group(1) if ttl_match else "N/A"  
                    
                    output = f"来自 {self.host} 的回复: 字节=32 时间={elapsed:.0f}ms TTL={ttl}\n"  
                    self.output_signal.emit(output)  
                else:  
                    stats['lost'] += 1  
                    self.output_signal.emit(f"请求超时。\n")  
                    
            except subprocess.TimeoutExpired:  
                stats['lost'] += 1  
                self.output_signal.emit(f"请求超时。\n")  
            except Exception as e:  
                self.output_signal.emit(f"错误: {str(e)}\n")  
                
            if i < self.count - 1 and self.is_running:  
                time.sleep(self.interval)  
        
        # 计算统计信息  
        if stats['times']:  
            stats['avg'] = sum(stats['times']) / len(stats['times'])  
            stats['loss_rate'] = (stats['lost'] / stats['sent']) * 100  
        else:  
            stats['min'] = 0  
            stats['loss_rate'] = 100  
            
        self.stats_signal.emit(stats)  
        self.finished_signal.emit()  
        
    def stop(self):  
        self.is_running = False  


class TracerouteWorker(QThread):  
    """路由跟踪工作线程"""  
    output_signal = pyqtSignal(str)  
    finished_signal = pyqtSignal()  
    
    def __init__(self, host, max_hops):  
        super().__init__()  
        self.host = host  
        self.max_hops = max_hops  
        self.is_running = True  
        
    def run(self):  
        self.output_signal.emit(f"正在追踪到 {self.host} 的路由，最多 {self.max_hops} 跳:\n")  
        self.output_signal.emit("-" * 70 + "\n")  
        
        system = platform.system().lower()  
        
        try:  
            if system == "windows":  
                cmd = ["tracert", "-h", str(self.max_hops), "-w", "3000", self.host]  
            else:  
                cmd = ["traceroute", "-m", str(self.max_hops), "-w", "3", self.host]  
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,   
                                      text=True, bufsize=1)  
            
            for line in process.stdout:  
                if not self.is_running:  
                    process.terminate()  
                    break  
                self.output_signal.emit(line)  
            
            process.wait()  
            
        except Exception as e:  
            self.output_signal.emit(f"\n错误: {str(e)}\n")  
            
        self.finished_signal.emit()  
        
    def stop(self):  
        self.is_running = False  


class PortScanWorker(QThread):  
    """端口扫描工作线程"""  
    output_signal = pyqtSignal(str)  
    progress_signal = pyqtSignal(int)  
    result_signal = pyqtSignal(list)  
    finished_signal = pyqtSignal()  
    
    def __init__(self, host, start_port, end_port, timeout, threads):  
        super().__init__()  
        self.host = host  
        self.start_port = start_port  
        self.end_port = end_port  
        self.timeout = timeout  
        self.threads = threads  
        self.is_running = True  
        self.open_ports = []  
        
    def run(self):  
        self.output_signal.emit(f"正在扫描 {self.host} ({self.start_port}-{self.end_port})...\n")  
        self.output_signal.emit(f"超时: {self.timeout}秒, 线程数: {self.threads}\n")  
        self.output_signal.emit("-" * 70 + "\n")  
        
        total_ports = self.end_port - self.start_port + 1  
        scanned = 0  
        
        from concurrent.futures import ThreadPoolExecutor, as_completed  
        
        def scan_port(port):  
            if not self.is_running:  
                return None  
                
            try:  
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
                sock.settimeout(self.timeout)  
                result = sock.connect_ex((self.host, port))  
                sock.close()  
                
                if result == 0:  
                    service = self.get_service_name(port)  
                    return (port, service, 'open')  
            except:  
                pass  
            return None  
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:  
            futures = {executor.submit(scan_port, port): port   
                      for port in range(self.start_port, self.end_port + 1)}  
            
            for future in as_completed(futures):  
                if not self.is_running:  
                    break  
                    
                result = future.result()  
                if result:  
                    port, service, status = result  
                    self.open_ports.append(result)  
                    msg = f"[开放] 端口 {port:5d} - {service}\n"  
                    self.output_signal.emit(msg)  
                
                scanned += 1  
                progress = int((scanned / total_ports) * 100)  
                self.progress_signal.emit(progress)  
        
        self.result_signal.emit(self.open_ports)  
        self.finished_signal.emit()  
        
    def stop(self):  
        self.is_running = False  
        
    @staticmethod  
    def get_service_name(port):  
        """获取常见端口服务名"""  
        services = {  
            20: "FTP-DATA", 21: "FTP", 22: "SSH", 23: "Telnet",  
            25: "SMTP", 53: "DNS", 80: "HTTP", 110: "POP3",  
            143: "IMAP", 443: "HTTPS", 445: "SMB", 465: "SMTPS",  
            587: "SMTP", 993: "IMAPS", 995: "POP3S", 1433: "MSSQL",  
            1521: "Oracle", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",  
            5900: "VNC", 6379: "Redis", 8080: "HTTP-Proxy", 8443: "HTTPS-Alt",  
            27017: "MongoDB", 27018: "MongoDB", 50000: "DB2"  
        }  
        return services.get(port, "Unknown")  


class SpeedTestWorker(QThread):  
    """速度测试工作线程"""  
    output_signal = pyqtSignal(str)  
    progress_signal = pyqtSignal(int)  
    result_signal = pyqtSignal(dict)  
    finished_signal = pyqtSignal()  
    
    def __init__(self, url, count, timeout):  
        super().__init__()  
        self.url = url  
        self.count = count  
        self.timeout = timeout  
        self.is_running = True  
        
    def run(self):  
        self.output_signal.emit(f"开始速度测试...\n")  
        self.output_signal.emit(f"测试URL: {self.url}\n")  
        self.output_signal.emit(f"测试次数: {self.count}\n")  
        self.output_signal.emit("-" * 70 + "\n")  
        
        results = {  
            'speeds': [],  
            'sizes': [],  
            'times': []  
        }  
        
        for i in range(self.count):  
            if not self.is_running:  
                break  
                
            try:  
                self.output_signal.emit(f"\n第 {i+1}/{self.count} 次测试:\n")  
                
                start_time = time.time()  
                response = requests.get(self.url, stream=True, timeout=self.timeout)  
                
                total_size = 0  
                chunk_count = 0  
                
                for chunk in response.iter_content(chunk_size=8192):  
                    if not self.is_running:  
                        break  
                    total_size += len(chunk)  
                    chunk_count += 1  
                    
                    # 每100个块更新一次  
                    if chunk_count % 100 == 0:  
                        elapsed = time.time() - start_time  
                        if elapsed > 0:  
                            current_speed = (total_size * 8) / (elapsed * 1024 * 1024)  
                            self.output_signal.emit(f"  下载中... {total_size/1024:.1f} KB, "  
                                                   f"速度: {current_speed:.2f} Mbps\r")  
                
                end_time = time.time()  
                duration = end_time - start_time  
                
                if duration > 0 and self.is_running:  
                    speed_mbps = (total_size * 8) / (duration * 1024 * 1024)  
                    results['speeds'].append(speed_mbps)  
                    results['sizes'].append(total_size)  
                    results['times'].append(duration)  
                    
                    self.output_signal.emit(f"  下载大小: {total_size / 1024:.2f} KB\n")  
                    self.output_signal.emit(f"  耗时: {duration:.2f} 秒\n")  
                    self.output_signal.emit(f"  速度: {speed_mbps:.2f} Mbps\n")  
                    
            except Exception as e:  
                self.output_signal.emit(f"  错误: {str(e)}\n")  
            
            self.progress_signal.emit(int((i + 1) / self.count * 100))  
        
        if results['speeds'] and self.is_running:  
            results['avg'] = sum(results['speeds']) / len(results['speeds'])  
            results['max'] = max(results['speeds'])  
            results['min'] = min(results['speeds'])  
            
        self.result_signal.emit(results)  
        self.finished_signal.emit()  
        
    def stop(self):  
        self.is_running = False  


class HTTPTestWorker(QThread):  
    """HTTP测试工作线程"""  
    output_signal = pyqtSignal(str)  
    result_signal = pyqtSignal(dict)  
    finished_signal = pyqtSignal()  
    
    def __init__(self, url, method, headers, body, timeout):  
        super().__init__()  
        self.url = url  
        self.method = method  
        self.headers = headers  
        self.body = body  
        self.timeout = timeout  
        
    def run(self):  
        self.output_signal.emit(f"发送 {self.method} 请求到: {self.url}\n")  
        self.output_signal.emit(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")  
        self.output_signal.emit("-" * 70 + "\n")  
        
        result = {}  
        
        try:  
            start_time = time.time()  
            
            # 解析headers  
            headers_dict = {}  
            if self.headers:  
                for line in self.headers.split('\n'):  
                    if ':' in line:  
                        key, value = line.split(':', 1)  
                        headers_dict[key.strip()] = value.strip()  
            
            # 发送请求  
            if self.method == 'GET':  
                response = requests.get(self.url, headers=headers_dict, timeout=self.timeout)  
            elif self.method == 'POST':  
                response = requests.post(self.url, headers=headers_dict, data=self.body, timeout=self.timeout)  
            elif self.method == 'PUT':  
                response = requests.put(self.url, headers=headers_dict, data=self.body, timeout=self.timeout)  
            elif self.method == 'DELETE':  
                response = requests.delete(self.url, headers=headers_dict, timeout=self.timeout)  
            elif self.method == 'HEAD':  
                response = requests.head(self.url, headers=headers_dict, timeout=self.timeout)  
            elif self.method == 'OPTIONS':  
                response = requests.options(self.url, headers=headers_dict, timeout=self.timeout)  
            elif self.method == 'PATCH':  
                response = requests.patch(self.url, headers=headers_dict, data=self.body, timeout=self.timeout)  
            
            end_time = time.time()  
            duration = (end_time - start_time) * 1000  
            
            result['status_code'] = response.status_code  
            result['duration'] = duration  
            result['size'] = len(response.content)  
            result['headers'] = dict(response.headers)  
            result['text'] = response.text[:5000]  # 限制长度  
            
            self.output_signal.emit(f"\n✓ 请求成功\n")  
            self.output_signal.emit(f"状态码: {response.status_code} {response.reason}\n")  
            self.output_signal.emit(f"响应时间: {duration:.2f} ms\n")  
            self.output_signal.emit(f"内容大小: {len(response.content)} bytes\n")  
            self.output_signal.emit(f"\n响应头:\n")  
            
            for key, value in response.headers.items():  
                self.output_signal.emit(f"  {key}: {value}\n")  
            
            if self.method != 'HEAD' and response.text:  
                self.output_signal.emit(f"\n响应内容 (前5000字符):\n")  
                self.output_signal.emit(response.text[:5000] + "\n")  
                
        except Exception as e:  
            self.output_signal.emit(f"\n✗ 请求失败: {str(e)}\n")  
            result['error'] = str(e)  
        
        self.result_signal.emit(result)  
        self.finished_signal.emit()  


class DNSLookupWorker(QThread):  
    """DNS查询工作线程"""  
    output_signal = pyqtSignal(str)  
    result_signal = pyqtSignal(dict)  
    finished_signal = pyqtSignal()  
    
    def __init__(self, domain):  
        super().__init__()  
        self.domain = domain  
        
    def run(self):  
        self.output_signal.emit(f"DNS查询: {self.domain}\n")  
        self.output_signal.emit(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")  
        self.output_signal.emit("-" * 70 + "\n")  
        
        result = {  
            'ipv4': [],  
            'ipv6': [],  
            'hostname': None  
        }  
        
        try:  
            # IPv4地址  
            self.output_signal.emit("\n📍 IPv4 地址 (A记录):\n")  
            try:  
                ipv4_list = socket.getaddrinfo(self.domain, None, socket.AF_INET)  
                seen = set()  
                for item in ipv4_list:  
                    ip = item[4][0]  
                    if ip not in seen:  
                        seen.add(ip)  
                        result['ipv4'].append(ip)  
                        self.output_signal.emit(f"  • {ip}\n")  
            except Exception as e:  
                self.output_signal.emit(f"  未找到IPv4地址: {e}\n")  
            
            # IPv6地址  
            self.output_signal.emit("\n📍 IPv6 地址 (AAAA记录):\n")  
            try:  
                ipv6_list = socket.getaddrinfo(self.domain, None, socket.AF_INET6)  
                seen = set()  
                for item in ipv6_list:  
                    ip = item[4][0]  
                    if ip not in seen:  
                        seen.add(ip)  
                        result['ipv6'].append(ip)  
                        self.output_signal.emit(f"  • {ip}\n")  
            except Exception as e:  
                self.output_signal.emit(f"  未找到IPv6地址: {e}\n")  
            
            # 反向DNS查询  
            if result['ipv4']:  
                self.output_signal.emit("\n📍 主机名 (PTR记录):\n")  
                try:  
                    hostname = socket.gethostbyaddr(result['ipv4'][0])  
                    result['hostname'] = hostname[0]  
                    self.output_signal.emit(f"  • {hostname[0]}\n")  
                    if hostname[1]:  
                        for alias in hostname[1]:  
                            self.output_signal.emit(f"  • {alias} (别名)\n")  
                except:  
                    self.output_signal.emit(f"  无法解析\n")  
                    
        except Exception as e:  
            self.output_signal.emit(f"\n错误: {str(e)}\n")  
        
        self.result_signal.emit(result)  
        self.finished_signal.emit()  


class LANScanWorker(QThread):  
    """局域网扫描工作线程"""  
    output_signal = pyqtSignal(str)  
    progress_signal = pyqtSignal(int)  
    device_signal = pyqtSignal(tuple)  
    finished_signal = pyqtSignal()  
    
    def __init__(self, network, timeout, threads):  
        super().__init__()  
        self.network = network  
        self.timeout = timeout  
        self.threads = threads  
        self.is_running = True  
        
    def run(self):  
        self.output_signal.emit(f"正在扫描局域网: {self.network}\n")  
        self.output_signal.emit(f"超时: {self.timeout}秒, 线程数: {self.threads}\n")  
        self.output_signal.emit("-" * 70 + "\n")  
        
        try:  
            network = ipaddress.ip_network(self.network, strict=False)  
            hosts = list(network.hosts())  
            total = len(hosts)  
            scanned = 0  
            
            from concurrent.futures import ThreadPoolExecutor, as_completed  
            
            def check_host(ip):  
                if not self.is_running:  
                    return None  
                    
                ip_str = str(ip)  
                
                # 尝试多个常见端口  
                ports_to_check = [445, 139, 22, 80, 443, 3389]  
                
                for port in ports_to_check:  
                    try:  
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
                        sock.settimeout(self.timeout)  
                        result = sock.connect_ex((ip_str, port))  
                        sock.close()  
                        
                        if result == 0:  
                            try:  
                                hostname = socket.gethostbyaddr(ip_str)[0]  
                            except:  
                                hostname = "Unknown"  
                            
                            # 尝试获取MAC地址 (仅Windows)  
                            mac = self.get_mac_address(ip_str)  
                            
                            return (ip_str, hostname, port, mac)  
                    except:  
                        continue  
                
                return None  
            
            with ThreadPoolExecutor(max_workers=self.threads) as executor:  
                futures = {executor.submit(check_host, ip): ip for ip in hosts}  
                
                for future in as_completed(futures):  
                    if not self.is_running:  
                        break  
                        
                    result = future.result()  
                    if result:  
                        ip, hostname, port, mac = result  
                        self.device_signal.emit((ip, hostname, port, mac))  
                        msg = f"[活动] {ip:15s} - {hostname:30s} (端口 {port})"  
                        if mac:  
                            msg += f" - MAC: {mac}"  
                        msg += "\n"  
                        self.output_signal.emit(msg)  
                    
                    scanned += 1  
                    progress = int((scanned / total) * 100)  
                    self.progress_signal.emit(progress)  
                    
        except Exception as e:  
            self.output_signal.emit(f"\n错误: {str(e)}\n")  
        
        self.finished_signal.emit()  
        
    def stop(self):  
        self.is_running = False  
        
    @staticmethod  
    def get_mac_address(ip):  
        """获取MAC地址 (仅Windows)"""  
        if platform.system().lower() != 'windows':  
            return None  
            
        try:  
            result = subprocess.run(['arp', '-a', ip], capture_output=True, text=True, timeout=1)  
            match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', result.stdout)  
            if match:  
                return match.group(0)  
        except:  
            pass  
        return None  


class WhoisWorker(QThread):  
    """Whois查询工作线程"""  
    output_signal = pyqtSignal(str)  
    finished_signal = pyqtSignal()  
    
    def __init__(self, domain):  
        super().__init__()  
        self.domain = domain  
        
    def run(self):  
        self.output_signal.emit(f"Whois查询: {self.domain}\n")  
        self.output_signal.emit(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")  
        self.output_signal.emit("-" * 70 + "\n\n")  
        
        try:  
            # 使用whois命令  
            if platform.system().lower() == 'windows':  
                self.output_signal.emit("提示: Windows系统需要安装whois工具\n")  
                self.output_signal.emit("可以使用在线服务: https://who.is/whois/{}\n".format(self.domain))  
            else:  
                result = subprocess.run(['whois', self.domain],   
                                      capture_output=True, text=True, timeout=30)  
                self.output_signal.emit(result.stdout)  
                
        except FileNotFoundError:  
            self.output_signal.emit("未找到whois命令，请先安装\n")  
            self.output_signal.emit("Linux: sudo apt-get install whois\n")  
            self.output_signal.emit("Mac: brew install whois\n")  
        except Exception as e:  
            self.output_signal.emit(f"错误: {str(e)}\n")  
        
        self.finished_signal.emit()  


class NetworkToolPro(QMainWindow):  
    """主窗口"""  
    
    def __init__(self):  
        super().__init__()  
        self.workers = []  
        self.init_ui()  
        
    def init_ui(self):  
        """初始化UI"""  
        self.setWindowTitle("NetworkToolPro - 专业网络工具集 v2.0")  
        self.setGeometry(100, 100, 1200, 800)  
        
        # 设置样式  
        self.setStyleSheet("""  
            QMainWindow {  
                background-color: #f5f5f5;  
            }  
            QTabWidget::pane {  
                border: 1px solid #cccccc;  
                background-color: white;  
                border-radius: 4px;  
            }  
            QTabBar::tab {  
                background-color: #e0e0e0;  
                color: #333333;  
                padding: 8px 20px;  
                margin-right: 2px;  
                border-top-left-radius: 4px;  
                border-top-right-radius: 4px;  
            }  
            QTabBar::tab:selected {  
                background-color: white;  
                color: #1976d2;  
                font-weight: bold;  
            }  
            QGroupBox {  
                font-weight: bold;  
                border: 2px solid #e0e0e0;  
                border-radius: 6px;  
                margin-top: 10px;  
                padding-top: 10px;  
            }  
            QGroupBox::title {  
                color: #1976d2;  
                subcontrol-origin: margin;  
                left: 10px;  
                padding: 0 5px;  
            }  
            QPushButton {  
                background-color: #1976d2;  
                color: white;  
                border: none;  
                padding: 8px 16px;  
                border-radius: 4px;  
                font-weight: bold;  
            }  
            QPushButton:hover {  
                background-color: #1565c0;  
            }  
            QPushButton:pressed {  
                background-color: #0d47a1;  
            }  
            QPushButton:disabled {  
                background-color: #cccccc;  
                color: #666666;  
            }  
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {  
                padding: 6px;  
                border: 1px solid #cccccc;  
                border-radius: 4px;  
                background-color: white;  
            }  
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {  
                border: 2px solid #1976d2;  
            }  
            QTextEdit {  
                border: 1px solid #cccccc;  
                border-radius: 4px;  
                background-color: #fafafa;  
                font-family: 'Consolas', 'Monaco', monospace;  
                font-size: 10pt;  
            }  
            QProgressBar {  
                border: 1px solid #cccccc;  
                border-radius: 4px;  
                text-align: center;  
                background-color: #e0e0e0;  
            }  
            QProgressBar::chunk {  
                background-color: #4caf50;  
                border-radius: 3px;  
            }  
            QTableWidget {  
                border: 1px solid #cccccc;  
                border-radius: 4px;  
                gridline-color: #e0e0e0;  
            }  
            QHeaderView::section {  
                background-color: #f5f5f5;  
                padding: 6px;  
                border: none;  
                border-bottom: 2px solid #1976d2;  
                font-weight: bold;  
            }  
        """)  
        
        # 创建菜单栏  
        self.create_menu_bar()  
        
        # 创建状态栏  
        self.statusBar = QStatusBar()  
        self.setStatusBar(self.statusBar)  
        self.statusBar.showMessage("就绪")  
        
        # 创建中央部件  
        central_widget = QWidget()  
        self.setCentralWidget(central_widget)  
        
        # 主布局  
        main_layout = QVBoxLayout(central_widget)  
        main_layout.setContentsMargins(10, 10, 10, 10)  
        
        # 创建标签页  
        self.tabs = QTabWidget()  
        main_layout.addWidget(self.tabs)  
        
        # 添加各个工具标签页  
        self.create_ping_tab()  
        self.create_traceroute_tab()  
        self.create_port_scan_tab()  
        self.create_speed_test_tab()  
        self.create_http_test_tab()  
        self.create_dns_lookup_tab()  
        self.create_lan_scan_tab()  
        self.create_whois_tab()  
        self.create_subnet_calc_tab()  
        
    def create_menu_bar(self):  
        """创建菜单栏"""  
        menubar = self.menuBar()  
        
        # 文件菜单  
        file_menu = menubar.addMenu("文件(&F)")  
        
        save_action = QAction("保存结果(&S)", self)  
        save_action.setShortcut("Ctrl+S")  
        save_action.triggered.connect(self.save_results)  
        file_menu.addAction(save_action)  
        
        file_menu.addSeparator()  
        
        exit_action = QAction("退出(&X)", self)  
        exit_action.setShortcut("Ctrl+Q")  
        exit_action.triggered.connect(self.close)  
        file_menu.addAction(exit_action)  
        
        # 工具菜单  
        tools_menu = menubar.addMenu("工具(&T)")  
        
        clear_action = QAction("清空当前标签(&C)", self)  
        clear_action.setShortcut("Ctrl+L")  
        clear_action.triggered.connect(self.clear_current_tab)  
        tools_menu.addAction(clear_action)  
        
        stop_action = QAction("停止所有任务(&S)", self)  
        stop_action.setShortcut("Ctrl+X")  
        stop_action.triggered.connect(self.stop_all_workers)  
        tools_menu.addAction(stop_action)  
        
        # 帮助菜单  
        help_menu = menubar.addMenu("帮助(&H)")  
        
        about_action = QAction("关于(&A)", self)  
        about_action.triggered.connect(self.show_about)  
        help_menu.addAction(about_action)  
        
    def create_ping_tab(self):  
        """创建Ping标签页"""  
        tab = QWidget()  
        self.tabs.addTab(tab, "🌐 Ping测试")  
        
        layout = QVBoxLayout(tab)  
        
        # 参数设置组  
        param_group = QGroupBox("参数设置")  
        param_layout = QGridLayout(param_group)  
        
        param_layout.addWidget(QLabel("目标地址:"), 0, 0)  
        self.ping_host = QLineEdit("www.baidu.com")  
        self.ping_host.setPlaceholderText("输入域名或IP地址")  
        param_layout.addWidget(self.ping_host, 0, 1, 1, 2)  
        
        param_layout.addWidget(QLabel("次数:"), 0, 3)  
        self.ping_count = QSpinBox()  
        self.ping_count.setRange(1, 1000)  
        self.ping_count.setValue(4)  
        param_layout.addWidget(self.ping_count, 0, 4)  
        
        param_layout.addWidget(QLabel("超时(秒):"), 1, 0)  
        self.ping_timeout = QDoubleSpinBox()  
        self.ping_timeout.setRange(0.1, 10)  
        self.ping_timeout.setValue(2.0)  
        self.ping_timeout.setSingleStep(0.1)  
        param_layout.addWidget(self.ping_timeout, 1, 1)  
        
        param_layout.addWidget(QLabel("间隔(秒):"), 1, 2)  
        self.ping_interval = QDoubleSpinBox()  
        self.ping_interval.setRange(0, 10)  
        self.ping_interval.setValue(1.0)  
        self.ping_interval.setSingleStep(0.1)  
        param_layout.addWidget(self.ping_interval, 1, 3)  
        
        # 按钮  
        btn_layout = QHBoxLayout()  
        self.ping_start_btn = QPushButton("开始 Ping")  
        self.ping_start_btn.clicked.connect(self.start_ping)  
        self.ping_stop_btn = QPushButton("停止")  
        self.ping_stop_btn.clicked.connect(self.stop_ping)  
        self.ping_stop_btn.setEnabled(False)  
        self.ping_clear_btn = QPushButton("清空")  
        self.ping_clear_btn.clicked.connect(lambda: self.ping_output.clear())  
        
        btn_layout.addWidget(self.ping_start_btn)  
        btn_layout.addWidget(self.ping_stop_btn)  
        btn_layout.addWidget(self.ping_clear_btn)  
        btn_layout.addStretch()  
        
        param_layout.addLayout(btn_layout, 2, 0, 1, 5)  
        
        layout.addWidget(param_group)  
        
        # 输出区域  
        output_group = QGroupBox("输出结果")  
        output_layout = QVBoxLayout(output_group)  
        
        self.ping_output = QTextEdit()  
        self.ping_output.setReadOnly(True)  
        output_layout.addWidget(self.ping_output)  
        
        # 统计信息  
        stats_layout = QHBoxLayout()  
        self.ping_stats = QLabel("已发送: 0 | 已接收: 0 | 丢失: 0 | 丢包率: 0%")  
        self.ping_stats.setStyleSheet("color: #1976d2; font-weight: bold;")  
        stats_layout.addWidget(self.ping_stats)  
        stats_layout.addStretch()  
        output_layout.addLayout(stats_layout)  
        
        layout.addWidget(output_group)  
        
        self.ping_worker = None  
        
    def create_traceroute_tab(self):  
        """创建路由跟踪标签页"""  
        tab = QWidget()  
        self.tabs.addTab(tab, "🗺️ 路由跟踪")  
        
        layout = QVBoxLayout(tab)  
        
        # 参数设置组  
        param_group = QGroupBox("参数设置")  
        param_layout = QGridLayout(param_group)  
        
        param_layout.addWidget(QLabel("目标地址:"), 0, 0)  
        self.trace_host = QLineEdit("www.google.com")  
        self.trace_host.setPlaceholderText("输入域名或IP地址")  
        param_layout.addWidget(self.trace_host, 0, 1, 1, 2)  
        
        param_layout.addWidget(QLabel("最大跳数:"), 0, 3)  
        self.trace_hops = QSpinBox()  
        self.trace_hops.setRange(1, 64)  
        self.trace_hops.setValue(30)  
        param_layout.addWidget(self.trace_hops, 0, 4)  
        
        # 按钮  
        btn_layout = QHBoxLayout()  
        self.trace_start_btn = QPushButton("开始跟踪")  
        self.trace_start_btn.clicked.connect(self.start_traceroute)  
        self.trace_stop_btn = QPushButton("停止")  
        self.trace_stop_btn.clicked.connect(self.stop_traceroute)  
        self.trace_stop_btn.setEnabled(False)  
        self.trace_clear_btn = QPushButton("清空")  
        self.trace_clear_btn.clicked.connect(lambda: self.trace_output.clear())  
        
        btn_layout.addWidget(self.trace_start_btn)  
        btn_layout.addWidget(self.trace_stop_btn)  
        btn_layout.addWidget(self.trace_clear_btn)  
        btn_layout.addStretch()  
        
        param_layout.addLayout(btn_layout, 1, 0, 1, 5)  
        
        layout.addWidget(param_group)  
        
        # 输出区域  
        output_group = QGroupBox("路由信息")  
        output_layout = QVBoxLayout(output_group)  
        
        self.trace_output = QTextEdit()  
        self.trace_output.setReadOnly(True)  
        output_layout.addWidget(self.trace_output)  
        
        layout.addWidget(output_group)  
        
        self.trace_worker = None  
        
    def create_port_scan_tab(self):  
        """创建端口扫描标签页"""  
        tab = QWidget()  
        self.tabs.addTab(tab, "🔍 端口扫描")  
        
        layout = QVBoxLayout(tab)  
        
        # 参数设置组  
        param_group = QGroupBox("扫描参数")  
        param_layout = QGridLayout(param_group)  
        
        param_layout.addWidget(QLabel("目标地址:"), 0, 0)  
        self.scan_host = QLineEdit("127.0.0.1")  
        self.scan_host.setPlaceholderText("输入域名或IP地址")  
        param_layout.addWidget(self.scan_host, 0, 1)  
        
        param_layout.addWidget(QLabel("起始端口:"), 0, 2)  
        self.scan_start_port = QSpinBox()  
        self.scan_start_port.setRange(1, 65535)  
        self.scan_start_port.setValue(1)  
        param_layout.addWidget(self.scan_start_port, 0, 3)  
        
        param_layout.addWidget(QLabel("结束端口:"), 1, 0)  
        self.scan_end_port = QSpinBox()  
        self.scan_end_port.setRange(1, 65535)  
        self.scan_end_port.setValue(1024)  
        param_layout.addWidget(self.scan_end_port, 1, 1)  
        
        param_layout.addWidget(QLabel("超时(秒):"), 1, 2)  
        self.scan_timeout = QDoubleSpinBox()  
        self.scan_timeout.setRange(0.1, 10)  
        self.scan_timeout.setValue(0.5)  
        self.scan_timeout.setSingleStep(0.1)  
        param_layout.addWidget(self.scan_timeout, 1, 3)  
        
        param_layout.addWidget(QLabel("线程数:"), 2, 0)  
        self.scan_threads = QSpinBox()  
        self.scan_threads.setRange(1, 500)  
        self.scan_threads.setValue(100)  
        param_layout.addWidget(self.scan_threads, 2, 1)  
        
        # 按钮  
        btn_layout = QHBoxLayout()  
        self.scan_start_btn = QPushButton("开始扫描")  
        self.scan_start_btn.clicked.connect(self.start_port_scan)  
        self.scan_stop_btn = QPushButton("停止")  
        self.scan_stop_btn.clicked.connect(self.stop_port_scan)  
        self.scan_stop_btn.setEnabled(False)  
        self.scan_clear_btn = QPushButton("清空")  
        self.scan_clear_btn.clicked.connect(self.clear_port_scan)  
        
        btn_layout.addWidget(self.scan_start_btn)  
        btn_layout.addWidget(self.scan_stop_btn)  
        btn_layout.addWidget(self.scan_clear_btn)  
        btn_layout.addStretch()  
        
        param_layout.addLayout(btn_layout, 3, 0, 1, 4)  
        
        # 进度条  
        self.scan_progress = QProgressBar()  
        param_layout.addWidget(self.scan_progress, 4, 0, 1, 4)  
        
        layout.addWidget(param_group)  
        
        # 分割器  
        splitter = QSplitter(Qt.Vertical)  
        
        # 结果表格  
        result_group = QGroupBox("开放端口")  
        result_layout = QVBoxLayout(result_group)  
        
        self.scan_table = QTableWidget()  
        self.scan_table.setColumnCount(3)  
        self.scan_table.setHorizontalHeaderLabels(["端口", "服务", "状态"])  
        self.scan_table.horizontalHeader().setStretchLastSection(True)  
        self.scan_table.setAlternatingRowColors(True)  
        result_layout.addWidget(self.scan_table)  
        
        splitter.addWidget(result_group)  
        
        # 日志输出  
        log_group = QGroupBox("扫描日志")  
        log_layout = QVBoxLayout(log_group)  
        
        self.scan_output = QTextEdit()  
        self.scan_output.setReadOnly(True)  
        self.scan_output.setMaximumHeight(150)  
        log_layout.addWidget(self.scan_output)  
        
        splitter.addWidget(log_group)  
        
        layout.addWidget(splitter)  
        
        self.scan_worker = None  
        
    def create_speed_test_tab(self):  
        """创建速度测试标签页"""  
        tab = QWidget()  
        self.tabs.addTab(tab, "⚡ 速度测试")  
        
        layout = QVBoxLayout(tab)  
        
        # 参数设置组  
        param_group = QGroupBox("测试设置")  
        param_layout = QGridLayout(param_group)  
        
        param_layout.addWidget(QLabel("测试URL:"), 0, 0)  
        self.speed_url = QLineEdit("http://speedtest.tele2.net/10MB.zip")  
        self.speed_url.setPlaceholderText("输入测试文件URL")  
        param_layout.addWidget(self.speed_url, 0, 1, 1, 3)  
        
        # 预设URL  
        preset_layout = QHBoxLayout()  
        preset_layout.addWidget(QLabel("快速选择:"))  
        
        preset_urls = [  
            ("1MB", "http://speedtest.tele2.net/1MB.zip"),  
            ("10MB", "http://speedtest.tele2.net/10MB.zip"),  
            ("100MB", "http://speedtest.tele2.net/100MB.zip"),  
        ]  
        
        for name, url in preset_urls:  
            btn = QPushButton(name)  
            btn.clicked.connect(lambda checked, u=url: self.speed_url.setText(u))  
            btn.setMaximumWidth(80)  
            preset_layout.addWidget(btn)  
        
        preset_layout.addStretch()  
        param_layout.addLayout(preset_layout, 1, 0, 1, 4)  
        
        param_layout.addWidget(QLabel("测试次数:"), 2, 0)  
        self.speed_count = QSpinBox()  
        self.speed_count.setRange(1, 10)  
        self.speed_count.setValue(3)  
        param_layout.addWidget(self.speed_count, 2, 1)  
        
        param_layout.addWidget(QLabel("超时(秒):"), 2, 2)  
        self.speed_timeout = QSpinBox()  
        self.speed_timeout.setRange(10, 300)  
        self.speed_timeout.setValue(60)  
        param_layout.addWidget(self.speed_timeout, 2, 3)  
        
        # 按钮  
        btn_layout = QHBoxLayout()  
        self.speed_start_btn = QPushButton("开始测试")  
        self.speed_start_btn.clicked.connect(self.start_speed_test)  
        self.speed_stop_btn = QPushButton("停止")  
        self.speed_stop_btn.clicked.connect(self.stop_speed_test)  
        self.speed_stop_btn.setEnabled(False)  
        self.speed_clear_btn = QPushButton("清空")  
        self.speed_clear_btn.clicked.connect(lambda: self.speed_output.clear())  
        
        btn_layout.addWidget(self.speed_start_btn)  
        btn_layout.addWidget(self.speed_stop_btn)  
        btn_layout.addWidget(self.speed_clear_btn)  
        btn_layout.addStretch()  
        
        param_layout.addLayout(btn_layout, 3, 0, 1, 4)  
        
        # 进度条  
        self.speed_progress = QProgressBar()  
        param_layout.addWidget(self.speed_progress, 4, 0, 1, 4)  
        
        layout.addWidget(param_group)  
        
        # 结果显示  
        result_group = QGroupBox("测试结果")  
        result_layout = QVBoxLayout(result_group)  
        
        # 统计卡片  
        stats_layout = QHBoxLayout()  
        
        self.speed_avg_label = self.create_stat_card("平均速度", "0.00 Mbps", "#4caf50")  
        self.speed_max_label = self.create_stat_card("最高速度", "0.00 Mbps", "#2196f3")  
        self.speed_min_label = self.create_stat_card("最低速度", "0.00 Mbps", "#ff9800")  
        
        stats_layout.addWidget(self.speed_avg_label)  
        stats_layout.addWidget(self.speed_max_label)  
        stats_layout.addWidget(self.speed_min_label)  
        
        result_layout.addLayout(stats_layout)  
        
        # 输出日志  
        self.speed_output = QTextEdit()  
        self.speed_output.setReadOnly(True)  
        result_layout.addWidget(self.speed_output)  
        
        layout.addWidget(result_group)  
        
        self.speed_worker = None  
        
    def create_stat_card(self, title, value, color):  
        """创建统计卡片"""  
        frame = QFrame()  
        frame.setStyleSheet(f"""  
            QFrame {{  
                background-color: white;  
                border: 2px solid {color};  
                border-radius: 8px;  
                padding: 10px;  
            }}  
        """)  
        
        layout = QVBoxLayout(frame)  
        
        title_label = QLabel(title)  
        title_label.setStyleSheet(f"color: {color}; font-size: 12pt; font-weight: bold;")  
        title_label.setAlignment(Qt.AlignCenter)  
        
        value_label = QLabel(value)  
        value_label.setStyleSheet("color: #333; font-size: 16pt; font-weight: bold;")  
        value_label.setAlignment(Qt.AlignCenter)  
        value_label.setObjectName("value")  
        
        layout.addWidget(title_label)  
        layout.addWidget(value_label)  
        
        return frame  
        
    def create_http_test_tab(self):  
        """创建HTTP测试标签页"""  
        tab = QWidget()  
        self.tabs.addTab(tab, "🌐 HTTP测试")  
        
        layout = QVBoxLayout(tab)  
        
        # 请求设置组  
        request_group = QGroupBox("请求设置")  
        request_layout = QGridLayout(request_group)  
        
        request_layout.addWidget(QLabel("URL:"), 0, 0)  
        self.http_url = QLineEdit("https://httpbin.org/get")  
        self.http_url.setPlaceholderText("输入完整URL")  
        request_layout.addWidget(self.http_url, 0, 1, 1, 3)  
        
        request_layout.addWidget(QLabel("方法:"), 1, 0)  
        self.http_method = QComboBox()  
        self.http_method.addItems(['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH'])  
        request_layout.addWidget(self.http_method, 1, 1)  
        
        request_layout.addWidget(QLabel("超时(秒):"), 1, 2)  
        self.http_timeout = QSpinBox()  
        self.http_timeout.setRange(1, 300)  
        self.http_timeout.setValue(10)  
        request_layout.addWidget(self.http_timeout, 1, 3)  
        
        request_layout.addWidget(QLabel("请求头:"), 2, 0, Qt.AlignTop)  
        self.http_headers = QTextEdit()  
        self.http_headers.setPlaceholderText("每行一个，格式: Header-Name: value\n例如:\nContent-Type: application/json\nAuthorization: Bearer token")  
        self.http_headers.setMaximumHeight(80)  
        request_layout.addWidget(self.http_headers, 2, 1, 2, 3)  
        
        request_layout.addWidget(QLabel("请求体:"), 4, 0, Qt.AlignTop)  
        self.http_body = QTextEdit()  
        self.http_body.setPlaceholderText("POST/PUT/PATCH 请求的数据")  
        self.http_body.setMaximumHeight(80)  
        request_layout.addWidget(self.http_body, 4, 1, 2, 3)  
        
        # 按钮  
        btn_layout = QHBoxLayout()  
        self.http_send_btn = QPushButton("发送请求")  
        self.http_send_btn.clicked.connect(self.start_http_test)  
        self.http_clear_btn = QPushButton("清空")  
        self.http_clear_btn.clicked.connect(lambda: self.http_output.clear())  
        
        btn_layout.addWidget(self.http_send_btn)  
        btn_layout.addWidget(self.http_clear_btn)  
        btn_layout.addStretch()  
        
        request_layout.addLayout(btn_layout, 6, 0, 1, 4)  
        
        layout.addWidget(request_group)  
        
        # 响应显示  
        response_group = QGroupBox("响应结果")  
        response_layout = QVBoxLayout(response_group)  
        
        self.http_output = QTextEdit()  
        self.http_output.setReadOnly(True)  
        response_layout.addWidget(self.http_output)  
        
        layout.addWidget(response_group)  
        
        self.http_worker = None  
        
    def create_dns_lookup_tab(self):  
        """创建DNS查询标签页"""  
        tab = QWidget()  
        self.tabs.addTab(tab, "🔎 DNS查询")  
        
        layout = QVBoxLayout(tab)  
        
        # 查询设置组  
        query_group = QGroupBox("查询设置")  
        query_layout = QGridLayout(query_group)  
        
        query_layout.addWidget(QLabel("域名:"), 0, 0)  
        self.dns_domain = QLineEdit("www.baidu.com")  
        self.dns_domain.setPlaceholderText("输入域名")  
        query_layout.addWidget(self.dns_domain, 0, 1, 1, 2)  
        
        # 按钮  
        btn_layout = QHBoxLayout()  
        self.dns_lookup_btn = QPushButton("查询")  
        self.dns_lookup_btn.clicked.connect(self.start_dns_lookup)  
        self.dns_clear_btn = QPushButton("清空")  
        self.dns_clear_btn.clicked.connect(lambda: self.dns_output.clear())  
        
        btn_layout.addWidget(self.dns_lookup_btn)  
        btn_layout.addWidget(self.dns_clear_btn)  
        btn_layout.addStretch()  
        
        query_layout.addLayout(btn_layout, 1, 0, 1, 3)  
        
        layout.addWidget(query_group)  
        
        # 结果显示  
        result_group = QGroupBox("查询结果")  
        result_layout = QVBoxLayout(result_group)  
        
        self.dns_output = QTextEdit()  
        self.dns_output.setReadOnly(True)  
        result_layout.addWidget(self.dns_output)  
        
        layout.addWidget(result_group)  
        
        self.dns_worker = None  
        
    def create_lan_scan_tab(self):  
        """创建局域网扫描标签页"""  
        tab = QWidget()  
        self.tabs.addTab(tab, "📡 局域网扫描")  
        
        layout = QVBoxLayout(tab)  
        
        # 扫描设置组  
        scan_group = QGroupBox("扫描设置")  
        scan_layout = QGridLayout(scan_group)  
        
        scan_layout.addWidget(QLabel("网络段:"), 0, 0)  
        self.lan_network = QLineEdit("192.168.1.0/24")  
        self.lan_network.setPlaceholderText("CIDR格式，如: 192.168.1.0/24")  
        scan_layout.addWidget(self.lan_network, 0, 1)  
        
        scan_layout.addWidget(QLabel("超时(秒):"), 0, 2)  
        self.lan_timeout = QDoubleSpinBox()  
        self.lan_timeout.setRange(0.1, 10)  
        self.lan_timeout.setValue(0.5)  
        self.lan_timeout.setSingleStep(0.1)  
        scan_layout.addWidget(self.lan_timeout, 0, 3)  
        
        scan_layout.addWidget(QLabel("线程数:"), 1, 0)  
        self.lan_threads = QSpinBox()  
        self.lan_threads.setRange(1, 500)  
        self.lan_threads.setValue(50)  
        scan_layout.addWidget(self.lan_threads, 1, 1)  
        
        # 按钮  
        btn_layout = QHBoxLayout()  
        self.lan_start_btn = QPushButton("开始扫描")  
        self.lan_start_btn.clicked.connect(self.start_lan_scan)  
        self.lan_stop_btn = QPushButton("停止")  
        self.lan_stop_btn.clicked.connect(self.stop_lan_scan)  
        self.lan_stop_btn.setEnabled(False)  
        self.lan_clear_btn = QPushButton("清空")  
        self.lan_clear_btn.clicked.connect(self.clear_lan_scan)  
        
        btn_layout.addWidget(self.lan_start_btn)  
        btn_layout.addWidget(self.lan_stop_btn)  
        btn_layout.addWidget(self.lan_clear_btn)  
        btn_layout.addStretch()  
        
        scan_layout.addLayout(btn_layout, 2, 0, 1, 4)  
        
        # 进度条  
        self.lan_progress = QProgressBar()  
        scan_layout.addWidget(self.lan_progress, 3, 0, 1, 4)  
        
        layout.addWidget(scan_group)  
        
        # 分割器  
        splitter = QSplitter(Qt.Vertical)  
        
        # 设备表格  
        device_group = QGroupBox("发现的设备")  
        device_layout = QVBoxLayout(device_group)  
        
        self.lan_table = QTableWidget()  
        self.lan_table.setColumnCount(4)  
        self.lan_table.setHorizontalHeaderLabels(["IP地址", "主机名", "开放端口", "MAC地址"])  
        header = self.lan_table.horizontalHeader()  
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  
        header.setSectionResizeMode(1, QHeaderView.Stretch)  
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  
        self.lan_table.setAlternatingRowColors(True)  
        device_layout.addWidget(self.lan_table)  
        
        splitter.addWidget(device_group)  
        
        # 日志输出  
        log_group = QGroupBox("扫描日志")  
        log_layout = QVBoxLayout(log_group)  
        
        self.lan_output = QTextEdit()  
        self.lan_output.setReadOnly(True)  
        self.lan_output.setMaximumHeight(150)  
        log_layout.addWidget(self.lan_output)  
        
        splitter.addWidget(log_group)  
        
        layout.addWidget(splitter)  
        
        self.lan_worker = None  
        
    def create_whois_tab(self):  
        """创建Whois查询标签页"""  
        tab = QWidget()  
        self.tabs.addTab(tab, "📋 Whois查询")  
        
        layout = QVBoxLayout(tab)  
        
        # 查询设置组  
        query_group = QGroupBox("查询设置")  
        query_layout = QGridLayout(query_group)  
        
        query_layout.addWidget(QLabel("域名:"), 0, 0)  
        self.whois_domain = QLineEdit("google.com")  
        self.whois_domain.setPlaceholderText("输入域名")  
        query_layout.addWidget(self.whois_domain, 0, 1, 1, 2)  
        
        # 按钮  
        btn_layout = QHBoxLayout()  
        self.whois_lookup_btn = QPushButton("查询")  
        self.whois_lookup_btn.clicked.connect(self.start_whois_lookup)  
        self.whois_clear_btn = QPushButton("清空")  
        self.whois_clear_btn.clicked.connect(lambda: self.whois_output.clear())  
        
        btn_layout.addWidget(self.whois_lookup_btn)  
        btn_layout.addWidget(self.whois_clear_btn)  
        btn_layout.addStretch()  
        
        query_layout.addLayout(btn_layout, 1, 0, 1, 3)  
        
        layout.addWidget(query_group)  
        
        # 结果显示  
        result_group = QGroupBox("查询结果")  
        result_layout = QVBoxLayout(result_group)  
        
        self.whois_output = QTextEdit()  
        self.whois_output.setReadOnly(True)  
        result_layout.addWidget(self.whois_output)  
        
        layout.addWidget(result_group)  
        
        self.whois_worker = None  
        
    def create_subnet_calc_tab(self):  
        """创建子网计算器标签页"""  
        tab = QWidget()  
        self.tabs.addTab(tab, "🔢 子网计算")  
        
        layout = QVBoxLayout(tab)  
        
        # 输入设置组  
        input_group = QGroupBox("输入参数")  
        input_layout = QGridLayout(input_group)  
        
        input_layout.addWidget(QLabel("IP地址:"), 0, 0)  
        self.subnet_ip = QLineEdit("192.168.1.100")  
        self.subnet_ip.setPlaceholderText("例如: 192.168.1.100")  
        input_layout.addWidget(self.subnet_ip, 0, 1)  
        
        input_layout.addWidget(QLabel("子网掩码:"), 0, 2)  
        self.subnet_mask = QLineEdit("255.255.255.0")  
        self.subnet_mask.setPlaceholderText("例如: 255.255.255.0")  
        input_layout.addWidget(self.subnet_mask, 0, 3)  
        
        input_layout.addWidget(QLabel("或 CIDR:"), 1, 0)  
        self.subnet_cidr = QLineEdit("192.168.1.0/24")  
        self.subnet_cidr.setPlaceholderText("例如: 192.168.1.0/24")  
        input_layout.addWidget(self.subnet_cidr, 1, 1, 1, 3)  
        
        # 按钮  
        btn_layout = QHBoxLayout()  
        calc_btn = QPushButton("计算")  
        calc_btn.clicked.connect(self.calculate_subnet)  
        clear_btn = QPushButton("清空")  
        clear_btn.clicked.connect(lambda: self.subnet_output.clear())  
        
        btn_layout.addWidget(calc_btn)  
        btn_layout.addWidget(clear_btn)  
        btn_layout.addStretch()  
        
        input_layout.addLayout(btn_layout, 2, 0, 1, 4)  
        
        layout.addWidget(input_group)  
        
        # 结果显示  
        result_group = QGroupBox("计算结果")  
        result_layout = QVBoxLayout(result_group)  
        
        self.subnet_output = QTextEdit()  
        self.subnet_output.setReadOnly(True)  
        result_layout.addWidget(self.subnet_output)  
        
        layout.addWidget(result_group)  
        
    # ==================== Ping功能 ====================  
    
    def start_ping(self):  
        """开始Ping测试"""  
        host = self.ping_host.text().strip()  
        if not host:  
            QMessageBox.warning(self, "警告", "请输入目标地址")  
            return  
            
        count = self.ping_count.value()  
        timeout = self.ping_timeout.value()  
        interval = self.ping_interval.value()  
        
        self.ping_output.clear()  
        self.ping_start_btn.setEnabled(False)  
        self.ping_stop_btn.setEnabled(True)  
        self.statusBar.showMessage("正在执行Ping测试...")  
        
        self.ping_worker = PingWorker(host, count, timeout, interval)  
        self.ping_worker.output_signal.connect(self.append_ping_output)  
        self.ping_worker.stats_signal.connect(self.update_ping_stats)  
        self.ping_worker.finished_signal.connect(self.ping_finished)  
        self.ping_worker.start()  
        
        self.workers.append(self.ping_worker)  
        
    def stop_ping(self):  
        """停止Ping测试"""  
        if self.ping_worker:  
            self.ping_worker.stop()  
            
    def append_ping_output(self, text):  
        """追加Ping输出"""  
        self.ping_output.append(text.rstrip())  
        self.ping_output.moveCursor(QTextCursor.End)  
        
    def update_ping_stats(self, stats):  
        """更新Ping统计"""  
        self.append_ping_output("\n" + "-" * 70)  
        self.append_ping_output(f"\nPing 统计信息:")  
        self.append_ping_output(f"    数据包: 已发送 = {stats['sent']}, 已接收 = {stats['received']}, 丢失 = {stats['lost']} ({stats['loss_rate']:.1f}% 丢失)")  
        
        if stats['times']:  
            self.append_ping_output(f"往返行程的估计时间(以毫秒为单位):")  
            self.append_ping_output(f"    最短 = {stats['min']:.0f}ms, 最长 = {stats['max']:.0f}ms, 平均 = {stats['avg']:.0f}ms")  
        
        self.ping_stats.setText(  
            f"已发送: {stats['sent']} | 已接收: {stats['received']} | "  
            f"丢失: {stats['lost']} | 丢包率: {stats['loss_rate']:.1f}%"  
        )  
        
    def ping_finished(self):  
        """Ping完成"""  
        self.ping_start_btn.setEnabled(True)  
        self.ping_stop_btn.setEnabled(False)  
        self.statusBar.showMessage("Ping测试完成", 3000)  
        if self.ping_worker in self.workers:  
            self.workers.remove(self.ping_worker)  
        
    # ==================== Traceroute功能 ====================  
    
    def start_traceroute(self):  
        """开始路由跟踪"""  
        host = self.trace_host.text().strip()  
        if not host:  
            QMessageBox.warning(self, "警告", "请输入目标地址")  
            return  
            
        max_hops = self.trace_hops.value()  
        
        self.trace_output.clear()  
        self.trace_start_btn.setEnabled(False)  
        self.trace_stop_btn.setEnabled(True)  
        self.statusBar.showMessage("正在执行路由跟踪...")  
        
        self.trace_worker = TracerouteWorker(host, max_hops)  
        self.trace_worker.output_signal.connect(self.append_trace_output)  
        self.trace_worker.finished_signal.connect(self.trace_finished)  
        self.trace_worker.start()  
        
        self.workers.append(self.trace_worker)  
        
    def stop_traceroute(self):  
        """停止路由跟踪"""  
        if self.trace_worker:  
            self.trace_worker.stop()  
            
    def append_trace_output(self, text):  
        """追加路由跟踪输出"""  
        self.trace_output.append(text.rstrip())  
        self.trace_output.moveCursor(QTextCursor.End)  
        
    def trace_finished(self):  
        """路由跟踪完成"""  
        self.trace_start_btn.setEnabled(True)  
        self.trace_stop_btn.setEnabled(False)  
        self.statusBar.showMessage("路由跟踪完成", 3000)  
        if self.trace_worker in self.workers:  
            self.workers.remove(self.trace_worker)  
        
    # ==================== 端口扫描功能 ====================  
    
    def start_port_scan(self):  
        """开始端口扫描"""  
        host = self.scan_host.text().strip()  
        if not host:  
            QMessageBox.warning(self, "警告", "请输入目标地址")  
            return  
            
        start_port = self.scan_start_port.value()  
        end_port = self.scan_end_port.value()  
        
        if start_port > end_port:  
            QMessageBox.warning(self, "警告", "起始端口不能大于结束端口")  
            return  
            
        timeout = self.scan_timeout.value()  
        threads = self.scan_threads.value()  
        
        self.scan_output.clear()  
        self.scan_table.setRowCount(0)  
        self.scan_progress.setValue(0)  
        self.scan_start_btn.setEnabled(False)  
        self.scan_stop_btn.setEnabled(True)  
        self.statusBar.showMessage("正在执行端口扫描...")  
        
        self.scan_worker = PortScanWorker(host, start_port, end_port, timeout, threads)  
        self.scan_worker.output_signal.connect(self.append_scan_output)  
        self.scan_worker.progress_signal.connect(self.scan_progress.setValue)  
        self.scan_worker.result_signal.connect(self.update_scan_result)  
        self.scan_worker.finished_signal.connect(self.scan_finished)  
        self.scan_worker.start()  
        
        self.workers.append(self.scan_worker)  
        
    def stop_port_scan(self):  
        """停止端口扫描"""  
        if self.scan_worker:  
            self.scan_worker.stop()  
            
    def append_scan_output(self, text):  
        """追加扫描输出"""  
        self.scan_output.append(text.rstrip())  
        self.scan_output.moveCursor(QTextCursor.End)  
        
    def update_scan_result(self, results):  
        """更新扫描结果表格"""  
        for port, service, status in results:  
            row = self.scan_table.rowCount()  
            self.scan_table.insertRow(row)  
            self.scan_table.setItem(row, 0, QTableWidgetItem(str(port)))  
            self.scan_table.setItem(row, 1, QTableWidgetItem(service))  
            self.scan_table.setItem(row, 2, QTableWidgetItem(status))  
            
        self.append_scan_output(f"\n扫描完成！共发现 {len(results)} 个开放端口。")  
        
    def scan_finished(self):  
        """扫描完成"""  
        self.scan_start_btn.setEnabled(True)  
        self.scan_stop_btn.setEnabled(False)  
        self.statusBar.showMessage("端口扫描完成", 3000)  
        if self.scan_worker in self.workers:  
            self.workers.remove(self.scan_worker)  
            
    def clear_port_scan(self):  
        """清空端口扫描"""  
        self.scan_output.clear()  
        self.scan_table.setRowCount(0)  
        self.scan_progress.setValue(0)  
        
    # ==================== 速度测试功能 ====================  
    
    def start_speed_test(self):  
        """开始速度测试"""  
        url = self.speed_url.text().strip()  
        if not url:  
            QMessageBox.warning(self, "警告", "请输入测试URL")  
            return  
            
        count = self.speed_count.value()  
        timeout = self.speed_timeout.value()  
        
        self.speed_output.clear()  
        self.speed_progress.setValue(0)  
        self.update_speed_stats(0, 0, 0)  
        self.speed_start_btn.setEnabled(False)  
        self.speed_stop_btn.setEnabled(True)  
        self.statusBar.showMessage("正在执行速度测试...")  
        
        self.speed_worker = SpeedTestWorker(url, count, timeout)  
        self.speed_worker.output_signal.connect(self.append_speed_output)  
        self.speed_worker.progress_signal.connect(self.speed_progress.setValue)  
        self.speed_worker.result_signal.connect(self.update_speed_result)  
        self.speed_worker.finished_signal.connect(self.speed_finished)  
        self.speed_worker.start()  
        
        self.workers.append(self.speed_worker)  
        
    def stop_speed_test(self):  
        """停止速度测试"""  
        if self.speed_worker:  
            self.speed_worker.stop()  
            
    def append_speed_output(self, text):  
        """追加速度测试输出"""  
        # 处理\r(覆盖当前行)  
        if '\r' in text:  
            self.speed_output.moveCursor(QTextCursor.End)  
            self.speed_output.moveCursor(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)  
            self.speed_output.textCursor().removeSelectedText()  
            self.speed_output.insertPlainText(text.replace('\r', ''))  
        else:  
            self.speed_output.append(text.rstrip())  
        self.speed_output.moveCursor(QTextCursor.End)  
        
    def update_speed_result(self, results):  
        """更新速度测试结果"""  
        if 'avg' in results:  
            self.append_speed_output("\n" + "-" * 70)  
            self.append_speed_output(f"\n速度测试统计:")  
            self.append_speed_output(f"  平均速度: {results['avg']:.2f} Mbps")  
            self.append_speed_output(f"  最高速度: {results['max']:.2f} Mbps")  
            self.append_speed_output(f"  最低速度: {results['min']:.2f} Mbps")  
            
            self.update_speed_stats(results['avg'], results['max'], results['min'])  
            
    def update_speed_stats(self, avg, max_speed, min_speed):  
        """更新速度统计卡片"""  
        self.speed_avg_label.findChild(QLabel, "value").setText(f"{avg:.2f} Mbps")  
        self.speed_max_label.findChild(QLabel, "value").setText(f"{max_speed:.2f} Mbps")  
        self.speed_min_label.findChild(QLabel, "value").setText(f"{min_speed:.2f} Mbps")  
        
    def speed_finished(self):  
        """速度测试完成"""  
        self.speed_start_btn.setEnabled(True)  
        self.speed_stop_btn.setEnabled(False)  
        self.statusBar.showMessage("速度测试完成", 3000)  
        if self.speed_worker in self.workers:  
            self.workers.remove(self.speed_worker)  
        
    # ==================== HTTP测试功能 ====================  
    
    def start_http_test(self):  
        """开始HTTP测试"""  
        url = self.http_url.text().strip()  
        if not url:  
            QMessageBox.warning(self, "警告", "请输入URL")  
            return  
            
        method = self.http_method.currentText()  
        headers = self.http_headers.toPlainText()  
        body = self.http_body.toPlainText()  
        timeout = self.http_timeout.value()  
        
        self.http_output.clear()  
        self.http_send_btn.setEnabled(False)  
        self.statusBar.showMessage("正在发送HTTP请求...")  
        
        self.http_worker = HTTPTestWorker(url, method, headers, body, timeout)  
        self.http_worker.output_signal.connect(self.append_http_output)  
        self.http_worker.result_signal.connect(self.update_http_result)  
        self.http_worker.finished_signal.connect(self.http_finished)  
        self.http_worker.start()  
        
        self.workers.append(self.http_worker)  
        
    def append_http_output(self, text):  
        """追加HTTP输出"""  
        self.http_output.append(text.rstrip())  
        self.http_output.moveCursor(QTextCursor.End)  
        
    def update_http_result(self, result):  
        """更新HTTP结果"""  
        pass  # 已在worker中输出  
        
    def http_finished(self):
        """HTTP测试完成"""
        self.http_send_btn.setEnabled(True)
        self.statusBar.showMessage("HTTP请求完成", 3000)
        if self.http_worker in self.workers:
            self.workers.remove(self.http_worker)
        
    # ==================== DNS查询功能 ====================
    
    def start_dns_lookup(self):
        """开始DNS查询"""
        domain = self.dns_domain.text().strip()
        if not domain:
            QMessageBox.warning(self, "警告", "请输入域名")
            return
            
        self.dns_output.clear()
        self.dns_lookup_btn.setEnabled(False)
        self.statusBar.showMessage("正在执行DNS查询...")
        
        self.dns_worker = DNSLookupWorker(domain)
        self.dns_worker.output_signal.connect(self.append_dns_output)
        self.dns_worker.result_signal.connect(self.update_dns_result)
        self.dns_worker.finished_signal.connect(self.dns_finished)
        self.dns_worker.start()
        
        self.workers.append(self.dns_worker)
        
    def append_dns_output(self, text):
        """追加DNS输出"""
        self.dns_output.append(text.rstrip())
        self.dns_output.moveCursor(QTextCursor.End)
        
    def update_dns_result(self, result):
        """更新DNS结果"""
        pass  # 已在worker中输出
        
    def dns_finished(self):
        """DNS查询完成"""
        self.dns_lookup_btn.setEnabled(True)
        self.statusBar.showMessage("DNS查询完成", 3000)
        if self.dns_worker in self.workers:
            self.workers.remove(self.dns_worker)
        
    # ==================== 局域网扫描功能 ====================
    
    def start_lan_scan(self):
        """开始局域网扫描"""
        network = self.lan_network.text().strip()
        if not network:
            QMessageBox.warning(self, "警告", "请输入网络段")
            return
            
        try:
            ipaddress.ip_network(network, strict=False)
        except ValueError:
            QMessageBox.warning(self, "警告", "无效的网络段格式")
            return
            
        timeout = self.lan_timeout.value()
        threads = self.lan_threads.value()
        
        self.lan_output.clear()
        self.lan_table.setRowCount(0)
        self.lan_progress.setValue(0)
        self.lan_start_btn.setEnabled(False)
        self.lan_stop_btn.setEnabled(True)
        self.statusBar.showMessage("正在扫描局域网...")
        
        self.lan_worker = LANScanWorker(network, timeout, threads)
        self.lan_worker.output_signal.connect(self.append_lan_output)
        self.lan_worker.progress_signal.connect(self.lan_progress.setValue)
        self.lan_worker.device_signal.connect(self.add_lan_device)
        self.lan_worker.finished_signal.connect(self.lan_finished)
        self.lan_worker.start()
        
        self.workers.append(self.lan_worker)
        
    def stop_lan_scan(self):
        """停止局域网扫描"""
        if self.lan_worker:
            self.lan_worker.stop()
            
    def append_lan_output(self, text):
        """追加局域网扫描输出"""
        self.lan_output.append(text.rstrip())
        self.lan_output.moveCursor(QTextCursor.End)
        
    def add_lan_device(self, device):
        """添加发现的设备到表格"""
        ip, hostname, port, mac = device
        row = self.lan_table.rowCount()
        self.lan_table.insertRow(row)
        self.lan_table.setItem(row, 0, QTableWidgetItem(ip))
        self.lan_table.setItem(row, 1, QTableWidgetItem(hostname))
        self.lan_table.setItem(row, 2, QTableWidgetItem(str(port)))
        self.lan_table.setItem(row, 3, QTableWidgetItem(mac or "N/A"))
        
    def lan_finished(self):
        """局域网扫描完成"""
        self.lan_start_btn.setEnabled(True)
        self.lan_stop_btn.setEnabled(False)
        device_count = self.lan_table.rowCount()
        self.append_lan_output(f"\n扫描完成！共发现 {device_count} 个活动设备。")
        self.statusBar.showMessage(f"局域网扫描完成，发现 {device_count} 个设备", 3000)
        if self.lan_worker in self.workers:
            self.workers.remove(self.lan_worker)
            
    def clear_lan_scan(self):
        """清空局域网扫描"""
        self.lan_output.clear()
        self.lan_table.setRowCount(0)
        self.lan_progress.setValue(0)
        
    # ==================== Whois查询功能 ====================
    
    def start_whois_lookup(self):
        """开始Whois查询"""
        domain = self.whois_domain.text().strip()
        if not domain:
            QMessageBox.warning(self, "警告", "请输入域名")
            return
            
        self.whois_output.clear()
        self.whois_lookup_btn.setEnabled(False)
        self.statusBar.showMessage("正在执行Whois查询...")
        
        self.whois_worker = WhoisWorker(domain)
        self.whois_worker.output_signal.connect(self.append_whois_output)
        self.whois_worker.finished_signal.connect(self.whois_finished)
        self.whois_worker.start()
        
        self.workers.append(self.whois_worker)
        
    def append_whois_output(self, text):
        """追加Whois输出"""
        self.whois_output.append(text.rstrip())
        self.whois_output.moveCursor(QTextCursor.End)
        
    def whois_finished(self):
        """Whois查询完成"""
        self.whois_lookup_btn.setEnabled(True)
        self.statusBar.showMessage("Whois查询完成", 3000)
        if self.whois_worker in self.workers:
            self.workers.remove(self.whois_worker)
        
    # ==================== 子网计算功能 ====================
    
    def calculate_subnet(self):
        """计算子网信息"""
        self.subnet_output.clear()
        
        # 优先使用CIDR格式
        cidr = self.subnet_cidr.text().strip()
        
        try:
            if cidr:
                # 使用CIDR
                network = ipaddress.ip_network(cidr, strict=False)
            else:
                # 使用IP和子网掩码
                ip = self.subnet_ip.text().strip()
                mask = self.subnet_mask.text().strip()
                
                if not ip or not mask:
                    QMessageBox.warning(self, "警告", "请输入IP地址和子网掩码，或使用CIDR格式")
                    return
                    
                # 将子网掩码转换为CIDR
                mask_obj = ipaddress.IPv4Address(mask)
                prefix_len = sum([bin(int(x)).count('1') for x in mask.split('.')])
                network = ipaddress.ip_network(f"{ip}/{prefix_len}", strict=False)
            
            # 计算各种信息
            output = []
            output.append("=" * 70)
            output.append("子网计算结果")
            output.append("=" * 70)
            output.append("")
            
            output.append("📍 基本信息:")
            output.append(f"  网络地址:     {network.network_address}")
            output.append(f"  广播地址:     {network.broadcast_address}")
            output.append(f"  子网掩码:     {network.netmask}")
            output.append(f"  通配符掩码:   {network.hostmask}")
            output.append(f"  CIDR表示:     {network.with_prefixlen}")
            output.append(f"  网络前缀:     /{network.prefixlen}")
            output.append("")
            
            output.append("📍 地址范围:")
            output.append(f"  第一个可用:   {list(network.hosts())[0] if network.num_addresses > 2 else 'N/A'}")
            output.append(f"  最后可用:     {list(network.hosts())[-1] if network.num_addresses > 2 else 'N/A'}")
            output.append(f"  总地址数:     {network.num_addresses}")
            output.append(f"  可用主机数:   {network.num_addresses - 2 if network.num_addresses > 2 else 0}")
            output.append("")
            
            output.append("📍 网络类别:")
            first_octet = int(str(network.network_address).split('.')[0])
            if 1 <= first_octet <= 126:
                net_class = "A类网络"
            elif 128 <= first_octet <= 191:
                net_class = "B类网络"
            elif 192 <= first_octet <= 223:
                net_class = "C类网络"
            elif 224 <= first_octet <= 239:
                net_class = "D类网络 (组播)"
            else:
                net_class = "E类网络 (保留)"
            output.append(f"  网络类别:     {net_class}")
            
            if network.is_private:
                output.append(f"  地址类型:     私有地址")
            elif network.is_loopback:
                output.append(f"  地址类型:     环回地址")
            elif network.is_link_local:
                output.append(f"  地址类型:     链路本地地址")
            else:
                output.append(f"  地址类型:     公网地址")
            output.append("")
            
            # 子网划分建议
            output.append("📍 子网划分参考:")
            for bits in [1, 2, 3, 4]:
                if network.prefixlen + bits <= 32:
                    new_prefix = network.prefixlen + bits
                    subnets = 2 ** bits
                    hosts_per_subnet = (2 ** (32 - new_prefix)) - 2
                    output.append(f"  划分为 {subnets:3d} 个子网: /{new_prefix} (每个 {hosts_per_subnet:6d} 主机)")
            output.append("")
            
            # 二进制表示
            output.append("📍 二进制表示:")
            ip_parts = str(network.network_address).split('.')
            mask_parts = str(network.netmask).split('.')
            
            output.append(f"  网络地址: {'.'.join([f'{int(x):08b}' for x in ip_parts])}")
            output.append(f"            {network.network_address}")
            output.append(f"  子网掩码: {'.'.join([f'{int(x):08b}' for x in mask_parts])}")
            output.append(f"            {network.netmask}")
            output.append("")
            
            output.append("=" * 70)
            
            self.subnet_output.setText('\n'.join(output))
            self.statusBar.showMessage("子网计算完成", 3000)
            
        except ValueError as e:
            QMessageBox.warning(self, "错误", f"无效的IP地址或子网掩码: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"计算失败: {str(e)}")
    
    # ==================== 通用功能 ====================
    
    def save_results(self):
        """保存当前标签页的结果"""
        current_index = self.tabs.currentIndex()
        tab_name = self.tabs.tabText(current_index)
        
        # 获取当前标签页的输出内容
        output_widgets = {
            0: self.ping_output,
            1: self.trace_output,
            2: self.scan_output,
            3: self.speed_output,
            4: self.http_output,
            5: self.dns_output,
            6: self.lan_output,
            7: self.whois_output,
            8: self.subnet_output,
        }
        
        output_widget = output_widgets.get(current_index)
        if not output_widget:
            return
            
        content = output_widget.toPlainText()
        if not content:
            QMessageBox.information(self, "提示", "没有可保存的内容")
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存结果",
            f"{tab_name.split()[1]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                QMessageBox.information(self, "成功", f"结果已保存到:\n{filename}")
                self.statusBar.showMessage(f"结果已保存", 3000)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def clear_current_tab(self):
        """清空当前标签页"""
        current_index = self.tabs.currentIndex()
        
        clear_functions = {
            0: lambda: (self.ping_output.clear(), 
                       self.ping_stats.setText("已发送: 0 | 已接收: 0 | 丢失: 0 | 丢包率: 0%")),
            1: lambda: self.trace_output.clear(),
            2: lambda: self.clear_port_scan(),
            3: lambda: (self.speed_output.clear(), 
                       self.update_speed_stats(0, 0, 0),
                       self.speed_progress.setValue(0)),
            4: lambda: self.http_output.clear(),
            5: lambda: self.dns_output.clear(),
            6: lambda: self.clear_lan_scan(),
            7: lambda: self.whois_output.clear(),
            8: lambda: self.subnet_output.clear(),
        }
        
        clear_func = clear_functions.get(current_index)
        if clear_func:
            clear_func()
            self.statusBar.showMessage("已清空", 2000)
    
    def stop_all_workers(self):
        """停止所有工作线程"""
        for worker in self.workers[:]:
            if hasattr(worker, 'stop'):
                worker.stop()
            if hasattr(worker, 'is_running'):
                worker.is_running = False
        self.workers.clear()
        self.statusBar.showMessage("已停止所有任务", 3000)
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h2>NetworkToolPro v2.0</h2>
        <p><b>专业网络工具集</b></p>
        <p>一款功能强大的网络诊断和测试工具</p>
        
        <h3>功能特性:</h3>
        <ul>
            <li>🌐 Ping测试 - 网络连通性检测</li>
            <li>🗺️ 路由跟踪 - 数据包路径追踪</li>
            <li>🔍 端口扫描 - 快速端口扫描</li>
            <li>⚡ 速度测试 - 网络速度测量</li>
            <li>🌐 HTTP测试 - HTTP请求测试</li>
            <li>🔎 DNS查询 - 域名解析查询</li>
            <li>📡 局域网扫描 - 发现网络设备</li>
            <li>📋 Whois查询 - 域名注册信息</li>
            <li>🔢 子网计算 - 子网信息计算</li>
        </ul>
        
        <h3>技术栈:</h3>
        <p>Python 3.x + PyQt5</p>
        
        <h3>版本信息:</h3>
        <p>版本: 2.0.0</p>
        <p>更新日期: 2024-12</p>
        
        <hr>
        <p style='color: #666;'>
        <small>© 2024 NetworkToolPro. All rights reserved.</small>
        </p>
        """
        
        QMessageBox.about(self, "关于 NetworkToolPro", about_text)
    
    def closeEvent(self, event):
        """关闭窗口事件"""
        # 停止所有工作线程
        self.stop_all_workers()
        
        # 等待线程结束
        for worker in self.workers:
            if worker.isRunning():
                worker.wait(1000)
        
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("NetworkToolPro")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("NetworkTools")
    
    # 设置应用程序图标 (如果有的话)
    # app.setWindowIcon(QIcon('icon.png'))
    
    # 创建主窗口
    window = NetworkToolPro()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()