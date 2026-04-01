const items = document.querySelector('.cart-items');
const total = document.querySelector('.total');
const empty = document.querySelector('.cart-empty');
const notification = document.querySelector('.notification');
const removeModal = document.getElementById('removeModal');
let removeId = null;

function getCart() {
    return JSON.parse(localStorage.getItem('cart') || '[]');
}

function getProfile() {
    const saved = localStorage.getItem('profile');
    if (saved) {
        const obj = JSON.parse(saved);
        return obj.name && obj.email ? obj : null;
    }
    return null;
}

function updateCartCount() {
    const c = getCart();
    const cc = document.querySelector('.cart-count');
    if (cc) {
        if (c.length > 0) {
            cc.textContent = c.length;
        } else {
            cc.textContent = '';
        }
    }
}

function showNotification(msg) {
    notification.textContent = msg;
    notification.classList.add('active');
    setTimeout(() => {
        notification.classList.remove('active');
    }, 2000);
}

function renderCart() {
    const c = getCart();
    items.innerHTML = '';
    total.innerHTML = '';
    empty.innerHTML = '';

    if (c.length === 0) {
        empty.setAttribute('data-test-id', 'cart-empty');
        empty.textContent = 'Cart is empty';
        return;
    }

    items.setAttribute('data-test-id', 'cart-list');
    let sum = 0;
    c.forEach(item => {
        sum += item.price;
        const card = document.createElement('div');
        card.className = 'card';
        card.setAttribute('data-test-id', 'cart-item');
        card.innerHTML = `
            <img src="./${item.image}" alt="${item.title}">
            <div class="info">
                <h2 class="title">${item.title}</h2>
                <p class="price">$${item.price.toLocaleString()}</p>
            </div>
            <button class="remove" data-id="${item.id}" data-test-id="cart-remove">Remove</button>
        `;
        items.appendChild(card);
    });

    const profile = getProfile();
    const totalDiv = document.createElement('div');
    const buttonsDiv = document.createElement('div');
    buttonsDiv.className = 'checkout-buttons';
    
    if (profile) {
        buttonsDiv.innerHTML = '<button class="checkout">Place order</button>';
    } else {
        buttonsDiv.innerHTML = '<button class="checkout" onclick="window.location.href=\'profile.html\'">Login to place an order</button>';
    }
    
    totalDiv.innerHTML = `<p class="total-price" data-test-id="cart-total">Total: $${sum.toLocaleString()}</p>`;
    totalDiv.appendChild(buttonsDiv);
    total.appendChild(totalDiv);

    const removeBtns = document.querySelectorAll('.remove');
    removeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            removeId = btn.getAttribute('data-id');
            removeModal.classList.add('active');
        });
    });

    const checkoutBtn = document.querySelector('.checkout');
    if (checkoutBtn && profile) {
        checkoutBtn.setAttribute('data-test-id', 'checkout-button');
        checkoutBtn.addEventListener('click', handleCheckout);
    }
}

function handleRemove() {
    if (!removeId) return;
    const c = getCart();
    const filtered = c.filter(item => item.id !== removeId);
    localStorage.setItem('cart', JSON.stringify(filtered));
    removeModal.classList.remove('active');
    removeId = null;
    renderCart();
    updateCartCount();
    showNotification('Looking for something better?');
}

function handleCheckout() {
    const btn = document.querySelector('.checkout');
    const buttonsDiv = document.querySelector('.checkout-buttons');
    if (!btn || !buttonsDiv) return;
    
    btn.disabled = true;
    
    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'cancel';
    cancelBtn.setAttribute('data-test-id', 'cancel-checkout-button');
    cancelBtn.textContent = 'Cancel';
    buttonsDiv.appendChild(cancelBtn);
    
    const cancelTimeout = setTimeout(() => {
        const c = getCart();
        const timestamp = Date.now();
        const orders = JSON.parse(localStorage.getItem('orders') || '[]');
        const order = {
            id: `ORD-${timestamp}`,
            items: [...c],
            total: c.reduce((sum, item) => sum + item.price, 0),
            date: new Date().toISOString()
        };
        orders.push(order);
        localStorage.setItem('orders', JSON.stringify(orders));
        localStorage.setItem('cart', '[]');
        window.location.href = './history.html';
    }, 1500);

    cancelBtn.addEventListener('click', () => {
        clearTimeout(cancelTimeout);
        btn.disabled = false;
        cancelBtn.remove();
    });
}

removeModal.querySelector('.modal-button').addEventListener('click', handleRemove);
removeModal.querySelector('.modal-button-secondary').addEventListener('click', () => {
    removeModal.classList.remove('active');
    removeId = null;
});

removeModal.addEventListener('click', (e) => {
    if (e.target === removeModal) {
        removeModal.classList.remove('active');
        removeId = null;
    }
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && removeModal.classList.contains('active')) {
        removeModal.classList.remove('active');
        removeId = null;
    }
});

renderCart();
updateCartCount();
