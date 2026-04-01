# CTF Tasks for Luxury Shop

## Web Challenges

### 1. SQL Injection — "Rich Buyer" (Easy)
**Description:** Find a way to bypass price filters and get expensive items for free.

**Implementation:**
```python
@app.route('/api/products/search')
def search_products():
    query = request.args.get('q', '')
    # Vulnerable: string concatenation
    products = Product.query.filter(
        f"title LIKE '%{query}%' OR description LIKE '%{query}%'"
    ).all()
    return jsonify([p.to_dict() for p in products])
```

**Flag:** `ctf{sql_injection_makes_you_richer}`

**Solution:** Payload: `' OR '1'='1` — returns all products including expensive ones.

---

### 2. IDOR — "VIP Access" (Medium)
**Description:** Access other users' orders without authentication.

**Implementation:**
```python
@app.route('/api/orders/<int:order_id>')
def get_order(order_id):
    # Vulnerable: no auth check
    order = Order.query.get_or_404(order_id)
    return jsonify(order.to_dict())
```

**Flag:** `ctf{idor_exposes_vip_orders}`

**Solution:** Iterate `/api/orders/1`, `/api/orders/2`... to find admin orders.

---

### 3. XSS — "Product Review" (Easy)
**Description:** Add a malicious review that executes JavaScript.

**Implementation:**
```python
@app.route('/api/reviews', methods=['POST'])
def add_review():
    data = request.get_json()
    review = Review(
        product_id=data['product_id'],
        text=data['text'],  # Not sanitized
        author=data['author']
    )
    db.session.add(review)
    db.session.commit()
    return jsonify(review.to_dict())
```

**Frontend (vulnerable):**
```html
<div class="review-text">{{ review.text }}</div>
<!-- Should be: {{ review.text | escape }} -->
```

**Flag:** `ctf{xss_in_product_reviews}`

**Solution:** Submit `<script>alert(document.cookie)</script>` as review text.

---

### 4. Race Condition — "Double Spend" (Hard)
**Description:** Use the same cart items twice before they're cleared.

**Implementation:**
```python
@app.route('/api/orders', methods=['POST'])
def create_order():
    cart_items = CartItem.query.all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    order = Order(total=total)
    db.session.add(order)
    
    # Race: delay before clearing cart
    import time
    time.sleep(0.5)
    
    CartItem.query.delete()
    db.session.commit()
    return jsonify(order.to_dict())
```

**Flag:** `ctf{race_condition_double_spending}`

**Solution:** Send multiple POST requests simultaneously to `/api/orders`.

---

### 5. Broken Access Control — "Cart Hijacking" (Medium)
**Description:** Modify another user's cart by guessing item IDs.

**Implementation:**
```python
@app.route('/api/cart/<int:item_id>', methods=['PUT'])
def update_cart_item(item_id):
    # Vulnerable: no ownership check
    cart_item = CartItem.query.get_or_404(item_id)
    data = request.get_json()
    cart_item.quantity = data.get('quantity', cart_item.quantity)
    db.session.commit()
    return jsonify(cart_item.to_dict())
```

**Flag:** `ctf{cart_hijacking_via_id_guessing}`

**Solution:** Iterate item IDs and modify quantities.

---

### 6. SSRF — "Product Image Fetcher" (Hard)
**Description:** Force the server to fetch internal resources.

**Implementation:**
```python
@app.route('/api/products/import', methods=['POST'])
def import_product():
    data = request.get_json()
    image_url = data.get('image_url')
    
    # Vulnerable: no URL validation
    import requests
    response = requests.get(image_url)
    
    # Save image...
    return jsonify({'status': 'imported'})
```

**Flag:** `ctf{ssrf_internal_network_access}`

**Solution:** Use `http://localhost:5000/api/admin/secret` or `http://169.254.169.254/` (cloud metadata).

---

### 7. Command Injection — "Image Processor" (Hard)
**Description:** Execute commands through image processing.

**Implementation:**
```python
@app.route('/api/products/<id>/resize', methods=['POST'])
def resize_image(id):
    data = request.get_json()
    width = data.get('width', '100')
    
    # Vulnerable: shell=True with user input
    import subprocess
    subprocess.run(
        f"convert images/{id}.jpg -resize {width}x{width} images/{id}_thumb.jpg",
        shell=True
    )
    return jsonify({'status': 'resized'})
```

**Flag:** `ctf{command_injection_via_image_resize}`

**Solution:** Payload: `100; cat /flag.txt #`

---

### 8. Path Traversal — "Product Download" (Medium)
**Description:** Download files outside the intended directory.

