# CTF Задачи для Luxury Shop

## Web Challenges

### 1. SQL Injection — "Богатый Покупатель" (Лёгкая)

**Описание:** Найдите способ обойти фильтры цен и получить дорогие товары бесплатно.

**Реализация:**

```python
@app.route('/api/products/search')
def search_products():
    query = request.args.get('q', '')
    # Уязвимость: конкатенация строк
    products = Product.query.filter(
        f"title LIKE '%{query}%' OR description LIKE '%{query}%'"
    ).all()
    return jsonify([p.to_dict() for p in products])
```

**Флаг:** `ctf{sql_injection_makes_you_richer}`

**Решение:** Payload: `' OR '1'='1` — возвращает все товары.

---

### 2. IDOR — "VIP Доступ" (Средняя)

**Описание:** Доступ к чужим заказам без аутентификации.

**Реализация:**

```python
@app.route('/api/orders/<int:order_id>')
def get_order(order_id):
    # Уязвимость: нет проверки прав
    order = Order.query.get_or_404(order_id)
    return jsonify(order.to_dict())
```

**Флаг:** `ctf{idor_exposes_vip_orders}`

**Решение:** Перебирать `/api/orders/1`, `/api/orders/2`... для поиска заказов админа.

---

### 3. XSS — "Отзыв о Товаре" (Лёгкая)

**Описание:** Добавить вредоносный отзыв с выполнением JavaScript.

**Реализация:**

```python
@app.route('/api/reviews', methods=['POST'])
def add_review():
    data = request.get_json()
    review = Review(
        product_id=data['product_id'],
        text=data['text'],  # Не санируется
        author=data['author']
    )
    db.session.add(review)
    db.session.commit()
    return jsonify(review.to_dict())
```

**Фронтенд (уязвимый):**

```html
<div class="review-text">{{ review.text }}</div>
<!-- Должно быть: {{ review.text | escape }} -->
```

**Флаг:** `ctf{xss_in_product_reviews}`

**Решение:** Отправить `<script>alert(document.cookie)</script>` как текст отзыва.

---

### 4. Race Condition — "Двойная Трата" (Сложная)

**Описание:** Использовать элементы корзины дважды до их очистки.

**Реализация:**

```python
@app.route('/api/orders', methods=['POST'])
def create_order():
    cart_items = CartItem.query.all()
    total = sum(item.product.price * item.quantity for item in cart_items)

    order = Order(total=total)
    db.session.add(order)

    # Race: задержка перед очисткой корзины
    import time
    time.sleep(0.5)

    CartItem.query.delete()
    db.session.commit()
    return jsonify(order.to_dict())
```

**Флаг:** `ctf{race_condition_double_spending}`

**Решение:** Отправить несколько POST запросов на `/api/orders` одновременно.

---

### 5. Broken Access Control — "Перехват Корзины" (Средняя)

**Описание:** Изменить чужую корзину через угадывание ID элементов.

**Реализация:**

```python
@app.route('/api/cart/<int:item_id>', methods=['PUT'])
def update_cart_item(item_id):
    # Уязвимость: нет проверки владельца
    cart_item = CartItem.query.get_or_404(item_id)
    data = request.get_json()
    cart_item.quantity = data.get('quantity', cart_item.quantity)
    db.session.commit()
    return jsonify(cart_item.to_dict())
```

**Флаг:** `ctf{cart_hijacking_via_id_guessing}`

**Решение:** Перебирать ID элементов и изменять количество.

---

### 6. SSRF — "Загрузчик Изображений" (Сложная)

**Описание:** Заставить сервер загружать внутренние ресурсы.

**Реализация:**

```python
@app.route('/api/products/import', methods=['POST'])
def import_product():
    data = request.get_json()
    image_url = data.get('image_url')

    # Уязвимость: нет валидации URL
    import requests
    response = requests.get(image_url)

    # Сохранение изображения...
    return jsonify({'status': 'imported'})
```

**Флаг:** `ctf{ssrf_internal_network_access}`

**Решение:** Использовать `http://localhost:5000/api/admin/secret` или `http://169.254.169.254/` (метаданные облака).

---

### 7. Command Injection — "Обработчик Изображений" (Сложная)

**Описание:** Выполнение команд через обработку изображений.

**Реализация:**

```python
@app.route('/api/products/<id>/resize', methods=['POST'])
def resize_image(id):
    data = request.get_json()
    width = data.get('width', '100')

    # Уязвимость: shell=True с пользовательским вводом
    import subprocess
    subprocess.run(
        f"convert images/{id}.jpg -resize {width}x{width} images/{id}_thumb.jpg",
        shell=True
    )
    return jsonify({'status': 'resized'})
```

**Флаг:** `ctf{command_injection_via_image_resize}`

**Решение:** Payload: `100; cat /flag.txt #`

---

### 8. Path Traversal — "Скачивание Товара" (Средняя)

**Описание:** Скачивание файлов за пределами разрешённой директории.

**Реализация:**

```python
@app.route('/api/products/<id>/manual')
def get_product_manual(id):
    # Уязвимость: нет валидации пути
    return send_from_directory('manuals', f'{id}.pdf')
```

**Флаг:** `ctf{path_traversal_exposes_source}`

**Решение:** Запрос `/api/products/../../../app.py/manual`

