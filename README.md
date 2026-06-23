# 📦 API de Pedidos — FastAPI + MongoDB + RabbitMQ + Kafka

API REST para gerenciamento de pedidos com persistência em MongoDB e comunicação assíncrona via RabbitMQ e Kafka.

---

## 🏗️ Arquitetura

```
pedidos-api/
├── app/
│   ├── main.py          # Entrypoint FastAPI
│   ├── database.py      # Conexão MongoDB (Motor)
│   ├── models.py        # Schemas Pydantic
│   ├── messaging.py     # Publicação RabbitMQ + Kafka
│   └── routers/
│       └── pedidos.py   # Endpoints de pedidos
├── tests/
│   └── test_pedidos.py  # Testes automatizados (Pytest)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── pytest.ini
```

---

## 🚀 Execução com Docker Compose

```bash
docker compose up --build
```

Todos os serviços sobem com um único comando:

| Serviço      | URL / Porta                          |
|-------------|--------------------------------------|
| FastAPI      | http://localhost:8000                |
| Swagger UI   | http://localhost:8000/docs           |
| MongoDB      | mongodb://localhost:27017            |
| RabbitMQ UI  | http://localhost:15672 (guest/guest) |
| Kafka        | localhost:9092                       |
| Zookeeper    | localhost:2181                       |

---

## 📋 Endpoints

### `POST /pedidos/`
Cadastra um novo pedido.

**Body:**
```json
{
  "nome_cliente": "João Silva",
  "nome_produto": "Notebook Dell",
  "quantidade": 1
}
```

**Resposta (201):**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "nome_cliente": "João Silva",
  "nome_produto": "Notebook Dell",
  "quantidade": 1,
  "status": "PENDENTE"
}
```

Ao cadastrar, a API:
- Gera um UUID único
- Salva no MongoDB (coleção `pedidos`)
- Publica mensagem na fila `pedidos_criados` do **RabbitMQ**
- Publica evento no tópico `pedidos-criados` do **Kafka**

---

### `GET /pedidos/`
Lista todos os pedidos cadastrados.

**Resposta (200):**
```json
[
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "nome_cliente": "João Silva",
    "nome_produto": "Notebook Dell",
    "quantidade": 1,
    "status": "PENDENTE"
  }
]
```

---

### `GET /health`
Verifica se a API está no ar.

---

## 🧪 Testes

Execute os testes localmente (sem Docker):

```bash
pip install -r requirements.txt
pytest -v
```

Os testes utilizam mocks para MongoDB, RabbitMQ e Kafka — nenhuma infraestrutura real é necessária.

**Cobertura dos testes:**
- ✅ Cadastro de pedido com sucesso
- ✅ Status inicial sempre `PENDENTE`
- ✅ Validação de quantidade inválida (≤ 0)
- ✅ Validação de campos obrigatórios
- ✅ Geração de IDs únicos por pedido
- ✅ Listagem retorna lista vazia
- ✅ Listagem após cadastro retorna pedidos
- ✅ Estrutura correta dos campos retornados
- ✅ Health check da API

---

## 🔧 Variáveis de Ambiente

| Variável                  | Padrão                          | Descrição                  |
|--------------------------|----------------------------------|----------------------------|
| `MONGO_URL`              | `mongodb://localhost:27017`     | URL do MongoDB             |
| `DB_NAME`                | `pedidos_db`                    | Nome do banco de dados     |
| `RABBITMQ_URL`           | `amqp://guest:guest@localhost/` | URL do RabbitMQ            |
| `KAFKA_BOOTSTRAP_SERVERS`| `localhost:9092`                | Brokers do Kafka           |
