from http import HTTPStatus

# API code values
QZONE_CODE_OK = 0
QZONE_CODE_UNKNOWN = -1
QZONE_CODE_LOGIN_EXPIRED = -3000
QZONE_CODE_PERMISSION_DENIED = 403
QZONE_CODE_PERMISSION_DENIED_LEGACY = -403

# Parser-level synthetic messages
QZONE_MSG_EMPTY_RESPONSE = "响应内容为空"
QZONE_MSG_INVALID_RESPONSE = "响应内容格式异常"
QZONE_MSG_JSON_PARSE_ERROR = "JSON 解析失败"
QZONE_MSG_NON_OBJECT_RESPONSE = "JSON 根节点不是对象"
QZONE_MSG_PERMISSION_DENIED = "权限不足"

# Internal metadata keys injected by client-side transport
QZONE_INTERNAL_META_KEY = "__qzone_internal__"
QZONE_INTERNAL_HTTP_STATUS_KEY = "http_status"

# HTTP status aliases used by the transport layer
HTTP_STATUS_UNAUTHORIZED = int(HTTPStatus.UNAUTHORIZED)
HTTP_STATUS_FORBIDDEN = int(HTTPStatus.FORBIDDEN)

# API Endpoints
QZONE_BASE_URL = "https://user.qzone.qq.com"
QZONE_UPLOAD_IMAGE_URL = "https://up.qzone.qq.com/cgi-bin/upload/cgi_upload_image"
QZONE_EMOTION_URL = "https://user.qzone.qq.com/proxy/domain/taotao.qzone.qq.com/cgi-bin/emotion_cgi_publish_v6"
QZONE_DOLIKE_URL = "https://user.qzone.qq.com/proxy/domain/w.qzone.qq.com/cgi-bin/likes/internal_dolike_app"
QZONE_LIST_URL = "https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6"
QZONE_COMMENT_URL = "https://user.qzone.qq.com/proxy/domain/taotao.qzone.qq.com/cgi-bin/emotion_cgi_re_feeds"
QZONE_VISITOR_URL = "https://h5.qzone.qq.com/proxy/domain/g.qzone.qq.com/cgi-bin/friendshow/cgi_get_visitor_more"
QZONE_DETAIL_URL = "https://h5.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msgdetail_v6"
QZONE_DELETE_URL = "https://h5.qzone.qq.com/proxy/domain/taotao.qzone.qq.com/cgi-bin/emotion_cgi_delete_v6"
QZONE_ZONE_LIST_URL = "https://user.qzone.qq.com/proxy/domain/ic2.qzone.qq.com/cgi-bin/feeds/feeds3_html_more"