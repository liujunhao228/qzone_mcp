from typing import Dict
from pydantic import BaseModel, Field


class QzoneContext(BaseModel):
    uin: int = Field(description="QQ 号")
    skey: str = Field(description="会话密钥")
    p_skey: str = Field(description="持久化会话密钥")
    cookies_str: str = Field(description="原始 Cookie 字符串")

    @property
    def gtk2(self) -> str:
        hash_val = 5381
        for ch in self.p_skey:
            hash_val += (hash_val << 5) + ord(ch)
        return str(hash_val & 0x7FFFFFFF)

    def cookies(self) -> Dict[str, str]:
        return {
            "uin": f"o{self.uin}",
            "skey": self.skey,
            "p_skey": self.p_skey,
        }

    def headers(self) -> Dict[str, str]:
        return {
            "Cookie": self.cookies_str,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://user.qzone.qq.com/",
        }
