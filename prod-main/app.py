from flask import Flask, send_from_directory, jsonify, request, g
from flask_cors import CORS
from datetime import datetime
import json
import os
import sqlite3

app = Flask(__name__, static_folder='.')
app.config['DATABASE'] = 'shop.db'
CORS(app)


# === Database ===
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    c = db.cursor()
    
    # Create tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS product (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            price INTEGER NOT NULL,
            image TEXT,
            description TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS cart_item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES product(id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS "order" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS order_item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES "order"(id),
            FOREIGN KEY (product_id) REFERENCES product(id)
        )
    ''')
    
    db.commit()
    
    # Initialize products if empty
    c.execute('SELECT COUNT(*) FROM product')
    if c.fetchone()[0] == 0:
        with open('data.json', 'r') as f:
            data = json.load(f)
        for p in data['products']:
            c.execute(
                'INSERT INTO product (id, title, type, price, image, description) VALUES (?, ?, ?, ?, ?, ?)',
                (p['id'], p['title'], p['type'], p['price'], p['image'], p['description'])
            )
        db.commit()
        print('✓ Products initialized from data.json')
    
    # Initialize sample orders if empty
    c.execute('SELECT COUNT(*) FROM "order"')
    if c.fetchone()[0] == 0:
        c.execute('SELECT id, price FROM product LIMIT 3')
        products = c.fetchall()
        if products:
            total = sum(p['price'] for p in products)
            c.execute('INSERT INTO "order" (total, status) VALUES (?, ?)', (total, 'completed'))
            order_id = c.lastrowid
            
            for p in products:
                c.execute(
                    'INSERT INTO order_item (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
                    (order_id, p['id'], 1, p['price'])
                )
            db.commit()
            print('✓ Sample orders initialized')
    
    # Print summary
    c.execute('SELECT COUNT(*) FROM product')
    products_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM cart_item')
    cart_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM "order"')
    orders_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM order_item')
    order_items_count = c.fetchone()[0]
    
    print(f'\n📊 Database Summary:')
    print(f'   Products: {products_count}')
    print(f'   Cart Items: {cart_count}')
    print(f'   Orders: {orders_count}')
    print(f'   Order Items: {order_items_count}\n')
    
    db.close()


# === Static Files ===
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)


# === API: Products ===
@app.route('/api/products', methods=['GET'])
def get_products():
    db = get_db()
    products = db.execute('SELECT * FROM product').fetchall()
    return jsonify([dict(p) for p in products])


@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    db = get_db()
    product = db.execute('SELECT * FROM product WHERE id = ?', (product_id,)).fetchone()
    if product is None:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(dict(product))


@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.get_json()
    db = get_db()
    db.execute(
        'INSERT INTO product (id, title, type, price, image, description) VALUES (?, ?, ?, ?, ?, ?)',
        (data.get('id'), data.get('title'), data.get('type'), data.get('price'), data.get('image'), data.get('description'))
    )
    db.commit()
    product = db.execute('SELECT * FROM product WHERE id = ?', (data.get('id'),)).fetchone()
    return jsonify(dict(product)), 201


# === API: Cart ===
@app.route('/api/cart', methods=['GET'])
def get_cart():
    db = get_db()
    items = db.execute('''
        SELECT ci.id, ci.product_id, ci.quantity, ci.created_at,
               p.id as p_id, p.title as p_title, p.type as p_type, p.price as p_price, p.image as p_image, p.description as p_description
        FROM cart_item ci
        JOIN product p ON ci.product_id = p.id
    ''').fetchall()
    
    cart_items = []
    total = 0
    for item in items:
        cart_items.append({
            'id': item['id'],
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'created_at': item['created_at'],
            'product': {
                'id': item['p_id'],
                'title': item['p_title'],
                'type': item['p_type'],
                'price': item['p_price'],
                'image': item['p_image'],
                'description': item['p_description']
            }
        })
        total += item['p_price'] * item['quantity']
    
    return jsonify({'items': cart_items, 'total': total})


@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    db = get_db()
    cart_item = db.execute('SELECT * FROM cart_item WHERE product_id = ?', (product_id,)).fetchone()
    
    if cart_item:
        db.execute('UPDATE cart_item SET quantity = quantity + ? WHERE product_id = ?', (quantity, product_id))
    else:
        db.execute('INSERT INTO cart_item (product_id, quantity) VALUES (?, ?)', (product_id, quantity))
    
    db.commit()
    
    item = db.execute('SELECT * FROM cart_item WHERE product_id = ?', (product_id,)).fetchone()
    return jsonify(dict(item)), 201


@app.route('/api/cart/<int:item_id>', methods=['PUT'])
def update_cart_item(item_id):
    data = request.get_json()
    db = get_db()
    db.execute('UPDATE cart_item SET quantity = ? WHERE id = ?', (data.get('quantity', 1), item_id))
    db.commit()
    item = db.execute('SELECT * FROM cart_item WHERE id = ?', (item_id,)).fetchone()
    return jsonify(dict(item))


@app.route('/api/cart/<int:item_id>', methods=['DELETE'])
def remove_from_cart(item_id):
    db = get_db()
    db.execute('DELETE FROM cart_item WHERE id = ?', (item_id,))
    db.commit()
    return jsonify({'message': 'Removed'}), 200


@app.route('/api/cart', methods=['DELETE'])
def clear_cart():
    db = get_db()
    db.execute('DELETE FROM cart_item')
    db.commit()
    return jsonify({'message': 'Cart cleared'}), 200


# === API: Orders ===
@app.route('/api/orders', methods=['GET'])
def get_orders():
    db = get_db()
    orders = db.execute('SELECT * FROM "order" ORDER BY created_at DESC').fetchall()
    
    result = []
    for order in orders:
        items = db.execute('''
            SELECT oi.*, p.id as p_id, p.title as p_title, p.type as p_type, p.image as p_image, p.description as p_description
            FROM order_item oi
            JOIN product p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order['id'],)).fetchall()
        
        order_dict = dict(order)
        order_dict['items'] = [
            {
                'id': i['id'],
                'order_id': i['order_id'],
                'product_id': i['product_id'],
                'quantity': i['quantity'],
                'price': i['price'],
                'product': {
                    'id': i['p_id'],
                    'title': i['p_title'],
                    'type': i['p_type'],
                    'image': i['p_image'],
                    'description': i['p_description']
                }
            } for i in items
        ]
        result.append(order_dict)
    
    return jsonify(result)


