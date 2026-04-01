document.addEventListener('DOMContentLoaded', function() {
    document.body.classList.add('fade-in');

    const form = document.querySelector('.auth-form');
    const usernameInput = form.querySelector('[name="username"]');
    const passwordInput = form.querySelector('[name="password"]');
    const errorContainer = document.querySelector('.error-container');
    const notificationContainer = document.querySelector('.notification-container');

    function createErrorElement(message) {
        const error = document.createElement('div');
        error.className = 'field-error';
        error.innerHTML = `
            ${message}
            <div class="progress-bar"></div>
        `;
        return error;
    }

    function showError(message) {
        errorContainer.innerHTML = '';
        const error = createErrorElement(message);
        errorContainer.appendChild(error);

        setTimeout(() => {
            error.style.animation = 'slideOut 0.3s forwards';
            setTimeout(() => error.remove(), 300);
        }, 3000);
    }

    function showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            ${message}
            <div class="progress-bar"></div>
        `;
        notificationContainer.appendChild(notification);

        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    function validateField(input, fieldName) {
        if (!input.value.trim()) {
            showError(`Пожалуйста, заполните поле "${fieldName}"`);
            input.focus();
            return false;
        }
        return true;
    }

    form.setAttribute('novalidate', true);

    form.addEventListener('submit', function(e) {
        const isUsernameValid = validateField(usernameInput, 'Логин');
        const isPasswordValid = validateField(passwordInput, 'Пароль');

        if (!isUsernameValid || !isPasswordValid) {
            e.preventDefault();
        } else {
            showNotification('Вход выполняется...', 'success');
        }
    });

    const passwordToggle = document.querySelector('.password-toggle');
    if (passwordToggle) {
        passwordToggle.addEventListener('click', function() {
            const eyeIcon = this.querySelector('.eye-icon');
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                eyeIcon.innerHTML = '<path d="M12 9a3 3 0 0 1 3 3 3 3 0 0 1-3 3 3 3 0 0 1-3-3 3 3 0 0 1 3-3m0-2a5 5 0 0 0-5 5 5 5 0 0 0 5 5 5 5 0 0 0 5-5 5 5 0 0 0-5-5zm0 6a1 1 0 0 0-1 1 1 1 0 0 0 1 1 1 1 0 0 0 1-1 1 1 0 0 0-1-1z"/>';
            } else {
                passwordInput.type = 'password';
                eyeIcon.innerHTML = '<path d="M12 9a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3m0 8a5 5 0 0 1-5-5 5 5 0 0 1 5-5 5 5 0 0 1 5 5 5 5 0 0 1-5 5m0-12.5C7 4.5 2.7 7.6 1 12c1.7 4.4 6 7.5 11 7.5s9.3-3.1 11-7.5c-1.7-4.4-6-7.5-11-7.5z"/>';
            }
        });
    }

    [usernameInput, passwordInput].forEach(input => {
        input.addEventListener('input', function() {
            this.style.borderColor = this.value.trim() ? '#ddd' : '#ff4444';
        });
    });
});