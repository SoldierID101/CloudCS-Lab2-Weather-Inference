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