# Отчёт по аудиту данных и функций (Frontend + Backend)

## Область проверки

- Папка проекта: `prod-main`
- Цель: проверить, где хранятся важные данные, и зафиксировать ключевые функции фронтенда и бэкенда.
- Критичные сущности: пользователи, пароли, баланс, корзина, заказы, избранное, адрес доставки, данные банковских карт.

## Краткий итог

- Основные бизнес-данные перенесены на бэкенд (SQLite `shop.db` + API).
- Добавлено хранение:
  - данных карты (при пополнении баланса) в таблице `payment_card`
  - избранного пользователя в таблице `user_favorite`
  - адреса доставки в поле `user.shipping_address`
- Оформление заказа теперь требует заполненный адрес доставки.
- На фронтенде в `localStorage` остались только данные сессии/темы и вспомогательные UI-данные.
- Ключевой риск: пароль пользователя всё ещё хранится в открытом виде в БД.

---

## Важные данные и где они хранятся

## Бэкенд (SQLite)

Файл БД: `shop.db` (настраивается в `app.py`).

Таблицы:

- `product`: каталог товаров
  - `id`, `title`, `type`, `price`, `image`, `description`
- `cart_item`: содержимое корзины
  - `id`, `product_id`, `quantity`, `created_at`
- `order`: заказы
  - `id`, `total`, `status`, `created_at`
- `order_item`: позиции заказа
  - `id`, `order_id`, `product_id`, `quantity`, `price`
- `user`: пользователи
  - `id`, `name`, `email`, `password`, `balance`, `notifications`, `shipping_address`, `role`, `created_at`
- `payment_card`: сохранённые данные карт пополнения
  - `id`, `user_id`, `card_number`, `card_expiry`, `card_name`, `card_cvv`, `created_at`
- `user_favorite`: избранные товары пользователя
  - `id`, `user_id`, `product_id`, `created_at`

Критичные данные, которые теперь находятся в БД:

- аккаунты пользователей
- баланс пользователей
- адрес доставки
- каталог товаров
- корзина
- история заказов
- избранное
- данные карт пополнения

## Фронтенд (`localStorage`)

- `luxary_current_user` — клиентская сессия (кэш профиля текущего пользователя)
- `luxary_theme` — тема интерфейса
- в `main.html` (отдельный модуль мессенджера): `messenger_chats`, `messenger_profile`, `messenger_settings`

Примечание: в `shop.html` избранное больше не хранится в `localStorage`, теперь идёт через API + БД.

---

## Проверка данных карты

Источник: `balance.html` + `app.py`

- Фронтенд собирает:
  - `cardNumber`, `cardExpiry`, `cardCvv`, `cardName`
- Фронтенд отправляет в API пополнения:
  - `amount`, `card_number`, `card_expiry`, `card_name`, `card_cvv`
- Бэкенд:
  - валидирует формат номера/срока/CVV
  - сохраняет запись в `payment_card`
  - пополняет баланс пользователя

Итог: данные карты **сохраняются в БД** (по твоему требованию).

---

## Фронтенд: ключевые функции

## `shop.html`

Основной функционал магазина:

- `loadProducts()` — загрузка товаров из API
- `fetchCart()` — загрузка корзины из API
- `addToCartAPI()` / `updateCartItemAPI()` / `removeCartItemAPI()` — работа с корзиной через API
- `createOrderAPI()` — оформление заказа через `POST /api/orders/checkout`
- `updateCartBadge()` — обновление счётчика корзины
- `fetchOrders()` — загрузка истории заказов
- `renderCart()`, `renderProducts()`, `renderFavorites()` — отрисовка UI
- `toggleFav(id)` — добавление/удаление избранного через API
- `loadFavorites()` — загрузка избранного пользователя с бэкенда
- `showSection()`, `updateFilters()`, `attachEvents()`, `showProductModal()`, `updateUserUI()`

Админ-функции:

- `renderAdminList()`, `editProduct()`
- `deleteProduct()` — удаление товара через API
- `addOrUpdateProduct()` — создание/обновление товара через API

## `auth.html`

- `handleLogin()` — вход через `POST /api/auth/login`
- `handleRegister()` — регистрация через `POST /api/auth/register` (включая `shipping_address`)
- `saveProfileChanges()` — обновление профиля через `PUT /api/users/<email>` (включая адрес доставки)
- `showProfilePanel()` — показывает адрес доставки/баланс/роль
- `getCurrentUser()`, `setCurrentUser()`, `logout()`, `enterGuestMode()`
- `applyTheme()`, `toggleTheme()`, `init()`

## `balance.html`

- Валидация формы карты и суммы
- Отправка пополнения с данными карты в `POST /api/users/<email>/topup`
- `updateUserSession()` — обновление клиентской сессии после успешного пополнения
- `showMessage()`, `applyTheme()`, `toggleTheme()`

## `index.html`

- `applyTheme()`, `toggleTheme()` (только тема и навигация)

## `main.html` (отдельный модуль)

- Полноценный модуль мессенджера, живёт отдельно от магазина
- Использует собственные ключи `localStorage` и не влияет на заказы/баланс/картотеку магазина

---

## Бэкенд: ключевые функции и API (`app.py`)

База данных:

- `get_db()`, `close_db()`, `init_db()`
- В `init_db()` добавлены новые таблицы и миграция `shipping_address` для старых БД.

Товары:

- `GET /api/products`
- `GET /api/products/<product_id>`
- `POST /api/products`
- `PUT /api/products/<product_id>`
- `DELETE /api/products/<product_id>`

Пользователи/авторизация:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/users/<email>`
- `PUT /api/users/<email>`
- `POST /api/users/<email>/topup` (сохранение карты + пополнение)

Избранное:

- `GET /api/users/<email>/favorites`
- `POST /api/users/<email>/favorites`
- `DELETE /api/users/<email>/favorites/<product_id>`

Корзина:

- `GET /api/cart`
- `POST /api/cart`
- `PUT /api/cart/<item_id>`
- `DELETE /api/cart/<item_id>`
- `DELETE /api/cart`

Заказы:

- `GET /api/orders`
- `POST /api/orders`
- `POST /api/orders/checkout`
  - проверка пользователя
  - обязательная проверка `shipping_address`
  - проверка корзины и баланса
  - списание баланса
  - создание заказа и позиций
  - очистка корзины

Отладка:

- `GET /debug`
- `GET /debug/data`

---

## Куда теперь сохраняются данные

- Пользователи, адрес доставки, баланс: `user`
- Карты: `payment_card`
- Избранное: `user_favorite`
- Товары: `product`
- Корзина: `cart_item`
- Заказы: `order` + `order_item`
- Тема и сессия в браузере: `localStorage`

---

## Риски и рекомендации

Высокий приоритет:

- Пароли в БД в открытом виде (`user.password`).
  - Рекомендуется внедрить `generate_password_hash()` и `check_password_hash()`.

Средний приоритет:

- `luxary_current_user` в `localStorage` можно подменить на клиенте.
  - Рекомендуется перейти на серверные сессии или JWT с проверкой на бэкенде.

Низкий приоритет:

- Ограничить `/debug/data` в production (содержит чувствительную диагностическую информацию).
- Неиспользуемые legacy JS-файлы можно убрать/архивировать, чтобы исключить случайный возврат к старой логике.

---

## Финальный вывод

- Требования выполнены: карты, избранное и адрес доставки вынесены в бэкенд и сохраняются в SQLite.
- Оформление заказа теперь зависит от наличия адреса доставки.
- Архитектура стала более серверной и консистентной; следующий важный шаг — защита паролей и сессий.

