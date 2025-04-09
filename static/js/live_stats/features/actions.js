import { appState } from '../core/state.js';

export function recordPlayerAction(playerNumber, actionType, zone) {
    console.log(`Игрок #${playerNumber} в зоне ${zone}: ${actionType}`);

    const actionData = {
        player: playerNumber,
        action: actionType,
        zone: zone,
        timestamp: new Date().toISOString()
    };

    fetch('/record_action', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(actionData)
    })
    .then(response => {
        if (!response.ok) {
            console.error('Ошибка сохранения действия');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

let longPressTimer = null;

export function startLongPress(e) {
    longPressTimer = setTimeout(() => {
        showAttackOptionsModal(e.target);
    }, LONG_PRESS_DURATION);
}

export function endLongPress() {
    if (longPressTimer) {
        clearTimeout(longPressTimer);
        longPressTimer = null;
    }
}

export function cancelLongPress() {
    if (longPressTimer) {
        clearTimeout(longPressTimer);
        longPressTimer = null;
    }
}

export function handleAttackPlusClick(e) {
    if (longPressTimer) {
        clearTimeout(longPressTimer);
        longPressTimer = null;

        const zone = e.target.closest('[data-zone]');
        const playerNumber = zone.querySelector('.player-field.filled')?.textContent.match(/#(\d+)/)?.[1];
        if (playerNumber) {
            recordPlayerAction(playerNumber, 'Удар +', zone.dataset.zone);
        }
    }
}