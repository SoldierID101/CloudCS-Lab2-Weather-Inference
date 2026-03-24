# CloudCS Lab 2 — Weather Inference Service with Keycloak

## Описание проекта

Данный проект представляет собой сервис инференса на базе **FastAPI**, разработанный в рамках лабораторных работ по дисциплине, связанной с облачными сервисами.

Во второй лабораторной работе сервис из Lab 1 был расширен:
- добавлена аутентификация и авторизация через **Keycloak**
- выполнена **контейнеризация** сервиса с помощью **Docker**
- настроена **оркестрация** всех сервисов через **docker-compose**

Сервис выполняет предсказание температуры по погодным параметрам.

---

## Используемые технологии

- Python
- FastAPI
- Uvicorn
- Scikit-learn
- Keycloak
- PostgreSQL
- Docker
- Docker Compose

---

## Структура проекта

```text
.
├── src/
│   ├── main.py
│   └── model_utils.py
├── models/
│   └── weather_pipeline.pkl
├── test/
│   ├── test_main.py
│   └── test_model_utils.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## Функциональность

Сервис предоставляет два основных endpoint:

- `GET /healthcheck` — проверка доступности сервиса
- `POST /predictions` — получение предсказания температуры

Endpoint `/predictions` защищён с использованием **Keycloak**.

Поддерживаются три сценария доступа:
- **privileged-client** — доступ разрешён
- **unprivileged-client** — доступ запрещён (`403 Forbidden`)
- запрос без токена — ошибка (`401 Unauthorized`)

---

## Аутентификация и авторизация

Для реализации аутентификации и авторизации используется **Keycloak**.

Настроены следующие клиенты:
- `inference-client` — клиент для проверки токенов
- `privileged-client` — клиент с доступом к `/predictions`
- `unprivileged-client` — клиент без доступа к `/predictions`

В Keycloak настроены:
- Realm: `inference`
- Resource: `/predictions`
- Policy: доступ только для `privileged-client`

---

## Запуск проекта через Docker Compose

### 1. Создать файл `.env`

На основе `.env.example` создать файл `.env` и заполнить реальные значения секретов.

Пример:

```env
MODEL_PATH=models/weather_pipeline.pkl
KEYCLOAK_SERVER_URL=http://keycloak:8080
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin12345

KEYCLOAK_REALM=inference

INFERENCE_CLIENT_ID=inference-client
INFERENCE_CLIENT_SECRET=YOUR_SECRET

PRIVILEGED_CLIENT_ID=privileged-client
PRIVILEGED_CLIENT_SECRET=YOUR_SECRET

UNPRIVILEGED_CLIENT_ID=unprivileged-client
UNPRIVILEGED_CLIENT_SECRET=YOUR_SECRET
```

### 2. Запустить сервисы

```bash
docker compose up --build
```

После запуска будут доступны:
- FastAPI: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Keycloak: `http://localhost:8080`

---

## Проверка работоспособности

### Healthcheck

```bash
curl http://localhost:8000/healthcheck
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

---

## Получение токена для privileged-client

```bash
curl -X POST "http://localhost:8080/realms/inference/protocol/openid-connect/token" ^
-H "Content-Type: application/x-www-form-urlencoded" ^
-d "grant_type=client_credentials" ^
-d "client_id=privileged-client" ^
-d "client_secret=YOUR_SECRET"
```

---

## Получение токена для unprivileged-client

```bash
curl -X POST "http://localhost:8080/realms/inference/protocol/openid-connect/token" ^
-H "Content-Type: application/x-www-form-urlencoded" ^
-d "grant_type=client_credentials" ^
-d "client_id=unprivileged-client" ^
-d "client_secret=YOUR_SECRET"
```

---

## Запрос на предсказание

```bash
curl -X POST "http://127.0.0.1:8000/predictions" ^
-H "Authorization: Bearer YOUR_ACCESS_TOKEN" ^
-H "Content-Type: application/json" ^
-d "{\"hour\":12,\"month\":3,\"precipitation\":0.0,\"pressure\":760.0,\"humidity\":50.0,\"wind_speed\":3.2,\"latitude\":55.75,\"longitude\":37.62,\"height\":150.0}"
```

Пример успешного ответа:

```json
{
  "prediction": {
    "temperature": 39.136
  },
  "client_id": "privileged-client"
}
```

---

## Тестирование доступа

### privileged-client
Ожидаемый результат:
- `200 OK`

### unprivileged-client
Ожидаемый результат:
- `403 Forbidden`

Пример ответа:

```json
{
  "detail": "This client is not allowed to access /predictions"
}
```

### без токена
Ожидаемый результат:
- `401 Unauthorized`

---

## Локальный запуск без Docker

Установка зависимостей:

```bash
pip install -r requirements.txt
```

Запуск приложения:

```bash
cd src
uvicorn main:app --reload
```

---

## Результат выполнения лабораторной работы

В ходе выполнения лабораторной работы были реализованы:

- аутентификация и авторизация сервиса через Keycloak
- разграничение доступа для привилегированного и непривилегированного клиента
- контейнеризация inference-сервиса с помощью Docker
- оркестрация сервисов `postgres`, `keycloak` и `inference` через `docker-compose`
- проверка работоспособности сервиса для всех предусмотренных сценариев доступа

---

## Автор проекта

Лабораторная работа выполнена студентом в рамках курса по облачным сервисам.