---

### 9. JWT Weak Secret — "Токен Админа" (Средняя)

**Описание:** Подделка JWT токена админа.

**Реализация:**

```python
import jwt

SECRET_KEY = "admin"  # Слабый секрет

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if data['username'] == 'admin' and data['password'] == 'admin123':
        token = jwt.encode(
            {'role': 'admin', 'username': data['username']},
            SECRET_KEY,
            algorithm='HS256'
        )
        return jsonify({'token': token})
```

**Флаг:** `ctf{weak_jwt_secret_cracked}`

**Решение:** Брутфорс секрета через `jwt-crack` или словарная атака.

---

### 10. Insecure Deserialization — "Импорт Корзины" (Сложная)

**Описание:** Эксплуатация десериализации pickle.

**Реализация:**

```python
import pickle
import base64

@app.route('/api/cart/import', methods=['POST'])
def import_cart():
    data = request.get_json()
    cart_data = base64.b64decode(data['cart_pickle'])

    # Уязвимость: pickle.loads с пользовательским вводом
    cart = pickle.loads(cart_data)

    return jsonify({'status': 'imported'})
```

**Флаг:** `ctf{pickle_rce_via_deserialization}`

**Решение:** Отправить malicious pickle payload с `os.system('cat /flag')`.

---

## Crypto Challenges

### 11. Weak Hash — "Сброс Пароля" (Лёгкая)

**Описание:** Взломать пароль админа из MD5 хеша.

**Реализация:**

```python
import hashlib

# В базе данных
admin_hash = "5f4dcc3b5aa765d61d8327deb882cf99"  # MD5 от 'password'

@app.route('/api/auth/reset', methods=['POST'])
def reset_password():
    data = request.get_json()
    user_hash = hashlib.md5(data['password'].encode()).hexdigest()

    if user_hash == admin_hash:
        return jsonify({'token': 'admin_access'})
```

**Флаг:** `ctf{md5_is_not_secure}`

**Решение:** Использовать онлайн MD5 крэкер или hashcat.

---

### 12. Predictable Session ID — "Перехват Сессии" (Средняя)

**Описание:** Предсказать следующий ID сессии.

**Реализация:**

```python
import random

sessions = {}

@app.route('/api/auth/login', methods=['POST'])
def login():
    # Уязвимость: предсказуемая сессия
    session_id = random.randint(1000, 9999)
    sessions[session_id] = {'user': 'admin'}
    return jsonify({'session_id': session_id})
```

**Флаг:** `ctf{predictable_session_ids}`

**Решение:** Брутфорс ID сессий от 1000 до 9999.

---

## Forensics Challenges

### 13. Database Leak — "Восстановление SQLite" (Средняя)

**Описание:** Найти удалённые заказы в SQLite базе.

**Реализация:**

```python
# Предоставить игрокам файл shop.db
# Удалённые заказы можно восстановить из WAL или свободных страниц
```

**Флаг:** `ctf{deleted_orders_recovered}`

**Решение:** Использовать `sqlite3 shop.db ".dump"` или forensic инструменты.

---

### 14. Log Analysis — "Активность Админа" (Лёгкая)

**Описание:** Найти флаг в логах сервера.

**Реализация:**

```python
# В логировании app.py
import logging
logging.basicConfig(filename='app.log', level=logging.INFO)

@app.route('/api/flag')
def get_flag():
    logging.info(f"Flag accessed: {os.environ.get('FLAG')}")
    return "OK"
```

**Флаг:** `ctf{logs_reveal_sensitive_data}`

**Решение:** Прочитать файл `app.log`.

---

## Misc Challenges

### 15. Hidden Endpoint — "Бэкдор Разработчика" (Лёгкая)

**Описание:** Найти скрытую debug конечную точку.

**Реализация:**

```python
@app.route('/api/debug/flag')
def debug_flag():
    if request.remote_addr == '127.0.0.1':
        return jsonify({'flag': os.environ.get('FLAG')})
    return jsonify({'error': 'Local only'})
```

**Флаг:** `ctf{hidden_debug_endpoint}`

**Решение:** Доступ через SSRF или спухинг заголовка `X-Forwarded-For: 127.0.0.1`.

---

### 16. HTTP Headers — "Секрет Админа" (Лёгкая)

**Описание:** Найти флаг в кастомных HTTP заголовках.

**Реализация:**

```python
@app.after_request
def add_headers(response):
    response.headers['X-CTF-Hint'] = 'Check admin config'
    return response

@app.route('/api/admin/config')
def admin_config():
    return jsonify({
        'debug': True,
        'secret': os.environ.get('FLAG'),
        'version': '1.0.0'
    })
```

**Флаг:** `ctf{headers_leak_secrets}`

---

## Система Баллов

| Сложность | Баллы   |
| --------- | ------- |
| Лёгкая    | 100-200 |
| Средняя   | 300-400 |
| Сложная   | 500-600 |

---

## Инструкция по Установке

1. Установить зависимости:

```bash
pip install flask flask-sqlalchemy flask-cors pyjwt
```

2. Запустить сервер:

```bash
python app.py
```

3. Установить флаги как переменные окружения:

```bash
export FLAG="ctf{actual_flag_here}"
```

4. Включить уязвимости раскомментированием соответствующих роутов в `app.py`.
