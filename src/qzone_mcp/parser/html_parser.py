from typing import List, Dict, Any
import logging

import bs4

from ..model import Feed, FeedComment


logger = logging.getLogger(__name__)


class QzoneHtmlParser:
    @staticmethod
    def parse_recent_feeds(data: dict) -> List[Feed]:
        if not data:
            logger.error("输入数据为空")
            return []
        
        data_inner = data.get("data", {})
        feeds: list = data_inner.get("data", [])
        
        if not isinstance(feeds, list):
            logger.error(f"feeds 不是列表类型，实际类型: {type(feeds)}")
            return []
        
        if not feeds:
            logger.warning("feeds 列表为空")
            return []
        
        try:
            posts = []
            for feed in feeds:
                if not feed:
                    continue
                
                appid = str(feed.get("appid", ""))
                if appid != "311":
                    continue
                
                uin = feed.get("uin", "")
                tid = feed.get("key", "")
                if not uin or not tid:
                    logger.error(f"无效的说说数据: uin={uin}, tid={tid}")
                    continue
                
                create_time = feed.get("abstime", "")
                nickname = feed.get("nickname", "")
                html_content = feed.get("html", "")
                if not html_content:
                    logger.error(f"说说内容为空: uin={uin}, tid={tid}")
                    continue

                soup = bs4.BeautifulSoup(html_content, "html.parser")

                text_div = soup.find("div", class_="f-info")
                text = text_div.get_text(strip=True) if text_div else ""

                rt_con = ""
                txt_box = soup.select_one("div.txt-box")
                if txt_box:
                    rt_con = txt_box.get_text(strip=True)
                    if "：" in rt_con:
                        rt_con = rt_con.split("：", 1)[1].strip()

                image_urls = []
                if img_box := soup.find("div", class_="img-box"):
                    for img in img_box.find_all("img"):
                        src = img.get("src")
                        if src and not str(src).startswith("http://qzonestyle.gtimg.cn"):
                            image_urls.append(src)

                img_tag = soup.select_one("div.video-img img")
                if img_tag and "src" in img_tag.attrs:
                    image_urls.append(img_tag["src"])

                videos = []
                video_div = soup.select_one("div.img-box.f-video-wrap.play")
                if video_div and "url3" in video_div.attrs:
                    videos.append(video_div["url3"])

                comments: List[FeedComment] = []
                comment_items = soup.select("li.comments-item.bor3")
                if comment_items:
                    for item in comment_items:
                        data_uin = str(item.get("data-uin", ""))
                        comment_tid = str(item.get("data-tid", ""))
                        comment_nickname = str(item.get("data-nick", ""))

                        content_div = item.select_one("div.comments-content")
                        if content_div:
                            for op in content_div.select("div.comments-op"):
                                op.decompose()
                            content = content_div.get_text(" ", strip=True).split(":", 1)[-1]
                        else:
                            content = ""

                        comment_time_span = item.select_one("span.state")
                        comment_time = comment_time_span.get_text(strip=True) if comment_time_span else ""

                        parent_tid = None
                        parent_div = item.find_parent("div", class_="mod-comments-sub")
                        if parent_div:
                            parent_li = parent_div.find_parent("li", class_="comments-item")
                            if parent_li:
                                parent_tid = str(parent_li.get("data-tid"))

                        comments.append(
                            FeedComment(
                                id=str(comment_tid) if comment_tid.isdigit() else "",
                                uin=int(data_uin) if data_uin.isdigit() else 0,
                                nickname=comment_nickname,
                                content=content,
                                time=comment_time,
                            )
                        )

                post = Feed(
                    tid=str(tid),
                    uin=int(uin),
                    nickname=str(nickname),
                    content=text,
                    images=[],
                    comments=len(comments),
                    comment_list=comments,
                    create_time=str(create_time),
                    rt_con=rt_con,
                    videos=videos,
                )
                posts.append(post)

            logger.info(f"成功解析 {len(posts)} 条最新说说")
            return posts
        except Exception as e:
            logger.error(f"解析说说错误：{e}")
            return []
