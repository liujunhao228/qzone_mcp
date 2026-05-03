import pytest

from qzone_mcp.session import QzoneSession, CookieParseError
from qzone_mcp.config import AppConfig


@pytest.mark.asyncio
async def test_parse_valid_cookies():
    cookie_str = "uin=o123456789; skey=abcdefg123456; p_skey=xyz7890; other=value"
    
    config = AppConfig()
    session = QzoneSession(config)
    
    ctx = await session._parse_cookies(cookie_str)
    
    assert ctx.uin == 123456789
    assert ctx.skey == "abcdefg123456"
    assert ctx.p_skey == "xyz7890"
    assert ctx.cookies_str == cookie_str


@pytest.mark.asyncio
async def test_parse_cookies_missing_uin():
    cookie_str = "skey=abcdefg123456; p_skey=xyz7890"
    
    config = AppConfig()
    session = QzoneSession(config)
    
    with pytest.raises(CookieParseError):
        await session._parse_cookies(cookie_str)


@pytest.mark.asyncio
async def test_parse_cookies_missing_skey():
    cookie_str = "uin=o123456789; p_skey=xyz7890"
    
    config = AppConfig()
    session = QzoneSession(config)
    
    with pytest.raises(CookieParseError):
        await session._parse_cookies(cookie_str)


@pytest.mark.asyncio
async def test_gtk2_calculation():
    config = AppConfig()
    session = QzoneSession(config)
    
    cookie_str = "uin=o123456789; skey=test; p_skey=abc"
    ctx = await session._parse_cookies(cookie_str)
    
    assert ctx.gtk2.isdigit()


@pytest.mark.asyncio
async def test_session_is_logged_in():
    config = AppConfig()
    session = QzoneSession(config)
    
    assert session.is_logged_in is False
    
    cookie_str = "uin=o123456789; skey=abc; p_skey=def"
    await session.login(cookie_str)
    
    assert session.is_logged_in is True
    
    await session.invalidate()
    assert session.is_logged_in is False