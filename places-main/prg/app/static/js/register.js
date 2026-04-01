document.addEventListener('DOMContentLoaded', function() {
    document.body.classList.add('fade-in');

    function showError(message) {
        const errorContainer = document.querySelector('.error-container');
        errorContainer.innerHTML = '';
        const error = document.createElement('div');
        error.className = 'field-error';
        error.innerHTML = `${message}<div class="progress-bar"></div>`;
        errorContainer.appendChild(error);

        setTimeout(() => {
            error.style.animation = 'slideOut 0.3s forwards';
            setTimeout(() => error.remove(), 300);
        }, 3000);
    }

    function initDatePicker() {
        const dateInput = document.querySelector('[name="birth_date"]');
        const calendarIcon = document.querySelector('.calendar-icon');
        const datepicker = document.querySelector('.custom-datepicker');
        const currentMonthYear = document.querySelector('.current-month-year');
        const daysGrid = document.querySelector('.days-grid');
        const prevMonthBtn = document.querySelector('.prev-month');
        const nextMonthBtn = document.querySelector('.next-month');
        const prevYearBtn = document.querySelector('.prev-year');
        const nextYearBtn = document.querySelector('.next-year');
        const clearBtn = document.querySelector('.clear-btn');
        const yearsContainer = document.querySelector('.datepicker-years');

        let currentDate = new Date();
        let selectedDate = null;
        const minYear = 1950;
        const maxYear = 2024;

        dateInput.type = 'text';
        dateInput.placeholder = 'дд.мм.гггг';

        function formatDate(date) {
            if (!date) return '';
            const day = String(date.getDate()).padStart(2, '0');
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const year = date.getFullYear();
            return `${day}.${month}.${year}`;
        }

        function parseDate(dateStr) {
            if (!dateStr) return null;

            if (!/^\d{2}\.\d{2}\.\d{4}$/.test(dateStr)) {
                return null;
            }

            const parts = dateStr.split('.');
            const day = parseInt(parts[0], 10);
            const month = parseInt(parts[1], 10) - 1;
            const year = parseInt(parts[2], 10);

            if (year < minYear || year > maxYear) return null;

            const date = new Date(year, month, day);

            if (date.getDate() !== day || date.getMonth() !== month || date.getFullYear() !== year) {
                return null;
            }

            return date;
        }

        function updateCalendar() {
            const year = currentDate.getFullYear();
            const month = currentDate.getMonth();

            const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                              'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
            currentMonthYear.textContent = `${monthNames[month]} ${year}`;

            daysGrid.innerHTML = '';

            ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].forEach(day => {
                const dayElement = document.createElement('div');
                dayElement.textContent = day;
                dayElement.style.fontWeight = 'bold';
                daysGrid.appendChild(dayElement);
            });

            const firstDay = new Date(year, month, 1);
            const lastDay = new Date(year, month + 1, 0);
            const firstDayOfWeek = (firstDay.getDay() + 6) % 7;

            for (let i = 0; i < firstDayOfWeek; i++) {
                daysGrid.appendChild(document.createElement('div')).className = 'day other-month';
            }

            for (let day = 1; day <= lastDay.getDate(); day++) {
                const date = new Date(year, month, day);
                const dayElement = document.createElement('div');
                dayElement.className = 'day';
                dayElement.textContent = day;

                if (selectedDate && selectedDate.getDate() === day &&
                    selectedDate.getMonth() === month && selectedDate.getFullYear() === year) {
                    dayElement.classList.add('selected');
                }

                if (year < minYear || year > maxYear) {
                    dayElement.classList.add('disabled');
                } else {
                    dayElement.addEventListener('click', () => {
                        selectedDate = date;
                        dateInput.value = formatDate(selectedDate);
                        updateCalendar();
                        datepicker.classList.remove('active');
                    });
                }

                daysGrid.appendChild(dayElement);
            }

            const totalDays = firstDayOfWeek + lastDay.getDate();
            const remainingCells = 7 - (totalDays % 7);
            if (remainingCells < 7) {
                for (let i = 1; i <= remainingCells; i++) {
                    daysGrid.appendChild(document.createElement('div')).className = 'day other-month';
                }
            }
        }

        function updateYears() {
            yearsContainer.innerHTML = '';
            for (let year = maxYear; year >= minYear; year--) {
                const yearElement = document.createElement('div');
                yearElement.textContent = year;
                if (currentDate.getFullYear() === year) yearElement.className = 'selected';

                yearElement.addEventListener('click', () => {
                    currentDate.setFullYear(year);
                    yearsContainer.classList.remove('active');
                    updateCalendar();
                });

                yearsContainer.appendChild(yearElement);
            }
        }

        function handleManualInput() {
            const value = dateInput.value.trim();
            if (!value) {
                selectedDate = null;
                return;
            }

            const date = parseDate(value);
            if (date) {
                selectedDate = date;
                currentDate = new Date(date);
                updateCalendar();
            } else {
                showError('Введите дату в формате дд.мм.гггг (1950-2024)');
                dateInput.value = '';
                selectedDate = null;
            }
        }

        function init() {
            if (dateInput.value) {
                const date = parseDate(dateInput.value);
                if (date) {
                    selectedDate = date;
                    currentDate = new Date(date);
                }
            }

            updateCalendar();
            updateYears();

            calendarIcon.addEventListener('click', (e) => {
                e.stopPropagation();
                datepicker.classList.toggle('active');
                yearsContainer.classList.remove('active');
            });

            prevMonthBtn.addEventListener('click', () => {
                currentDate.setMonth(currentDate.getMonth() - 1);
                updateCalendar();
            });

            nextMonthBtn.addEventListener('click', () => {
                currentDate.setMonth(currentDate.getMonth() + 1);
                updateCalendar();
            });

            prevYearBtn.addEventListener('click', () => {
                const newYear = currentDate.getFullYear() - 1;
                if (newYear >= minYear) {
                    currentDate.setFullYear(newYear);
                    updateCalendar();
                }
            });

            nextYearBtn.addEventListener('click', () => {
                const newYear = currentDate.getFullYear() + 1;
                if (newYear <= maxYear) {
                    currentDate.setFullYear(newYear);
                    updateCalendar();
                }
            });

            currentMonthYear.addEventListener('click', () => {
                yearsContainer.classList.toggle('active');
            });

            clearBtn.addEventListener('click', () => {
                selectedDate = null;
                dateInput.value = '';
                datepicker.classList.remove('active');
            });

            document.addEventListener('click', (e) => {
                if (!datepicker.contains(e.target) && e.target !== calendarIcon) {
                    datepicker.classList.remove('active');
                    yearsContainer.classList.remove('active');
                }
            });

            dateInput.addEventListener('blur', handleManualInput);
            dateInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    handleManualInput();
                }
            });
        }

        init();
    }

    initDatePicker();

    const form = document.querySelector('.auth-form');

    function validateForm() {
        let isValid = true;

        const email = form.querySelector('[name="email"]').value.trim();
        if (!email) {
            showError('Введите email');
            isValid = false;
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            showError('Введите корректный email');
            isValid = false;
        }

        const birthDate = form.querySelector('[name="birth_date"]').value.trim();
        if (!birthDate) {
            showError('Введите дату рождения');
            isValid = false;
        } else {
            const date = parseDate(birthDate);
            if (!date) {
                showError('Дата рождения должна быть в формате дд.мм.гггг (1950-2024)');
                isValid = false;
            }
        }

        return isValid;
    }

    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            if (validateForm()) {
                form.submit();
            }
        });
    }

    function parseDate(dateStr) {
        if (!dateStr) return null;
        if (!/^\d{2}\.\d{2}\.\d{4}$/.test(dateStr)) return null;

        const parts = dateStr.split('.');
        const day = parseInt(parts[0], 10);
        const month = parseInt(parts[1], 10) - 1;
        const year = parseInt(parts[2], 10);

        if (year < 1950 || year > 2024) return null;

        const date = new Date(year, month, day);
        if (date.getDate() !== day || date.getMonth() !== month || date.getFullYear() !== year) {
            return null;
        }

        return date;
    }
});