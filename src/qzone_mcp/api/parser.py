import datetime
import json
import re
from typing import Any, Tuple, List

import json5
from bs4 import BeautifulSoup

from .constants import (
    QZONE_CODE_UNKNOWN,
    QZONE_MSG_EMPTY_RESPONSE,
    QZONE_MSG_INVALID_RESPONSE,
    QZONE_MSG_JSON_PARSE_ERROR,
    QZONE_MSG_NON_OBJECT_RESPONSE,
)
from .model import Feed, FeedImage, FeedComment


def _safe_cell(text: str, max_len: int = 30) -> str:
    if not text:
        return "-"
    text = str(text)
    text = text.replace("\n", " ").replace("|", "｜").strip()
    if len(text) > max_len:
        text = text[:max_len] + "…"
    return text or "-"


class QzoneParser:
    @staticmethod
    def _error_payload(message: str) -> dict[str, Any]:
        return {"code": QZONE_CODE_UNKNOWN, "message": message, "data": {}}

    @staticmethod
    def parse_response(text: str, *, debug: bool = False) -> dict[str, Any]:
        if debug:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"响应数据: {text}")

        if not text or not text.strip():
            return QzoneParser._error_payload(QZONE_MSG_EMPTY_RESPONSE)

        if m := re.search(
            r"callback\s*\(\s*([^{]*(\{.*\})[^)]*)\s*\)",
            text,
            re.I | re.S,
        ):
            json_str = m.group(2)
        else:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end < start:
                return QzoneParser._error_payload(QZONE_MSG_INVALID_RESPONSE)
            json_str = text[start : end + 1]

        json_str = json_str.replace("undefined", "null").strip()

        try:
            data = json5.loads(json_str)
        except (ValueError, json.JSONDecodeError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"JSON 解析错误: {e}")
            return QzoneParser._error_payload(QZONE_MSG_JSON_PARSE_ERROR)

        if not isinstance(data, dict):
            import logging
            logger = logging.getLogger(__name__)
            logger.error("JSON 解析结果不是 dict")
            return QzoneParser._error_payload(QZONE_MSG_NON_OBJECT_RESPONSE)

        if debug:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"解析后数据: {data}")

        return data

    @staticmethod
    def parse_upload_result(payload: dict[str, Any]) -> Tuple[str, str]:
        data = payload["data"]
        picbo = data["url"].split("&bo=", 1)[1]

        richval = ",{},{},{},{},{},{},,{},{}".format(
            data["albumid"],
            data["lloc"],
            data["sloc"],
            data["type"],
            data["height"],
            data["width"],
            data["height"],
            data["width"],
        )
        return picbo, richval

    @staticmethod
    def parse_visitors(data: dict[str, Any]) -> str:
        data = data.get("data") or {}
        items = data.get("items")

        if not isinstance(items, list) or not items:
            return "### 最近来访明细\n\n暂无访客记录"

        src_map: dict[int, str] = {
            0: "访问空间",
            13: "查看动态",
            32: "手机QQ",
            41: "国际版QQ/TIM",
        }

        lines: List[str] = []
        lines.append("\n### 最近来访明细\n")
        lines.append("| 时间 | 访客 | 来源 | 状态 | 带来了 |")
        lines.append("| --- | --- | --- | --- | --- |")

        for v in items:
            if not isinstance(v, dict):
                continue

            ts = v.get("time")
            ts_int = ts if isinstance(ts, int) else 0
            dt = datetime.datetime.fromtimestamp(ts_int).strftime("%m-%d %H:%M")

            name = v.get("name")
            visitor = _safe_cell(name if isinstance(name, str) else "匿名", 16)

            src_val = v.get("src")
            src_key = src_val if isinstance(src_val, int) else -1
            src = _safe_cell(src_map.get(src_key, f"未知({src_key})"), 12)

            status_parts: List[str] = []
            yellow = v.get("yellow")
            if isinstance(yellow, int) and yellow > 0:
                status_parts.append(f"LV{yellow}")
            if v.get("is_hide_visit"):
                status_parts.append("隐身")
            status = _safe_cell(" / ".join(status_parts), 12)

            remark = "-"
            shuos = v.get("shuoshuoes")
            if isinstance(shuos, list):
                for s in shuos:
                    if isinstance(s, dict):
                        title = s.get("name")
                        if isinstance(title, str) and title.strip():
                            remark = _safe_cell(f"说说:{title}", 30)
                            break

            if remark == "-":
                uins = v.get("uins")
                if isinstance(uins, list):
                    names = []
                    for u in uins:
                        if isinstance(u, dict):
                            n = u.get("name")
                            if isinstance(n, str) and n.strip():
                                names.append(n)
                    if names:
                        remark = _safe_cell("、".join(names), 30)

            lines.append(
                f"| {_safe_cell(dt, 16)} | {visitor} | {src} | {status} | {remark} |"
            )

        today = data.get("todaycount", 0)
        total = data.get("totalcount", 0)
        lines.append(f"今日访客共 {today} 人，最近30天访客共 {total} 人")

        return "\n".join(lines)

    @staticmethod
    def parse_feeds(data: dict[str, Any], with_detail: bool = False) -> List[Feed]:
        msglist = data.get("msglist", [])
        if not isinstance(msglist, list):
            msglist = []

        posts: List[Feed] = []
        for msg in msglist:
            if not isinstance(msg, dict):
                continue

            image_urls: List[str] = []
            for img_data in msg.get("pic", []):
                if isinstance(img_data, dict):
                    for key in ("url2", "url3", "url1", "smallurl"):
                        if raw := img_data.get(key):
                            image_urls.append(raw)
                            break

            for video in msg.get("video") or []:
                if isinstance(video, dict):
                    video_image_url = video.get("url1") or video.get("pic_url")
                    if video_image_url:
                        image_urls.append(video_image_url)

            rt_con = msg.get("rt_con", {}).get("content", "")
            if isinstance(rt_con, dict):
                rt_con = rt_con.get("content", "") or ""

            comment_list: List[FeedComment] = []
            if with_detail:
                comments_data = msg.get("commentlist", [])
                for comm in comments_data:
                    if isinstance(comm, dict):
                        comment = FeedComment(
                            id=str(comm.get("commentid", "")),
                            uin=comm.get("uin", 0),
                            nickname=comm.get("name", ""),
                            content=comm.get("content", ""),
                            time=comm.get("time", "")
                        )
                        comment_list.append(comment)

            images = [FeedImage(url=url) for url in image_urls]

            post = Feed(
                tid=str(msg.get("tid", "")),
                uin=msg.get("uin", 0),
                nickname=msg.get("name", ""),
                content=msg.get("content", "").strip(),
                images=images,
                likes=msg.get("likenum", 0),
                comments=len(comment_list) if comment_list else msg.get("commentnum", 0),
                shares=msg.get("sharenum", 0),
                time=str(msg.get("created_time", "")),
                comment_list=comment_list,
                is_liked=msg.get("isliked", 0) == 1,
            )
            posts.append(post)

        return posts