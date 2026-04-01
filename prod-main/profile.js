const form = document.getElementById('profileForm');
const name = document.getElementById('name');
const email = document.getElementById('email');
const notify = document.getElementById('notifications');
const nameErr = name.parentElement.querySelector('.error-message');
const emailErr = email.parentElement.querySelector('.error-message');
const msg = document.querySelector('.success-message');

function loadProfile() {
    const data = localStorage.getItem('profile');
    if (data) {
        const obj = JSON.parse(data);
        name.value = obj.name || '';
        email.value = obj.email || '';
        notify.checked = obj.notifications || false;
    }
}

function validateName() {
    const val = name.value.trim();
    if (!val) {
        nameErr.textContent = 'Name is required';
        name.classList.add('error');
        return false;
    }
    nameErr.textContent = '';
    name.classList.remove('error');
    return true;
}

function validateEmail() {
    const val = email.value.trim();
    if (!val) {
        emailErr.textContent = 'E-mail is required';
        email.classList.add('error');
        return false;
    }
    
    const count = (val.match(/@/g) || []).length;
    if (count !== 1) {
        emailErr.textContent = 'E-mail must contain exactly one @ symbol';
        email.classList.add('error');
        return false;
    }
    
    const idx = val.indexOf('@');
    const after = val.substring(idx + 1);
    const dots = (after.match(/\./g) || []).length;
    if (dots > 1) {
        emailErr.textContent = 'E-mail must contain exactly one dot after @';
        email.classList.add('error');
        return false;
    }
    
    emailErr.textContent = '';
    email.classList.remove('error');
    return true;
}

function showSuccess() {
    msg.textContent = 'Data saved';
    msg.classList.add('active');
    setTimeout(() => {
        msg.classList.remove('active');
    }, 2000);
}

function saveProfile() {
    const obj = {
        name: name.value.trim(),
        email: email.value.trim(),
        notifications: notify.checked
    };
    localStorage.setItem('profile', JSON.stringify(obj));
    showSuccess();
}

form.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const nameOk = validateName();
    const emailOk = validateEmail();
    
    if (nameOk && emailOk) {
        saveProfile();
    }
});

name.addEventListener('blur', validateName);
email.addEventListener('blur', validateEmail);

loadProfile();

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

updateCartCount();
