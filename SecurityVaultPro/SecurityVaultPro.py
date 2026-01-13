#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SecurityVaultPro - 企业级密码管理和安全审计工具
完全重构版本 - 增强功能与优化体验
Version: 2.0
github网址：https://github.com/lyp0746
QQ邮箱：1610369302@qq.com
作者：LYP
"""

import sys
import json
import os
import re
import secrets
import string
import hashlib
import hmac
import time
import base64
import sqlite3
import csv
import zlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import urllib.request
import urllib.parse

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    print("请安装 cryptography: pip install cryptography")
    sys.exit(1)


# ==================== 常量定义 ====================
APP_NAME = "SecurityVaultPro"
APP_VERSION = "2.0"
DB_VERSION = 2

# 颜色方案
COLORS = {
    'primary': '#2196F3',
    'success': '#4CAF50',
    'warning': '#FF9800',
    'danger': '#F44336',
    'dark': '#212121',
    'light': '#FAFAFA',
    'accent': '#FF4081',
}

# 图标映射（使用Unicode字符）
ICONS = {
    'password': '🔐',
    'add': '➕',
    'edit': '✏️',
    'delete': '🗑️',
    'search': '🔍',
    'security': '🛡️',
    'generate': '🎲',
    'copy': '📋',
    'save': '💾',
    'export': '📤',
    'import': '📥',
    'settings': '⚙️',
    'lock': '🔒',
    'unlock': '🔓',
    'eye': '👁️',
    'dashboard': '📊',
    'history': '📜',
    'favorite': '⭐',
    'tag': '🏷️',
    'warning': '⚠️',
    'check': '✓',
    'clock': '⏰',
    '2fa': '🔐',
    'folder': '📁',
}


# ==================== 加密模块（增强版）====================
class CryptoManager:
    """加密管理器 - 增强版"""

    @staticmethod
    def derive_key(password: str, salt: bytes, iterations: int = 200000) -> bytes:
        """从密码派生加密密钥（增加迭代次数）"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    @staticmethod
    def encrypt_data(data: str, key: bytes) -> bytes:
        """加密数据"""
        if not data:
            return b''
        f = Fernet(key)
        # 压缩后加密
        compressed = zlib.compress(data.encode())
        return f.encrypt(compressed)

    @staticmethod
    def decrypt_data(encrypted_data: bytes, key: bytes) -> str:
        """解密数据"""
        if not encrypted_data:
            return ''
        try:
            f = Fernet(key)
            decrypted = f.decrypt(encrypted_data)
            # 解压缩
            decompressed = zlib.decompress(decrypted)
            return decompressed.decode()
        except:
            return ''

    @staticmethod
    def generate_salt() -> bytes:
        """生成随机盐值"""
        return secrets.token_bytes(32)

    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码用于验证"""
        return hashlib.sha256(password.encode()).hexdigest()


# ==================== 密码强度分析器（增强版）====================
class PasswordAnalyzer:
    """密码强度分析器 - 增强版"""

    COMMON_PASSWORDS = {'123456', 'password', '12345678', 'qwerty', '123456789', '12345', '1234', '111111', '1234567',
                        'dragon', '123123', 'baseball', 'iloveyou', 'trustno1', '1234567890', 'sunshine', 'master',
                        'welcome', 'shadow', 'ashley', 'football', 'jesus', 'michael', 'ninja', 'mustang', 'password1',
                        'admin', 'root'}

    COMMON_PATTERNS = [
        r'(.)\1{2,}',  # 重复字符
        r'(012|123|234|345|456|567|678|789|890)',  # 连续数字
        r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',  # 连续字母
        r'(qwerty|asdfgh|zxcvbn)',  # 键盘模式
    ]

    @classmethod
    def analyze_strength(cls, password: str) -> Dict:
        """分析密码强度 - 增强版"""
        if not password:
            return {
                'score': 0,
                'strength': '无',
                'color': 'gray',
                'issues': ['密码为空'],
                'suggestions': ['请输入密码'],
                'length': 0,
                'complexity': 0,
                'entropy': 0,
                'crack_time': '即时'
            }

        score = 0
        issues = []
        suggestions = []

        # 长度检查（优化评分）
        length = len(password)
        if length >= 20:
            score += 35
        elif length >= 16:
            score += 30
        elif length >= 12:
            score += 20
        elif length >= 8:
            score += 10
        else:
            issues.append(f'密码过短 (当前: {length}字符)')
            suggestions.append('使用至少12个字符，推荐16+')
            score += length

        # 复杂度检查
        has_lower = bool(re.search(r'[a-z]', password))
        has_upper = bool(re.search(r'[A-Z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password))

        complexity = sum([has_lower, has_upper, has_digit, has_special])
        score += complexity * 12

        if complexity == 4:
            score += 10  # 奖励使用所有字符类型

        if not has_lower and not has_upper:
            issues.append('缺少字母')
            suggestions.append('添加大小写字母')
        if not has_upper:
            suggestions.append('添加大写字母')
        if not has_digit:
            suggestions.append('添加数字')
        if not has_special:
            suggestions.append('添加特殊字符 (!@#$%...)')

        # 模式检查
        for pattern in cls.COMMON_PATTERNS:
            if re.search(pattern, password.lower()):
                issues.append('包含常见字符模式')
                score -= 15
                break

        # 常见密码检查
        if password.lower() in cls.COMMON_PASSWORDS:
            issues.append('使用了极弱的常见密码')
            score -= 40
            suggestions.append('请使用完全不同的密码')

        # 字典词汇检查（简化版）
        if len(password) >= 4:
            common_words = ['love', 'admin', 'user', 'test', 'pass', 'word']
            for word in common_words:
                if word in password.lower():
                    issues.append('包含常见单词')
                    score -= 10
                    break

        # 熵值计算
        charset_size = 0
        if has_lower:
            charset_size += 26
        if has_upper:
            charset_size += 26
        if has_digit:
            charset_size += 10
        if has_special:
            charset_size += 32

        import math
        entropy = 0
        if charset_size > 0:
            entropy = length * math.log2(charset_size)
            score += min(entropy / 3, 20)

        # 多样性检查
        unique_chars = len(set(password))
        diversity_ratio = unique_chars / length if length > 0 else 0
        if diversity_ratio > 0.8:
            score += 5
        elif diversity_ratio < 0.5:
            issues.append('字符重复度过高')
            score -= 5

        score = max(0, min(100, score))

        # 破解时间估算
        crack_time = cls.estimate_crack_time(entropy)

        # 强度等级（更细致的分级）
        if score >= 90:
            strength = '极强'
            color = 'darkgreen'
        elif score >= 75:
            strength = '很强'
            color = 'green'
        elif score >= 60:
            strength = '强'
            color = 'lightgreen'
        elif score >= 45:
            strength = '中等'
            color = 'orange'
        elif score >= 25:
            strength = '弱'
            color = 'darkorange'
        else:
            strength = '极弱'
            color = 'red'

        return {
            'score': int(score),
            'strength': strength,
            'color': color,
            'issues': issues,
            'suggestions': suggestions,
            'length': length,
            'complexity': complexity,
            'entropy': round(entropy, 2),
            'crack_time': crack_time,
            'diversity': round(diversity_ratio * 100, 1)
        }

    @staticmethod
    def estimate_crack_time(entropy: float) -> str:
        """估算破解时间"""
        if entropy == 0:
            return '即时'

        # 假设每秒10亿次尝试
        attempts_per_second = 1e9
        total_combinations = 2 ** entropy
        seconds = total_combinations / (2 * attempts_per_second)

        if seconds < 1:
            return '不到1秒'
        elif seconds < 60:
            return f'{int(seconds)}秒'
        elif seconds < 3600:
            return f'{int(seconds/60)}分钟'
        elif seconds < 86400:
            return f'{int(seconds/3600)}小时'
        elif seconds < 31536000:
            return f'{int(seconds/86400)}天'
        elif seconds < 31536000 * 100:
            return f'{int(seconds/31536000)}年'
        elif seconds < 31536000 * 1000:
            return f'{int(seconds/31536000)}年'
        elif seconds < 31536000 * 1000000:
            return f'{int(seconds/31536000/1000)}千年'
        else:
            return '数十亿年'


# ==================== 密码生成器（增强版）====================
class PasswordGenerator:
    """安全密码生成器 - 增强版"""

    WORD_LIST = [
        'Alpha', 'Bravo', 'Charlie', 'Delta', 'Echo', 'Foxtrot',
        'Golf', 'Hotel', 'India', 'Juliet', 'Kilo', 'Lima',
        'Mike', 'November', 'Oscar', 'Papa', 'Quebec', 'Romeo',
        'Sierra', 'Tango', 'Uniform', 'Victor', 'Whiskey', 'Xray',
        'Yankee', 'Zulu', 'Dragon', 'Phoenix', 'Tiger', 'Eagle',
    ]

    @classmethod
    def generate(cls, length: int = 16, use_lower: bool = True, use_upper: bool = True,
                 use_digits: bool = True, use_special: bool = True,
                 exclude_ambiguous: bool = True, mode: str = 'random') -> str:
        """生成随机密码"""
        if mode == 'memorable':
            return cls.generate_memorable(length)
        elif mode == 'pin':
            return cls.generate_pin(length)
        else:
            return cls.generate_random(length, use_lower, use_upper,
                                      use_digits, use_special, exclude_ambiguous)

    @staticmethod
    def generate_random(length: int, use_lower: bool, use_upper: bool,
                       use_digits: bool, use_special: bool,
                       exclude_ambiguous: bool) -> str:
        """生成随机密码"""
        charset = ''
        required_chars = []

        if use_lower:
            chars = string.ascii_lowercase
            if exclude_ambiguous:
                chars = chars.replace('l', '').replace('o', '')
            charset += chars
            required_chars.append(secrets.choice(chars))

        if use_upper:
            chars = string.ascii_uppercase
            if exclude_ambiguous:
                chars = chars.replace('I', '').replace('O', '')
            charset += chars
            required_chars.append(secrets.choice(chars))

        if use_digits:
            chars = string.digits
            if exclude_ambiguous:
                chars = chars.replace('0', '').replace('1', '')
            charset += chars
            required_chars.append(secrets.choice(chars))

        if use_special:
            chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
            charset += chars
            required_chars.append(secrets.choice(chars))

        if not charset:
            charset = string.ascii_letters + string.digits

        # 确保密码足够长
        if length < len(required_chars):
            length = len(required_chars)

        # 生成密码
        password_chars = required_chars + [
            secrets.choice(charset) for _ in range(length - len(required_chars))
        ]

        # 使用 Fisher-Yates shuffle
        password_list = list(password_chars)
        for i in range(len(password_list) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            password_list[i], password_list[j] = password_list[j], password_list[i]

        return ''.join(password_list)

    @classmethod
    def generate_memorable(cls, num_words: int = 4) -> str:
        """生成易记密码（单词组合）"""
        words = [secrets.choice(cls.WORD_LIST) for _ in range(num_words)]
        separators = ['-', '_', '.', '!']
        separator = secrets.choice(separators)

        # 添加数字
        number = secrets.randbelow(100)
        return separator.join(words) + str(number)

    @staticmethod
    def generate_pin(length: int = 6) -> str:
        """生成PIN码"""
        return ''.join([secrets.choice(string.digits) for _ in range(length)])


# ==================== TOTP管理器（增强版）====================
class TOTPManager:
    """TOTP 双因素认证管理器 - 增强版"""

    @staticmethod
    def generate_secret() -> str:
        """生成随机密钥"""
        return base64.b32encode(secrets.token_bytes(20)).decode('utf-8')

    @staticmethod
    def get_totp_token(secret: str, time_step: int = 30) -> str:
        """生成TOTP令牌"""
        try:
            # 移除空格和换行
            secret = secret.replace(' ', '').replace('\n', '').upper()
            key = base64.b32decode(secret)
            msg = int(time.time() / time_step).to_bytes(8, byteorder='big')
            h = hmac.new(key, msg, hashlib.sha1).digest()
            offset = h[-1] & 0x0F
            truncated = int.from_bytes(h[offset:offset+4], byteorder='big') & 0x7FFFFFFF
            token = str(truncated % 1000000).zfill(6)
            return token
        except Exception as e:
            return "ERROR"

    @staticmethod
    def verify_token(secret: str, token: str, window: int = 1) -> bool:
        """验证TOTP令牌"""
        try:
            current_time = int(time.time() / 30)
            secret = secret.replace(' ', '').replace('\n', '').upper()
            key = base64.b32decode(secret)

            for i in range(-window, window + 1):
                msg = (current_time + i).to_bytes(8, byteorder='big')
                h = hmac.new(key, msg, hashlib.sha1).digest()
                offset = h[-1] & 0x0F
                truncated = int.from_bytes(h[offset:offset+4], byteorder='big') & 0x7FFFFFFF
                expected = str(truncated % 1000000).zfill(6)
                if expected == token:
                    return True
            return False
        except:
            return False

    @staticmethod
    def get_remaining_time(time_step: int = 30) -> int:
        """获取剩余时间"""
        return time_step - (int(time.time()) % time_step)

    @staticmethod
    def get_qr_code_url(secret: str, account: str, issuer: str = APP_NAME) -> str:
        """生成QR码URL"""
        url = f'otpauth://totp/{issuer}:{account}?secret={secret}&issuer={issuer}'
        return url


# ==================== 数据库管理器（增强版）====================
class DatabaseManager:
    """密码库数据库管理 - 增强版"""

    def __init__(self, db_path: str, encryption_key: bytes):
        self.db_path = db_path
        self.key = encryption_key
        self.conn = None
        self.connect()
        self.create_tables()
        self.upgrade_database()

    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute('PRAGMA foreign_keys = ON')
        self.conn.execute('PRAGMA journal_mode = WAL')  # 写前日志模式提高性能

    def create_tables(self):
        """创建数据表"""
        cursor = self.conn.cursor()

        # 密码表（增强字段）
        cursor.execute('''  
            CREATE TABLE IF NOT EXISTS passwords (  
                id INTEGER PRIMARY KEY AUTOINCREMENT,  
                title TEXT NOT NULL,  
                username TEXT,  
                password BLOB NOT NULL,  
                url TEXT,  
                notes BLOB,  
                category TEXT,  
                tags TEXT,  
                totp_secret BLOB,  
                created_at TEXT,  
                modified_at TEXT,  
                last_used TEXT,  
                expires_at TEXT,  
                is_favorite INTEGER DEFAULT 0,  
                strength_score INTEGER DEFAULT 0,  
                icon TEXT  
            )  
        ''')

        # 密码历史表
        cursor.execute('''  
            CREATE TABLE IF NOT EXISTS password_history (  
                id INTEGER PRIMARY KEY AUTOINCREMENT,  
                password_id INTEGER,  
                password BLOB NOT NULL,  
                changed_at TEXT,  
                FOREIGN KEY (password_id) REFERENCES passwords(id) ON DELETE CASCADE  
            )  
        ''')

        # 审计日志表
        cursor.execute('''  
            CREATE TABLE IF NOT EXISTS audit_log (  
                id INTEGER PRIMARY KEY AUTOINCREMENT,  
                action TEXT,  
                password_id INTEGER,  
                timestamp TEXT,  
                details TEXT,  
                ip_address TEXT  
            )  
        ''')

        # 设置表
        cursor.execute('''  
            CREATE TABLE IF NOT EXISTS settings (  
                key TEXT PRIMARY KEY,  
                value TEXT  
            )  
        ''')

        # 附件表
        cursor.execute('''  
            CREATE TABLE IF NOT EXISTS attachments (  
                id INTEGER PRIMARY KEY AUTOINCREMENT,  
                password_id INTEGER,  
                filename TEXT,  
                data BLOB,  
                size INTEGER,  
                created_at TEXT,  
                FOREIGN KEY (password_id) REFERENCES passwords(id) ON DELETE CASCADE  
            )  
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_passwords_title ON passwords(title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_passwords_category ON passwords(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_passwords_favorite ON passwords(is_favorite)')

        self.conn.commit()

    def upgrade_database(self):
        """升级数据库结构"""
        cursor = self.conn.cursor()

        # 检查版本
        cursor.execute("SELECT value FROM settings WHERE key = 'db_version'")
        result = cursor.fetchone()
        current_version = int(result[0]) if result else 1

        if current_version < DB_VERSION:
            # 执行升级脚本
            if current_version < 2:
                # 添加新字段
                try:
                    cursor.execute('ALTER TABLE passwords ADD COLUMN icon TEXT')
                except:
                    pass

            # 更新版本
            cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                         ('db_version', str(DB_VERSION)))
            self.conn.commit()

    def add_password(self, title: str, username: str, password: str,
                     url: str = '', notes: str = '', category: str = '',
                     tags: str = '', totp_secret: str = '',
                     expires_at: str = '', icon: str = '') -> int:
        """添加密码条目"""
        cursor = self.conn.cursor()

        # 加密敏感数据
        encrypted_password = CryptoManager.encrypt_data(password, self.key)
        encrypted_notes = CryptoManager.encrypt_data(notes, self.key) if notes else b''
        encrypted_totp = CryptoManager.encrypt_data(totp_secret, self.key) if totp_secret else b''

        # 计算密码强度
        strength_score = PasswordAnalyzer.analyze_strength(password)['score']

        now = datetime.now().isoformat()
        cursor.execute('''  
            INSERT INTO passwords (title, username, password, url, notes, category,   
                                   tags, totp_secret, created_at, modified_at,   
                                   strength_score, expires_at, icon)  
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)  
        ''', (title, username, encrypted_password, url, encrypted_notes,
              category, tags, encrypted_totp, now, now, strength_score, expires_at, icon))

        self.conn.commit()
        password_id = cursor.lastrowid

        # 记录到历史
        self.add_password_history(password_id, password)

        # 审计日志
        self.log_action('CREATE', password_id, f'创建密码条目: {title}')

        return password_id

    def get_all_passwords(self, include_expired: bool = True) -> List[Dict]:
        """获取所有密码条目"""
        cursor = self.conn.cursor()

        query = 'SELECT * FROM passwords'
        if not include_expired:
            query += " WHERE expires_at IS NULL OR expires_at = '' OR expires_at > ?"
            cursor.execute(query + ' ORDER BY is_favorite DESC, modified_at DESC',
                         (datetime.now().isoformat(),))
        else:
            cursor.execute(query + ' ORDER BY is_favorite DESC, modified_at DESC')

        rows = cursor.fetchall()

        passwords = []
        for row in rows:
            try:
                pwd_dict = {
                    'id': row[0],
                    'title': row[1],
                    'username': row[2],
                    'password': CryptoManager.decrypt_data(row[3], self.key),
                    'url': row[4],
                    'notes': CryptoManager.decrypt_data(row[5], self.key) if row[5] else '',
                    'category': row[6],
                    'tags': row[7] if row[7] else '',
                    'totp_secret': CryptoManager.decrypt_data(row[8], self.key) if row[8] else '',
                    'created_at': row[9],
                    'modified_at': row[10],
                    'last_used': row[11],
                    'expires_at': row[12] if row[12] else '',
                    'is_favorite': bool(row[13]),
                    'strength_score': row[14] if row[14] else 0,
                    'icon': row[15] if len(row) > 15 else ''
                }
                passwords.append(pwd_dict)
            except Exception as e:
                print(f"解密错误: {e}")
                continue

        return passwords

    def get_password_by_id(self, password_id: int) -> Optional[Dict]:
        """通过ID获取密码"""
        passwords = self.get_all_passwords()
        for pwd in passwords:
            if pwd['id'] == password_id:
                return pwd
        return None

    def update_password(self, password_id: int, **kwargs):
        """更新密码条目"""
        updates = []
        values = []

        # 记录旧密码到历史
        if 'password' in kwargs:
            old_pwd = self.get_password_by_id(password_id)
            if old_pwd:
                self.add_password_history(password_id, old_pwd['password'])

        for key, value in kwargs.items():
            if key in ['password', 'notes', 'totp_secret'] and value is not None:
                updates.append(f'{key} = ?')
                values.append(CryptoManager.encrypt_data(value, self.key))
            elif key not in ['password', 'notes', 'totp_secret']:
                updates.append(f'{key} = ?')
                values.append(value)

        # 更新强度分数
        if 'password' in kwargs:
            strength_score = PasswordAnalyzer.analyze_strength(kwargs['password'])['score']
            updates.append('strength_score = ?')
            values.append(strength_score)

        updates.append('modified_at = ?')
        values.append(datetime.now().isoformat())
        values.append(password_id)

        cursor = self.conn.cursor()
        cursor.execute(f'UPDATE passwords SET {", ".join(updates)} WHERE id = ?', values)
        self.conn.commit()

        self.log_action('UPDATE', password_id, f'更新密码条目')

    def delete_password(self, password_id: int):
        """删除密码条目"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM passwords WHERE id = ?', (password_id,))
        self.conn.commit()
        self.log_action('DELETE', password_id, f'删除密码条目')

    def mark_as_used(self, password_id: int):
        """标记为已使用"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE passwords SET last_used = ? WHERE id = ?',
                      (datetime.now().isoformat(), password_id))
        self.conn.commit()

    def toggle_favorite(self, password_id: int):
        """切换收藏状态"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE passwords SET is_favorite = NOT is_favorite WHERE id = ?',
                      (password_id,))
        self.conn.commit()

    def add_password_history(self, password_id: int, password: str):
        """添加密码历史记录"""
        cursor = self.conn.cursor()
        encrypted = CryptoManager.encrypt_data(password, self.key)
        cursor.execute('''  
            INSERT INTO password_history (password_id, password, changed_at)  
            VALUES (?, ?, ?)  
        ''', (password_id, encrypted, datetime.now().isoformat()))
        self.conn.commit()

    def get_password_history(self, password_id: int) -> List[Dict]:
        """获取密码历史"""
        cursor = self.conn.cursor()
        cursor.execute('''  
            SELECT password, changed_at FROM password_history   
            WHERE password_id = ? ORDER BY changed_at DESC  
        ''', (password_id,))

        history = []
        for row in cursor.fetchall():
            try:
                history.append({
                    'password': CryptoManager.decrypt_data(row[0], self.key),
                    'changed_at': row[1]
                })
            except:
                continue

        return history

    def search_passwords(self, query: str) -> List[Dict]:
        """搜索密码（模糊搜索）"""
        all_passwords = self.get_all_passwords()
        query_lower = query.lower()

        results = []
        for pwd in all_passwords:
            if (query_lower in pwd['title'].lower() or
                query_lower in pwd['username'].lower() or
                query_lower in pwd['url'].lower() or
                query_lower in pwd['category'].lower() or
                query_lower in pwd['tags'].lower() or
                query_lower in pwd['notes'].lower()):
                results.append(pwd)

        return results

    def get_passwords_by_category(self, category: str) -> List[Dict]:
        """按分类获取密码"""
        passwords = self.get_all_passwords()
        return [p for p in passwords if p['category'] == category]

    def get_favorites(self) -> List[Dict]:
        """获取收藏的密码"""
        passwords = self.get_all_passwords()
        return [p for p in passwords if p['is_favorite']]

    def get_expiring_passwords(self, days: int = 30) -> List[Dict]:
        """获取即将过期的密码"""
        passwords = self.get_all_passwords()
        threshold = datetime.now() + timedelta(days=days)

        expiring = []
        for pwd in passwords:
            if pwd['expires_at']:
                try:
                    expires = datetime.fromisoformat(pwd['expires_at'])
                    if expires <= threshold:
                        expiring.append(pwd)
                except:
                    pass

        return expiring

    def log_action(self, action: str, password_id: int, details: str, ip: str = '127.0.0.1'):
        """记录操作日志"""
        cursor = self.conn.cursor()
        cursor.execute('''  
            INSERT INTO audit_log (action, password_id, timestamp, details, ip_address)  
            VALUES (?, ?, ?, ?, ?)  
        ''', (action, password_id, datetime.now().isoformat(), details, ip))
        self.conn.commit()

    def get_audit_logs(self, limit: int = 100) -> List[Dict]:
        """获取审计日志"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        return [
            {
                'id': row[0],
                'action': row[1],
                'password_id': row[2],
                'timestamp': row[3],
                'details': row[4],
                'ip_address': row[5] if len(row) > 5 else ''
            }
            for row in rows
        ]

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        cursor = self.conn.cursor()

        stats = {}

        # 总数
        cursor.execute('SELECT COUNT(*) FROM passwords')
        stats['total'] = cursor.fetchone()[0]

        # 收藏数
        cursor.execute('SELECT COUNT(*) FROM passwords WHERE is_favorite = 1')
        stats['favorites'] = cursor.fetchone()[0]

        # 分类统计
        cursor.execute('SELECT category, COUNT(*) FROM passwords GROUP BY category')
        stats['by_category'] = dict(cursor.fetchall())

        # 强度统计
        cursor.execute('''  
            SELECT   
                SUM(CASE WHEN strength_score >= 80 THEN 1 ELSE 0 END) as strong,  
                SUM(CASE WHEN strength_score >= 50 AND strength_score < 80 THEN 1 ELSE 0 END) as medium,  
                SUM(CASE WHEN strength_score < 50 THEN 1 ELSE 0 END) as weak  
            FROM passwords  
        ''')
        row = cursor.fetchone()
        stats['strength'] = {
            'strong': row[0] or 0,
            'medium': row[1] or 0,
            'weak': row[2] or 0
        }

        return stats

    def export_to_csv(self, file_path: str) -> bool:
        """导出到CSV"""
        try:
            passwords = self.get_all_passwords()
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['标题', '用户名', '密码', 'URL', '分类', '标签', '备注'])

                for pwd in passwords:
                    writer.writerow([
                        pwd['title'],
                        pwd['username'],
                        pwd['password'],
                        pwd['url'],
                        pwd['category'],
                        pwd['tags'],
                        pwd['notes']
                    ])
            return True
        except Exception as e:
            print(f"导出失败: {e}")
            return False

    def import_from_csv(self, file_path: str) -> int:
        """从CSV导入"""
        count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        self.add_password(
                            title=row.get('标题', ''),
                            username=row.get('用户名', ''),
                            password=row.get('密码', ''),
                            url=row.get('URL', ''),
                            category=row.get('分类', ''),
                            tags=row.get('标签', ''),
                            notes=row.get('备注', '')
                        )
                        count += 1
                    except:
                        continue
            return count
        except Exception as e:
            print(f"导入失败: {e}")
            return count

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()


# ==================== 安全审计线程（增强版）====================
class SecurityAuditThread(QThread):
    """安全审计后台线程 - 增强版"""
    progress = pyqtSignal(int, str)
    result = pyqtSignal(dict)

    def __init__(self, passwords: List[Dict]):
        super().__init__()
        self.passwords = passwords

    def run(self):
        """执行安全审计"""
        total = len(self.passwords)
        if total == 0:
            self.result.emit({
                'weak_passwords': [],
                'reused_passwords': [],
                'old_passwords': [],
                'expiring_passwords': [],
                'no_2fa': [],
                'total_count': 0,
                'health_score': 100
            })
            return

        weak_passwords = []
        reused_passwords = []
        old_passwords = []
        expiring_passwords = []
        no_2fa = []
        password_map = defaultdict(list)

        for i, entry in enumerate(self.passwords):
            self.progress.emit(int((i + 1) / total * 100), f'正在分析: {entry["title"]}')

            # 密码强度检查
            score = entry.get('strength_score', 0)
            if score < 60:
                analysis = PasswordAnalyzer.analyze_strength(entry['password'])
                weak_passwords.append({
                    'id': entry['id'],
                    'title': entry['title'],
                    'score': score,
                    'strength': analysis['strength'],
                    'issues': analysis['issues']
                })

            # 密码重用检查
            pwd_hash = hashlib.sha256(entry['password'].encode()).hexdigest()
            password_map[pwd_hash].append(entry['title'])

            # 旧密码检查（超过90天）
            try:
                modified = datetime.fromisoformat(entry['modified_at'])
                age_days = (datetime.now() - modified).days
                if age_days > 90:
                    old_passwords.append({
                        'id': entry['id'],
                        'title': entry['title'],
                        'age_days': age_days
                    })
            except:
                pass

            # 过期检查
            if entry.get('expires_at'):
                try:
                    expires = datetime.fromisoformat(entry['expires_at'])
                    if expires <= datetime.now():
                        expiring_passwords.append({
                            'id': entry['id'],
                            'title': entry['title'],
                            'expired': True,
                            'days_ago': (datetime.now() - expires).days
                        })
                    elif expires <= datetime.now() + timedelta(days=30):
                        expiring_passwords.append({
                            'id': entry['id'],
                            'title': entry['title'],
                            'expired': False,
                            'days_left': (expires - datetime.now()).days
                        })
                except:
                    pass

            # 2FA检查
            if not entry.get('totp_secret'):
                # 重要账户应该开启2FA
                important_keywords = ['bank', '银行', 'email', '邮箱', 'admin', '管理']
                if any(kw in entry['title'].lower() or kw in entry['url'].lower()
                       for kw in important_keywords):
                    no_2fa.append({
                        'id': entry['id'],
                        'title': entry['title']
                    })

        # 找出重用密码
        for pwd_hash, titles in password_map.items():
            if len(titles) > 1:
                reused_passwords.append({
                    'count': len(titles),
                    'titles': titles
                })

        # 计算健康度分数
        health_score = 100
        health_score -= len(weak_passwords) * 2
        health_score -= len(reused_passwords) * 5
        health_score -= len(old_passwords) * 1
        health_score -= len(expiring_passwords) * 3
        health_score -= len(no_2fa) * 2
        health_score = max(0, health_score)

        self.result.emit({
            'weak_passwords': weak_passwords,
            'reused_passwords': reused_passwords,
            'old_passwords': old_passwords,
            'expiring_passwords': expiring_passwords,
            'no_2fa': no_2fa,
            'total_count': total,
            'health_score': health_score
        })


# ==================== 自定义控件 ====================
class PasswordStrengthWidget(QWidget):
    """密码强度可视化控件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.score = 0
        self.strength = ''
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setMaximumHeight(8)
        layout.addWidget(self.progress)

        self.label = QLabel('未评估')
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.setLayout(layout)

    def update_strength(self, analysis: Dict):
        """更新强度显示"""
        self.score = analysis['score']
        self.strength = analysis['strength']

        self.progress.setValue(self.score)
        self.label.setText(f"{self.strength} - {self.score}/100")

        # 设置颜色
        color = analysis.get('color', 'gray')
        self.progress.setStyleSheet(f'''  
            QProgressBar {{  
                border: none;  
                border-radius: 4px;  
                background-color: #E0E0E0;  
            }}  
            QProgressBar::chunk {{  
                background-color: {color};  
                border-radius: 4px;  
            }}  
        ''')