@app.route('/api/orders', methods=['POST'])
def create_order():
    db = get_db()
    cart_items = db.execute('SELECT * FROM cart_item').fetchall()
    
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400
    
    # Calculate total
    total = 0
    for item in cart_items:
        product = db.execute('SELECT price FROM product WHERE id = ?', (item['product_id'],)).fetchone()
        total += product['price'] * item['quantity']
    
    # Create order
    db.execute('INSERT INTO "order" (total, status) VALUES (?, ?)', (total, 'completed'))
    order_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    
    # Create order items
    for item in cart_items:
        product = db.execute('SELECT price FROM product WHERE id = ?', (item['product_id'],)).fetchone()
        db.execute(
            'INSERT INTO order_item (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
            (order_id, item['product_id'], item['quantity'], product['price'])
        )
    
    # Clear cart
    db.execute('DELETE FROM cart_item')
    db.commit()
    
    # Return order with items
    order = db.execute('SELECT * FROM "order" WHERE id = ?', (order_id,)).fetchone()
    items = db.execute('SELECT * FROM order_item WHERE order_id = ?', (order_id,)).fetchall()
    
    order_dict = dict(order)
    order_dict['items'] = [dict(i) for i in items]
    
    return jsonify(order_dict), 201


# === Debug Page ===
@app.route('/debug')
def debug_page():
    return send_from_directory('.', 'debug.html')


@app.route('/debug/data')
def debug_data():
    db = get_db()
    
    # Database info
    db_info = {
        'uri': f"sqlite:///{app.config['DATABASE']}",
        'products_count': db.execute('SELECT COUNT(*) FROM product').fetchone()[0],
        'cart_items_count': db.execute('SELECT COUNT(*) FROM cart_item').fetchone()[0],
        'orders_count': db.execute('SELECT COUNT(*) FROM "order"').fetchone()[0],
        'order_items_count': db.execute('SELECT COUNT(*) FROM order_item').fetchone()[0],
    }
    
    # System info
    system_info = {
        'python_version': os.popen('python3 --version').read().strip(),
        'flask_version': os.popen('python3 -c "import flask; print(flask.__version__)"').read().strip(),
        'cwd': os.getcwd(),
        'flag': os.environ.get('FLAG', 'Not set'),
    }
    
    # All products
    products = db.execute('SELECT * FROM product').fetchall()
    
    # All cart items
    cart_items = db.execute('SELECT * FROM cart_item').fetchall()
    
    # All orders with items
    orders = db.execute('SELECT * FROM "order"').fetchall()
    orders_data = []
    for order in orders:
        items = db.execute('SELECT * FROM order_item WHERE order_id = ?', (order['id'],)).fetchall()
        order_dict = dict(order)
        order_dict['items'] = [dict(i) for i in items]
        orders_data.append(order_dict)
    
    # All order items
    order_items = db.execute('SELECT * FROM order_item').fetchall()
    
    # Config
    config = {
        'debug': app.debug,
        'secret_key': str(app.secret_key) if app.secret_key else 'Not set',
        'cors_enabled': True,
    }
    
    # Environment variables (filter sensitive)
    env_vars = [f'{k} = {v}' for k, v in sorted(os.environ.items())
                if 'SECRET' not in k.upper() and 'PASSWORD' not in k.upper()]
    
    # Database schema
    db_schema = {
        'product': ['id', 'title', 'type', 'price', 'image', 'description'],
        'cart_item': ['id', 'product_id', 'quantity', 'created_at'],
        'order': ['id', 'total', 'status', 'created_at'],
        'order_item': ['id', 'order_id', 'product_id', 'quantity', 'price'],
    }
    
    return jsonify({
        'flag': system_info['flag'],
        'system': system_info,
        'database': db_info,
        'config': config,
        'products': [dict(p) for p in products],
        'cart_items': [dict(item) for item in cart_items],
        'orders': orders_data,
        'order_items': [dict(i) for i in order_items],
        'env_vars': env_vars,
        'db_schema': db_schema
    })


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5002)
