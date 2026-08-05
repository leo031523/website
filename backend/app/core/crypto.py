import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class DecryptionError(Exception):
    """API key 密文無法解密（master key 更換或資料損毀）。"""


def _derive_fernet_key(secret: str) -> bytes:
    """把任意長度的 AI_MASTER_KEY 字串，透過 SHA-256 派生成 Fernet
    要求的 32-byte urlsafe-base64 金鑰，讓 .env 設定方式跟 JWT_SECRET
    一樣單純（貼一串隨機字串即可，不需要另外跑指令產生特定格式）。"""
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _fernet() -> Fernet:
    return Fernet(_derive_fernet_key(settings.ai_master_key))


def encrypt_secret(plain: str) -> str:
    return _fernet().encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise DecryptionError("API key 無法解密，可能是 AI_MASTER_KEY 已變更") from exc


def mask_secret(plain: str) -> str:
    """後台顯示用的遮罩尾碼，例如 sk-...ab12。絕不回傳完整 key。"""
    if len(plain) <= 4:
        return "*" * len(plain)
    return f"{'*' * 4}{plain[-4:]}"
