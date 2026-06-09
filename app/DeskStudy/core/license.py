"""
许可证管理模块
支持按期限授权: 1天、1个月、半年、1年
增加多重安全防护措施
"""

import hashlib
import base64
import json
import os
import uuid
import platform
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import threading
import time

from app.DeskStudy.utils.logger import get_logger

logger = get_logger(__name__)

# ==================== 安全配置 ====================
# 注意：生产环境应该将密钥混淆或使用外部加密
_SECRET_PART_1 = "D3sk"
_SECRET_PART_2 = "St8dy"
_SECRET_PART_3 = "2026"
SECRET_KEY = _SECRET_PART_1 + _SECRET_PART_2 + _SECRET_PART_3

LICENSE_TYPES = {
    "trial": {"name": "试用版", "days": 1},
    "weekly": {"name": "周卡", "days": 7},
    "monthly": {"name": "月卡", "days": 30},
    "half_year": {"name": "半年卡", "days": 180},
    "yearly": {"name": "年卡", "days": 365},
}

LICENSE_DIR = Path.home() / ".deskstudy"
LICENSE_FILE = LICENSE_DIR / "license.dat"
TIME_RECORD_FILE = LICENSE_DIR / ".syscache"  # 隐藏时间记录


def _get_cpu_id() -> str:
    """获取CPU ID (Windows)"""
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                "wmic cpu get processorid",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                return lines[1].strip()
    except Exception:
        pass
    return "unknown"


def _get_disk_serial() -> str:
    """获取硬盘序列号 (Windows)"""
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                "wmic diskdrive get serialnumber",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                return lines[1].strip()
    except Exception:
        pass
    return "unknown"


def _get_machine_id() -> str:
    """
    获取机器唯一标识（多因素）
    结合：MAC地址 + CPU ID + 硬盘序列号 + 主机名
    """
    try:
        # 获取多个硬件标识
        mac = uuid.getnode()
        machine_name = os.environ.get("COMPUTERNAME", os.environ.get("HOSTNAME", "unknown"))
        cpu_id = _get_cpu_id()
        disk_serial = _get_disk_serial()

        # 组合多个因素
        raw = f"{mac}|{cpu_id}|{disk_serial}|{machine_name}|DeskStudy"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]
    except Exception:
        return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:32]


def _xor_encrypt(data: str, key: str) -> str:
    """简单XOR加密（增加破解难度）"""
    result = []
    for i, char in enumerate(data):
        result.append(chr(ord(char) ^ ord(key[i % len(key)])))
    return ''.join(result)


def _sign_data(data: str) -> str:
    """对数据进行签名"""
    sign_str = data + SECRET_KEY
    return hashlib.sha512(sign_str.encode()).hexdigest()


def _encode_license(license_data: Dict[str, Any]) -> str:
    """编码许可证数据（加密存储）"""
    # 先添加校验字段
    json_str = json.dumps(license_data, sort_keys=True)
    license_data["checksum"] = hashlib.md5(json_str.encode()).hexdigest()[:8]

    # 重新序列化（包含 checksum）后再签名
    final_json = json.dumps(license_data, sort_keys=True)
    signature = _sign_data(final_json)

    # 加密
    encrypted = _xor_encrypt(final_json, SECRET_KEY[:16])

    payload = encrypted + "|" + signature
    return base64.b64encode(payload.encode()).decode()


def _decode_license(encoded: str) -> Optional[Dict[str, Any]]:
    """解码许可证字符串"""
    try:
        payload = base64.b64decode(encoded.encode()).decode()
        parts = payload.rsplit("|", 1)
        if len(parts) != 2:
            return None

        encrypted, signature = parts

        # 解密
        try:
            json_str = _xor_encrypt(encrypted, SECRET_KEY[:16])
            data = json.loads(json_str)
        except Exception:
            # 兼容旧格式
            data = json.loads(encrypted)

        # 验证签名
        expected_sig = _sign_data(json.dumps(data, sort_keys=True))
        if signature != expected_sig:
            logger.warning("许可证签名验证失败")
            return None

        return data
    except Exception as e:
        logger.error(f"解码许可证失败: {e}")
        return None