class ModernButton(QPushButton):
    """现代风格按钮"""

    def __init__(self, text='', icon='', primary=False, danger=False, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)

        if icon:
            self.setText(f"{icon} {text}")

        # 设置样式
        if primary:
            self.setStyleSheet(f'''  
                QPushButton {{  
                    background-color: {COLORS['primary']};  
                    color: white;  
                    border: none;  
                    padding: 8px 16px;  
                    border-radius: 4px;  
                    font-weight: bold;  
                }}  
                QPushButton:hover {{  
                    background-color: #1976D2;  
                }}  
                QPushButton:pressed {{  
                    background-color: #0D47A1;  
                }}  
            ''')
        elif danger:
            self.setStyleSheet(f'''  
                QPushButton {{  
                    background-color: {COLORS['danger']};  
                    color: white;  
                    border: none;  
                    padding: 8px 16px;  
                    border-radius: 4px;  
                }}  
                QPushButton:hover {{  
                    background-color: #D32F2F;  
                }}  
            ''')
        else:
            self.setStyleSheet('''  
                QPushButton {  
                    background-color: #EEEEEE;  
                    border: 1px solid #BDBDBD;  
                    padding: 8px 16px;  
                    border-radius: 4px;  
                }  
                QPushButton:hover {  
                    background-color: #E0E0E0;  
                }  
            ''')


