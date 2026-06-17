# Особистий фінансовий менеджер

Веб-застосунок для обліку особистих фінансів з підтримкою імпорту транзакцій через Monobank API та webhook.

## Стек технологій

| Рівень | Технологія |
|--------|-----------|
| Backend | Flask 3, SQLAlchemy 2, Flask-JWT-Extended |
| База даних | PostgreSQL 16 |
| Черги завдань | Celery 5 + Redis 7 |
| Frontend | React 18, Vite, Tailwind CSS, Recharts |
| Контейнеризація | Docker + Docker Compose |

## Архітектура

```
┌─────────────┐     ┌──────────────┐     ┌───────────┐
│   React SPA  │────▶│  Flask API   │────▶│ PostgreSQL │
│  (nginx:80)  │     │(gunicorn:5000│     └───────────┘
└─────────────┘     └──────────────┘
                           │               ┌───────────┐
                           └──────────────▶│   Redis   │
                                           └─────┬─────┘
                                                 │
                                           ┌─────▼─────┐
                                           │   Celery   │
                                           │   Worker   │
                                           └───────────┘
```

## Швидкий старт (Docker)

### 1. Клонуйте репозиторій

```bash
git clone <repo-url>
```

### 2. Налаштуйте змінні середовища

```bash
cp .env.example .env
```

Відредагуйте `.env` та заповніть:

```env
# Генерація Fernet-ключа:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=<your-fernet-key>

JWT_SECRET_KEY=<your-jwt-secret>
WEBHOOK_SECRET=<your-webhook-secret>
```

### 3. Запустіть

```bash
docker compose up --build
```

Застосунок буде доступний на [http://localhost](http://localhost).

---

## Локальна розробка (без Docker)

### Backend

```bash
cd backend

# Створіть та активуйте віртуальне середовище
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# або
.venv\Scripts\activate         # Windows

# Встановіть залежності
pip install -r requirements.txt

# Встановіть змінні середовища
export FLASK_APP=app
export FLASK_ENV=development
export DATABASE_URL=postgresql://finance:finance@localhost:5432/finance
export CELERY_BROKER_URL=redis://localhost:6379/0
export CELERY_RESULT_BACKEND=redis://localhost:6379/0
export ENCRYPTION_KEY=<your-fernet-key>
export JWT_SECRET_KEY=<your-jwt-secret>
export WEBHOOK_SECRET=<your-webhook-secret>

# Запустіть міграції
flask db upgrade

# Запустіть сервер
flask run
```

### Celery Worker

```bash
# В окремому терміналі (з тієї ж теки backend, з активованим venv)
celery -A app.extensions.celery worker --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Застосунок: [http://localhost:3000](http://localhost:3000)  
API: [http://localhost:5000](http://localhost:5000)

---

## Тести

### Backend (pytest)

```bash
cd backend
pip install pytest
pytest tests/ -v
```

### Frontend (Vitest)

```bash
cd frontend
npm install
npm test
```

---

## Основні можливості

- **Автентифікація** — реєстрація/вхід, HttpOnly JWT cookies, зміна пароля
- **Транзакції** — ручне додавання, фільтрація за датою/типом/категорією, пагінація
- **Категорії** — системні (за MCC-кодом) та власні, пріоритети, регулярні вирази в описі
- **Бюджети** — місячні бюджети з прогрес-баром, копіювання з попереднього місяця
- **Аналітика** — кругова діаграма витрат, місячний тренд, теплова карта активності
- **Monobank** — підключення рахунків через токен, імпорт виписок за будь-який період, webhook для нових транзакцій в реальному часі
- **PrivatBank** — актуальний курс валют (з кешуванням у Redis)
- **Сповіщення** — попередження при досягненні 70% та 100% бюджету

## Структура проєкту

```
.
├── backend/
│   ├── app/
│   │   ├── api/          # Blueprint-и: auth, transactions, budgets, …
│   │   ├── models/       # SQLAlchemy-моделі
│   │   ├── services/     # Бізнес-логіка (monobank, categorizer, analytics, …)
│   │   └── utils/        # Шифрування, валідатори
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/          # Axios-клієнт з CSRF та авто-рефрешем
│   │   ├── components/   # UI-компоненти та графіки
│   │   ├── context/      # AuthContext
│   │   └── pages/        # Сторінки застосунку
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── .env.example
```

## Налаштування Monobank Webhook

1. Перейдіть у **Налаштування → Підключити Monobank**.
2. Введіть API-токен Monobank.
3. Нові транзакції надходитимуть у реальному часі.

> **Важливо**: для роботи webhook сервер має бути доступний з інтернету (або через ngrok під час розробки).