def _record_last_time() -> None:
    """记录最后运行时间（防止时间回拨）"""
    try:
        LICENSE_DIR.mkdir(parents=True, exist_ok=True)
        record = {
            "last_time": datetime.now().isoformat(),
            "counter": int(time.time())
        }
        with open(TIME_RECORD_FILE, "w") as f:
            # 简单混淆
            encoded = base64.b64encode(json.dumps(record).encode()).decode()
            f.write(encoded)
    except Exception:
        pass


def _check_time_tampering() -> bool:
    """
    检测时间篡改
    返回 True 表示时间正常，False 表示可能被篡改
    """
    try:
        if not TIME_RECORD_FILE.exists():
            _record_last_time()
            return True

        with open(TIME_RECORD_FILE, "r") as f:
            encoded = f.read()
            record = json.loads(base64.b64decode(encoded.encode()).decode())

        last_time = datetime.fromisoformat(record["last_time"])
        current_time = datetime.now()

        # 如果当前时间比上次记录早超过1小时，可能被篡改
        if (last_time - current_time).total_seconds() > 3600:
            logger.warning("检测到系统时间可能被回拨")
            return False

        # 更新记录
        _record_last_time()
        return True
    except Exception:
        _record_last_time()
        return True


def generate_license_key(
    license_type: str,
    machine_id: Optional[str] = None,
    custom_days: Optional[int] = None
) -> str:
    """
    生成许可证密钥

    Args:
        license_type: 许可证类型 (trial/weekly/monthly/half_year/yearly)
        machine_id: 机器ID, 为空则不绑定
        custom_days: 自定义天数, 覆盖默认天数

    Returns:
        许可证密钥字符串
    """
    if license_type not in LICENSE_TYPES:
        raise ValueError(f"无效的许可证类型: {license_type}")

    lt = LICENSE_TYPES[license_type]
    days = custom_days if custom_days is not None else lt["days"]

    now = datetime.now()
    license_data = {
        "type": license_type,
        "name": lt["name"],
        "days": days,
        "machine_id": machine_id or "",
        "issued_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "expires_at": (now + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S"),
        "version": 2,  # 版本号
        "nonce": os.urandom(8).hex(),  # 随机数防重放
    }

    return _encode_license(license_data)


def validate_license_key(key: str, check_time: bool = True) -> Dict[str, Any]:
    """
    验证许可证密钥

    Returns:
        {"valid": bool, "reason": str, "info": dict or None}
    """
    data = _decode_license(key)
    if data is None:
        return {"valid": False, "reason": "无效的许可证格式", "info": None}

    if data.get("machine_id"):
        current_machine = _get_machine_id()
        if data["machine_id"] != current_machine:
            return {"valid": False, "reason": "许可证与本机不匹配", "info": data}

    # 检测时间篡改
    if check_time and not _check_time_tampering():
        return {"valid": False, "reason": "系统时间异常，请校准后重试", "info": data}

    try:
        expires_at = datetime.strptime(data["expires_at"], "%Y-%m-%d %H:%M:%S")
    except (ValueError, KeyError):
        return {"valid": False, "reason": "许可证日期格式错误", "info": data}

    if datetime.now() > expires_at:
        return {"valid": False, "reason": f"许可证已过期 (过期时间: {data['expires_at']})", "info": data}

    remaining = expires_at - datetime.now()
    data["remaining_days"] = remaining.days

    return {"valid": True, "reason": "许可证有效", "info": data}


