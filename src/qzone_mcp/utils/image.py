from typing import Optional, List
import base64
import logging

import aiohttp

logger = logging.getLogger(__name__)


async def download_file(url: str) -> Optional[bytes]:
    url = url.replace("https://", "http://")
    try:
        async with aiohttp.ClientSession() as client:
            response = await client.get(url)
            return await response.read()
    except Exception as e:
        logger.error(f"图片下载失败: {e}")
        return None


async def normalize_images(images: Optional[List[bytes | str]]) -> List[bytes]:
    if not images:
        return []

    cleaned: List[bytes] = []
    for item in images:
        if isinstance(item, bytes):
            cleaned.append(item)
        elif isinstance(item, str):
            file = await download_file(item)
            if file:
                cleaned.append(file)
        else:
            raise TypeError(f"image 必须是 str 或 bytes，收到 {type(item)}")
    return cleaned


def encode_image_base64(image: bytes) -> str:
    return base64.b64encode(image).decode()
