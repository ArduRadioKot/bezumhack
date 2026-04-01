let allProducts = [];
let c = JSON.parse(localStorage.getItem('cart') || '[]');
let p = null;

async function loadProducts() {
    renderSkeletons();
    
    const minLoadTime = new Promise(resolve => setTimeout(resolve, 1500));
    const dataLoad = fetch('./data.json').then(response => response.json());
    
    try {
        const [data] = await Promise.all([dataLoad, minLoadTime]);
        allProducts = data.products;
        
        renderProducts(allProducts);
        
        const checkboxes = document.querySelectorAll('.filters input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', filterProducts);
        });
        
        s2();
        u();
    } catch (error) {
        console.error('Error loading products:', error);
    }
}

function s2() {
    const m1 = document.querySelector('.modal-overlay');
    const m2 = document.querySelector('.modal-close');
    const m3 = document.querySelector('.modal-button');
    
    m2.addEventListener('click', c1);
    m3.addEventListener('click', h);
    
    m1.addEventListener('click', (e) => {
        if (e.target === m1) {
            c1();
        }
    });
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && m1.classList.contains('active')) {
            c1();
        }
    });
}

loadProducts();

const filterMapping = {
    'yachty': 'Yacht',
    'planety': 'Plane',
    'manison': 'Mansion',
    'island': 'Island'
};

function renderSkeletons() {
    const catalog = document.querySelector('.catalog');
    catalog.innerHTML = '';
    
    for (let i = 0; i < 12; i++) {
        const card = document.createElement('div');
        card.setAttribute('data-test-id', 'skeleton-card');
        card.innerHTML = `
            <div data-skeleton></div>
            <div class="card-filter" data-skeleton></div>
            <div class="card-title" data-skeleton></div>
            <div class="card-price" data-skeleton></div>
        `;
        catalog.appendChild(card);
    }
}

function renderProducts(products) {
    const catalog = document.querySelector('.catalog');
    catalog.innerHTML = '';
    
    products.forEach(product => {
        const card = document.createElement('div');
        card.setAttribute('data-test-id', 'product-card');
        card.innerHTML = `
            <img src="./${product.image}" alt="${product.title}">
            <h2 class="card-filter" data-test-id="product-type">${product.type}</h2>
            <h2 class="card-title" data-test-id="product-title">${product.title}</h2>
            <p class="card-price" data-test-id="product-price">$${product.price.toLocaleString()}</p>
        `;
        card.addEventListener('click', () => o(product));
        catalog.appendChild(card);
    });
}

function u() {
    localStorage.setItem('cart', JSON.stringify(c));
    const cc = document.querySelector('.cart-count');
    if (cc) {
        if (c.length > 0) {
            cc.textContent = c.length;
        } else {
            cc.textContent = '';
        }
    }
}

function o(product) {
    p = product;
    const m = document.querySelector('.modal-overlay');
    const mi = document.querySelector('.modal-image');
    const mt = document.querySelector('.modal-type');
    const mti = document.querySelector('.modal-title');
    const md = document.querySelector('.modal-description');
    const mp = document.querySelector('.modal-price');
    const mb = document.querySelector('.modal-button');
    
    mi.src = `./${product.image}`;
    mi.alt = product.title;
    mt.textContent = product.type;
    mti.textContent = product.title;
    md.textContent = product.description;
    mp.textContent = `$${product.price.toLocaleString()}`;
    
    const ic = c.some(item => item.id === product.id);
    if (ic) {
        mb.textContent = 'Remove from cart';
        mb.setAttribute('data-test-id', 'remove-from-cart');
    } else {
        mb.textContent = 'Add to cart';
        mb.setAttribute('data-test-id', 'add-to-cart');
    }
    
    m.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function c1() {
    const m = document.querySelector('.modal-overlay');
    m.classList.remove('active');
    document.body.style.overflow = '';
    p = null;
}

function s(message) {
    const n = document.querySelector('.notification');
    n.textContent = message;
    n.classList.add('active');
    
    setTimeout(() => {
        n.classList.remove('active');
    }, 2000);
}

function h() {
    if (!p) return;
    
    const mb = document.querySelector('.modal-button');
    const ic = c.some(item => item.id === p.id);
    
    mb.disabled = true;
    
    if (ic) {
        c = c.filter(item => item.id !== p.id);
        mb.textContent = 'Removed';
        s('Looking for something better?');
        
        setTimeout(() => {
            mb.textContent = 'Add to cart';
            mb.setAttribute('data-test-id', 'add-to-cart');
            mb.disabled = false;
        }, 2000);
    } else {
        c.push(p);
        mb.textContent = 'Added';
        s('Great choice!');
        
        setTimeout(() => {
            mb.textContent = 'Remove from cart';
            mb.setAttribute('data-test-id', 'remove-from-cart');
            mb.disabled = false;
        }, 2000);
    }
    
    u();
}

function filterProducts() {
    const checkboxes = document.querySelectorAll('.filters input[type="checkbox"]');
    const activeFilters = [];
    
    checkboxes.forEach(checkbox => {
        if (checkbox.checked) {
            activeFilters.push(filterMapping[checkbox.value]);
        }
    });
    
    if (activeFilters.length === 0) {
        renderProducts(allProducts);
    } else {
        const filteredProducts = allProducts.filter(product => 
            activeFilters.includes(product.type)
        );
        renderProducts(filteredProducts);
    }
}

