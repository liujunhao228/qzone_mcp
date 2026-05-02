import pytest

from qzone_mcp.api.model import ApiResponse
from qzone_mcp.api.constants import QZONE_CODE_OK, QZONE_CODE_UNKNOWN


class TestApiResponse:
    def test_from_raw_success(self):
        raw = {"code": 0, "data": {"result": "success"}}
        response = ApiResponse.from_raw(raw)
        assert response.ok is True
        assert response.code == 0
        assert response.message is None
        assert response.data["result"] == "success"

    def test_from_raw_failure(self):
        raw = {"code": -1, "message": "error occurred"}
        response = ApiResponse.from_raw(raw)
        assert response.ok is False
        assert response.code == -1
        assert response.message == "error occurred"
        assert response.data == {}

    def test_from_raw_custom_code_key(self):
        raw = {"status": 0, "data": {"value": 123}}
        response = ApiResponse.from_raw(raw, code_key="status")
        assert response.ok is True
        assert response.code == 0

    def test_from_raw_custom_msg_key(self):
        raw = {"code": -1, "msg": "custom error"}
        response = ApiResponse.from_raw(raw, msg_key="msg")
        assert response.message == "custom error"

    def test_from_raw_multiple_msg_keys(self):
        raw = {"code": -1, "message": "", "msg": "error message"}
        response = ApiResponse.from_raw(raw, msg_key=("message", "msg"))
        assert response.message == "error message"

    def test_from_raw_data_key(self):
        raw = {"code": 0, "result": {"items": [1, 2, 3]}}
        response = ApiResponse.from_raw(raw, data_key="result")
        assert response.data == {"items": [1, 2, 3]}

    def test_from_raw_with_internal_meta(self):
        raw = {"code": 0, "data": {"value": 1}, "__qzone_internal__": {"http_status": 200}}
        response = ApiResponse.from_raw(raw)
        assert response.ok is True
        assert "__qzone_internal__" not in response.data

    def test_model_dump(self):
        raw = {"code": 0, "data": {"test": "value"}}
        response = ApiResponse.from_raw(raw)
        dumped = response.model_dump()
        assert dumped["ok"] is True
        assert dumped["code"] == 0
        assert dumped["data"]["test"] == "value"

    def test_model_copy(self):
        response = ApiResponse(ok=True, code=0, message=None, data={"a": 1}, raw={})
        copied = response.model_copy()
        assert copied.ok == response.ok
        assert copied.data == response.data
        assert copied is not response
