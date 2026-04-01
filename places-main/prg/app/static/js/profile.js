document.addEventListener('DOMContentLoaded', function() {
    const elements = document.querySelectorAll('.animate-fade-in, .animate-slide-up');
    elements.forEach((el, index) => {
        el.style.animationDelay = `${index * 0.1}s`;
    });

    const avatar = document.querySelector('.avatar-circle');
    const userName = document.querySelector('.user-name').textContent.trim();
    const initials = getInitials(userName);
    avatar.textContent = initials;

    const header = document.querySelector('.profile-header');
    window.addEventListener('scroll', function() {
        const scrollPosition = window.pageYOffset;
        header.style.boxShadow = `0 ${2 + scrollPosition * 0.05}px ${10 + scrollPosition * 0.1}px rgba(0, 0, 0, ${0.1 + scrollPosition * 0.001})`;
    });
});

function getInitials(name) {
    return name.split(' ')
        .map(part => part.charAt(0))
        .join('')
        .toUpperCase();
}