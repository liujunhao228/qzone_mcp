from cryptography.fernet import Fernet
from pathlib import Path
from typing import Optional


class CryptoManager:
    _KEY_FILE_NAME = ".qzone_key"
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.key_path = data_dir / self._KEY_FILE_NAME
        self._fernet: Optional[Fernet] = None
        self._ensure_key()
    
    @property
    def fernet(self) -> Fernet:
        if self._fernet is None:
            self._load_key()
        return self._fernet
    
    def _ensure_key(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.key_path.exists():
            self._generate_key()
    
    def _generate_key(self) -> None:
        key = Fernet.generate_key()
        with open(self.key_path, "wb") as f:
            f.write(key)
        self.key_path.chmod(0o600)
        self._fernet = Fernet(key)
    
    def _load_key(self) -> None:
        try:
            with open(self.key_path, "rb") as f:
                key = f.read()
            self._fernet = Fernet(key)
        except Exception as e:
            raise RuntimeError(f"无法加载加密密钥: {e}")
    
    def encrypt(self, data: str) -> str:
        if not data:
            return ""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, data: str) -> str:
        if not data:
            return ""
        return self.fernet.decrypt(data.encode()).decode()
    
    def backup_key(self, backup_path: Path) -> None:
        with open(self.key_path, "rb") as src:
            with open(backup_path, "wb") as dst:
                dst.write(src.read())
        backup_path.chmod(0o600)
    
    def restore_key(self, backup_path: Path) -> None:
        with open(backup_path, "rb") as src:
            with open(self.key_path, "wb") as dst:
                dst.write(src.read())
        self.key_path.chmod(0o600)
        self._load_key()
