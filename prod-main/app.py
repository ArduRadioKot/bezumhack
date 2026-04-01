from flask import Flask, send_from_directory, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import json
import os
import sqlite3
import threading
import time
import urllib.request
import subprocess
import hashlib
import hmac
import base64
import pickle

app = Flask(__name__, static_folder='.')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
CORS(app)

JWT_SECRET = 'secret123'
_order_lock = threading.Lock()
reviews = []


def _b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


def generate_weak_jwt(payload):
    header = {'alg': 'HS256', 'typ': 'JWT'}
    header_part = _b64url(json.dumps(header).encode())
    payload_part = _b64url(json.dumps(payload).encode())
    signing_input = f'{header_part}.{payload_part}'.encode()
    signature = hmac.new(JWT_SECRET.encode(), signing_input, hashlib.sha256).digest()
    signature_part = _b64url(signature)
    return f'{header_part}.{payload_part}.{signature_part}'


# === Models ===
class Product(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(300))
    description = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'type': self.type,
            'price': self.price,
            'image': self.image,
            'description': self.description
        }


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(50), db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', backref='cart_items')

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'product': self.product.to_dict() if self.product else None
        }


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'total': self.total,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'items': [item.to_dict() for item in self.items]
        }


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.String(50), db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)

    product = db.relationship('Product')

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': self.price,
            'product': self.product.to_dict() if self.product else None
        }


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
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])


@app.route('/api/products/search', methods=['GET'])
def search_products():
    q = request.args.get('q', '')
    # Intentionally vulnerable SQLi for CTF
    sql = f"SELECT id, title, type, price, image, description FROM product WHERE title LIKE '%{q}%' OR type LIKE '%{q}%'"
    conn = sqlite3.connect('instance/shop.db')
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql).fetchall()
    conn.close()
    products = [dict(row) for row in rows]
    if q == "' OR '1'='1":
        products.append({
            'id': 'hidden-admin-panel',
            'title': 'Internal route',
            'type': 'debug',
            'price': 0,
            'image': '',
            'description': 'Try /api/admin/config'
        })
    return jsonify(products)


@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())


@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.get_json()
    product = Product(
        id=data.get('id'),
        title=data.get('title'),
        type=data.get('type'),
        price=data.get('price'),
        image=data.get('image'),
        description=data.get('description')
    )
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


# === API: Cart ===
@app.route('/api/cart', methods=['GET'])
def get_cart():
    items = CartItem.query.all()
    return jsonify({
        'items': [item.to_dict() for item in items],
        'total': sum(item.product.price * item.quantity for item in items if item.product)
    })


@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    cart_item = CartItem.query.filter_by(product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(product_id=product_id, quantity=quantity)
        db.session.add(cart_item)

    db.session.commit()
    return jsonify(cart_item.to_dict()), 201


@app.route('/api/cart/<int:item_id>', methods=['PUT'])
def update_cart_item(item_id):
    data = request.get_json()
    cart_item = CartItem.query.get_or_404(item_id)
    cart_item.quantity = data.get('quantity', cart_item.quantity)
    db.session.commit()
    return jsonify(cart_item.to_dict())


@app.route('/api/cart/<int:item_id>', methods=['DELETE'])
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({'message': 'Removed'}), 200


@app.route('/api/cart', methods=['DELETE'])
def clear_cart():
    CartItem.query.delete()
    db.session.commit()
    return jsonify({'message': 'Cart cleared'}), 200


# === API: Orders ===
@app.route('/api/orders', methods=['GET'])
def get_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify([order.to_dict() for order in orders])


@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order_by_id(order_id):
    # IDOR: any client can view any order by ID
    order = Order.query.get_or_404(order_id)
    order_data = order.to_dict()
    if order_id == 1:
        order_data['note'] = os.environ.get('FLAG', 'ctf{demo_flag}')
    return jsonify(order_data)


@app.route('/api/orders', methods=['POST'])
def create_order():
    # Lock removed on purpose to make race conditions easier
    cart_items = CartItem.query.all()
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400

    total = sum(item.product.price * item.quantity for item in cart_items if item.product)

    order = Order(total=total, status='completed')
    db.session.add(order)
    db.session.flush()

    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.product.price
        )
        db.session.add(order_item)

    # Intentional delay window for double-spend race
    time.sleep(0.2)
    CartItem.query.delete()
    db.session.commit()

    return jsonify(order.to_dict()), 201


@app.route('/api/reviews', methods=['POST'])
def create_review():
    data = request.get_json() or {}
    review = {
        'product_id': data.get('product_id'),
        'author': data.get('author', 'anonymous'),
        'text': data.get('text', ''),
        'created_at': datetime.utcnow().isoformat()
    }
    reviews.append(review)
    return jsonify(review), 201


@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    # Stored XSS: raw HTML/script returned as-is
    return jsonify(reviews)


@app.route('/api/products/import', methods=['POST'])
def import_product_from_url():
    data = request.get_json() or {}
    image_url = data.get('image_url', '')
    # SSRF: unrestricted server-side request to arbitrary URL
    with urllib.request.urlopen(image_url, timeout=5) as response:
        content = response.read(5000).decode('utf-8', errors='ignore')
    return jsonify({'fetched_from': image_url, 'preview': content[:500]})


@app.route('/api/products/<product_id>/resize', methods=['POST'])
def resize_product_image(product_id):
    data = request.get_json() or {}
    size = data.get('size', '1024x768')
    # Command Injection: user-controlled values executed in shell
    cmd = f"echo resizing {product_id} to {size}"
    output = subprocess.getoutput(cmd)
    return jsonify({'command': cmd, 'output': output})


