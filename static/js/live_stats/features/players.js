import { appState } from '../core/state.js';
import { updateZone1Actions } from '../ui/serve-ui.js';

// Основные экспортируемые функции
export function placePlayerOnField(field, number, name, color, zone) {
    field.textContent = name;
    field.style.backgroundColor = color;
    field.classList.replace('empty', 'filled');

    document.querySelector(`#players-header .player-tag[data-number="${number}"]`)
        .style.display = 'none';

    appState.playersOnField[number] = zone;
    field.onclick = () => window.openRemoveModal(number, field);

    if (zone === '1' || zone === '4') {
        updateZone1Actions();
    }
}

export function returnPlayerToBench(playerNumber) {
    const playerElement = document.querySelector(
        `#players-header .player-tag[data-number="${playerNumber}"]`
    );
    if (playerElement) {
        playerElement.style.display = 'inline-block';
    }
    delete appState.playersOnField[playerNumber];
}

export function initPlayerTags() {
    document.querySelectorAll('#players-header .player-tag').forEach(player => {
        player.addEventListener('dragstart', function(e) {
            e.dataTransfer.setData('playerNumber', this.dataset.number);
            e.dataTransfer.setData('playerName',
                `#${this.dataset.number} ${this.dataset.lastName} ${this.dataset.firstName}`);
            e.dataTransfer.setData('playerColor', this.style.backgroundColor);
        });

        player.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
            this.style.boxShadow = '0 0 10px rgba(0,0,0,0.2)';
        });

        player.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.boxShadow = '';
        });
    });
}

export function resetField(field) {
    const zone = field.closest('[data-zone]').dataset.zone;
    field.textContent = `Зона ${zone}`;
    field.style.backgroundColor = '#e0e0e0';
    field.classList.replace('filled', 'empty');

    const newField = field.cloneNode(true);
    field.replaceWith(newField);
    window.setupFieldEvents(newField);
}

export function clearAllPlayers() {
    document.querySelectorAll('.player-field.filled').forEach(field => {
        const playerNumber = field.textContent.match(/#(\d+)/)?.[1];
        if (playerNumber) {
            returnPlayerToBench(playerNumber);
            resetField(field);
        }
    });
}

// Экспортируем функции в глобальную область для court.js
window.placePlayerOnField = placePlayerOnField;
window.returnPlayerToBench = returnPlayerToBench;


// ----- Все ниже для вставки игроков в зоны на площадке во время игры -----
// features/players.js

export function initPlayers() {
    // Инициализация обработчиков клика по позициям
    document.querySelectorAll('.player-field').forEach(field => {
        field.addEventListener('click', handlePlayerClick);
    });
}

function handlePlayerClick(e) {
    const field = e.currentTarget;
    const zone = field.dataset.zone;
    showSubstitutionModal(zone);
}

export function showSubstitutionModal(zone) {
    // Используем существующий модуль модальных окон
    const modalContent = `
        <h3>Выберите замену для зоны ${zone}</h3>
        <div class="substitute-list" id="substitute-list-${zone}"></div>
    `;

    window.modalManager.open({
        id: 'substitution-modal',
        content: modalContent,
        onOpen: () => populateSubstitutes(zone)
    });
}

function populateSubstitutes(zone) {
    const container = document.getElementById(`substitute-list-${zone}`);
    const currentPlayers = getCurrentFieldPlayers();

    window.state.teamPlayers.forEach(player => {
        if (!currentPlayers.has(player.number)) {
            const btn = document.createElement('button');
            btn.className = 'substitute-btn';
            btn.textContent = `${player.number} - ${player.name}`;
            btn.onclick = () => substitutePlayer(zone, player.number);
            container.appendChild(btn);
        }
    });
}

function getCurrentFieldPlayers() {
    const players = new Set();
    document.querySelectorAll('.player-field').forEach(field => {
        players.add(field.dataset.playerNumber);
    });
    return players;
}

function substitutePlayer(zone, newPlayerNumber) {
    const field = document.querySelector(`.player-field[data-zone="${zone}"]`);
    const player = window.state.teamPlayers.find(p => p.number === newPlayerNumber);

    if (field && player) {
        // Обновляем данные на поле
        field.dataset.playerNumber = player.number;
        field.querySelector('.player-number').textContent = player.number;
        field.querySelector('.player-name').textContent = player.name;

        // Закрываем модальное окно
        window.modalManager.close('substitution-modal');

        // Обновляем состояние приложения
        window.state.updatePlayerPosition(zone, player.number);
    }
}