class SearchBox(QLineEdit):
    """搜索框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(f'{ICONS["search"]} 搜索密码...')
        self.setStyleSheet('''  
            QLineEdit {  
                padding: 8px 12px;  
                border: 2px solid #E0E0E0;  
                border-radius: 20px;  
                background-color: white;  
                font-size: 13px;  
            }  
            QLineEdit:focus {  
                border-color: #2196F3;  
            }  
        ''')


# ==================== 对话框（增强版）====================
class PasswordDialog(QDialog):
    """密码条目编辑对话框 - 增强版"""

    def __init__(self, parent=None, password_data: Dict = None, db: DatabaseManager = None):
        super().__init__(parent)
        self.password_data = password_data or {}
        self.db = db
        self.init_ui()
        self.setStyleSheet('''  
            QDialog {  
                background-color: white;  
            }  
            QLineEdit, QTextEdit, QComboBox {  
                padding: 8px;  
                border: 1px solid #E0E0E0;  
                border-radius: 4px;  
                background-color: white;  
            }  
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {  
                border: 2px solid #2196F3;  
            }  
        ''')

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle('编辑密码' if self.password_data else '添加密码')
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # 标题
        title_label = QLabel('编辑密码条目' if self.password_data else '新建密码条目')
        title_label.setStyleSheet('font-size: 18px; font-weight: bold; color: #212121;')
        layout.addWidget(title_label)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet('background-color: #E0E0E0;')
        layout.addWidget(line)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_content = QWidget()
        form = QFormLayout(scroll_content)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        # 图标选择
        icon_layout = QHBoxLayout()
        self.icon_combo = QComboBox()
        self.icon_combo.addItems(['', '🔐', '🌐', '💼', '🏦', '📧', '🎮', '🛒', '☁️'])
        self.icon_combo.setCurrentText(self.password_data.get('icon', ''))
        icon_layout.addWidget(self.icon_combo)
        icon_layout.addStretch()
        form.addRow('图标:', icon_layout)

        # 标题 *
        self.title_edit = QLineEdit(self.password_data.get('title', ''))
        self.title_edit.setPlaceholderText('例如: Gmail账户')
        form.addRow('标题 *:', self.title_edit)

        # 用户名
        self.username_edit = QLineEdit(self.password_data.get('username', ''))
        self.username_edit.setPlaceholderText('用户名或邮箱')
        form.addRow('用户名:', self.username_edit)

        # 密码 *
        pwd_layout = QVBoxLayout()
        pwd_input_layout = QHBoxLayout()

        self.password_edit = QLineEdit(self.password_data.get('password', ''))
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText('输入强密码')
        pwd_input_layout.addWidget(self.password_edit)

        self.show_pwd_btn = ModernButton(ICONS['eye'])
        self.show_pwd_btn.setFixedWidth(50)
        self.show_pwd_btn.clicked.connect(self.toggle_password_visibility)
        pwd_input_layout.addWidget(self.show_pwd_btn)

        self.generate_btn = ModernButton(ICONS['generate'], '生成', primary=True)
        self.generate_btn.clicked.connect(self.generate_password)
        pwd_input_layout.addWidget(self.generate_btn)

        pwd_layout.addLayout(pwd_input_layout)

        # 密码强度
        self.strength_widget = PasswordStrengthWidget()
        pwd_layout.addWidget(self.strength_widget)

        form.addRow('密码 *:', pwd_layout)

        # URL
        self.url_edit = QLineEdit(self.password_data.get('url', ''))
        self.url_edit.setPlaceholderText('https://example.com')
        form.addRow('网址:', self.url_edit)

        # 分类
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        categories = ['', '工作', '个人', '金融', '社交', '邮箱', '购物', '娱乐', '其他']
        self.category_combo.addItems(categories)
        self.category_combo.setCurrentText(self.password_data.get('category', ''))
        form.addRow('分类:', self.category_combo)

        # 标签
        self.tags_edit = QLineEdit(self.password_data.get('tags', ''))
        self.tags_edit.setPlaceholderText('标签1, 标签2, 标签3')
        form.addRow('标签:', self.tags_edit)

        # 过期时间
        expire_layout = QHBoxLayout()
        self.expire_check = QCheckBox('设置过期时间')
        self.expire_date = QDateEdit()
        self.expire_date.setCalendarPopup(True)
        self.expire_date.setDate(QDate.currentDate().addDays(90))
        self.expire_date.setEnabled(False)

        if self.password_data.get('expires_at'):
            try:
                exp_date = datetime.fromisoformat(self.password_data['expires_at'])
                self.expire_date.setDate(QDate(exp_date.year, exp_date.month, exp_date.day))
                self.expire_check.setChecked(True)
                self.expire_date.setEnabled(True)
            except:
                pass

        self.expire_check.stateChanged.connect(
            lambda: self.expire_date.setEnabled(self.expire_check.isChecked())
        )

        expire_layout.addWidget(self.expire_check)
        expire_layout.addWidget(self.expire_date)
        expire_layout.addStretch()
        form.addRow('过期:', expire_layout)

        # 备注
        self.notes_edit = QTextEdit(self.password_data.get('notes', ''))
        self.notes_edit.setPlaceholderText('添加备注信息...')
        self.notes_edit.setMaximumHeight(100)
        form.addRow('备注:', self.notes_edit)

        # 2FA设置
        totp_group = QGroupBox('双因素认证 (2FA)')
        totp_layout = QVBoxLayout()

        totp_input_layout = QHBoxLayout()
        self.totp_edit = QLineEdit(self.password_data.get('totp_secret', ''))
        self.totp_edit.setPlaceholderText('输入TOTP密钥（可选）')
        totp_input_layout.addWidget(self.totp_edit)

        gen_totp_btn = ModernButton('生成密钥')
        gen_totp_btn.clicked.connect(self.generate_totp_secret)
        totp_input_layout.addWidget(gen_totp_btn)

        totp_layout.addLayout(totp_input_layout)

        # 当前TOTP码显示
        if self.password_data.get('totp_secret'):
            self.totp_display = QLabel()
            self.totp_display.setStyleSheet('''  
                QLabel {  
                    font-size: 24px;  
                    font-weight: bold;  
                    color: #2196F3;  
                    padding: 10px;  
                    background-color: #E3F2FD;  
                    border-radius: 4px;  
                }  
            ''')
            totp_layout.addWidget(self.totp_display)

            # 定时器更新TOTP
            self.totp_timer = QTimer()
            self.totp_timer.timeout.connect(self.update_totp_display)
            self.totp_timer.start(1000)
            self.update_totp_display()

        totp_group.setLayout(totp_layout)
        form.addRow('', totp_group)

        # 密码历史（如果有）
        if self.password_data and self.db:
            history = self.db.get_password_history(self.password_data['id'])
            if history:
                history_group = QGroupBox(f'密码历史 ({len(history)}条)')
                history_layout = QVBoxLayout()

                history_list = QListWidget()
                history_list.setMaximumHeight(100)
                for h in history[:5]:  # 只显示最近5条
                    try:
                        dt = datetime.fromisoformat(h['changed_at'])
                        item_text = f"{dt.strftime('%Y-%m-%d %H:%M')} - {'*' * 12}"
                        history_list.addItem(item_text)
                    except:
                        pass

                history_layout.addWidget(history_list)
                history_group.setLayout(history_layout)
                form.addRow('', history_group)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # 按钮组
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = ModernButton('取消')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = ModernButton(f'{ICONS["save"]} 保存', primary=True)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # 连接信号
        self.password_edit.textChanged.connect(self.update_strength)
        self.update_strength()

    def toggle_password_visibility(self):
        """切换密码可见性"""
        if self.password_edit.echoMode() == QLineEdit.Password:
            self.password_edit.setEchoMode(QLineEdit.Normal)
            self.show_pwd_btn.setText(ICONS['lock'])
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.show_pwd_btn.setText(ICONS['eye'])

    def generate_password(self):
        """生成密码"""
        dialog = PasswordGeneratorDialog(self)
        if dialog.exec_():
            self.password_edit.setText(dialog.generated_password)

    def generate_totp_secret(self):
        """生成TOTP密钥"""
        secret = TOTPManager.generate_secret()
        self.totp_edit.setText(secret)

        # 显示QR码URL
        account = self.username_edit.text() or self.title_edit.text()
        qr_url = TOTPManager.get_qr_code_url(secret, account)

        QMessageBox.information(self, '密钥已生成',
            f'TOTP密钥: {secret}\n\n'  
            f'请在身份验证器应用中手动输入此密钥\n'  
            f'或扫描以下URL对应的二维码:\n\n{qr_url}')

    def update_totp_display(self):
        """更新TOTP显示"""
        if hasattr(self, 'totp_display'):
            secret = self.totp_edit.text() or self.password_data.get('totp_secret', '')
            if secret:
                token = TOTPManager.get_totp_token(secret)
                remaining = TOTPManager.get_remaining_time()
                self.totp_display.setText(f'{token}  ({remaining}s)')

    def update_strength(self):
        """更新密码强度"""
        password = self.password_edit.text()
        analysis = PasswordAnalyzer.analyze_strength(password)
        self.strength_widget.update_strength(analysis)

    def get_data(self) -> Dict:
        """获取表单数据"""
        data = {
            'title': self.title_edit.text().strip(),
            'username': self.username_edit.text().strip(),
            'password': self.password_edit.text(),
            'url': self.url_edit.text().strip(),
            'category': self.category_combo.currentText().strip(),
            'tags': self.tags_edit.text().strip(),
            'notes': self.notes_edit.toPlainText().strip(),
            'totp_secret': self.totp_edit.text().strip(),
            'icon': self.icon_combo.currentText()
        }

        # 过期时间
        if self.expire_check.isChecked():
            exp_date = self.expire_date.date()
            dt = datetime(exp_date.year(), exp_date.month(), exp_date.day())
            data['expires_at'] = dt.isoformat()
        else:
            data['expires_at'] = ''

        return data


class PasswordGeneratorDialog(QDialog):
    """密码生成器对话框 - 增强版"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.generated_password = ''
        self.init_ui()
        self.setStyleSheet('''  
                QDialog {  
                    background-color: white;  
                }  
                QGroupBox {  
                    font-weight: bold;  
                    border: 2px solid #E0E0E0;  
                    border-radius: 6px;  
                    margin-top: 10px;  
                    padding-top: 10px;  
                }  
                QGroupBox::title {  
                    subcontrol-origin: margin;  
                    left: 10px;  
                    padding: 0 5px;  
                }  
            ''')

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle('密码生成器')
        self.setMinimumWidth(500)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # 标题
        title = QLabel(f'{ICONS["generate"]} 密码生成器')
        title.setStyleSheet('font-size: 18px; font-weight: bold; color: #212121;')
        layout.addWidget(title)

        # 生成的密码显示
        display_group = QGroupBox('生成的密码')
        display_layout = QVBoxLayout()

        self.password_display = QLineEdit()
        self.password_display.setReadOnly(True)
        self.password_display.setFont(QFont('Courier New', 14))
        self.password_display.setStyleSheet('''  
                QLineEdit {  
                    padding: 15px;  
                    font-weight: bold;  
                    background-color: #E3F2FD;  
                    border: 2px solid #2196F3;  
                    border-radius: 6px;  
                }  
            ''')
        display_layout.addWidget(self.password_display)

        # 强度显示
        self.strength_widget = PasswordStrengthWidget()
        display_layout.addWidget(self.strength_widget)

        display_group.setLayout(display_layout)
        layout.addWidget(display_group)

        # 生成模式
        mode_group = QGroupBox('生成模式')
        mode_layout = QVBoxLayout()

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(['随机密码', '易记密码', 'PIN码'])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo)

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # 随机密码选项
        self.random_options = QGroupBox('选项')
        options_layout = QVBoxLayout()

        # 长度滑块
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel('长度:'))
        self.length_slider = QSlider(Qt.Horizontal)
        self.length_slider.setMinimum(6)
        self.length_slider.setMaximum(64)
        self.length_slider.setValue(16)
        self.length_slider.valueChanged.connect(self.update_length_label)
        length_layout.addWidget(self.length_slider)
        self.length_label = QLabel('16')
        self.length_label.setStyleSheet('font-weight: bold; color: #2196F3;')
        length_layout.addWidget(self.length_label)
        options_layout.addLayout(length_layout)

        # 字符类型选择
        self.lowercase_cb = QCheckBox('小写字母 (a-z)')
        self.lowercase_cb.setChecked(True)
        options_layout.addWidget(self.lowercase_cb)

        self.uppercase_cb = QCheckBox('大写字母 (A-Z)')
        self.uppercase_cb.setChecked(True)
        options_layout.addWidget(self.uppercase_cb)

        self.digits_cb = QCheckBox('数字 (0-9)')
        self.digits_cb.setChecked(True)
        options_layout.addWidget(self.digits_cb)

        self.special_cb = QCheckBox('特殊字符 (!@#$%^&*...)')
        self.special_cb.setChecked(True)
        options_layout.addWidget(self.special_cb)

        self.exclude_ambiguous_cb = QCheckBox('排除易混淆字符 (0, O, l, 1, I)')
        self.exclude_ambiguous_cb.setChecked(True)
        options_layout.addWidget(self.exclude_ambiguous_cb)

        self.random_options.setLayout(options_layout)
        layout.addWidget(self.random_options)

        # 易记密码选项
        self.memorable_options = QGroupBox('选项')
        memorable_layout = QVBoxLayout()

        word_count_layout = QHBoxLayout()
        word_count_layout.addWidget(QLabel('单词数量:'))
        self.word_count_spin = QSpinBox()
        self.word_count_spin.setMinimum(2)
        self.word_count_spin.setMaximum(8)
        self.word_count_spin.setValue(4)
        word_count_layout.addWidget(self.word_count_spin)
        word_count_layout.addStretch()
        memorable_layout.addLayout(word_count_layout)

        self.memorable_options.setLayout(memorable_layout)
        self.memorable_options.setVisible(False)
        layout.addWidget(self.memorable_options)

        # PIN码选项
        self.pin_options = QGroupBox('选项')
        pin_layout = QVBoxLayout()

        pin_length_layout = QHBoxLayout()
        pin_length_layout.addWidget(QLabel('PIN长度:'))
        self.pin_length_spin = QSpinBox()
        self.pin_length_spin.setMinimum(4)
        self.pin_length_spin.setMaximum(12)
        self.pin_length_spin.setValue(6)
        pin_length_layout.addWidget(self.pin_length_spin)
        pin_length_layout.addStretch()
        pin_layout.addLayout(pin_length_layout)

        self.pin_options.setLayout(pin_layout)
        self.pin_options.setVisible(False)
        layout.addWidget(self.pin_options)

        layout.addStretch()

        # 按钮组
        btn_layout = QHBoxLayout()

        generate_btn = ModernButton(f'{ICONS["generate"]} 重新生成', primary=True)
        generate_btn.clicked.connect(self.generate)
        btn_layout.addWidget(generate_btn)

        copy_btn = ModernButton(f'{ICONS["copy"]} 复制')
        copy_btn.clicked.connect(self.copy_password)
        btn_layout.addWidget(copy_btn)

        use_btn = ModernButton(f'{ICONS["check"]} 使用此密码')
        use_btn.clicked.connect(self.accept)
        btn_layout.addWidget(use_btn)

        cancel_btn = ModernButton('取消')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # 自动生成第一个密码
        self.generate()

    def on_mode_changed(self):
        """模式改变"""
        mode = self.mode_combo.currentText()

        self.random_options.setVisible(mode == '随机密码')
        self.memorable_options.setVisible(mode == '易记密码')
        self.pin_options.setVisible(mode == 'PIN码')

        self.generate()

    def update_length_label(self):
        """更新长度标签"""
        self.length_label.setText(str(self.length_slider.value()))

    def generate(self):
        """生成密码"""
        mode = self.mode_combo.currentText()

        if mode == '随机密码':
            length = self.length_slider.value()
            password = PasswordGenerator.generate(
                length=length,
                use_lower=self.lowercase_cb.isChecked(),
                use_upper=self.uppercase_cb.isChecked(),
                use_digits=self.digits_cb.isChecked(),
                use_special=self.special_cb.isChecked(),
                exclude_ambiguous=self.exclude_ambiguous_cb.isChecked(),
                mode='random'
            )
        elif mode == '易记密码':
            num_words = self.word_count_spin.value()
            password = PasswordGenerator.generate_memorable(num_words)
        else:  # PIN码
            length = self.pin_length_spin.value()
            password = PasswordGenerator.generate_pin(length)

        self.password_display.setText(password)
        self.generated_password = password

        # 更新强度
        analysis = PasswordAnalyzer.analyze_strength(password)
        self.strength_widget.update_strength(analysis)

    def copy_password(self):
        """复制密码到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.generated_password)
        QMessageBox.information(self, '成功', '密码已复制到剪贴板')


class LoginDialog(QDialog):
    """登录/创建保险库对话框 - 增强版"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vault_path = None
        self.encryption_key = None
        self.init_ui()
        self.setStyleSheet('''  
                QDialog {  
                    background-color: #FAFAFA;  
                }  
            ''')

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f'{APP_NAME} - 登录')
        self.setMinimumWidth(500)

        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Logo和标题
        logo_layout = QVBoxLayout()
        logo_layout.setAlignment(Qt.AlignCenter)

        logo_label = QLabel(ICONS['password'])
        logo_label.setStyleSheet('font-size: 64px;')
        logo_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_label)

        title = QLabel(APP_NAME)
        title.setStyleSheet('font-size: 24px; font-weight: bold; color: #212121;')
        title.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(title)

        subtitle = QLabel(f'企业级密码管理工具 v{APP_VERSION}')
        subtitle.setStyleSheet('font-size: 13px; color: #757575;')
        subtitle.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(subtitle)

        layout.addLayout(logo_layout)

        # 表单区域
        form_widget = QWidget()
        form_widget.setStyleSheet('''  
                QWidget {  
                    background-color: white;  
                    border-radius: 8px;  
                }  
            ''')
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(15)

        # 保险库路径
        path_label = QLabel('保险库位置:')
        path_label.setStyleSheet('font-weight: bold; color: #212121;')
        form_layout.addWidget(path_label)

        path_input_layout = QHBoxLayout()
        self.vault_path_edit = QLineEdit()
        self.vault_path_edit.setPlaceholderText('选择保险库文件...')

        # 默认路径
        default_vault = str(Path.cwd() / '.securityvault' / 'vault.db')
        self.vault_path_edit.setText(default_vault)

        path_input_layout.addWidget(self.vault_path_edit)

        browse_btn = ModernButton(f'{ICONS["folder"]} 浏览')
        browse_btn.clicked.connect(self.browse_vault_file)
        path_input_layout.addWidget(browse_btn)

        form_layout.addLayout(path_input_layout)

        # 主密码
        pwd_label = QLabel('主密码:')
        pwd_label.setStyleSheet('font-weight: bold; color: #212121;')
        form_layout.addWidget(pwd_label)

        pwd_layout = QHBoxLayout()
        self.master_password_edit = QLineEdit()
        self.master_password_edit.setEchoMode(QLineEdit.Password)
        self.master_password_edit.setPlaceholderText('输入主密码')
        self.master_password_edit.returnPressed.connect(self.open_vault)
        pwd_layout.addWidget(self.master_password_edit)

        show_btn = ModernButton(ICONS['eye'])
        show_btn.setFixedWidth(50)
        show_btn.clicked.connect(self.toggle_master_password)
        pwd_layout.addWidget(show_btn)

        form_layout.addLayout(pwd_layout)

        # 提示
        tip = QLabel('💡 主密码用于加密您的所有数据，请务必牢记')
        tip.setStyleSheet('color: #FF9800; font-size: 12px;')
        tip.setWordWrap(True)
        form_layout.addWidget(tip)

        layout.addWidget(form_widget)

        # 按钮组
        btn_layout = QHBoxLayout()

        self.create_btn = ModernButton(f'{ICONS["add"]} 创建新保险库')
        self.create_btn.clicked.connect(self.create_vault)
        btn_layout.addWidget(self.create_btn)

        self.open_btn = ModernButton(f'{ICONS["unlock"]} 打开保险库', primary=True)
        self.open_btn.clicked.connect(self.open_vault)
        btn_layout.addWidget(self.open_btn)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def toggle_master_password(self):
        """切换主密码显示"""
        if self.master_password_edit.echoMode() == QLineEdit.Password:
            self.master_password_edit.setEchoMode(QLineEdit.Normal)
        else:
            self.master_password_edit.setEchoMode(QLineEdit.Password)

    def browse_vault_file(self):
        """浏览保险库文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, '选择保险库文件', str(Path.cwd()), 'Database Files (*.db)'
        )
        if file_path:
            self.vault_path_edit.setText(file_path)

    def create_vault(self):
        """创建新保险库"""
        vault_path = self.vault_path_edit.text().strip()
        master_password = self.master_password_edit.text()

        if not vault_path or not master_password:
            QMessageBox.warning(self, '错误', '请输入保险库路径和主密码')
            return

        if len(master_password) < 8:
            QMessageBox.warning(self, '错误', '主密码至少需要8个字符')
            return

            # 检查密码强度
        analysis = PasswordAnalyzer.analyze_strength(master_password)
        if analysis['score'] < 60:
            reply = QMessageBox.question(
                self, '密码强度较弱',
                f'您的主密码强度为: {analysis["strength"]} ({analysis["score"]}/100)\n\n'
                f'建议使用更强的密码。是否继续？',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

                # 确认密码
        confirm_password, ok = QInputDialog.getText(
            self, '确认密码', '请再次输入主密码:', QLineEdit.Password
        )

        if not ok or confirm_password != master_password:
            QMessageBox.warning(self, '错误', '密码不匹配')
            return

            # 检查文件是否存在
        if Path(vault_path).exists():
            reply = QMessageBox.question(
                self, '文件已存在',
                '保险库文件已存在，是否覆盖？',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        try:
            # 创建目录
            vault_dir = Path(vault_path).parent
            vault_dir.mkdir(parents=True, exist_ok=True)

            # 生成加密密钥
            salt = CryptoManager.generate_salt()
            key = CryptoManager.derive_key(master_password, salt)

            # 保存salt
            salt_file = Path(vault_path).with_suffix('.salt')
            with open(salt_file, 'wb') as f:
                f.write(salt)

                # 保存密码哈希用于快速验证
            pwd_hash_file = Path(vault_path).with_suffix('.hash')
            with open(pwd_hash_file, 'w') as f:
                f.write(CryptoManager.hash_password(master_password))

                # 创建数据库
            db = DatabaseManager(vault_path, key)
            db.close()

            self.vault_path = vault_path
            self.encryption_key = key

            QMessageBox.information(self, '成功', '保险库创建成功！')
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, '错误', f'创建保险库失败:\n{str(e)}')

    def open_vault(self):
        """打开保险库"""
        vault_path = self.vault_path_edit.text().strip()
        master_password = self.master_password_edit.text()

        if not vault_path or not master_password:
            QMessageBox.warning(self, '错误', '请输入保险库路径和主密码')
            return

        if not Path(vault_path).exists():
            QMessageBox.warning(self, '错误', '保险库文件不存在')
            return

        salt_file = Path(vault_path).with_suffix('.salt')
        if not salt_file.exists():
            QMessageBox.warning(self, '错误', '保险库配置文件损坏')
            return

        try:
            # 读取salt
            with open(salt_file, 'rb') as f:
                salt = f.read()

                # 快速验证（可选）
            pwd_hash_file = Path(vault_path).with_suffix('.hash')
            if pwd_hash_file.exists():
                with open(pwd_hash_file, 'r') as f:
                    stored_hash = f.read()
                    if CryptoManager.hash_password(master_password) != stored_hash:
                        QMessageBox.critical(self, '错误', '主密码错误')
                        return

                        # 派生密钥
            key = CryptoManager.derive_key(master_password, salt)

            # 尝试打开数据库并解密测试
            db = DatabaseManager(vault_path, key)
            passwords = db.get_all_passwords()
            db.close()

            self.vault_path = vault_path
            self.encryption_key = key

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法打开保险库:\n{str(e)}\n\n主密码可能错误')

            # ==================== 主窗口（完全重构）====================


class SecurityVaultPro(QMainWindow):
    """主窗口 - 完全重构版"""

    def __init__(self):
        super().__init__()
        self.db = None
        self.encryption_key = None
        self.vault_path = None
        self.passwords = []
        self.filtered_passwords = []
        self.current_filter = 'all'

        self.init_ui()
        self.apply_styles()
        self.show_login()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f'{APP_NAME} v{APP_VERSION}')
        self.setGeometry(100, 50, 1200, 800)

        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧边栏
        self.create_sidebar(main_layout)

        # 右侧内容区
        self.create_content_area(main_layout)

        # 状态栏
        self.statusBar().setStyleSheet('background-color: #FAFAFA; padding: 5px;')
        self.statusBar().showMessage('准备就绪')

        # 定时器
        self.totp_timer = QTimer()
        self.totp_timer.timeout.connect(self.update_totp_codes)
        self.totp_timer.start(1000)

        self.auto_lock_timer = QTimer()
        self.auto_lock_timer.timeout.connect(self.auto_lock)
        self.auto_lock_timer.start(300000)  # 5分钟自动锁定

        self.disable_ui()

    def create_sidebar(self, parent_layout):
        """创建侧边栏"""
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f'''  
                QWidget {{  
                    background-color: {COLORS['dark']};  
                    color: white;  
                }}  
            ''')

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Logo区域
        logo_widget = QWidget()
        logo_widget.setStyleSheet('padding: 20px;')
        logo_layout = QVBoxLayout(logo_widget)

        logo_label = QLabel(ICONS['password'])
        logo_label.setStyleSheet('font-size: 36px;')
        logo_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_label)

        app_name = QLabel(APP_NAME)
        app_name.setStyleSheet('font-size: 16px; font-weight: bold;')
        app_name.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(app_name)

        sidebar_layout.addWidget(logo_widget)

        # 搜索框
        search_container = QWidget()
        search_container.setStyleSheet('padding: 10px;')
        search_layout = QVBoxLayout(search_container)

        self.sidebar_search = QLineEdit()
        self.sidebar_search.setPlaceholderText(f'{ICONS["search"]} 搜索...')
        self.sidebar_search.setStyleSheet('''  
                QLineEdit {  
                    background-color: #424242;  
                    border: none;  
                    border-radius: 4px;  
                    padding: 8px;  
                    color: white;  
                }  
            ''')
        self.sidebar_search.textChanged.connect(self.on_search)
        search_layout.addWidget(self.sidebar_search)

        sidebar_layout.addWidget(search_container)

        # 导航菜单
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.NoFrame)
        nav_scroll.setStyleSheet('background-color: transparent; border: none;')

        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(2)

        # 导航项目
        nav_items = [
            ('all', ICONS['password'], '所有密码'),
            ('favorites', ICONS['favorite'], '收藏夹'),
            ('dashboard', ICONS['dashboard'], '仪表盘'),
            ('security', ICONS['security'], '安全审计'),
            ('generator', ICONS['generate'], '密码生成器'),
            ('2fa', ICONS['2fa'], '双因素认证'),
            ('history', ICONS['history'], '历史记录'),
            ('settings', ICONS['settings'], '设置'),
        ]

        self.nav_buttons = {}
        for key, icon, text in nav_items:
            btn = QPushButton(f'{icon}  {text}')
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self.switch_view(k))
            btn.setStyleSheet('''  
                    QPushButton {  
                        text-align: left;  
                        padding: 15px 20px;  
                        border: none;  
                        background-color: transparent;  
                        color: white;  
                        font-size: 14px;  
                    }  
                    QPushButton:hover {  
                        background-color: #424242;  
                    }  
                    QPushButton:checked {  
                        background-color: #2196F3;  
                        font-weight: bold;  
                    }  
                ''')
            nav_layout.addWidget(btn)
            self.nav_buttons[key] = btn

            # 默认选中
        self.nav_buttons['all'].setChecked(True)

        nav_layout.addStretch()
        nav_scroll.setWidget(nav_widget)
        sidebar_layout.addWidget(nav_scroll)

        # 底部统计
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet('''  
                padding: 15px;  
                background-color: #1976D2;  
                color: white;  
                font-size: 12px;  
            ''')
        self.stats_label.setWordWrap(True)
        sidebar_layout.addWidget(self.stats_label)

        parent_layout.addWidget(sidebar)

    def create_content_area(self, parent_layout):
        """创建内容区域"""
        content = QWidget()
        content.setStyleSheet('background-color: #FAFAFA;')
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 工具栏
        toolbar = self.create_toolbar()
        content_layout.addWidget(toolbar)

        # 堆叠窗口（不同视图）
        self.stacked_widget = QStackedWidget()

        # 1. 密码列表视图
        self.passwords_view = self.create_passwords_view()
        self.stacked_widget.addWidget(self.passwords_view)

        # 2. 仪表盘视图
        self.dashboard_view = self.create_dashboard_view()
        self.stacked_widget.addWidget(self.dashboard_view)

        # 3. 安全审计视图
        self.audit_view = self.create_audit_view()
        self.stacked_widget.addWidget(self.audit_view)

        # 4. 密码生成器视图
        self.generator_view = self.create_generator_view()
        self.stacked_widget.addWidget(self.generator_view)

        # 5. 2FA视图
        self.totp_view = self.create_totp_view()
        self.stacked_widget.addWidget(self.totp_view)

        # 6. 历史记录视图
        self.history_view = self.create_history_view()
        self.stacked_widget.addWidget(self.history_view)

        # 7. 设置视图
        self.settings_view = self.create_settings_view()
        self.stacked_widget.addWidget(self.settings_view)

        content_layout.addWidget(self.stacked_widget)

        parent_layout.addWidget(content, 1)

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QWidget()
        toolbar.setStyleSheet('''  
                QWidget {  
                    background-color: white;  
                    border-bottom: 1px solid #E0E0E0;  
                }  
            ''')
        toolbar.setFixedHeight(60)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(15, 5, 15, 5)

        # 左侧按钮
        self.add_btn = ModernButton(ICONS['add'], '添加', primary=True)
        self.add_btn.clicked.connect(self.add_password)
        layout.addWidget(self.add_btn)

        self.edit_btn = ModernButton(ICONS['edit'], '编辑')
        self.edit_btn.clicked.connect(self.edit_password)
        layout.addWidget(self.edit_btn)

        self.delete_btn = ModernButton(ICONS['delete'], '删除', danger=True)
        self.delete_btn.clicked.connect(self.delete_password)
        layout.addWidget(self.delete_btn)

        layout.addSpacing(20)

        self.export_btn = ModernButton(ICONS['export'], '导出')
        self.export_btn.clicked.connect(self.export_passwords)
        layout.addWidget(self.export_btn)

        self.import_btn = ModernButton(ICONS['import'], '导入')
        self.import_btn.clicked.connect(self.import_passwords)
        layout.addWidget(self.import_btn)

        layout.addStretch()

        # 右侧信息
        self.vault_label = QLabel()
        self.vault_label.setStyleSheet('color: #757575; font-size: 12px;')
        layout.addWidget(self.vault_label)

        layout.addSpacing(10)

        lock_btn = ModernButton(ICONS['lock'], '锁定')
        lock_btn.clicked.connect(self.lock_vault)
        layout.addWidget(lock_btn)

        return toolbar

    def create_passwords_view(self):
        """创建密码列表视图"""
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(15, 15, 15, 15)

        # 过滤和排序栏
        filter_layout = QHBoxLayout()

        filter_label = QLabel('分类:')
        filter_layout.addWidget(filter_label)

        self.category_filter = QComboBox()
        self.category_filter.addItems(['全部', '工作', '个人', '金融', '社交', '邮箱', '购物', '娱乐', '其他'])
        self.category_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.category_filter)

        filter_layout.addSpacing(20)

        sort_label = QLabel('排序:')
        filter_layout.addWidget(sort_label)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['最近修改', '标题', '创建时间', '强度'])
        self.sort_combo.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.sort_combo)

        filter_layout.addStretch()

        # 显示模式切换
        self.view_mode_btn = ModernButton('📋 列表')
        self.view_mode_btn.clicked.connect(self.toggle_view_mode)
        filter_layout.addWidget(self.view_mode_btn)

        layout.addLayout(filter_layout)

        # 密码表格
        self.password_table = QTableWidget()
        self.password_table.setColumnCount(7)
        self.password_table.setHorizontalHeaderLabels(['', '标题', '用户名', '密码', 'URL', '分类', '强度'])
        self.password_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.password_table.setSelectionMode(QTableWidget.SingleSelection)
        self.password_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.password_table.setAlternatingRowColors(True)
        self.password_table.verticalHeader().setVisible(False)
        self.password_table.doubleClicked.connect(self.copy_password)
        self.password_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.password_table.customContextMenuRequested.connect(self.show_context_menu)

        # 设置列宽
        header = self.password_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.password_table.setColumnWidth(0, 40)

        # 样式
        self.password_table.setStyleSheet('''  
                QTableWidget {  
                    background-color: white;  
                    border: 1px solid #E0E0E0;  
                    border-radius: 4px;  
                    gridline-color: #F5F5F5;  
                }  
                QTableWidget::item {  
                    padding: 8px;  
                }  
                QTableWidget::item:selected {  
                    background-color: #E3F2FD;  
                    color: black;  
                }  
                QHeaderView::section {  
                    background-color: #FAFAFA;  
                    padding: 10px;  
                    border: none;  
                    border-bottom: 2px solid #E0E0E0;  
                    font-weight: bold;  
                }  
            ''')

        layout.addWidget(self.password_table)

        # 底部统计
        self.count_label = QLabel()
        self.count_label.setStyleSheet('color: #757575; font-size: 12px; padding: 5px;')
        layout.addWidget(self.count_label)

        return view

    def create_dashboard_view(self):
        """创建仪表盘视图"""
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 标题
        title = QLabel(f'{ICONS["dashboard"]} 仪表盘')
        title.setStyleSheet('font-size: 24px; font-weight: bold; color: #212121;')
        layout.addWidget(title)

        # 统计卡片行
        cards_layout = QHBoxLayout()

        self.total_card = self.create_stat_card('总密码数', '0', COLORS['primary'])
        self.weak_card = self.create_stat_card('弱密码', '0', COLORS['warning'])
        self.reused_card = self.create_stat_card('重复密码', '0', COLORS['danger'])
        self.strong_card = self.create_stat_card('强密码', '0', COLORS['success'])

        cards_layout.addWidget(self.total_card)
        cards_layout.addWidget(self.weak_card)
        cards_layout.addWidget(self.reused_card)
        cards_layout.addWidget(self.strong_card)

        layout.addLayout(cards_layout)

        # 图表区域
        charts_layout = QHBoxLayout()

        # 分类分布
        category_group = QGroupBox('密码分类分布')
        category_layout = QVBoxLayout()
        self.category_chart = QListWidget()
        self.category_chart.setStyleSheet('''  
                QListWidget {  
                    background-color: white;  
                    border: 1px solid #E0E0E0;  
                    border-radius: 4px;  
                }  
            ''')
        category_layout.addWidget(self.category_chart)
        category_group.setLayout(category_layout)
        charts_layout.addWidget(category_group)

        # 强度分布
        strength_group = QGroupBox('密码强度分布')
        strength_layout = QVBoxLayout()
        self.strength_chart = QListWidget()
        self.strength_chart.setStyleSheet('''  
                QListWidget {  
                    background-color: white;  
                    border: 1px solid #E0E0E0;  
                    border-radius: 4px;  
                }  
            ''')
        strength_layout.addWidget(self.strength_chart)
        strength_group.setLayout(strength_layout)
        charts_layout.addWidget(strength_group)

        layout.addLayout(charts_layout)

        # 最近活动
        activity_group = QGroupBox('最近活动')
        activity_layout = QVBoxLayout()
        self.activity_list = QListWidget()
        self.activity_list.setStyleSheet('''  
                QListWidget {  
                    background-color: white;  
                    border: 1px solid #E0E0E0;  
                    border-radius: 4px;  
                }  
            ''')
        activity_layout.addWidget(self.activity_list)
        activity_group.setLayout(activity_layout)
        layout.addWidget(activity_group)

        return view

    def create_stat_card(self, title, value, color):
        """创建统计卡片"""
        card = QWidget()
        card.setStyleSheet(f'''  
                QWidget {{  
                    background-color: white;  
                    border-left: 4px solid {color};  
                    border-radius: 4px;  
                }}  
            ''')
        card.setMinimumHeight(100)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)

        title_label = QLabel(title)
        title_label.setStyleSheet('font-size: 12px; color: #757575;')
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(f'font-size: 32px; font-weight: bold; color: {color};')
        value_label.setObjectName('value_label')
        layout.addWidget(value_label)

        layout.addStretch()

        return card

    def create_audit_view(self):
        """创建安全审计视图"""
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题和按钮
        header_layout = QHBoxLayout()

        title = QLabel(f'{ICONS["security"]} 安全审计')
        title.setStyleSheet('font-size: 24px; font-weight: bold; color: #212121;')
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.audit_btn = ModernButton(f'{ICONS["security"]} 开始审计', primary=True)
        self.audit_btn.clicked.connect(self.run_security_audit)
        header_layout.addWidget(self.audit_btn)

        layout.addLayout(header_layout)

        # 进度条
        self.audit_progress = QProgressBar()
        self.audit_progress.setTextVisible(True)
        self.audit_progress.setStyleSheet(f'''  
                QProgressBar {{  
                    border: 1px solid #E0E0E0;  
                    border-radius: 4px;  
                    text-align: center;  
                    background-color: white;  
                }}  
                QProgressBar::chunk {{  
                    background-color: {COLORS['primary']};  
                    border-radius: 3px;  
                }}  
            ''')
        self.audit_progress.setVisible(False)
        layout.addWidget(self.audit_progress)

        self.audit_status = QLabel()
        self.audit_status.setStyleSheet('color: #757575; font-size: 12px; padding: 5px;')
        self.audit_status.setVisible(False)
        layout.addWidget(self.audit_status)

        # 审计结果
        self.audit_result = QTextEdit()
        self.audit_result.setReadOnly(True)
        self.audit_result.setStyleSheet('''  
                QTextEdit {  
                    background-color: white;  
                    border: 1px solid #E0E0E0;  
                    border-radius: 4px;  
                    padding: 15px;  
                }  
            ''')
        layout.addWidget(self.audit_result)

        return view

    def create_generator_view(self):
        """创建密码生成器视图"""
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel(f'{ICONS["generate"]} 密码生成器')
        title.setStyleSheet('font-size: 24px; font-weight: bold; color: #212121;')
        layout.addWidget(title)

        # 居中容器
        center_widget = QWidget()
        center_widget.setMaximumWidth(700)
        center_layout = QVBoxLayout(center_widget)

        # 生成的密码显示
        self.gen_display = QLineEdit()
        self.gen_display.setReadOnly(True)
        self.gen_display.setFont(QFont('Courier New', 18))
        self.gen_display.setAlignment(Qt.AlignCenter)
        self.gen_display.setStyleSheet('''  
                QLineEdit {  
                    padding: 20px;  
                    font-weight: bold;  
                    background-color: #E3F2FD;  
                    border: 2px solid #2196F3;  
                    border-radius: 8px;  
                }  
            ''')
        center_layout.addWidget(self.gen_display)

        # 强度显示
        self.gen_strength_widget = PasswordStrengthWidget()
        center_layout.addWidget(self.gen_strength_widget)

        # 按钮
        btn_layout = QHBoxLayout()

        gen_btn = ModernButton(f'{ICONS["generate"]} 生成新密码', primary=True)
        gen_btn.clicked.connect(self.quick_generate_password)
        btn_layout.addWidget(gen_btn)

        copy_btn = ModernButton(f'{ICONS["copy"]} 复制')
        copy_btn.clicked.connect(lambda: self.copy_to_clipboard(self.gen_display.text()))
        btn_layout.addWidget(copy_btn)

        advanced_btn = ModernButton('高级选项...')
        advanced_btn.clicked.connect(self.open_advanced_generator)
        btn_layout.addWidget(advanced_btn)

        center_layout.addLayout(btn_layout)

        # 居中显示
        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(center_widget)
        h_layout.addStretch()

        layout.addLayout(h_layout)
        layout.addStretch()

        return view

    def create_totp_view(self):
        """创建2FA视图"""
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        header_layout = QHBoxLayout()

        title = QLabel(f'{ICONS["2fa"]} 双因素认证')
        title.setStyleSheet('font-size: 24px; font-weight: bold; color: #212121;')
        header_layout.addWidget(title)

        header_layout.addStretch()

        # 剩余时间显示
        self.totp_countdown = QLabel()
        self.totp_countdown.setStyleSheet('''  
                font-size: 18px;  
                font-weight: bold;  
                color: #2196F3;  
                padding: 10px;  
                background-color: #E3F2FD;  
                border-radius: 4px;  
            ''')
        header_layout.addWidget(self.totp_countdown)

        layout.addLayout(header_layout)

        # 说明
        info = QLabel('双击TOTP代码可复制到剪贴板')
        info.setStyleSheet('color: #757575; font-size: 12px; padding: 5px;')
        layout.addWidget(info)

        # TOTP列表
        self.totp_table = QTableWidget()
        self.totp_table.setColumnCount(4)
        self.totp_table.setHorizontalHeaderLabels(['图标', '账户', 'TOTP代码', '剩余时间'])
        self.totp_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.totp_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.totp_table.setAlternatingRowColors(True)
        self.totp_table.verticalHeader().setVisible(False)
        self.totp_table.doubleClicked.connect(self.copy_totp_token)

        header = self.totp_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.totp_table.setColumnWidth(0, 50)

        self.totp_table.setStyleSheet('''  
                QTableWidget {  
                    background-color: white;  
                    border: 1px solid #E0E0E0;  
                    border-radius: 4px;  
                    gridline-color: #F5F5F5;  
                }  
                QTableWidget::item {  
                    padding: 12px;  
                }  
                QTableWidget::item:selected {  
                    background-color: #E3F2FD;  
                    color: black;  
                }  
                QHeaderView::section {  
                    background-color: #FAFAFA;  
                    padding: 12px;  
                    border: none;  
                    border-bottom: 2px solid #E0E0E0;  
                    font-weight: bold;  
                }  
            ''')

        layout.addWidget(self.totp_table)

        return view

    def create_history_view(self):
        """创建历史记录视图"""
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel(f'{ICONS["history"]} 操作历史')
        title.setStyleSheet('font-size: 24px; font-weight: bold; color: #212121;')
        layout.addWidget(title)

        # 历史列表
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(['时间', '操作', '密码ID', '详情'])
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.verticalHeader().setVisible(False)

        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        self.history_table.setStyleSheet('''  
                QTableWidget {  
                    background-color: white;  
                    border: 1px solid #E0E0E0;  
                    border-radius: 4px;  
                    gridline-color: #F5F5F5;  
                }  
                QTableWidget::item {  
                    padding: 10px;  
                }  
                QHeaderView::section {  
                    background-color: #FAFAFA;  
                    padding: 10px;  
                    border: none;  
                    border-bottom: 2px solid #E0E0E0;  
                    font-weight: bold;  
                }  
            ''')

        layout.addWidget(self.history_table)

        # 刷新按钮
        refresh_btn = ModernButton('🔄 刷新', primary=True)
        refresh_btn.clicked.connect(self.load_history)
        layout.addWidget(refresh_btn)

        return view

    def create_settings_view(self):
        """创建设置视图"""
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel(f'{ICONS["settings"]} 设置')
        title.setStyleSheet('font-size: 24px; font-weight: bold; color: #212121;')
        layout.addWidget(title)

        # 设置选项
        settings_group = QGroupBox('常规设置')
        settings_layout = QVBoxLayout()

        # 自动锁定
        auto_lock_layout = QHBoxLayout()
        auto_lock_layout.addWidget(QLabel('自动锁定时间:'))
        self.auto_lock_spin = QSpinBox()
        self.auto_lock_spin.setRange(1, 60)
        self.auto_lock_spin.setValue(5)
        self.auto_lock_spin.setSuffix(' 分钟')
        auto_lock_layout.addWidget(self.auto_lock_spin)
        auto_lock_layout.addStretch()
        settings_layout.addLayout(auto_lock_layout)

        # 剪贴板清除
        clipboard_layout = QHBoxLayout()
        self.clipboard_check = QCheckBox('复制后自动清除剪贴板')
        self.clipboard_check.setChecked(True)
        clipboard_layout.addWidget(self.clipboard_check)
        clipboard_layout.addStretch()
        settings_layout.addLayout(clipboard_layout)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # 安全选项
        security_group = QGroupBox('安全选项')
        security_layout = QVBoxLayout()

        change_pwd_btn = ModernButton('更改主密码')
        change_pwd_btn.clicked.connect(self.change_master_password)
        security_layout.addWidget(change_pwd_btn)

        backup_btn = ModernButton('备份保险库')
        backup_btn.clicked.connect(self.backup_vault)
        security_layout.addWidget(backup_btn)

        security_group.setLayout(security_layout)
        layout.addWidget(security_group)

        # 关于
        about_group = QGroupBox('关于')
        about_layout = QVBoxLayout()

        about_text = QLabel(f'''  
                <b>{APP_NAME}</b> v{APP_VERSION}<br>  
                企业级密码管理和安全审计工具<br><br>  
                <b>特性:</b><br>  
                • AES-256加密<br>  
                • 密码强度分析<br>  
                • 安全审计<br>  
                • 双因素认证<br>  
                • 密码生成器<br><br>  
                © 2024 All rights reserved.  
            ''')
        about_text.setWordWrap(True)
        about_layout.addWidget(about_text)

        about_group.setLayout(about_layout)
        layout.addWidget(about_group)

        layout.addStretch()

        return view

    def apply_styles(self):
        """应用全局样式"""
        self.setStyleSheet(f'''  
                QMainWindow {{  
                    background-color: #FAFAFA;  
                }}  
                QGroupBox {{  
                    font-weight: bold;  
                    border: 1px solid #E0E0E0;  
                    border-radius: 6px;  
                    margin-top: 10px;  
                    padding-top: 10px;  
                    background-color: white;  
                }}  
                QGroupBox::title {{  
                    subcontrol-origin: margin;  
                    left: 10px;  
                    padding: 0 5px;  
                }}  
            ''')

    def show_login(self):
        """显示登录对话框"""
        dialog = LoginDialog(self)
        if dialog.exec_():
            self.vault_path = dialog.vault_path
            self.encryption_key = dialog.encryption_key
            self.db = DatabaseManager(self.vault_path, self.encryption_key)
            self.enable_ui()
            self.load_passwords()
            self.update_stats()
            self.load_history()
            self.vault_label.setText(f'{ICONS["lock"]} {Path(self.vault_path).name}')
            self.statusBar().showMessage('保险库已打开')
        else:
            QApplication.quit()

    def enable_ui(self):
        """启用UI"""
        self.add_btn.setEnabled(True)
        self.edit_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.import_btn.setEnabled(True)

        for btn in self.nav_buttons.values():
            btn.setEnabled(True)

    def disable_ui(self):
        """禁用UI"""
        self.add_btn.setEnabled(False)
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.import_btn.setEnabled(False)

        for btn in self.nav_buttons.values():
            btn.setEnabled(False)

    def switch_view(self, view_name):
        """切换视图"""
        # 取消其他按钮选中状态
        for key, btn in self.nav_buttons.items():
            if key != view_name:
                btn.setChecked(False)

        self.current_filter = view_name

        # 切换堆叠窗口
        view_index = {
            'all': 0,
            'favorites': 0,
            'dashboard': 1,
            'security': 2,
            'generator': 3,
            '2fa': 4,
            'history': 5,
            'settings': 6
        }

        self.stacked_widget.setCurrentIndex(view_index.get(view_name, 0))

        # 特殊处理
        if view_name in ['all', 'favorites']:
            self.apply_filters()
        elif view_name == 'dashboard':
            self.update_dashboard()
        elif view_name == 'generator':
            self.quick_generate_password()
        elif view_name == '2fa':
            self.update_totp_codes()
        elif view_name == 'history':
            self.load_history()

    def load_passwords(self):
        """加载密码列表"""
        if not self.db:
            return

        try:
            self.passwords = self.db.get_all_passwords()
            self.apply_filters()
            self.update_stats()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'加载密码失败:\n{str(e)}')

    def apply_filters(self):
        """应用过滤和排序"""
        # 过滤
        if self.current_filter == 'favorites':
            filtered = [p for p in self.passwords if p['is_favorite']]
        else:
            filtered = self.passwords.copy()

            # 分类过滤
        if hasattr(self, 'category_filter'):
            category = self.category_filter.currentText()
            if category and category != '全部':
                filtered = [p for p in filtered if p['category'] == category]

                # 搜索过滤
        search_text = self.sidebar_search.text().lower()
        if search_text:
            filtered = [p for p in filtered if
                        search_text in p['title'].lower() or
                        search_text in p['username'].lower() or
                        search_text in p['url'].lower() or
                        search_text in p['notes'].lower()]

            # 排序
        if hasattr(self, 'sort_combo'):
            sort_by = self.sort_combo.currentText()
            if sort_by == '最近修改':
                filtered.sort(key=lambda x: x['modified_at'], reverse=True)
            elif sort_by == '标题':
                filtered.sort(key=lambda x: x['title'].lower())
            elif sort_by == '创建时间':
                filtered.sort(key=lambda x: x['created_at'], reverse=True)
            elif sort_by == '强度':
                filtered.sort(key=lambda x: x['strength_score'], reverse=True)

        self.filtered_passwords = filtered
        self.display_passwords(filtered)

    def display_passwords(self, passwords: List[Dict]):
        """显示密码列表"""
        self.password_table.setRowCount(len(passwords))

        for i, pwd in enumerate(passwords):
            # 图标/收藏
            icon_item = QTableWidgetItem(pwd.get('icon', '') or ICONS['password'])
            if pwd['is_favorite']:
                icon_item.setText(ICONS['favorite'])
            icon_item.setTextAlignment(Qt.AlignCenter)
            icon_item.setFont(QFont('', 16))
            self.password_table.setItem(i, 0, icon_item)

            # 标题
            title_item = QTableWidgetItem(pwd['title'])
            title_item.setFont(QFont('', 10, QFont.Bold))
            self.password_table.setItem(i, 1, title_item)

            # 用户名
            self.password_table.setItem(i, 2, QTableWidgetItem(pwd['username']))

            # 密码（隐藏）
            pwd_item = QTableWidgetItem('●' * 12)
            pwd_item.setForeground(QColor(COLORS['primary']))
            self.password_table.setItem(i, 3, pwd_item)

            # URL
            self.password_table.setItem(i, 4, QTableWidgetItem(pwd['url']))

            # 分类
            cat_item = QTableWidgetItem(pwd['category'])
            cat_item.setForeground(QColor(COLORS['primary']))
            self.password_table.setItem(i, 5, cat_item)

            # 强度
            score = pwd['strength_score']
            if score >= 80:
                color = COLORS['success']
                strength = '强'
            elif score >= 60:
                color = COLORS['primary']
                strength = '中'
            else:
                color = COLORS['danger']
                strength = '弱'

            strength_item = QTableWidgetItem(strength)
            strength_item.setForeground(QColor(color))
            strength_item.setFont(QFont('', 9, QFont.Bold))
            strength_item.setTextAlignment(Qt.AlignCenter)
            self.password_table.setItem(i, 6, strength_item)

            # 行高
            self.password_table.setRowHeight(i, 45)

        # 更新计数
        self.count_label.setText(f'显示 {len(passwords)} 条密码')

    def on_search(self):
        """搜索响应"""
        self.apply_filters()

    def add_password(self):
        """添加密码"""
        if not self.db:
            return

        dialog = PasswordDialog(self, db=self.db)
        if dialog.exec_():
            data = dialog.get_data()

            if not data['title']:
                QMessageBox.warning(self, '错误', '标题不能为空')
                return

            if not data['password']:
                QMessageBox.warning(self, '错误', '密码不能为空')
                return

            try:
                self.db.add_password(**data)
                self.load_passwords()
                self.statusBar().showMessage('密码已添加', 3000)
                QMessageBox.information(self, '成功', '密码已成功添加到保险库')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'添加密码失败:\n{str(e)}')

    def edit_password(self):
        """编辑密码"""
        if not self.db:
            return

        selected = self.password_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, '提示', '请先选择一个密码条目')
            return

        pwd = self.filtered_passwords[selected]

        dialog = PasswordDialog(self, password_data=pwd, db=self.db)
        if dialog.exec_():
            data = dialog.get_data()

            try:
                self.db.update_password(pwd['id'], **data)
                self.load_passwords()
                self.statusBar().showMessage('密码已更新', 3000)
                QMessageBox.information(self, '成功', '密码已成功更新')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'更新密码失败:\n{str(e)}')

    def delete_password(self):
        """删除密码"""
        if not self.db:
            return

        selected = self.password_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, '提示', '请先选择一个密码条目')
            return

        pwd = self.filtered_passwords[selected]

        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除密码条目 "{pwd["title"]}" 吗？\n\n此操作不可恢复！',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.delete_password(pwd['id'])
                self.load_passwords()
                self.statusBar().showMessage('密码已删除', 3000)
                QMessageBox.information(self, '成功', '密码已成功删除')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'删除密码失败:\n{str(e)}')

    def copy_password(self):
        """复制密码到剪贴板"""
        selected = self.password_table.currentRow()
        if selected < 0:
            return

        pwd = self.filtered_passwords[selected]

        # 标记为已使用
        if self.db:
            self.db.mark_as_used(pwd['id'])

        # 复制到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(pwd['password'])

        self.statusBar().showMessage(f'密码已复制: {pwd["title"]}', 5000)

        # 自动清除剪贴板（30秒后）
        if hasattr(self, 'clipboard_check') and self.clipboard_check.isChecked():
            QTimer.singleShot(30000, lambda: clipboard.clear())

    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.statusBar().showMessage('已复制到剪贴板', 3000)

    def show_context_menu(self, position):
        """显示右键菜单"""
        selected = self.password_table.currentRow()
        if selected < 0:
            return

        pwd = self.filtered_passwords[selected]

        menu = QMenu()
        menu.setStyleSheet('''
            QMenu {
                background-color: white;
                border: 1px solid #E0E0E0;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
            }
            QMenu::item:selected {
                background-color: #E3F2FD;
            }
        ''')

        copy_pwd = menu.addAction(f'{ICONS["copy"]} 复制密码')
        copy_user = menu.addAction(f'{ICONS["copy"]} 复制用户名')
        copy_url = menu.addAction(f'{ICONS["copy"]} 复制URL')

        menu.addSeparator()

        toggle_fav = menu.addAction(
            f'{ICONS["favorite"]} 取消收藏' if pwd['is_favorite'] else f'{ICONS["favorite"]} 添加到收藏'
        )

        menu.addSeparator()

        edit_action = menu.addAction(f'{ICONS["edit"]} 编辑')
        delete_action = menu.addAction(f'{ICONS["delete"]} 删除')

        action = menu.exec_(self.password_table.mapToGlobal(position))

        if action == copy_pwd:
            self.copy_password()
        elif action == copy_user:
            self.copy_to_clipboard(pwd['username'])
        elif action == copy_url:
            self.copy_to_clipboard(pwd['url'])
        elif action == toggle_fav:
            self.db.toggle_favorite(pwd['id'])
            self.load_passwords()
        elif action == edit_action:
            self.edit_password()
        elif action == delete_action:
            self.delete_password()

    def toggle_view_mode(self):
        """切换视图模式"""
        # 简化版：仅更改图标
        if '列表' in self.view_mode_btn.text():
            self.view_mode_btn.setText('🔲 网格')
        else:
            self.view_mode_btn.setText('📋 列表')

    def export_passwords(self):
        """导出密码"""
        if not self.db:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, '导出密码', str(Path.cwd()), 'CSV文件 (*.csv);;所有文件 (*)'
        )

        if file_path:
            try:
                if self.db.export_to_csv(file_path):
                    QMessageBox.information(self, '成功', f'密码已导出到:\n{file_path}')
                else:
                    QMessageBox.warning(self, '失败', '导出失败')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'导出失败:\n{str(e)}')

    def import_passwords(self):
        """导入密码"""
        if not self.db:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, '导入密码', str(Path.cwd()), 'CSV文件 (*.csv);;所有文件 (*)'
        )

        if file_path:
            reply = QMessageBox.question(
                self, '确认导入',
                '导入操作将添加CSV文件中的所有密码到保险库。\n\n是否继续？',
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                try:
                    count = self.db.import_from_csv(file_path)
                    self.load_passwords()
                    QMessageBox.information(self, '成功', f'成功导入 {count} 条密码')
                except Exception as e:
                    QMessageBox.critical(self, '错误', f'导入失败:\n{str(e)}')

    def update_stats(self):
        """更新统计信息"""
        if not self.db:
            return

        stats = self.db.get_statistics()

        # 侧边栏统计
        self.stats_label.setText(
            f'📊 统计\n'
            f'总计: {stats["total"]}\n'
            f'收藏: {stats["favorites"]}\n'
            f'强密码: {stats["strength"]["strong"]}\n'
            f'弱密码: {stats["strength"]["weak"]}'
        )

        # 仪表盘统计卡片
        self.total_card.findChild(QLabel, 'value_label').setText(str(stats['total']))
        self.weak_card.findChild(QLabel, 'value_label').setText(str(stats['strength']['weak']))
        self.reused_card.findChild(QLabel, 'value_label').setText('0')  # 需要审计获取
        self.strong_card.findChild(QLabel, 'value_label').setText(str(stats['strength']['strong']))

    def update_dashboard(self):
        """更新仪表盘"""
        if not self.db:
            return

        stats = self.db.get_statistics()

        # 分类图表
        self.category_chart.clear()
        for category, count in stats['by_category'].items():
            if category:
                item = QListWidgetItem(f'{category}: {count}')
                self.category_chart.addItem(item)

        # 强度图表
        self.strength_chart.clear()
        self.strength_chart.addItem(f'强密码: {stats["strength"]["strong"]}')
        self.strength_chart.addItem(f'中等密码: {stats["strength"]["medium"]}')
        self.strength_chart.addItem(f'弱密码: {stats["strength"]["weak"]}')

        # 最近活动
        self.activity_list.clear()
        logs = self.db.get_audit_logs(10)
        for log in logs:
            try:
                dt = datetime.fromisoformat(log['timestamp'])
                time_str = dt.strftime('%Y-%m-%d %H:%M')
                item_text = f'{time_str} - {log["action"]}: {log["details"]}'
                self.activity_list.addItem(item_text)
            except:
                pass

    def run_security_audit(self):
        """运行安全审计"""
        if not self.passwords:
            QMessageBox.information(self, '提示', '没有密码可供审计')
            return

        self.audit_btn.setEnabled(False)
        self.audit_progress.setVisible(True)
        self.audit_status.setVisible(True)
        self.audit_result.clear()

        # 创建审计线程
        self.audit_thread = SecurityAuditThread(self.passwords)
        self.audit_thread.progress.connect(self.on_audit_progress)
        self.audit_thread.result.connect(self.on_audit_complete)
        self.audit_thread.start()

    def on_audit_progress(self, value, message):
        """审计进度更新"""
        self.audit_progress.setValue(value)
        self.audit_status.setText(message)

    def on_audit_complete(self, result):
        """审计完成"""
        self.audit_btn.setEnabled(True)
        self.audit_progress.setVisible(False)
        self.audit_status.setVisible(False)

        # 显示结果
        html = f'''
        <html>
        <head>
            <style>
                body {{ font-family: Arial; font-size: 13px; }}
                h2 {{ color: #2196F3; }}
                h3 {{ color: #757575; margin-top: 20px; }}
                .score {{ font-size: 48px; font-weight: bold; }}
                .excellent {{ color: #4CAF50; }}
                .good {{ color: #8BC34A; }}
                .average {{ color: #FF9800; }}
                .poor {{ color: #F44336; }}
                .issue {{ background-color: #FFEBEE; padding: 10px; margin: 5px 0; border-left: 4px solid #F44336; }}
                .warning {{ background-color: #FFF3E0; padding: 10px; margin: 5px 0; border-left: 4px solid #FF9800; }}
                ul {{ margin: 5px 0; padding-left: 20px; }}
            </style>
        </head>
        <body>
        '''

        # 健康度分数
        score = result['health_score']
        if score >= 90:
            score_class = 'excellent'
            score_text = '优秀'
        elif score >= 75:
            score_class = 'good'
            score_text = '良好'
        elif score >= 50:
            score_class = 'average'
            score_text = '一般'
        else:
            score_class = 'poor'
            score_text = '较差'

        html += f'''
        <h2>{ICONS["security"]} 安全审计报告</h2>
        <p>审计时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>总密码数: {result['total_count']}</p>
        
        <h2>安全健康度</h2>
        <div class="score {score_class}">{score}/100</div>
        <p>评级: <b>{score_text}</b></p>
        '''

        # 弱密码
        if result['weak_passwords']:
            html += f'''
            <h3>{ICONS["warning"]} 弱密码 ({len(result["weak_passwords"])})</h3>
            <p>以下密码强度不足，建议立即更换:</p>
            '''
            for pwd in result['weak_passwords'][:10]:
                html += f'''
                <div class="issue">
                    <b>{pwd['title']}</b> - 强度: {pwd['strength']} ({pwd['score']}/100)<br>
                    问题: {', '.join(pwd['issues'])}
                </div>
                '''
            if len(result['weak_passwords']) > 10:
                html += f'<p>...还有 {len(result["weak_passwords"]) - 10} 个弱密码</p>'
        else:
            html += f'<h3>{ICONS["check"]} 弱密码</h3><p>未发现弱密码 ✓</p>'

        # 重用密码
        if result['reused_passwords']:
            html += f'''
            <h3>{ICONS["warning"]} 重复使用的密码 ({len(result["reused_passwords"])})</h3>
            <p>以下密码被多个账户使用，存在安全风险:</p>
            '''
            for item in result['reused_passwords'][:10]:
                html += f'''
                <div class="warning">
                    使用次数: {item['count']}<br>
                    账户: {', '.join(item['titles'])}
                </div>
                '''
        else:
            html += f'<h3>{ICONS["check"]} 密码重用</h3><p>未发现重复使用的密码 ✓</p>'

        # 旧密码
        if result['old_passwords']:
            html += f'''
            <h3>{ICONS["clock"]} 陈旧密码 ({len(result["old_passwords"])})</h3>
            <p>以下密码超过90天未更新:</p>
            <ul>
            '''
            for pwd in result['old_passwords'][:10]:
                html += f'<li>{pwd["title"]} ({pwd["age_days"]}天)</li>'
            html += '</ul>'
        else:
            html += f'<h3>{ICONS["check"]} 密码时效</h3><p>所有密码都较新 ✓</p>'

        # 即将过期
        if result['expiring_passwords']:
            html += f'''
            <h3>{ICONS["warning"]} 即将过期的密码 ({len(result["expiring_passwords"])})</h3>
            <ul>
            '''
            for pwd in result['expiring_passwords']:
                if pwd.get('expired'):
                    html += f'<li>{pwd["title"]} - 已过期 {pwd["days_ago"]}天</li>'
                else:
                    html += f'<li>{pwd["title"]} - 还有 {pwd["days_left"]}天过期</li>'
            html += '</ul>'

        # 缺少2FA
        if result['no_2fa']:
            html += f'''
            <h3>{ICONS["2fa"]} 未启用2FA ({len(result["no_2fa"])})</h3>
            <p>建议为以下重要账户启用双因素认证:</p>
            <ul>
            '''
            for pwd in result['no_2fa']:
                html += f'<li>{pwd["title"]}</li>'
            html += '</ul>'

        # 建议
        html += '''
        <h3>安全建议</h3>
        <ul>
            <li>立即更换所有弱密码</li>
            <li>为每个账户使用唯一的密码</li>
            <li>定期更新密码（建议90天）</li>
            <li>为重要账户启用双因素认证</li>
            <li>使用密码生成器创建强密码</li>
        </ul>
        </body>
        </html>
        '''

        self.audit_result.setHtml(html)

        # 更新重用密码计数
        self.reused_card.findChild(QLabel, 'value_label').setText(str(len(result['reused_passwords'])))

    def quick_generate_password(self):
        """快速生成密码"""
        password = PasswordGenerator.generate(length=16)
        self.gen_display.setText(password)

        analysis = PasswordAnalyzer.analyze_strength(password)
        self.gen_strength_widget.update_strength(analysis)

    def open_advanced_generator(self):
        """打开高级密码生成器"""
        dialog = PasswordGeneratorDialog(self)
        if dialog.exec_():
            self.gen_display.setText(dialog.generated_password)
            analysis = PasswordAnalyzer.analyze_strength(dialog.generated_password)
            self.gen_strength_widget.update_strength(analysis)

    def update_totp_codes(self):
        """更新TOTP代码"""
        if self.stacked_widget.currentIndex() != 4:  # 不在2FA视图则跳过
            return

        # 更新倒计时
        remaining = TOTPManager.get_remaining_time()
        self.totp_countdown.setText(f'{ICONS["clock"]} {remaining}秒')

        # 获取有TOTP的密码
        totp_passwords = [p for p in self.passwords if p.get('totp_secret')]

        self.totp_table.setRowCount(len(totp_passwords))

        for i, pwd in enumerate(totp_passwords):
            # 图标
            icon_item = QTableWidgetItem(pwd.get('icon', '') or ICONS['password'])
            icon_item.setTextAlignment(Qt.AlignCenter)
            icon_item.setFont(QFont('', 16))
            self.totp_table.setItem(i, 0, icon_item)

            # 账户
            account = f"{pwd['title']}\n{pwd['username']}"
            account_item = QTableWidgetItem(account)
            self.totp_table.setItem(i, 1, account_item)

            # TOTP代码
            token = TOTPManager.get_totp_token(pwd['totp_secret'])
            token_item = QTableWidgetItem(token)
            token_item.setFont(QFont('Courier New', 18, QFont.Bold))
            token_item.setForeground(QColor(COLORS['primary']))
            token_item.setTextAlignment(Qt.AlignCenter)
            self.totp_table.setItem(i, 2, token_item)

            # 剩余时间
            remaining_item = QTableWidgetItem(f'{remaining}s')
            remaining_item.setTextAlignment(Qt.AlignCenter)
            self.totp_table.setItem(i, 3, remaining_item)

            self.totp_table.setRowHeight(i, 60)

    def copy_totp_token(self):
        """复制TOTP令牌"""
        selected = self.totp_table.currentRow()
        if selected < 0:
            return

        token_item = self.totp_table.item(selected, 2)
        if token_item:
            token = token_item.text()
            clipboard = QApplication.clipboard()
            clipboard.setText(token)
            self.statusBar().showMessage(f'TOTP代码已复制: {token}', 5000)

    def load_history(self):
        """加载历史记录"""
        if not self.db:
            return

        logs = self.db.get_audit_logs(100)

        self.history_table.setRowCount(len(logs))

        for i, log in enumerate(logs):
            try:
                dt = datetime.fromisoformat(log['timestamp'])
                time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                time_str = log['timestamp']

            self.history_table.setItem(i, 0, QTableWidgetItem(time_str))
            self.history_table.setItem(i, 1, QTableWidgetItem(log['action']))
            self.history_table.setItem(i, 2, QTableWidgetItem(str(log.get('password_id', ''))))
            self.history_table.setItem(i, 3, QTableWidgetItem(log.get('details', '')))

    def change_master_password(self):
        """更改主密码"""
        if not self.db or not self.vault_path:
            return

        # 输入当前密码
        old_password, ok = QInputDialog.getText(
            self, '更改主密码', '请输入当前主密码:', QLineEdit.Password
        )

        if not ok or not old_password:
            return

        # 验证当前密码
        salt_file = Path(self.vault_path).with_suffix('.salt')
        pwd_hash_file = Path(self.vault_path).with_suffix('.hash')

        if pwd_hash_file.exists():
            with open(pwd_hash_file, 'r') as f:
                stored_hash = f.read()
                if CryptoManager.hash_password(old_password) != stored_hash:
                    QMessageBox.critical(self, '错误', '当前密码错误')
                    return

        # 输入新密码
        new_password, ok = QInputDialog.getText(
            self, '更改主密码', '请输入新主密码:', QLineEdit.Password
        )

        if not ok or not new_password:
            return

        if len(new_password) < 8:
            QMessageBox.warning(self, '错误', '新密码至少需要8个字符')
            return

        # 确认新密码
        confirm_password, ok = QInputDialog.getText(
            self, '更改主密码', '请再次输入新主密码:', QLineEdit.Password
        )

        if not ok or confirm_password != new_password:
            QMessageBox.warning(self, '错误', '密码不匹配')
            return

        try:
            # 读取旧salt
            with open(salt_file, 'rb') as f:
                old_salt = f.read()

            # 派生旧密钥
            old_key = CryptoManager.derive_key(old_password, old_salt)

            # 生成新salt和密钥
            new_salt = CryptoManager.generate_salt()
            new_key = CryptoManager.derive_key(new_password, new_salt)

            # 重新加密所有数据
            passwords = self.db.get_all_passwords()

            # 关闭当前数据库
            self.db.close()

            # 重新打开并更新
            self.db = DatabaseManager(self.vault_path, new_key)

            for pwd in passwords:
                self.db.update_password(
                    pwd['id'],
                    password=pwd['password'],
                    notes=pwd['notes'],
                    totp_secret=pwd['totp_secret']
                )

            # 保存新salt和哈希
            with open(salt_file, 'wb') as f:
                f.write(new_salt)

            with open(pwd_hash_file, 'w') as f:
                f.write(CryptoManager.hash_password(new_password))

            self.encryption_key = new_key

            QMessageBox.information(self, '成功', '主密码已成功更改')

        except Exception as e:
            QMessageBox.critical(self, '错误', f'更改主密码失败:\n{str(e)}')

    def backup_vault(self):
        """备份保险库"""
        if not self.vault_path:
            return

        backup_path, _ = QFileDialog.getSaveFileName(
            self, '备份保险库',
            str(Path.cwd() / f'vault_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'),
            'Database Files (*.db)'
        )

        if backup_path:
            try:
                import shutil

                # 复制数据库文件
                shutil.copy2(self.vault_path, backup_path)

                # 复制salt文件
                salt_file = Path(self.vault_path).with_suffix('.salt')
                if salt_file.exists():
                    shutil.copy2(salt_file, Path(backup_path).with_suffix('.salt'))

                # 复制哈希文件
                hash_file = Path(self.vault_path).with_suffix('.hash')
                if hash_file.exists():
                    shutil.copy2(hash_file, Path(backup_path).with_suffix('.hash'))

                QMessageBox.information(self, '成功', f'保险库已备份到:\n{backup_path}')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'备份失败:\n{str(e)}')

    def lock_vault(self):
        """锁定保险库"""
        reply = QMessageBox.question(
            self, '锁定保险库',
            '确定要锁定保险库吗？',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.db:
                self.db.close()
                self.db = None

            self.passwords = []
            self.filtered_passwords = []
            self.password_table.setRowCount(0)
            self.disable_ui()
            self.vault_label.setText('')
            self.statusBar().showMessage('保险库已锁定')

            # 重新显示登录
            self.show_login()

    def auto_lock(self):
        """自动锁定"""
        if self.db:
            self.lock_vault()

    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(
            self, '退出',
            '确定要退出吗？',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.db:
                self.db.close()
            event.accept()
        else:
            event.ignore()


# ==================== 主程序入口 ====================
def main():
    """主程序入口"""
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("SecurityVault")

    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    # 设置应用样式
    app.setStyle('Fusion')

    # 创建主窗口
    window = SecurityVaultPro()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()