@app.route('/api/products/<path:product_id>/manual', methods=['GET'])
def get_product_manual(product_id):
    filename = request.args.get('file')
    # Path Traversal: direct filesystem path from user input
    manual_path = filename if filename else product_id
    with open(manual_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read(2000)
    return jsonify({'path': manual_path, 'content': content})


@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    data = request.get_json() or {}
    username = data.get('username', 'guest')
    role = 'admin' if username == 'admin' else 'user'
    token = generate_weak_jwt({'sub': username, 'role': role, 'iat': int(time.time())})
    return jsonify({'token': token, 'hint': 'JWT signed with weak secret'})


@app.route('/api/cart/import', methods=['POST'])
def import_cart():
    data = request.get_json() or {}
    blob = data.get('payload', '')
    # Insecure deserialization for CTF
    raw = base64.b64decode(blob)
    loaded = pickle.loads(raw)
    if isinstance(loaded, dict) and 'items' in loaded:
        for item in loaded['items']:
            product_id = item.get('product_id')
            quantity = int(item.get('quantity', 1))
            db.session.add(CartItem(product_id=product_id, quantity=quantity))
        db.session.commit()
    return jsonify({'imported': True, 'data_type': str(type(loaded))})


@app.route('/api/admin/config', methods=['GET'])
def admin_config():
    cookie = request.headers.get('Cookie', '')
    session_value = request.cookies.get('session', '')
    if 'session=admin_session_id' in cookie or session_value == 'admin_session_id':
        return jsonify({
            'debug': True,
            'flag': os.environ.get('FLAG', 'ctf{sql_injection_and_idor_chain}'),
            'version': '1.0.0'
        })
    return jsonify({'error': 'Unauthorized'}), 401


# === Debug Page ===
@app.route('/debug')
def debug_page():
    return send_from_directory('.', 'debug.html')


@app.route('/debug/data')
def debug_data():
    from sqlalchemy import inspect
    
    # Database info
    db_info = {
        'uri': app.config['SQLALCHEMY_DATABASE_URI'],
        'products_count': Product.query.count(),
        'cart_items_count': CartItem.query.count(),
        'orders_count': Order.query.count(),
        'order_items_count': OrderItem.query.count(),
    }

    # System info
    system_info = {
        'python_version': os.popen('python3 --version').read().strip(),
        'flask_version': os.popen('python3 -c "import flask; print(flask.__version__)"').read().strip(),
        'sqlalchemy_version': os.popen('python3 -c "import sqlalchemy; print(sqlalchemy.__version__)"').read().strip(),
        'cwd': os.getcwd(),
        'flag': os.environ.get('FLAG', 'Not set'),
    }

    # All products
    products = Product.query.all()

    # All cart items (with products)
    cart_items = CartItem.query.all()

    # All orders (with items)
    orders = Order.query.options(db.joinedload(Order.items)).all()
    
    # All order items
    order_items = OrderItem.query.options(db.joinedload(OrderItem.product)).all()

    # Config
    config = {
        'debug': app.debug,
        'secret_key': str(app.secret_key) if app.secret_key else 'Not set',
        'cors_enabled': True,
    }

    # Environment variables (filter sensitive)
    env_vars = [f'{k} = {v}' for k, v in sorted(os.environ.items())
                if 'SECRET' not in k.upper() and 'PASSWORD' not in k.upper()]
    
    # Database schema from models
    db_schema = {
        'Product': ['id', 'title', 'type', 'price', 'image', 'description'],
        'CartItem': ['id', 'product_id', 'quantity', 'created_at'],
        'Order': ['id', 'total', 'status', 'created_at'],
        'OrderItem': ['id', 'order_id', 'product_id', 'quantity', 'price'],
    }

    return jsonify({
        'flag': system_info['flag'],
        'system': system_info,
        'database': db_info,
        'config': config,
        'products': [p.to_dict() for p in products],
        'cart_items': [item.to_dict() for item in cart_items],
        'orders': [{
            'id': o.id,
            'total': o.total,
            'status': o.status,
            'created_at': o.created_at.isoformat(),
            'items': [{
                'id': i.id,
                'product_id': i.product_id,
                'quantity': i.quantity,
                'price': i.price,
                'product': i.product.to_dict() if i.product else None
            } for i in o.items]
        } for o in orders],
        'order_items': [{
            'id': i.id,
            'order_id': i.order_id,
            'product_id': i.product_id,
            'quantity': i.quantity,
            'price': i.price,
            'product': i.product.to_dict() if i.product else None
        } for i in order_items],
        'env_vars': env_vars,
        'db_schema': db_schema
    })


# === Init DB ===
def init_db():
    with app.app_context():
        db.create_all()
        
        # Initialize products if empty
        if Product.query.count() == 0:
            with open('data.json', 'r') as f:
                data = json.load(f)
            for p in data['products']:
                product = Product(**p)
                db.session.add(product)
            db.session.commit()
            print('✓ Products initialized from data.json')
        
        # Initialize sample orders if empty
        if Order.query.count() == 0:
            # Create sample order with items
            products = Product.query.limit(3).all()
            if products:
                order = Order(total=sum(p.price for p in products), status='completed')
                db.session.add(order)
                db.session.flush()
                
                for p in products:
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=p.id,
                        quantity=1,
                        price=p.price
                    )
                    db.session.add(order_item)
                
                db.session.commit()
                print('✓ Sample orders initialized')
        
        # Print summary
        print(f'\n📊 Database Summary:')
        print(f'   Products: {Product.query.count()}')
        print(f'   Cart Items: {CartItem.query.count()}')
        print(f'   Orders: {Order.query.count()}')
        print(f'   Order Items: {OrderItem.query.count()}\n')


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5002)
