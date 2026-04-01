# Luxury Shop API Documentation

## Base URL
```
http://localhost:5000/api
```

---

## Products

### Get All Products
**GET** `/products`

Returns a list of all products.

**Response:** `200 OK`
```json
[
  {
    "id": "yacht-001",
    "title": "Azimut 77 Yacht",
    "type": "Yacht",
    "price": 3500000,
    "image": "images/yachts/yacht-001.jpg",
    "description": "Luxurious 77-foot motor yacht..."
  }
]
```

---

### Get Single Product
**GET** `/products/<id>`

Returns a single product by ID.

**Response:** `200 OK`
```json
{
  "id": "yacht-001",
  "title": "Azimut 77 Yacht",
  "type": "Yacht",
  "price": 3500000,
  "image": "images/yachts/yacht-001.jpg",
  "description": "Luxurious 77-foot motor yacht..."
}
```

---

### Create Product
**POST** `/products`

Creates a new product.

**Request Body:**
```json
{
  "id": "yacht-004",
  "title": "New Yacht",
  "type": "Yacht",
  "price": 5000000,
  "image": "images/yachts/yacht-004.jpg",
  "description": "Description..."
}
```

**Response:** `201 Created`
```json
{
  "id": "yacht-004",
  "title": "New Yacht",
  ...
}
```

---

## Cart

### Get Cart
**GET** `/cart`

Returns current cart items and total.

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": 1,
      "product_id": "yacht-001",
      "quantity": 2,
      "product": {
        "id": "yacht-001",
        "title": "Azimut 77 Yacht",
        "price": 3500000,
        ...
      }
    }
  ],
  "total": 7000000
}
```

---

### Add to Cart
**POST** `/cart`

Adds a product to the cart.

**Request Body:**
```json
{
  "product_id": "yacht-001",
  "quantity": 1
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "product_id": "yacht-001",
  "quantity": 1,
  "product": { ... }
}
```

---

### Update Cart Item
**PUT** `/cart/<item_id>`

Updates quantity of a cart item.

**Request Body:**
```json
{
  "quantity": 3
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "product_id": "yacht-001",
  "quantity": 3,
  "product": { ... }
}
```

---

### Remove from Cart
**DELETE** `/cart/<item_id>`

Removes a single item from the cart.

**Response:** `200 OK`
```json
{
  "message": "Removed"
}
```

---

### Clear Cart
**DELETE** `/cart`

Removes all items from the cart.

**Response:** `200 OK`
```json
{
  "message": "Cart cleared"
}
```

---

## Orders

### Get Orders (History)
**GET** `/orders`

Returns all orders (purchase history).

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "total": 7000000,
    "status": "completed",
    "created_at": "2026-04-01T12:00:00",
    "items": [
      {
        "product_id": "yacht-001",
        "quantity": 2,
        "price": 3500000,
        "product": { ... }
      }
    ]
  }
]
```

---

### Create Order
**POST** `/orders`

Creates an order from current cart items and clears the cart.

**Response:** `201 Created`
```json
{
  "id": 1,
  "total": 7000000,
  "status": "completed",
  "created_at": "2026-04-01T12:00:00",
  "items": [ ... ]
}
```

**Error:** `400 Bad Request` (if cart is empty)
```json
{
  "error": "Cart is empty"
}
```

---

## Data Models

### Product
| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier |
| title | string | Product name |
| type | string | Category (Yacht/Plane/Mansion/Island) |
| price | integer | Price in USD |
| image | string | Image path |
| description | string | Product description |

### CartItem
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Cart item ID |
| product_id | string | Product reference |
| quantity | integer | Quantity |
| product | Product | Full product object |

### Order
| Field | Type | Description |
|-------|------|-------------|
| id | integer | Order ID |
| total | integer | Total amount |
| status | string | Order status |
| created_at | datetime | Creation timestamp |
| items | array | Order items list |
