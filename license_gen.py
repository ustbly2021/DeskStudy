"""
DeskStudy 许可证生成工具
用于管理员离线生成许可证密钥

使用方法:
  python license_gen.py trial                           # 生成1天试用密钥(不绑定机器)
  python license_gen.py weekly                          # 生成7天周卡密钥
  python license_gen.py monthly                         # 生成月卡密钥(不绑定机器)
  python license_gen.py half_year                       # 生成半年卡密钥(不绑定机器)
  python license_gen.py yearly                          # 生成年卡密钥(不绑定机器)
  python license_gen.py monthly --machine-id <机器码>    # 生成绑定机器的月卡密钥
  python license_gen.py monthly --days 60               # 生成60天的月卡密钥
"""

import hashlib
import base64
import json
import os
import argparse
from datetime import datetime, timedelta

# ==================== 安全配置（与 license.py 保持一致）====================
_SECRET_PART_1 = ""
_SECRET_PART_2 = ""
_SECRET_PART_3 = ""
SECRET_KEY = _SECRET_PART_1 + _SECRET_PART_2 + _SECRET_PART_3

LICENSE_TYPES = {
    "trial": {"name": "试用版", "days": 1},
    "weekly": {"name": "周卡", "days": 7},
    "monthly": {"name": "月卡", "days": 30},
    "half_year": {"name": "半年卡", "days": 180},
    "yearly": {"name": "年卡", "days": 365},
}


def _xor_encrypt(data: str, key: str) -> str:
    """简单XOR加密（与 license.py 保持一致）"""
    result = []
    for i, char in enumerate(data):
        result.append(chr(ord(char) ^ ord(key[i % len(key)])))
    return ''.join(result)


def _sign_data(data: str) -> str:
    """对数据进行签名（SHA512）"""
    sign_str = data + SECRET_KEY
    return hashlib.sha512(sign_str.encode()).hexdigest()


def _encode_license(license_data: dict) -> str:
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


def _decode_license(encoded: str) -> dict:
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
            return None

        # 验证签名
        expected_sig = _sign_data(json.dumps(data, sort_keys=True))
        if signature != expected_sig:
            return None

        return data
    except Exception:
        return None


def generate_license_key(license_type: str, machine_id: str = "", custom_days: int = None) -> str:
    """生成许可证密钥"""
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
        "version": 2,  # 新版本号
        "nonce": os.urandom(8).hex(),  # 随机数防重放
    }
    return _encode_license(license_data)


def validate_license_key(key: str) -> dict:
    """验证许可证密钥"""
    data = _decode_license(key)
    if data is None:
        return {"valid": False, "reason": "无效的许可证格式", "info": None}

    try:
        expires_at = datetime.strptime(data["expires_at"], "%Y-%m-%d %H:%M:%S")
    except (ValueError, KeyError):
        return {"valid": False, "reason": "许可证日期格式错误", "info": data}

    if datetime.now() > expires_at:
        return {"valid": False, "reason": f"许可证已过期", "info": data}

    remaining = expires_at - datetime.now()
    data["remaining_days"] = remaining.days

    return {"valid": True, "reason": "许可证有效", "info": data}


def main():
    parser = argparse.ArgumentParser(description="DeskStudy 许可证生成工具")
    parser.add_argument(
        "type",
        choices=list(LICENSE_TYPES.keys()),
        help="许可证类型"
    )
    parser.add_argument(
        "--machine-id", "-m",
        default="",
        help="机器码 (从用户端获取, 留空则不绑定机器)"
    )
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=None,
        help="自定义天数 (覆盖默认天数)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("  DeskStudy 许可证生成工具 v2.0")
    print("=" * 60)

    lt = LICENSE_TYPES[args.type]
    days = args.days if args.days is not None else lt["days"]

    print(f"\n许可证类型: {lt['name']}")
    print(f"有效天数: {days} 天")
    if args.machine_id:
        print(f"绑定机器: {args.machine_id}")
    else:
        print("绑定机器: 无 (通用密钥)")

    key = generate_license_key(
        license_type=args.type,
        machine_id=args.machine_id,
        custom_days=args.days
    )

    print(f"\n{'=' * 60}")
    print("许可证密钥:")
    print(f"{'=' * 60}")
    print(key)
    print(f"{'=' * 60}")

    result = validate_license_key(key)
    if result["valid"]:
        info = result["info"]
        print(f"\n验证通过!")
        print(f"  类型: {info['name']}")
        print(f"  签发: {info['issued_at']}")
        print(f"  到期: {info['expires_at']}")
        print(f"  剩余: {info['remaining_days']} 天")
    else:
        print(f"\n验证失败: {result['reason']}")


if __name__ == "__main__":
    main()
