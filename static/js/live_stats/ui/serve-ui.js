import { appState } from '../core/state.js';
import { recordPlayerAction } from '../features/actions.js';

export function updateServeUI() {
    const serveButton = document.getElementById('serve-toggle-btn');
    if (serveButton) {
        serveButton.textContent = appState.isOurServe ? '🎾 Соперник подает' : '🎾 Мы подаем';
        serveButton.style.backgroundColor = appState.isOurServe ? '#F44336' : '#4CAF50';
    }
}

export function updateZone1Actions() {
    const zone1 = document.getElementById('zone-1');
    if (!zone1) return;

    const currentZone = zone1.closest('[data-zone]');
    const oldServingRow = currentZone.querySelector('.serving-row');
    if (oldServingRow) {
        oldServingRow.remove();
    }

    if (appState.isOurServe) {
        const servingRow = document.createElement('div');
        servingRow.className = 'serving-row';
        servingRow.innerHTML = `
            <div class="serving-field ace-serve">Ace</div>
            <div class="serving-field normal-serve">Подача</div>
            <div class="serving-field error-serve">Подача -</div>
        `;

        const playerField = currentZone.querySelector('.player-field');
        if (playerField) {
            currentZone.insertBefore(servingRow, playerField);
        }

        servingRow.querySelectorAll('.serving-field').forEach(button => {
            button.addEventListener('click', function() {
                const playerNumber = currentZone.querySelector('.player-field.filled')?.textContent.match(/#(\d+)/)?.[1];
                if (playerNumber) {
                    const actionType = this.classList.contains('ace-serve') ? 'serve_ace' :
                                     this.classList.contains('error-serve') ? 'serve_error' : 'serve_normal';
                    recordPlayerAction(playerNumber, actionType, currentZone.dataset.zone);
                }
            });
        });
    }
}