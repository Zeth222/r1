import asyncio
import httpx

from bot.data import uniswap


def test_fetch_positions_handles_null(monkeypatch):
    async def handler(request):
        return httpx.Response(200, json={"data": None}, headers={"content-type": "application/json"})

    transport = httpx.MockTransport(handler)
    monkeypatch.setenv("UNISWAP_SUBGRAPH_URL", "http://example.com")

    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            return await uniswap.fetch_positions(client, owner="0x0")

    res = asyncio.run(run())
    assert res is None


def test_fetch_positions_empty(monkeypatch):
    async def handler(request):
        return httpx.Response(200, json={"data": {"positions": []}}, headers={"content-type": "application/json"})

    transport = httpx.MockTransport(handler)
    monkeypatch.setenv("UNISWAP_SUBGRAPH_URL", "http://example.com")

    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            return await uniswap.fetch_positions(client, owner="0x0")

    res = asyncio.run(run())
    assert res == []


def test_fetch_positions_with_errors(monkeypatch):
    async def handler(request):
        return httpx.Response(200, json={"errors": [{"message": "boom"}]}, headers={"content-type": "application/json"})

    transport = httpx.MockTransport(handler)
    monkeypatch.setenv("UNISWAP_SUBGRAPH_URL", "http://example.com")

    async def run():
        async with httpx.AsyncClient(transport=transport) as client:
            return await uniswap.fetch_positions(client, owner="0x0")

    res = asyncio.run(run())
    assert res is None

def test_with_thegraph_api_key_helper(monkeypatch):
    base = "https://gateway.thegraph.com/api/subgraphs/id/XYZ"
    monkeypatch.setenv("THEGRAPH_API_KEY", "ABC123")
    assert (
        uniswap._with_thegraph_api_key(base)
        == "https://gateway.thegraph.com/api/ABC123/subgraphs/id/XYZ"
    )


def test_subgraph_url_includes_api_key(monkeypatch):
    base = "https://gateway.thegraph.com/api/subgraphs/id/XYZ"
    monkeypatch.setenv("UNISWAP_SUBGRAPH_URL", base)
    monkeypatch.setenv("THEGRAPH_API_KEY", "ABC123")
    assert (
        uniswap._subgraph_url()
        == "https://gateway.thegraph.com/api/ABC123/subgraphs/id/XYZ"
    )

