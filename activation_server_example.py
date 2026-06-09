"""
激活服务器示例代码 (Flask)
将此代码部署到你的服务器上

安装依赖: pip install flask sqlalchemy
运行: python activation_server.py
"""

from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import hashlib
import json
import base64
import secrets
import string
from functools import wraps

app = Flask(__name__)

# 配置
SECRET_KEY = "DeskStudy2026SecretKeyForLicense"  # 与客户端一致
DATABASE_URI = "sqlite:///activation.db"  # 或使用 MySQL/PostgreSQL

# 简单的内存存储（生产环境请使用数据库）
activation_codes = {}  # {code: {"type": "monthly", "used": False, "machine_id": None, "used_at": None}}
license_records = {}   # {machine_id: {"license_key": xxx, "expires_at": xxx}}


def generate_license_key(license_type: str, machine_id: str, days: int) -> str:
    """生成许可证密钥"""
    now = datetime.now()
    license_data = {
        "type": license_type,
        "name": {"trial": "试用版", "monthly": "月卡", "half_year": "半年卡", "yearly": "年卡"}.get(license_type, "未知"),
        "days": days,
        "machine_id": machine_id,
        "issued_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "expires_at": (now + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S"),
        "version": 1,
    }

    json_str = json.dumps(license_data, sort_keys=True)
    signature = hashlib.sha256((json_str + SECRET_KEY).encode()).hexdigest()
    payload = json_str + "|" + signature
    return base64.b64encode(payload.encode()).decode()


def generate_activation_code(length: int = 16) -> str:
    """生成激活码"""
    chars = string.ascii_uppercase + string.digits
    code = '-'.join([''.join(secrets.choice(chars) for _ in range(4)) for _ in range(4)])
    return code


def validate_request(f):
    """验证请求的装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "无效的请求数据"}), 400
        return f(*args, **kwargs)
    return decorated


# ==================== 管理接口 ====================

@app.route("/admin/create_code", methods=["POST"])
def create_activation_code():
    """
    创建激活码（管理接口）

    请求参数:
    {
        "admin_key": "your_admin_key",
        "license_type": "monthly",  # trial/monthly/half_year/yearly
        "count": 1,  # 生成数量
        "days": 30   # 可选，自定义天数
    }
    """
    data = request.get_json()

    # 验证管理员密钥
    if data.get("admin_key") != "YOUR_ADMIN_SECRET_KEY":
        return jsonify({"success": False, "message": "无权限"}), 403

    license_type = data.get("license_type", "monthly")
    count = data.get("count", 1)
    custom_days = data.get("days")

    days_map = {
        "trial": 1,
        "weekly": 7,
        "monthly": 30,
        "half_year": 180,
        "yearly": 365
    }

    days = custom_days or days_map.get(license_type, 30)

    codes = []
    for _ in range(count):
        code = generate_activation_code()
        activation_codes[code] = {
            "type": license_type,
            "days": days,
            "used": False,
            "machine_id": None,
            "used_at": None,
            "created_at": datetime.now().isoformat()
        }
        codes.append(code)

    return jsonify({
        "success": True,
        "message": f"成功创建 {count} 个激活码",
        "codes": codes
    })


@app.route("/admin/list_codes", methods=["GET"])
def list_activation_codes():
    """列出所有激活码（管理接口）"""
    admin_key = request.args.get("admin_key")
    if admin_key != "YOUR_ADMIN_SECRET_KEY":
        return jsonify({"success": False, "message": "无权限"}), 403

    return jsonify({
        "success": True,
        "codes": activation_codes
    })


# ==================== 客户端接口 ====================

@app.route("/api/activate", methods=["POST"])
@validate_request
def activate():
    """
    激活接口

    请求参数:
    {
        "activation_code": "XXXX-XXXX-XXXX-XXXX",
        "machine_id": "用户机器码",
        "app_version": "1.0.0"
    }
    """
    data = request.get_json()
    code = data.get("activation_code", "").strip().upper()
    machine_id = data.get("machine_id", "")

    if not code or not machine_id:
        return jsonify({"success": False, "message": "参数不完整"}), 400

    # 检查激活码是否存在
    if code not in activation_codes:
        return jsonify({"success": False, "message": "激活码无效"}), 400

    code_info = activation_codes[code]

    # 检查是否已使用
    if code_info["used"]:
        # 如果是同一台机器，返回已有的许可证
        if code_info["machine_id"] == machine_id:
            record = license_records.get(machine_id, {})
            return jsonify({
                "success": True,
                "message": "该设备已激活",
                "license_key": record.get("license_key"),
                "expires_at": record.get("expires_at"),
                "license_type": code_info["type"]
            })
        else:
            return jsonify({"success": False, "message": "激活码已被其他设备使用"}), 400

    # 激活
    license_type = code_info["type"]
    days = code_info["days"]
    license_key = generate_license_key(license_type, machine_id, days)

    # 更新激活码状态
    code_info["used"] = True
    code_info["machine_id"] = machine_id
    code_info["used_at"] = datetime.now().isoformat()

    # 保存许可证记录
    license_records[machine_id] = {
        "license_key": license_key,
        "activation_code": code,
        "type": license_type,
        "days": days,
        "expires_at": (datetime.now() + timedelta(days=days)).isoformat(),
        "created_at": datetime.now().isoformat()
    }

    return jsonify({
        "success": True,
        "message": f"激活成功！有效期 {days} 天",
        "license_key": license_key,
        "expires_at": license_records[machine_id]["expires_at"],
        "license_type": license_type
    })


@app.route("/api/check_status", methods=["POST"])
@validate_request
def check_status():
    """
    查询激活状态

    请求参数:
    {
        "activation_code": "XXXX-XXXX-XXXX-XXXX",
        "machine_id": "用户机器码"
    }
    """
    data = request.get_json()
    code = data.get("activation_code", "").strip().upper()
    machine_id = data.get("machine_id", "")

    if code in activation_codes:
        code_info = activation_codes[code]
        return jsonify({
            "success": True,
            "used": code_info["used"],
            "type": code_info["type"],
            "days": code_info["days"],
            "is_current_device": code_info["machine_id"] == machine_id
        })

    return jsonify({"success": False, "message": "激活码不存在"})


if __name__ == "__main__":
    print("=" * 50)
    print("DeskStudy 激活服务器")
    print("=" * 50)
    print("\n管理接口:")
    print("  POST /admin/create_code - 创建激活码")
    print("  GET  /admin/list_codes  - 列出激活码")
    print("\n客户端接口:")
    print("  POST /api/activate    - 激活")
    print("  POST /api/check_status - 查询状态")
    print("\n" + "=" * 50)

    # 生产环境请使用 gunicorn 或 uWSGI
    app.run(host="0.0.0.0", port=5000, debug=True)
