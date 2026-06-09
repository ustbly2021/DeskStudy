"""
在线激活服务
用户输入激活码，自动获取机器码并请求服务器激活
"""

import hashlib
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from datetime import datetime

from app.DeskStudy.utils.logger import get_logger

logger = get_logger(__name__)

# 激活服务器地址（需要替换为你的服务器）
ACTIVATION_SERVER = "https://your-server.com/api"


class OnlineActivationService:
    """在线激活服务"""

    def __init__(self, server_url: Optional[str] = None):
        self.server_url = server_url or ACTIVATION_SERVER
        self.timeout = 10  # 请求超时时间（秒）

    def _get_machine_id(self) -> str:
        """获取机器唯一标识"""
        import uuid
        import os

        try:
            mac = uuid.getnode()
            machine_name = os.environ.get("COMPUTERNAME", os.environ.get("HOSTNAME", "unknown"))
            raw = f"{mac}-{machine_name}-DeskStudy"
            return hashlib.sha256(raw.encode()).hexdigest()[:32]
        except Exception:
            return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:32]

    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """发送HTTP请求"""
        url = f"{self.server_url}/{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "DeskStudy/1.0"
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers=headers,
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = response.read().decode("utf-8")
                return json.loads(result)

        except urllib.error.HTTPError as e:
            logger.error(f"HTTP错误: {e.code} - {e.reason}")
            try:
                error_body = e.read().decode("utf-8")
                error_data = json.loads(error_body)
                return {"success": False, "message": error_data.get("message", f"服务器错误: {e.code}")}
            except Exception:
                return {"success": False, "message": f"服务器错误: {e.code}"}

        except urllib.error.URLError as e:
            logger.error(f"网络错误: {e.reason}")
            return {"success": False, "message": f"网络连接失败: {e.reason}"}

        except Exception as e:
            logger.error(f"请求失败: {e}")
            return {"success": False, "message": f"请求失败: {str(e)}"}

    def activate(self, activation_code: str) -> Dict[str, Any]:
        """
        使用激活码激活

        Args:
            activation_code: 激活码（用户购买后获得）

        Returns:
            {"success": bool, "message": str, "license_key": str (if success)}
        """
        machine_id = self._get_machine_id()

        logger.info(f"正在激活，机器码: {machine_id}")

        # 发送激活请求
        result = self._make_request("activate", {
            "activation_code": activation_code,
            "machine_id": machine_id,
            "app_version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        })

        if result is None:
            return {"success": False, "message": "服务器无响应"}

        if result.get("success"):
            logger.info(f"激活成功: {result.get('message', '')}")
            return {
                "success": True,
                "message": result.get("message", "激活成功"),
                "license_key": result.get("license_key"),
                "expires_at": result.get("expires_at"),
                "license_type": result.get("license_type")
            }
        else:
            logger.warning(f"激活失败: {result.get('message', '')}")
            return {
                "success": False,
                "message": result.get("message", "激活失败")
            }

    def check_status(self, activation_code: str) -> Dict[str, Any]:
        """
        查询激活码状态

        Returns:
            {"success": bool, "message": str, "status": dict}
        """
        machine_id = self._get_machine_id()

        result = self._make_request("check_status", {
            "activation_code": activation_code,
            "machine_id": machine_id
        })

        if result is None:
            return {"success": False, "message": "服务器无响应"}

        return result

    def get_machine_id_display(self) -> str:
        """获取用于显示的机器码（格式化）"""
        machine_id = self._get_machine_id()
        # 格式化为 4-4-4-4-4 格式，方便用户查看
        return "-".join([machine_id[i:i+4].upper() for i in range(0, len(machine_id), 4)])[:19]


# 离线激活辅助功能（作为备选方案）
class OfflineActivationHelper:
    """离线激活辅助工具"""

    @staticmethod
    def generate_activation_request(machine_id: str) -> str:
        """
        生成激活请求码（用户发给你，你生成许可证）
        """
        import base64
        data = {
            "machine_id": machine_id,
            "timestamp": datetime.now().isoformat()
        }
        return base64.b64encode(json.dumps(data).encode()).decode()

    @staticmethod
    def parse_activation_request(request_code: str) -> Optional[Dict[str, Any]]:
        """
        解析激活请求码（你用这个获取用户的机器码）
        """
        try:
            import base64
            data = json.loads(base64.b64decode(request_code.encode()).decode())
            return data
        except Exception:
            return None
