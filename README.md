# FastAPI Microservices – Event Driven Architecture

This project demonstrates a **production-style FastAPI microservices architecture** using:

- JWT authentication (USER / ADMIN roles)
- Event-driven communication with Redis Streams
- Idempotent consumers
- Docker & Docker Compose
- Clear service separation and responsibility

The goal of this project is **learning real-world backend architecture**, not just CRUD APIs.

---

## 🧱 Architecture Overview

### Services

| Service | Responsibility |
|------|---------------|
| **User Service** | User registration, login, JWT issuance |
| **Inventory Service** | Product management, stock handling |
| **Payment Service** | Order creation and payment simulation |
| **Redis** | Event bus between services |

---

## 🔐 Authentication & Authorization

### Roles

- **USER**
  - Can create orders
  - Can read product information

- **ADMIN**
  - Can create, update, and delete products
  - Can read product information

### JWT Rules

- JWT is issued by the **User Service**
- Inventory and Payment services **verify JWT locally**
- Authorization is role-based per endpoint

> Note:  
> Service-to-service calls currently forward the user JWT for authorization.  
> A dedicated SERVICE role or OAuth2 client-credentials flow can be added later as a production enhancement.

---

## 🔁 Event Flow (Order Lifecycle)

1. USER creates an order via **Payment Service**
2. Payment Service publishes `order_completed` event to Redis
3. Inventory Consumer:
   - Checks product availability
   - Updates quantity if sufficient
   - Otherwise publishes a refund event
4. Payment Consumer handles refund events

---

## 🛡️ Idempotency

Consumers are **idempotent**:

- Redis Stream message ID is used as idempotency key
- Redis `SET` tracks processed messages
- Prevents duplicate processing on restarts or re-deliveries

This ensures **effectively-once processing** on top of Redis Streams’ at-least-once delivery.

---

## 🐳 Docker Setup

### Docker Images

All services are containerized and published to **Docker Hub**.

### Run with Docker Compose

```bash
docker compose up
