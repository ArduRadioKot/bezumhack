let cardIdCounter = 0;

function addCard(columnId) {
    const column = document.getElementById(columnId);
    const card = document.createElement('div');
    card.classList.add('card');
    card.draggable = true;
    card.id = 'card-' + cardIdCounter++;

    // Color picker
    const colorPicker = document.createElement('input');
    colorPicker.type = 'color';
    colorPicker.value = '#f9f9f9'; // Default card color
    colorPicker.style.marginRight = '5px';
    colorPicker.addEventListener('change', function(event) {
        card.style.backgroundColor = event.target.value;
    });
    card.appendChild(colorPicker);

    const cardText = document.createElement('span');
    cardText.textContent = 'New Card';
    cardText.addEventListener('click', function() {
        const newText = prompt('Enter new card name:', cardText.textContent);
        if (newText) {
            cardText.textContent = newText;
        }
    });
    card.appendChild(cardText);

    const deleteButton = document.createElement('button');
    deleteButton.classList.add('delete-button');
    deleteButton.textContent = 'Delete';
    deleteButton.onclick = function() {
        card.remove();
    };
    card.appendChild(deleteButton);

    card.addEventListener('dragstart', dragStart);
    column.appendChild(card);
}

function allowDrop(event) {
    event.preventDefault();
}

function dragStart(event) {
    event.dataTransfer.setData('text/plain', event.target.id);
}

function drop(event) {
    event.preventDefault();
    const cardId = event.dataTransfer.getData('text/plain');
    const card = document.getElementById(cardId);
    const column = event.target;

    if (column.classList.contains('column')) {
        column.appendChild(card);
    }
}

document.getElementById('theme-toggle').addEventListener('click', function() {
    document.body.classList.toggle('dark-mode');
});
