from app.config import Settings


def test_parse_addresses_list():
    settings = Settings(
        XRPL_WS_URL="ws",
        XRPL_RPC_URL="http",
        XRPL_ACCOUNT_ADDRESSES=["a", "b"],
        DB_PATH=":memory:",
        API_KEY="key",
    )
    assert settings.xrpl_account_addresses == ["a", "b"]
