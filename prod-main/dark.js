const toggle = document.querySelector('[dark]');
const icon = toggle.querySelector('img');

function applyTheme(dark) {
    if (dark) {
        document.documentElement.classList.add('dark-theme');
        icon.src = './images/icons/sun.svg';
        icon.alt = 'Light';
    } else {
        document.documentElement.classList.remove('dark-theme');
        icon.src = './images/icons/moon.svg';
        icon.alt = 'Dark';
    }
}

function loadTheme() {
    const saved = localStorage.getItem('theme');
    const dark = saved === 'dark';
    applyTheme(dark);
}

function toggleTheme() {
    const dark = document.documentElement.classList.contains('dark-theme');
    const theme = dark ? 'light' : 'dark';
    localStorage.setItem('theme', theme);
    applyTheme(theme === 'dark');
}

toggle.addEventListener('click', toggleTheme);
loadTheme();