class LicenseManager:
    """许可证管理器"""

    def __init__(self):
        self._machine_id = _get_machine_id()
        self._license_info: Optional[Dict[str, Any]] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._stop_heartbeat = threading.Event()
        self._load()

    @property
    def machine_id(self) -> str:
        return self._machine_id

    @property
    def is_licensed(self) -> bool:
        if self._license_info is None:
            return False
        result = validate_license_key(self._license_info.get("_raw_key", ""))
        return result["valid"]

    @property
    def license_info(self) -> Optional[Dict[str, Any]]:
        if not self.is_licensed:
            return None
        return self._license_info

    @property
    def remaining_days(self) -> int:
        if not self.is_licensed:
            return 0
        return self._license_info.get("remaining_days", 0)

    @property
    def license_type_name(self) -> str:
        if not self.is_licensed:
            return "未激活"
        return self._license_info.get("name", "未知")

    def _load(self) -> None:
        """从本地加载许可证"""
        if not LICENSE_FILE.exists():
            self._license_info = None
            return

        try:
            with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()

            data = _decode_license(content)
            if data is None:
                self._license_info = None
                return

            result = validate_license_key(content)
            data["_raw_key"] = content
            if result["valid"]:
                data["remaining_days"] = result["info"]["remaining_days"]
            self._license_info = data
        except Exception as e:
            logger.error(f"加载许可证失败: {e}")
            self._license_info = None

    def activate(self, key: str) -> Dict[str, Any]:
        """
        激活许可证
        如果许可证未绑定机器，首次激活时自动绑定当前机器

        Returns:
            {"success": bool, "message": str}
        """
        result = validate_license_key(key)
        if not result["valid"]:
            return {"success": False, "message": result["reason"]}

        data = result["info"]

        # 如果许可证未绑定机器，首次激活时自动绑定当前机器
        if not data.get("machine_id"):
            data["machine_id"] = self._machine_id
            # 重新生成绑定后的许可证密钥
            key = _encode_license(data)
            logger.info(f"通用密钥已自动绑定到当前机器: {self._machine_id[:16]}...")

        LICENSE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(LICENSE_FILE, "w", encoding="utf-8") as f:
                f.write(key)

            data["_raw_key"] = key
            self._license_info = data

            # 记录时间
            _record_last_time()

            logger.info(f"许可证激活成功: {data.get('name', '')}, 到期: {data.get('expires_at', '')}")
            return {"success": True, "message": f"激活成功！有效期至 {data['expires_at']}"}
        except Exception as e:
            logger.error(f"保存许可证失败: {e}")
            return {"success": False, "message": f"保存许可证失败: {str(e)}"}

    def deactivate(self) -> None:
        """注销许可证"""
        try:
            if LICENSE_FILE.exists():
                LICENSE_FILE.unlink()
            if TIME_RECORD_FILE.exists():
                TIME_RECORD_FILE.unlink()
            self._license_info = None
            logger.info("许可证已注销")
        except Exception as e:
            logger.error(f"注销许可证失败: {e}")

    def check(self) -> Dict[str, Any]:
        """
        检查许可证状态

        Returns:
            {"licensed": bool, "remaining_days": int, "type_name": str, "expires_at": str}
        """
        if not self.is_licensed:
            return {
                "licensed": False,
                "remaining_days": 0,
                "type_name": "未激活",
                "expires_at": "",
            }

        info = self._license_info
        return {
            "licensed": True,
            "remaining_days": info.get("remaining_days", 0),
            "type_name": info.get("name", "未知"),
            "expires_at": info.get("expires_at", ""),
        }

    def start_heartbeat(self, server_url: str, interval: int = 3600) -> None:
        """
        启动心跳检测（在线验证）
        interval: 心跳间隔（秒），默认1小时
        """
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return

        self._stop_heartbeat.clear()

        def heartbeat():
            while not self._stop_heartbeat.is_set():
                try:
                    # TODO: 调用服务器验证接口
                    pass
                except Exception:
                    pass
                time.sleep(interval)

        self._heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        self._heartbeat_thread.start()

    def stop_heartbeat(self) -> None:
        """停止心跳检测"""
        self._stop_heartbeat.set()
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=5)
