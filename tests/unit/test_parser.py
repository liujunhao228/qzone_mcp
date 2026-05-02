import pytest

from qzone_mcp.api.parser import QzoneParser
from qzone_mcp.api.constants import (
    QZONE_CODE_UNKNOWN,
    QZONE_MSG_EMPTY_RESPONSE,
    QZONE_MSG_INVALID_RESPONSE,
    QZONE_MSG_JSON_PARSE_ERROR,
)


class TestQzoneParser:
    def test_parse_empty_response(self):
        result = QzoneParser.parse_response("")
        assert result["code"] == QZONE_CODE_UNKNOWN
        assert result["message"] == QZONE_MSG_EMPTY_RESPONSE

    def test_parse_invalid_response(self):
        result = QzoneParser.parse_response("this is not json")
        assert result["code"] == QZONE_CODE_UNKNOWN
        assert result["message"] == QZONE_MSG_INVALID_RESPONSE

    def test_parse_valid_json(self):
        json_str = '{"code": 0, "data": {"name": "test"}}'
        result = QzoneParser.parse_response(json_str)
        assert result["code"] == 0
        assert result["data"]["name"] == "test"

    def test_parse_jsonp_response(self):
        jsonp_str = 'callback({"code": 0, "message": "success"});'
        result = QzoneParser.parse_response(jsonp_str)
        assert result["code"] == 0
        assert result["message"] == "success"

    def test_parse_json_with_undefined(self):
        json_str = '{"code": 0, "data": undefined}'
        result = QzoneParser.parse_response(json_str)
        assert result["code"] == 0
        assert result["data"] is None

    def test_parse_json5_features(self):
        json5_str = '{"code": 0, "data": {"name": "test", "count": 1, // comment\n"active": true}}'
        result = QzoneParser.parse_response(json5_str)
        assert result["code"] == 0
        assert result["data"]["name"] == "test"
        assert result["data"]["count"] == 1

    def test_parse_response_with_extra_chars(self):
        raw_str = 'some garbage{"code": 0, "data": {"value": 123}}more garbage'
        result = QzoneParser.parse_response(raw_str)
        assert result["code"] == 0
        assert result["data"]["value"] == 123

    def test_parse_visitors_empty(self):
        data = {"data": {"items": []}}
        result = QzoneParser.parse_visitors(data)
        assert "暂无访客记录" in result

    def test_parse_visitors_with_data(self):
        data = {
            "data": {
                "items": [
                    {
                        "time": 1704067200,
                        "name": "访客1",
                        "src": 0,
                        "yellow": 5,
                        "is_hide_visit": False,
                    }
                ],
                "todaycount": 10,
                "totalcount": 100,
            }
        }
        result = QzoneParser.parse_visitors(data)
        assert "访客1" in result
        assert "访问空间" in result
        assert "LV5" in result
        assert "今日访客共 10 人" in result

    def test_parse_feeds_empty(self):
        data = {"msglist": []}
        result = QzoneParser.parse_feeds(data)
        assert len(result) == 0

    def test_parse_feeds_with_data(self):
        data = {
            "msglist": [
                {
                    "tid": "12345",
                    "uin": 123456789,
                    "name": "测试用户",
                    "content": "这是一条说说",
                    "pic": [{"url2": "https://example.com/img.jpg"}],
                    "likenum": 10,
                    "commentnum": 5,
                    "sharenum": 2,
                    "created_time": 1704067200,
                    "isliked": 0,
                }
            ]
        }
        result = QzoneParser.parse_feeds(data)
        assert len(result) == 1
        assert result[0].tid == "12345"
        assert result[0].nickname == "测试用户"
        assert result[0].content == "这是一条说说"
        assert len(result[0].images) == 1
        assert result[0].likes == 10
        assert result[0].comments == 5

    def test_parse_feeds_with_detail(self):
        data = {
            "msglist": [
                {
                    "tid": "12345",
                    "uin": 123456789,
                    "name": "测试用户",
                    "content": "这是一条说说",
                    "commentlist": [
                        {
                            "commentid": "c1",
                            "uin": 987654321,
                            "name": "评论者",
                            "content": "好棒",
                            "time": "2024-01-01",
                        }
                    ],
                }
            ]
        }
        result = QzoneParser.parse_feeds(data, with_detail=True)
        assert len(result) == 1
        assert len(result[0].comment_list) == 1
        assert result[0].comment_list[0].content == "好棒"
