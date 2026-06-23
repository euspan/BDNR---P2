import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    """Cliente HTTP assíncrono com mocks de banco e mensageria."""

    mock_collection = MagicMock()
    mock_collection.insert_one = AsyncMock(return_value=None)

    # Lista de pedidos para simular o banco
    pedidos_armazenados = []

    async def fake_find():
        for p in pedidos_armazenados:
            yield p

    mock_collection.find = MagicMock(return_value=fake_find())

    async def fake_insert(doc):
        pedidos_armazenados.append(doc)

    mock_collection.insert_one = fake_insert

    with (
        patch("app.routers.pedidos.get_collection", return_value=mock_collection),
        patch("app.routers.pedidos.publish_rabbitmq", new_callable=AsyncMock),
        patch("app.routers.pedidos.publish_kafka", new_callable=AsyncMock),
        patch("app.main.connect_db", new_callable=AsyncMock),
        patch("app.main.close_db", new_callable=AsyncMock),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac, pedidos_armazenados


# ── Testes de Cadastro ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_criar_pedido_sucesso(client):
    ac, _ = client
    payload = {
        "nome_cliente": "Maria Souza",
        "nome_produto": "Smartphone Samsung",
        "quantidade": 2,
    }
    response = await ac.post("/pedidos/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["nome_cliente"] == "Maria Souza"
    assert data["nome_produto"] == "Smartphone Samsung"
    assert data["quantidade"] == 2
    assert data["status"] == "PENDENTE"
    assert "id" in data
    assert len(data["id"]) > 0


@pytest.mark.asyncio
async def test_criar_pedido_status_inicial_pendente(client):
    ac, _ = client
    payload = {
        "nome_cliente": "Carlos Lima",
        "nome_produto": "Teclado Mecânico",
        "quantidade": 1,
    }
    response = await ac.post("/pedidos/", json=payload)
    assert response.status_code == 201
    assert response.json()["status"] == "PENDENTE"


@pytest.mark.asyncio
async def test_criar_pedido_quantidade_invalida(client):
    ac, _ = client
    payload = {
        "nome_cliente": "Ana Costa",
        "nome_produto": "Mouse",
        "quantidade": 0,  # inválido
    }
    response = await ac.post("/pedidos/", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_pedido_campos_obrigatorios(client):
    ac, _ = client
    response = await ac.post("/pedidos/", json={"nome_cliente": "Teste"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_pedido_gera_id_unico(client):
    ac, _ = client
    payload = {"nome_cliente": "João", "nome_produto": "Produto X", "quantidade": 1}

    r1 = await ac.post("/pedidos/", json=payload)
    r2 = await ac.post("/pedidos/", json=payload)

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] != r2.json()["id"]


# ── Testes de Listagem ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_listar_pedidos_vazio(client):
    ac, _ = client
    response = await ac.get("/pedidos/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_listar_pedidos_apos_cadastro(client):
    ac, pedidos_db = client

    payload = {
        "nome_cliente": "Lucas Mendes",
        "nome_produto": "Monitor 4K",
        "quantidade": 1,
    }
    criar = await ac.post("/pedidos/", json=payload)
    assert criar.status_code == 201
    pedido_id = criar.json()["id"]

    # Garante que o find retorna o doc inserido
    async def fake_find_com_dados():
        for p in pedidos_db:
            yield p

    mock_col = MagicMock()
    mock_col.find = MagicMock(return_value=fake_find_com_dados())
    mock_col.insert_one = AsyncMock()

    with patch("app.routers.pedidos.get_collection", return_value=mock_col):
        response = await ac.get("/pedidos/")

    assert response.status_code == 200
    ids = [p["id"] for p in response.json()]
    assert pedido_id in ids


@pytest.mark.asyncio
async def test_listar_pedidos_estrutura_correta(client):
    ac, pedidos_db = client

    payload = {"nome_cliente": "Teste", "nome_produto": "Item", "quantidade": 3}
    await ac.post("/pedidos/", json=payload)

    async def fake_find_com_dados():
        for p in pedidos_db:
            yield p

    mock_col = MagicMock()
    mock_col.find = MagicMock(return_value=fake_find_com_dados())
    mock_col.insert_one = AsyncMock()

    with patch("app.routers.pedidos.get_collection", return_value=mock_col):
        response = await ac.get("/pedidos/")

    assert response.status_code == 200
    for pedido in response.json():
        assert "id" in pedido
        assert "nome_cliente" in pedido
        assert "nome_produto" in pedido
        assert "quantidade" in pedido
        assert "status" in pedido


# ── Teste de Health ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check(client):
    ac, _ = client
    response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
