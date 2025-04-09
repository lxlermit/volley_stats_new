// Для team_management.js
/**
 * Модуль для управления составом команды
 * @module teamManagement
 */

export function initTeamManagement() {
    // Элементы модального окна
    const settingsModal = document.getElementById('settings-modal');
    const settingsBtn = document.getElementById('settings-btn');
    const settingsClose = document.querySelector('.settings-close');

    // Кнопки действий
    const clearPlayersBtn = document.getElementById('clear-players-btn');
    const setStartingLineupBtn = document.getElementById('set-starting-lineup-btn');
    const rotateClockwiseBtn = document.getElementById('rotate-clockwise-btn');
    const rotateCounterBtn = document.getElementById('rotate-counter-btn');

    // Обработчики открытия/закрытия модального окна
    if (settingsBtn) {
        settingsBtn.addEventListener('click', openSettingsModal);
    }

    if (settingsClose) {
        settingsClose.addEventListener('click', closeSettingsModal);
    }

    // Обработчики кнопок управления
    if (clearPlayersBtn) {
        clearPlayersBtn.addEventListener('click', clearAllPlayers);
    }

    if (setStartingLineupBtn) {
        setStartingLineupBtn.addEventListener('click', setStartingLineup);
    }

    if (rotateClockwiseBtn) {
        rotateClockwiseBtn.addEventListener('click', rotatePlayersClockwise);
    }

    if (rotateCounterBtn) {
        rotateCounterBtn.addEventListener('click', rotatePlayersCounterClockwise);
    }

    /**
     * Открывает модальное окно управления составом
     */
    function openSettingsModal() {
        settingsModal.style.display = 'block';
        document.body.classList.add('modal-open');
    }

    /**
     * Закрывает модальное окно управления составом
     */
    function closeSettingsModal() {
        settingsModal.style.display = 'none';
        document.body.classList.remove('modal-open');
    }

    /**
     * Очищает все игровые зоны (убирает всех игроков с поля)
     */
    function clearAllPlayers() {
        const playerFields = document.querySelectorAll('.player-field');

        playerFields.forEach(function(field) {
            field.dataset.playerNumber = '';
            field.textContent = `Зона ${field.dataset.zone}`;
        });

        console.log('Все игроки убраны с поля');
        closeSettingsModal();
    }

    /**
     * Восстанавливает стартовый состав из настроек команды
     */
    function setStartingLineup() {
        if (!window.teamData || !window.teamData.starting_lineup) {
            console.error('Данные стартового состава не найдены');
            return;
        }

        const startingLineup = window.teamData.starting_lineup;

        for (const [position, playerNumber] of Object.entries(startingLineup)) {
            if (!playerNumber) continue;

            const zoneNumber = position.split('_')[1];
            const field = document.querySelector(`.player-field[data-zone="${zoneNumber}"]`);

            if (field) {
                const player = window.playersData.find(p => p.number === playerNumber);
                if (player) {
                    field.dataset.playerNumber = player.number;
                    field.textContent = `${player.number} - ${player.last_name} ${player.first_name[0]}.`;
                }
            }
        }

        console.log('Стартовый состав восстановлен');
        closeSettingsModal();
    }

    /**
     * Перемещает всех игроков по часовой стрелке
     */
    function rotatePlayersClockwise() {
        const playerFields = Array.from(document.querySelectorAll('.player-field'))
            .sort((a, b) => parseInt(a.dataset.zone) - parseInt(b.dataset.zone));

        if (playerFields.length !== 6) {
            console.error('Не найдены все 6 игровых зон');
            return;
        }

        // Сохраняем игроков из последней зоны
        const lastPlayer = {
            number: playerFields[5].dataset.playerNumber,
            text: playerFields[5].textContent
        };

        // Перемещаем игроков с 1 по 5 зону
        for (let i = 5; i > 0; i--) {
            playerFields[i].dataset.playerNumber = playerFields[i-1].dataset.playerNumber;
            playerFields[i].textContent = playerFields[i-1].textContent;
        }

        // Переносим игрока из последней зоны в первую
        playerFields[0].dataset.playerNumber = lastPlayer.number;
        playerFields[0].textContent = lastPlayer.text;

        console.log('Игроки перемещены по часовой стрелке');
        closeSettingsModal();
    }

    /**
     * Перемещает всех игроков против часовой стрелки
     */
    function rotatePlayersCounterClockwise() {
        const playerFields = Array.from(document.querySelectorAll('.player-field'))
            .sort((a, b) => parseInt(a.dataset.zone) - parseInt(b.dataset.zone));

        if (playerFields.length !== 6) {
            console.error('Не найдены все 6 игровых зон');
            return;
        }

        // Сохраняем игроков из первой зоны
        const firstPlayer = {
            number: playerFields[0].dataset.playerNumber,
            text: playerFields[0].textContent
        };

        // Перемещаем игроков со 2 по 6 зону
        for (let i = 0; i < 5; i++) {
            playerFields[i].dataset.playerNumber = playerFields[i+1].dataset.playerNumber;
            playerFields[i].textContent = playerFields[i+1].textContent;
        }

        // Переносим игрока из первой зоны в последнюю
        playerFields[5].dataset.playerNumber = firstPlayer.number;
        playerFields[5].textContent = firstPlayer.text;

        console.log('Игроки перемещены против часовой стрелки');
        closeSettingsModal();
    }
}

//// Добавляем в глобальную область видимости
//window.initTeamManagement = initTeamManagement;

// Инициализируем систему замен при загрузке модуля
document.addEventListener('DOMContentLoaded', function() {
    initTeamManagement();
});