**Implementation:**
```python
@app.route('/api/products/<id>/manual')
def get_product_manual(id):
    # Vulnerable: no path validation
    return send_from_directory('manuals', f'{id}.pdf')
```

**Flag:** `ctf{path_traversal_exposes_source}`

**Solution:** Request `/api/products/../../../app.py/manual`

---

### 9. JWT Weak Secret — "Admin Token" (Medium)
**Description:** Forge an admin JWT token.

**Implementation:**
```python
import jwt

SECRET_KEY = "admin"  # Weak secret

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

**Flag:** `ctf{weak_jwt_secret_cracked}`

**Solution:** Brute-force secret with `jwt-crack` or dictionary attack.

---

### 10. Insecure Deserialization — "Cart Import" (Hard)
**Description:** Exploit pickle deserialization.

**Implementation:**
```python
import pickle
import base64

@app.route('/api/cart/import', methods=['POST'])
def import_cart():
    data = request.get_json()
    cart_data = base64.b64decode(data['cart_pickle'])
    
    # Vulnerable: pickle.loads with user input
    cart = pickle.loads(cart_data)
    
    return jsonify({'status': 'imported'})
```

**Flag:** `ctf{pickle_rce_via_deserialization}`

**Solution:** Send malicious pickle payload that executes `os.system('cat /flag')`.

---

## Crypto Challenges

### 11. Weak Hash — "Password Reset" (Easy)
**Description:** Crack admin password from MD5 hash.

**Implementation:**
```python
import hashlib

# In database
admin_hash = "5f4dcc3b5aa765d61d8327deb882cf99"  # MD5 of 'password'

@app.route('/api/auth/reset', methods=['POST'])
def reset_password():
    data = request.get_json()
    user_hash = hashlib.md5(data['password'].encode()).hexdigest()
    
    if user_hash == admin_hash:
        return jsonify({'token': 'admin_access'})
```

**Flag:** `ctf{md5_is_not_secure}`

**Solution:** Use online MD5 cracker or hashcat.

---

### 12. Predictable Session ID — "Session Hijack" (Medium)
**Description:** Predict next session ID.

**Implementation:**
```python
import random

sessions = {}

@app.route('/api/auth/login', methods=['POST'])
def login():
    # Vulnerable: predictable session
    session_id = random.randint(1000, 9999)
    sessions[session_id] = {'user': 'admin'}
    return jsonify({'session_id': session_id})
```

**Flag:** `ctf{predictable_session_ids}`

**Solution:** Brute-force session IDs 1000-9999.

---

## Forensics Challenges

### 13. Database Leak — "SQLite Recovery" (Medium)
**Description:** Find deleted orders in SQLite database.

**Implementation:**
```python
# Provide players with shop.db file
# Deleted orders can be recovered from WAL or free pages
```

**Flag:** `ctf{deleted_orders_recovered}`

**Solution:** Use `sqlite3 shop.db ".dump"` or forensic tools.

---

### 14. Log Analysis — "Admin Activity" (Easy)
**Description:** Find the flag in server logs.

**Implementation:**
```python
# In app.py logging
import logging
logging.basicConfig(filename='app.log', level=logging.INFO)

@app.route('/api/flag')
def get_flag():
    logging.info(f"Flag accessed: {os.environ.get('FLAG')}")
    return "OK"
```

**Flag:** `ctf{logs_reveal_sensitive_data}`

**Solution:** Read `app.log` file.

---

## Misc Challenges

### 15. Hidden Endpoint — "Developer Backdoor" (Easy)
**Description:** Find hidden debug endpoint.

**Implementation:**
```python
@app.route('/api/debug/flag')
def debug_flag():
    if request.remote_addr == '127.0.0.1':
        return jsonify({'flag': os.environ.get('FLAG')})
    return jsonify({'error': 'Local only'})
```

**Flag:** `ctf{hidden_debug_endpoint}`

**Solution:** Access via SSRF or header spoofing `X-Forwarded-For: 127.0.0.1`.

---

### 16. HTTP Headers — "Admin Secret" (Easy)
**Description:** Find flag in custom HTTP headers.

**Implementation:**
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

**Flag:** `ctf{headers_leak_secrets}`

---

## Points System

| Difficulty | Points |
|------------|--------|
| Easy | 100-200 |
| Medium | 300-400 |
| Hard | 500-600 |

---

## Setup Instructions

1. Install dependencies:
```bash
pip install flask flask-sqlalchemy flask-cors pyjwt
```

2. Run the server:
```bash
python app.py
```

3. Set flags as environment variables:
```bash
export FLAG="ctf{actual_flag_here}"
```

4. Enable vulnerabilities by uncommenting specific routes in `app.py`.
