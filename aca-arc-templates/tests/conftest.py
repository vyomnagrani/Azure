import httpx
import pytest

from app.main import create_app
from app.repository import InMemoryInventoryRepository


@pytest.fixture
async def client():
    app = create_app(InMemoryInventoryRepository())
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as test_client:
        yield test_client

