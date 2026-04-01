document.addEventListener('DOMContentLoaded', function() {
    // Элементы поиска
    const searchInput = document.getElementById('search-input');
    const services = document.querySelectorAll('.service');

    // Обработка поиска
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();

        services.forEach(service => {
            const title = service.dataset.title;
            if (title.includes(searchTerm)) {
                service.style.display = 'flex';
            } else {
                service.style.display = 'none';
            }
        });
    });

    // Горячая клавиша для поиска
    document.addEventListener('keydown', function(e) {
        if (e.key === '/' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            searchInput.focus();
        }
    });

    // Обработка кнопки профиля
    const profileBtn = document.querySelector('.profile-btn');
    if (profileBtn) {
        profileBtn.addEventListener('click', function() {
            window.location.href = '/profile/';
        });
    }



    const logoutBtn = document.querySelector('.logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            window.location.href = '/logout/';
        });
    }

    const loginBtn = document.querySelector('.login-btn');
    if (loginBtn) {
        loginBtn.addEventListener('click', function() {
            window.location.href = '/login/';
        });
    }

    // Обработка кнопки "Создать услугу"
    const createBtn = document.querySelector('.create-btn');
    if (createBtn) {
        createBtn.addEventListener('click', function() {
            window.location.href = '/create-service/';
        });
    }
});