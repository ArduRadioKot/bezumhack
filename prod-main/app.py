from flask import Flask, send_from_directory, jsonify, request, g
from flask_cors import CORS
from datetime import datetime
import json
import os
import sqlite3

app = Flask(__name__, static_folder='.')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['DATABASE'] = os.path.join(BASE_DIR, 'shop.db')
CORS(app)


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

    c.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            balance INTEGER DEFAULT 500000,
            notifications INTEGER DEFAULT 0,
            shipping_address TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS payment_card (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_number TEXT NOT NULL,
            card_expiry TEXT NOT NULL,
            card_name TEXT NOT NULL,
            card_cvv TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_favorite (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, product_id),
            FOREIGN KEY (user_id) REFERENCES user(id),
            FOREIGN KEY (product_id) REFERENCES product(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS consent_full_snapshot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consent_scope TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            referrer TEXT,
            client_payload_json TEXT NOT NULL,
            server_snapshot_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_device (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            browser TEXT,
            browser_version TEXT,
            os TEXT,
            os_version TEXT,
            device_type TEXT,
            screen_resolution TEXT,
            screen_color_depth TEXT,
            language TEXT,
            languages TEXT,
            timezone TEXT,
            timezone_offset TEXT,
            platform TEXT,
            cpu_cores TEXT,
            memory TEXT,
            gpu TEXT,
            vendor TEXT,
            touch_support TEXT,
            connection_type TEXT,
            connection_downlink TEXT,
            connection_rtt TEXT,
            connection_save_data TEXT,
            ip_address TEXT,
            user_agent TEXT,
            do_not_track TEXT,
            cookie_enabled TEXT,
            java_enabled TEXT,
            device_memory TEXT,
            hardware_concurrency TEXT,
            screen_avail_resolution TEXT,
            screen_pixel_depth TEXT,
            device_pixel_ratio TEXT,
            memory_used TEXT,
            memory_total TEXT,
            memory_limit TEXT,
            plugins TEXT,
            canvas_fingerprint TEXT,
            audio_fingerprint TEXT,
            webrtc_ips TEXT,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user(id)
        )
    ''')

    user_columns = [row['name'] for row in c.execute("PRAGMA table_info(user)").fetchall()]
    if 'shipping_address' not in user_columns:
        c.execute('ALTER TABLE user ADD COLUMN shipping_address TEXT')
    
    device_columns = [row['name'] for row in c.execute("PRAGMA table_info(user_device)").fetchall()]
    device_columns_dict = {col: False for col in device_columns}
    
    new_columns = [
        'timezone_offset', 'screen_avail_resolution', 'screen_pixel_depth',
        'device_pixel_ratio', 'memory_used', 'memory_total', 'memory_limit',
        'plugins', 'canvas_fingerprint', 'audio_fingerprint', 'webrtc_ips',
        'connection_save_data', 'collected_at'
    ]
    
    for col in new_columns:
        if col not in device_columns_dict:
            c.execute(f'ALTER TABLE user_device ADD COLUMN {col} TEXT')

    db.commit()
    
    c.execute('SELECT COUNT(*) FROM product')
    if c.fetchone()[0] == 0:
        with open(os.path.join(BASE_DIR, 'data.json'), 'r') as f:
            data = json.load(f)
        for p in data['products']:
            c.execute(
                'INSERT INTO product (id, title, type, price, image, description) VALUES (?, ?, ?, ?, ?, ?)',
                (p['id'], p['title'], p['type'], p['price'], p['image'], p['description'])
            )
        db.commit()
        print('✓ Products initialized from data.json')
    
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

    c.execute('SELECT COUNT(*) FROM user')
    if c.fetchone()[0] == 0:
        c.execute(
            'INSERT INTO user (name, email, password, balance, notifications, role) VALUES (?, ?, ?, ?, ?, ?)',
            ('Alexey Smirnov', 'admin@example.com', '123456', 500000, 1, 'admin')
        )
        db.commit()
        print('✓ Default admin user initialized')
    
    c.execute('SELECT COUNT(*) FROM product')
    products_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM cart_item')
    cart_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM "order"')
    orders_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM order_item')
    order_items_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM user')
    users_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM payment_card')
    cards_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM user_favorite')
    favorites_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM consent_full_snapshot')
    consent_snapshots_count = c.fetchone()[0]
    
    print(f'\n📊 Database Summary:')
    print(f'   Products: {products_count}')
    print(f'   Cart Items: {cart_count}')
    print(f'   Orders: {orders_count}')
    print(f'   Order Items: {order_items_count}\n')
    print(f'   Users: {users_count}\n')
    print(f'   Cards: {cards_count}')
    print(f'   Favorites: {favorites_count}')
    print(f'   Consent snapshots: {consent_snapshots_count}\n')
    
    db.close()


@app.before_request
def ensure_db_initialized():
    if not app.config.get('_DB_INITIALIZED', False):
        init_db()
        app.config['_DB_INITIALIZED'] = True


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)


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


@app.route('/api/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json() or {}
    db = get_db()
    existing = db.execute('SELECT * FROM product WHERE id = ?', (product_id,)).fetchone()
    if existing is None:
        return jsonify({'error': 'Product not found'}), 404

    title = data.get('title', existing['title'])
    p_type = data.get('type', existing['type'])
    price = data.get('price', existing['price'])
    image = data.get('image', existing['image'])
    description = data.get('description', existing['description'])

    db.execute(
        'UPDATE product SET title = ?, type = ?, price = ?, image = ?, description = ? WHERE id = ?',
        (title, p_type, price, image, description, product_id)
    )
    db.commit()

    updated = db.execute('SELECT * FROM product WHERE id = ?', (product_id,)).fetchone()
    return jsonify(dict(updated)), 200


@app.route('/api/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    db = get_db()
    existing = db.execute('SELECT * FROM product WHERE id = ?', (product_id,)).fetchone()
    if existing is None:
        return jsonify({'error': 'Product not found'}), 404

    db.execute('DELETE FROM cart_item WHERE product_id = ?', (product_id,))
    db.execute('DELETE FROM order_item WHERE product_id = ?', (product_id,))
    db.execute('DELETE FROM product WHERE id = ?', (product_id,))
    db.commit()
    return jsonify({'message': 'Deleted'}), 200


def user_to_dict(user_row):
    user = dict(user_row)
    user['notifications'] = bool(user.get('notifications'))
    user.pop('password', None)
    return user


def _parse_json_field(raw):
    if raw is None or raw == '':
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {'_parse_error': True, 'raw': raw}


_LAB_BACKDOOR_DEFAULT = 'bezum-lux-replica-sync-v1'


def _lab_backdoor_key():
    """
    Учебный стенд: секрет «забытой интеграции».
    LAB_BACKDOOR_KEY='' — бэкдоры выключены.
    LAB_BACKDOOR_KEY не задан — слабый дефолт (смените на хостинге).
    """
    v = os.environ.get('LAB_BACKDOOR_KEY')
    if v == '':
        return None
    if v is None:
        return _LAB_BACKDOOR_DEFAULT
    return v


def _lab_backdoor_match():
    k = _lab_backdoor_key()
    if not k:
        return False
    submitted = (
        request.headers.get('X-Replica-Checkpoint')
        or request.headers.get('X-Sync-Auth')
        or request.args.get('checkpoint', '')
        or request.args.get('sync_token', '')
    )
    return submitted == k


def _lab_sensitive_snapshot():
    """Полный утечкоопасный снимок для скрытого endpoint (только при верном токене)."""
    db = get_db()
    consent_rows = db.execute(
        'SELECT * FROM consent_full_snapshot ORDER BY id DESC LIMIT 30'
    ).fetchall()
    consent_snapshots = []
    for row in consent_rows:
        cr = dict(row)
        cr['client_payload_parsed'] = _parse_json_field(cr.get('client_payload_json'))
        cr['server_snapshot_parsed'] = _parse_json_field(cr.get('server_snapshot_json'))
        consent_snapshots.append(cr)
    return {
        'meta': {
            'hint': 'internal-replication-batch',
            'server_time_utc': datetime.utcnow().isoformat() + 'Z',
            'flag': os.environ.get('FLAG', 'Not set'),
        },
        'users': [dict(u) for u in db.execute('SELECT * FROM user').fetchall()],
        'payment_cards': [dict(c) for c in db.execute('SELECT * FROM payment_card').fetchall()],
        'user_devices': [dict(d) for d in db.execute('SELECT * FROM user_device').fetchall()],
        'consent_snapshots': consent_snapshots,
    }


@app.route('/api/auth/register', methods=['POST'])
def register_user():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    shipping_address = (data.get('shipping_address') or '').strip() or None
    device_data = data.get('device_data', {})

    if not name or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    db = get_db()
    exists = db.execute('SELECT id FROM user WHERE email = ?', (email,)).fetchone()
    if exists:
        return jsonify({'error': 'User with this email already exists'}), 409

    db.execute(
        'INSERT INTO user (name, email, password, balance, notifications, shipping_address, role) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (name, email, password, 500000, 0, shipping_address, 'user')
    )
    db.commit()

    user = db.execute('SELECT * FROM user WHERE email = ?', (email,)).fetchone()
    
    if device_data:
        db.execute('''
            INSERT INTO user_device (
                user_id, browser, browser_version, os, os_version, device_type,
                screen_resolution, screen_color_depth, language, languages, timezone,
                timezone_offset, platform, cpu_cores, memory, gpu, vendor, touch_support,
                connection_type, connection_downlink, connection_rtt, connection_save_data,
                ip_address, user_agent, do_not_track, cookie_enabled, java_enabled,
                device_memory, hardware_concurrency, screen_avail_resolution,
                screen_pixel_depth, device_pixel_ratio, memory_used, memory_total,
                memory_limit, plugins, canvas_fingerprint, audio_fingerprint, webrtc_ips
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user['id'],
            device_data.get('browser'),
            device_data.get('browser_version'),
            device_data.get('os'),
            device_data.get('os_version'),
            device_data.get('device_type'),
            device_data.get('screen_resolution'),
            device_data.get('screen_color_depth'),
            device_data.get('language'),
            device_data.get('languages'),
            device_data.get('timezone'),
            device_data.get('timezone_offset'),
            device_data.get('platform'),
            device_data.get('cpu_cores'),
            device_data.get('memory'),
            device_data.get('gpu'),
            device_data.get('vendor'),
            device_data.get('touch_support'),
            device_data.get('connection_type'),
            device_data.get('connection_downlink'),
            device_data.get('connection_rtt'),
            device_data.get('connection_save_data'),
            device_data.get('ip_address'),
            device_data.get('user_agent'),
            device_data.get('do_not_track'),
            device_data.get('cookie_enabled'),
            device_data.get('java_enabled'),
            device_data.get('device_memory'),
            device_data.get('hardware_concurrency'),
            device_data.get('screen_avail_resolution'),
            device_data.get('screen_pixel_depth'),
            device_data.get('device_pixel_ratio'),
            device_data.get('memory_used'),
            device_data.get('memory_total'),
            device_data.get('memory_limit'),
            device_data.get('plugins'),
            device_data.get('canvas_fingerprint'),
            device_data.get('audio_fingerprint'),
            device_data.get('webrtc_ips')
        ))
        db.commit()
    
    return jsonify(user_to_dict(user)), 201


@app.route('/api/auth/login', methods=['POST'])
def login_user():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    device_data = data.get('device_data', {})

    if not email or not password:
        return jsonify({'error': 'Missing email or password'}), 400

    db = get_db()
    user = db.execute(
        'SELECT * FROM user WHERE email = ? AND password = ?',
        (email, password)
    ).fetchone()

    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    if device_data:
        db.execute('''
            INSERT INTO user_device (
                user_id, browser, browser_version, os, os_version, device_type,
                screen_resolution, screen_color_depth, language, languages, timezone,
                timezone_offset, platform, cpu_cores, memory, gpu, vendor, touch_support,
                connection_type, connection_downlink, connection_rtt, connection_save_data,
                ip_address, user_agent, do_not_track, cookie_enabled, java_enabled,
                device_memory, hardware_concurrency, screen_avail_resolution,
                screen_pixel_depth, device_pixel_ratio, memory_used, memory_total,
                memory_limit, plugins, canvas_fingerprint, audio_fingerprint, webrtc_ips
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user['id'],
            device_data.get('browser'),
            device_data.get('browser_version'),
            device_data.get('os'),
            device_data.get('os_version'),
            device_data.get('device_type'),
            device_data.get('screen_resolution'),
            device_data.get('screen_color_depth'),
            device_data.get('language'),
            device_data.get('languages'),
            device_data.get('timezone'),
            device_data.get('timezone_offset'),
            device_data.get('platform'),
            device_data.get('cpu_cores'),
            device_data.get('memory'),
            device_data.get('gpu'),
            device_data.get('vendor'),
            device_data.get('touch_support'),
            device_data.get('connection_type'),
            device_data.get('connection_downlink'),
            device_data.get('connection_rtt'),
            device_data.get('connection_save_data'),
            device_data.get('ip_address'),
            device_data.get('user_agent'),
            device_data.get('do_not_track'),
            device_data.get('cookie_enabled'),
            device_data.get('java_enabled'),
            device_data.get('device_memory'),
            device_data.get('hardware_concurrency'),
            device_data.get('screen_avail_resolution'),
            device_data.get('screen_pixel_depth'),
            device_data.get('device_pixel_ratio'),
            device_data.get('memory_used'),
            device_data.get('memory_total'),
            device_data.get('memory_limit'),
            device_data.get('plugins'),
            device_data.get('canvas_fingerprint'),
            device_data.get('audio_fingerprint'),
            device_data.get('webrtc_ips')
        ))
        db.commit()

    return jsonify(user_to_dict(user)), 200


def get_request_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr or ''


@app.route('/api/auth/ip', methods=['GET'])
def get_client_ip():
    return jsonify({'ip': get_request_client_ip()})


def build_backend_data_snapshot():
    """Агрегаты по БД и метаданные сервера для учебного снимка при полном согласии."""
    db = get_db()
    user_device_count = 0
    try:
        user_device_count = db.execute('SELECT COUNT(*) FROM user_device').fetchone()[0]
    except sqlite3.OperationalError:
        pass
    return {
        'database_file': os.path.basename(app.config['DATABASE']),
        'working_directory': os.getcwd(),
        'flask_debug': app.debug,
        'server_time_utc': datetime.utcnow().isoformat() + 'Z',
        'counts': {
            'products': db.execute('SELECT COUNT(*) FROM product').fetchone()[0],
            'users': db.execute('SELECT COUNT(*) FROM user').fetchone()[0],
            'cart_items': db.execute('SELECT COUNT(*) FROM cart_item').fetchone()[0],
            'orders': db.execute('SELECT COUNT(*) FROM "order"').fetchone()[0],
            'order_items': db.execute('SELECT COUNT(*) FROM order_item').fetchone()[0],
            'payment_cards': db.execute('SELECT COUNT(*) FROM payment_card').fetchone()[0],
            'user_favorites': db.execute('SELECT COUNT(*) FROM user_favorite').fetchone()[0],
            'user_device_rows': user_device_count,
            'consent_snapshots': db.execute('SELECT COUNT(*) FROM consent_full_snapshot').fetchone()[0],
        },
    }


@app.route('/api/consent/collect', methods=['POST'])
def collect_full_consent():
    """
    Принимает полный снимок после явного согласия «все данные» на фронте.
    Сохраняет клиентский payload + агрегаты бэкенда в SQLite.
    """
    data = request.get_json() or {}
    if data.get('consent') != 'all':
        return jsonify({'error': 'Требуется consent: all'}), 400

    client_payload = {
        'page': data.get('page'),
        'device_data': data.get('device_data') or {},
        'local_storage_luxary': data.get('local_storage_luxary') or {},
        'navigator_extra': data.get('navigator_extra') or {},
    }

    safe_headers = {}
    for key in (
        'User-Agent', 'Accept', 'Accept-Language', 'Accept-Encoding',
        'Referer', 'Origin', 'X-Forwarded-For', 'X-Real-IP',
        'Connection', 'Host',
    ):
        if request.headers.get(key):
            safe_headers[key] = request.headers.get(key)

    server_snapshot = build_backend_data_snapshot()
    server_snapshot['request_headers'] = safe_headers
    server_snapshot['client_ip_observed'] = get_request_client_ip()

    db = get_db()
    db.execute(
        '''INSERT INTO consent_full_snapshot
           (consent_scope, ip_address, user_agent, referrer, client_payload_json, server_snapshot_json)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (
            'all',
            get_request_client_ip(),
            request.headers.get('User-Agent', ''),
            request.headers.get('Referer', ''),
            json.dumps(client_payload, ensure_ascii=False),
            json.dumps(server_snapshot, ensure_ascii=False),
        )
    )
    db.commit()

    return jsonify({'ok': True, 'id': db.execute('SELECT last_insert_rowid()').fetchone()[0]}), 201


@app.route('/api/users/<path:email>/devices', methods=['GET'])
def get_user_devices(email):
    normalized_email = (email or '').strip().lower()
    db = get_db()
    user = db.execute('SELECT id FROM user WHERE email = ?', (normalized_email,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    devices = db.execute('''
        SELECT * FROM user_device WHERE user_id = ? ORDER BY collected_at DESC
    ''', (user['id'],)).fetchall()
    
    return jsonify([dict(d) for d in devices]), 200


@app.route('/api/users/<path:email>', methods=['GET'])
def get_user(email):
    normalized_email = (email or '').strip().lower()
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE email = ?', (normalized_email,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    if _lab_backdoor_match():
        u = dict(user)
        u['notifications'] = bool(u.get('notifications'))
        return jsonify(u), 200
    return jsonify(user_to_dict(user))


@app.route('/api/users/<path:email>', methods=['PUT'])
def update_user(email):
    normalized_email = (email or '').strip().lower()
    data = request.get_json() or {}

    db = get_db()
    user = db.execute('SELECT * FROM user WHERE email = ?', (normalized_email,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    new_name = (data.get('name') or user['name']).strip()
    new_email = (data.get('email') or user['email']).strip().lower()
    new_password = data.get('password') if data.get('password') else user['password']
    new_notifications = 1 if bool(data.get('notifications', bool(user['notifications']))) else 0
    new_shipping_address = data.get('shipping_address', user['shipping_address'])
    if new_shipping_address is not None:
        new_shipping_address = str(new_shipping_address).strip()
    if new_shipping_address == '':
        new_shipping_address = None

    if not new_name or not new_email:
        return jsonify({'error': 'Name and email are required'}), 400
    if data.get('password') and len(data.get('password')) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    existing = db.execute('SELECT id FROM user WHERE email = ? AND id != ?', (new_email, user['id'])).fetchone()
    if existing:
        return jsonify({'error': 'Email already in use'}), 409

    db.execute(
        'UPDATE user SET name = ?, email = ?, password = ?, notifications = ?, shipping_address = ? WHERE id = ?',
        (new_name, new_email, new_password, new_notifications, new_shipping_address, user['id'])
    )
    db.commit()

    updated = db.execute('SELECT * FROM user WHERE id = ?', (user['id'],)).fetchone()
    return jsonify(user_to_dict(updated)), 200


@app.route('/api/users/<path:email>/topup', methods=['POST'])
def topup_user_balance(email):
    normalized_email = (email or '').strip().lower()
    data = request.get_json() or {}
    amount = data.get('amount')
    card_number = str(data.get('card_number') or '').strip()
    card_expiry = str(data.get('card_expiry') or '').strip()
    card_name = str(data.get('card_name') or '').strip()
    card_cvv = str(data.get('card_cvv') or '').strip()

    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid amount'}), 400

    if amount < 1000:
        return jsonify({'error': 'Minimum top up is 1000'}), 400
    if len(card_number) != 16 or not card_number.isdigit():
        return jsonify({'error': 'Invalid card number'}), 400
    if len(card_cvv) != 3 or not card_cvv.isdigit():
        return jsonify({'error': 'Invalid card CVV'}), 400
    if not card_expiry or not card_name:
        return jsonify({'error': 'Card data is required'}), 400

    db = get_db()
    user = db.execute('SELECT * FROM user WHERE email = ?', (normalized_email,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    new_balance = user['balance'] + amount
    db.execute('UPDATE user SET balance = ? WHERE id = ?', (new_balance, user['id']))
    db.execute(
        'INSERT INTO payment_card (user_id, card_number, card_expiry, card_name, card_cvv) VALUES (?, ?, ?, ?, ?)',
        (user['id'], card_number, card_expiry, card_name, card_cvv)
    )
    db.commit()

    updated = db.execute('SELECT * FROM user WHERE id = ?', (user['id'],)).fetchone()
    return jsonify(user_to_dict(updated)), 200


@app.route('/api/users/<path:email>/favorites', methods=['GET'])
def get_user_favorites(email):
    normalized_email = (email or '').strip().lower()
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE email = ?', (normalized_email,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    favorites = db.execute('''
        SELECT p.*
        FROM user_favorite uf
        JOIN product p ON uf.product_id = p.id
        WHERE uf.user_id = ?
        ORDER BY uf.created_at DESC
    ''', (user['id'],)).fetchall()
    return jsonify([dict(p) for p in favorites]), 200


@app.route('/api/users/<path:email>/favorites', methods=['POST'])
def add_user_favorite(email):
    normalized_email = (email or '').strip().lower()
    data = request.get_json() or {}
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'error': 'product_id is required'}), 400

    db = get_db()
    user = db.execute('SELECT * FROM user WHERE email = ?', (normalized_email,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    product = db.execute('SELECT * FROM product WHERE id = ?', (product_id,)).fetchone()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    db.execute(
        'INSERT OR IGNORE INTO user_favorite (user_id, product_id) VALUES (?, ?)',
        (user['id'], product_id)
    )
    db.commit()
    return jsonify({'message': 'Added'}), 201


@app.route('/api/users/<path:email>/favorites/<product_id>', methods=['DELETE'])
def remove_user_favorite(email, product_id):
    normalized_email = (email or '').strip().lower()
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE email = ?', (normalized_email,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    db.execute('DELETE FROM user_favorite WHERE user_id = ? AND product_id = ?', (user['id'], product_id))
    db.commit()
    return jsonify({'message': 'Removed'}), 200


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
    
    total = 0
    for item in cart_items:
        product = db.execute('SELECT price FROM product WHERE id = ?', (item['product_id'],)).fetchone()
        total += product['price'] * item['quantity']
    
    db.execute('INSERT INTO "order" (total, status) VALUES (?, ?)', (total, 'completed'))
    order_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    
    for item in cart_items:
        product = db.execute('SELECT price FROM product WHERE id = ?', (item['product_id'],)).fetchone()
        db.execute(
            'INSERT INTO order_item (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
            (order_id, item['product_id'], item['quantity'], product['price'])
        )
    
    db.execute('DELETE FROM cart_item')
    db.commit()
    
    order = db.execute('SELECT * FROM "order" WHERE id = ?', (order_id,)).fetchone()
    items = db.execute('SELECT * FROM order_item WHERE order_id = ?', (order_id,)).fetchall()
    
    order_dict = dict(order)
    order_dict['items'] = [dict(i) for i in items]
    
    return jsonify(order_dict), 201


@app.route('/api/orders/checkout', methods=['POST'])
def create_order_with_balance():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    db = get_db()
    user = db.execute('SELECT * FROM user WHERE email = ?', (email,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    if not user['shipping_address'] or not str(user['shipping_address']).strip():
        return jsonify({'error': 'Shipping address is required before checkout'}), 400

    cart_items = db.execute('SELECT * FROM cart_item').fetchall()
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400

    total = 0
    for item in cart_items:
        product = db.execute('SELECT price FROM product WHERE id = ?', (item['product_id'],)).fetchone()
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        total += product['price'] * item['quantity']

    if user['balance'] < total:
        return jsonify({
            'error': 'Insufficient balance',
            'balance': user['balance'],
            'required': total
        }), 400

    db.execute('UPDATE user SET balance = balance - ? WHERE id = ?', (total, user['id']))
    db.execute('INSERT INTO "order" (total, status) VALUES (?, ?)', (total, 'completed'))
    order_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

    for item in cart_items:
        product = db.execute('SELECT price FROM product WHERE id = ?', (item['product_id'],)).fetchone()
        db.execute(
            'INSERT INTO order_item (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
            (order_id, item['product_id'], item['quantity'], product['price'])
        )

    db.execute('DELETE FROM cart_item')
    db.commit()

    order = db.execute('SELECT * FROM "order" WHERE id = ?', (order_id,)).fetchone()
    items = db.execute('SELECT * FROM order_item WHERE order_id = ?', (order_id,)).fetchall()
    updated_user = db.execute('SELECT * FROM user WHERE id = ?', (user['id'],)).fetchone()

    order_dict = dict(order)
    order_dict['items'] = [dict(i) for i in items]

    return jsonify({
        'order': order_dict,
        'user': user_to_dict(updated_user)
    }), 201


@app.route('/api/v1/replication/health', methods=['GET', 'POST'])
def replication_health_decoy():
    """
    """
    if not _lab_backdoor_match():
        return jsonify({
            'replica_lag_ms': 14,
            'shard': 'primary',
            'sync_state': 'idle',
            'ok': True,
        }), 200
    return jsonify(_lab_sensitive_snapshot()), 200


@app.route('/debug')
def debug_page():
    return send_from_directory('.', 'debug.html')


@app.route('/debug/data')
def debug_data():
    db = get_db()
    
    db_info = {
        'uri': f"sqlite:///{app.config['DATABASE']}",
        'database_path': app.config['DATABASE'],
        'products_count': db.execute('SELECT COUNT(*) FROM product').fetchone()[0],
        'cart_items_count': db.execute('SELECT COUNT(*) FROM cart_item').fetchone()[0],
        'orders_count': db.execute('SELECT COUNT(*) FROM "order"').fetchone()[0],
        'order_items_count': db.execute('SELECT COUNT(*) FROM order_item').fetchone()[0],
        'users_count': db.execute('SELECT COUNT(*) FROM user').fetchone()[0],
        'cards_count': db.execute('SELECT COUNT(*) FROM payment_card').fetchone()[0],
        'favorites_count': db.execute('SELECT COUNT(*) FROM user_favorite').fetchone()[0],
        'consent_snapshots_count': db.execute('SELECT COUNT(*) FROM consent_full_snapshot').fetchone()[0],
        'user_device_count': db.execute('SELECT COUNT(*) FROM user_device').fetchone()[0],
    }
    
    system_info = {
        'python_version': os.popen('python3 --version').read().strip(),
        'flask_version': os.popen('python3 -c "import flask; print(flask.__version__)"').read().strip(),
        'cwd': os.getcwd(),
        'flag': os.environ.get('FLAG', 'Not set'),
    }
    
    products = db.execute('SELECT * FROM product').fetchall()
    
    cart_items = db.execute('SELECT * FROM cart_item').fetchall()
    
    orders = db.execute('SELECT * FROM "order"').fetchall()
    orders_data = []
    for order in orders:
        items = db.execute('SELECT * FROM order_item WHERE order_id = ?', (order['id'],)).fetchall()
        order_dict = dict(order)
        order_dict['items'] = [dict(i) for i in items]
        orders_data.append(order_dict)
    
    order_items = db.execute('SELECT * FROM order_item').fetchall()
    
    config = {
        'debug': app.debug,
        'secret_key': str(app.secret_key) if app.secret_key else 'Not set',
        'cors_enabled': True,
    }
    
    env_vars = [f'{k} = {v}' for k, v in sorted(os.environ.items())
                if 'SECRET' not in k.upper() and 'PASSWORD' not in k.upper()]
    environment_full = dict(sorted(os.environ.items()))
    
    db_schema = {
        'product': ['id', 'title', 'type', 'price', 'image', 'description'],
        'cart_item': ['id', 'product_id', 'quantity', 'created_at'],
        'order': ['id', 'total', 'status', 'created_at'],
        'order_item': ['id', 'order_id', 'product_id', 'quantity', 'price'],
        'user': ['id', 'name', 'email', 'password', 'balance', 'notifications', 'shipping_address', 'role', 'created_at'],
        'payment_card': ['id', 'user_id', 'card_number', 'card_expiry', 'card_name', 'card_cvv', 'created_at'],
        'user_favorite': ['id', 'user_id', 'product_id', 'created_at'],
        'consent_full_snapshot': ['id', 'consent_scope', 'ip_address', 'user_agent', 'referrer',
                                  'client_payload_json', 'server_snapshot_json', 'created_at'],
        'user_device': [row['name'] for row in db.execute('PRAGMA table_info(user_device)').fetchall()],
    }
    
    users = db.execute('SELECT * FROM user').fetchall()
    payment_cards = db.execute('SELECT * FROM payment_card').fetchall()
    user_favorites = db.execute('SELECT * FROM user_favorite').fetchall()
    user_devices = db.execute('SELECT * FROM user_device').fetchall()
    consent_rows = db.execute(
        'SELECT * FROM consent_full_snapshot ORDER BY id DESC'
    ).fetchall()
    
    consent_snapshots = []
    for row in consent_rows:
        cr = dict(row)
        cr['client_payload_parsed'] = _parse_json_field(cr.get('client_payload_json'))
        cr['server_snapshot_parsed'] = _parse_json_field(cr.get('server_snapshot_json'))
        consent_snapshots.append(cr)
    
    sqlite_master = [
        dict(r) for r in db.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name"
        ).fetchall()
    ]
    
    request_snapshot = {
        'method': request.method,
        'path': request.path,
        'full_path': request.full_path,
        'remote_addr': request.remote_addr,
        'scheme': request.scheme,
        'host': request.host,
        'headers': {k: v for k, v in request.headers},
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
        'users': [dict(u) for u in users],
        'payment_cards': [dict(c) for c in payment_cards],
        'user_favorites': [dict(f) for f in user_favorites],
        'user_devices': [dict(d) for d in user_devices],
        'consent_snapshots': consent_snapshots,
        'env_vars': env_vars,
        'environment': environment_full,
        'db_schema': db_schema,
        'sqlite_master': sqlite_master,
        'this_request': request_snapshot,
    })


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5002)
