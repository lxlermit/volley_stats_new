import { appState, matchState } from '../core/state.js';
import { returnPlayerToBench, resetField } from '../features/players.js';
import { flipCourt } from '../features/court.js';
import { recordPlayerAction } from '../features/actions.js';
import { updateScoreDisplay } from '../features/score.js';
import { updateServeUI, updateZone1Actions } from './serve-ui.js';

export function initModal() {
    const removeModalClose = document.querySelector('#remove-player-modal .close, #cancel-remove');
    if (removeModalClose) {
        removeModalClose.onclick = () => {
            document.getElementById('remove-player-modal').style.display = 'none';
        };
    }

    window.addEventListener('click', function(event) {
        if (event.target === document.getElementById('remove-player-modal')) {
            event.target.style.display = 'none';
        }
    });
}

export function openRemoveModal(playerNumber, fieldElement) {
    const modal = document.getElementById('remove-player-modal');
    if (!modal) return;

    const playerInfo = document.getElementById('player-to-remove-info');
    if (playerInfo) {
        playerInfo.textContent = `Игрок #${playerNumber} будет отправлен на скамейку.`;
    }

    const confirmButton = document.getElementById('confirm-remove');
    if (confirmButton) {
        confirmButton.onclick = () => {
            returnPlayerToBench(playerNumber);
            resetField(fieldElement);
            modal.style.display = 'none';
        };
    }

    modal.style.display = 'block';
}

export function showAttackOptionsModal(button) {
    const modal = document.getElementById('attack-modal');
    if (!modal) return;

    const zone = button.closest('[data-zone]');
    const playerField = zone.querySelector('.player-field.filled');
    if (!playerField) return;

    const playerNumber = playerField.textContent.match(/#(\d+)/)?.[1];
    if (!playerNumber) return;

    const rect = button.getBoundingClientRect();
    const modalContent = modal.querySelector('.attack-modal-content');
    modalContent.style.position = 'fixed';
    modalContent.style.left = `${rect.left}px`;
    modalContent.style.top = `${rect.bottom + 5}px`;

    const closeButton = modal.querySelector('.close');
    closeButton.onclick = function() {
        modal.style.display = 'none';
    };

    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    document.getElementById('attack-cross').onclick = function() {
        recordPlayerAction(playerNumber, 'Удар + по диагонали', zone.dataset.zone);
        modal.style.display = 'none';
    };

    document.getElementById('attack-line').onclick = function() {
        recordPlayerAction(playerNumber, 'Удар + по линии', zone.dataset.zone);
        modal.style.display = 'none';
    };

    document.getElementById('attack-tip').onclick = function() {
        recordPlayerAction(playerNumber, 'Удар + скидка', zone.dataset.zone);
        modal.style.display = 'none';
    };

    document.getElementById('attack-block-out').onclick = function() {
        recordPlayerAction(playerNumber, 'Удар + в аут с блока', zone.dataset.zone);
        modal.style.display = 'none';
    };

    modal.style.display = 'block';
    longPressTimer = null;
}

export function initSettingsModal() {
    const modal = document.getElementById('settings-modal');
    if (!modal) return;

    const settingsButton = document.getElementById('settings-btn');
    if (settingsButton) {
        settingsButton.addEventListener('click', function(e) {
            e.stopPropagation();
            modal.style.display = 'block';
        });
    }

    const closeButton = modal.querySelector('.close');
    if (closeButton) {
        closeButton.addEventListener('click', function(e) {
            e.stopPropagation();
            modal.style.display = 'none';
        });
    }

    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    const setupModalButton = function(id, callback) {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                callback();
                modal.style.display = 'none';
            });
        }
    };

    setupModalButton('mirror-btn', flipCourt);

    setupModalButton('serve-toggle-btn', function() {
        appState.isOurServe = !appState.isOurServe;
        updateServeUI();
        updateZone1Actions();
    });

    setupModalButton('clear-to-serve', function() {
        console.log('Очистка до подачи');
    });

    setupModalButton('undo-last-action', function() {
        console.log('Отмена до предыдущей подачи');
    });

    setupModalButton('save-match', function() {
        console.log('Сохранение матча');
    });

    setupModalButton('end-set-from-settings', function() {
        if (matchState.currentSet > matchState.maxSets) return;

        const setResult = {
            our: matchState.ourScore,
            opponent: matchState.opponentScore
        };

        fetch('/save_set', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                set_number: matchState.currentSet,
                result: setResult
            })
        })
        .then(response => {
            if (response.ok) {
                const setElement = document.getElementById(`set-${matchState.currentSet}`);
                if (setElement) {
                    setElement.textContent = `${matchState.ourScore}:${matchState.opponentScore}`;
                }

                matchState.ourScore = 0;
                matchState.opponentScore = 0;
                matchState.currentSet++;
                updateScoreDisplay();
            }
        })
        .catch(error => {
            console.error('Ошибка сохранения партии:', error);
        });
    });

    setupModalButton('end-game-from-settings', function() {
        const setResult = {
            our: matchState.ourScore,
            opponent: matchState.opponentScore
        };

        fetch('/save_set', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                set_number: matchState.currentSet,
                result: setResult,
                end_match: true
            })
        })
        .then(() => {
            window.location.href = "/";
        })
        .catch(error => {
            console.error('Ошибка завершения матча:', error);
        });
    });

    setupModalButton('clear-players', clearAllPlayers);
}