const orders = document.querySelector('.orders');
const empty = document.querySelector('.empty');

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}.${month}.${year}`;
}

function renderOrders() {
    const saved = JSON.parse(localStorage.getItem('orders') || '[]');
    orders.innerHTML = '';
    empty.innerHTML = '';

    if (saved.length === 0) {
        empty.setAttribute('data-test-id', 'orders-empty');
        empty.textContent = 'Order history is empty';
        return;
    }

    orders.setAttribute('data-test-id', 'orders-list');
    const sorted = [...saved].reverse();

    sorted.forEach(order => {
        const orderDiv = document.createElement('div');
        orderDiv.className = 'order';
        orderDiv.setAttribute('data-test-id', 'orders-item');
        
        const header = document.createElement('div');
        header.className = 'order-header';
        header.innerHTML = `
            <h2 class="order-number">Order ${order.id}</h2>
            <p class="order-date">${formatDate(order.date)}</p>
        `;
        orderDiv.appendChild(header);

        const tagsDiv = document.createElement('div');
        tagsDiv.className = 'order-tags';
        
        const types = [...new Set(order.items.map(item => item.type))];
        types.forEach(type => {
            const tag = document.createElement('span');
            tag.className = 'order-tag';
            tag.textContent = type;
            tagsDiv.appendChild(tag);
        });
        
        orderDiv.appendChild(tagsDiv);

        const totalDiv = document.createElement('div');
        totalDiv.className = 'order-total';
        totalDiv.textContent = `Total: $${order.total.toLocaleString()}`;
        orderDiv.appendChild(totalDiv);
        
        orders.appendChild(orderDiv);
    });
}

function updateCartCount() {
    const c = JSON.parse(localStorage.getItem('cart') || '[]');
    const cc = document.querySelector('.cart-count');
    if (cc) {
        if (c.length > 0) {
            cc.textContent = c.length;
        } else {
            cc.textContent = '';
        }
    }
}

renderOrders();
updateCartCount();
