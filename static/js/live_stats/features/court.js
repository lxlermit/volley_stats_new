import { appState } from '../core/state.js';
import { updateZone1Actions } from '../ui/serve-ui.js';

export function setupFieldEvents(field) {
    field.addEventListener('dragover', function(e) {
        e.preventDefault();
        if (this.classList.contains('empty')) {
            this.style.backgroundColor = '#d0d0d0';
        }
    });

    field.addEventListener('dragleave', function() {
        if (this.classList.contains('empty')) {
            this.style.backgroundColor = '#e0e0e0';
        }
    });

    field.addEventListener('drop', function(e) {
        e.preventDefault();
        const zone = this.closest('[data-zone]').dataset.zone;
        const playerNumber = e.dataTransfer.getData('playerNumber');
        const playerName = e.dataTransfer.getData('playerName');
        const playerColor = e.dataTransfer.getData('playerColor');

        if (this.classList.contains('filled')) {
            const currentPlayerNumber = this.textContent.match(/#(\d+)/)[1];
            window.returnPlayerToBench(currentPlayerNumber);
        }

        window.placePlayerOnField(this, playerNumber, playerName, playerColor, zone);
    });
}

export function initZoneFields() {
    document.querySelectorAll('.player-field.empty').forEach(field => {
        setupFieldEvents(field);
    });
}

export function flipCourt() {
    const courtArea = document.getElementById('court-area');
    if (!courtArea) return;

    appState.isFlipped = !appState.isFlipped;
    courtArea.classList.toggle('flipped', appState.isFlipped);

    const zonesState = {};
    document.querySelectorAll('.net-zone, .back-zone').forEach(zone => {
        const currentZone = zone.dataset.zone;
        zonesState[currentZone] = {
            playerHtml: zone.querySelector('.player-field').outerHTML,
            actionRowsHtml: Array.from(zone.querySelectorAll('.action-row, .receive-row, .serving-row'))
                              .filter(row => row.innerHTML.trim() !== '')
                              .map(row => row.outerHTML),
            number: zone.querySelector('.player-field.filled')?.textContent.match(/#(\d+)/)?.[1]
        };
    });

    document.querySelectorAll('.net-zone, .back-zone').forEach(zone => {
        const currentZone = zone.dataset.zone;
        const targetZone = appState.zoneMapping[currentZone];

        zone.innerHTML = `
            ${zonesState[targetZone]?.actionRowsHtml.join('') || ''}
            ${zonesState[targetZone]?.playerHtml || `<div class="player-field empty" id="player-${targetZone}" data-zone="${targetZone}">Зона ${targetZone}</div>`}
        `;

        const playerField = zone.querySelector('.player-field');
        if (playerField.classList.contains('filled')) {
            const playerNumber = zonesState[targetZone]?.number;
            if (playerNumber) {
                playerField.onclick = () => window.openRemoveModal(playerNumber, playerField);
            }
        } else {
            setupFieldEvents(playerField);
        }

        zone.dataset.zone = targetZone;
        zone.id = `zone-${targetZone}`;
        setupActionButtons(zone);
    });

    updateZone1Actions();
}

export function setupActionButtons(zone) {
    zone.querySelectorAll('.action-field').forEach(button => {
        if (button.classList.contains('attack-plus')) {
            button.addEventListener('mousedown', window.startLongPress);
            button.addEventListener('mouseup', window.endLongPress);
            button.addEventListener('mouseleave', window.cancelLongPress);
            button.addEventListener('click', window.handleAttackPlusClick);
        } else {
            button.addEventListener('click', function() {
                const zoneNumber = zone.dataset.zone;
                const actionType = this.textContent.trim();
                const playerNumber = zone.querySelector('.player-field.filled')?.textContent.match(/#(\d+)/)?.[1];
                if (playerNumber) {
                    window.recordPlayerAction(playerNumber, actionType, zoneNumber);
                }
            });
        }
    });
}

export function setupActionButtonsForAllZones() {
    document.querySelectorAll('.net-zone, .back-zone').forEach(zone => {
        setupActionButtons(zone);
    });
}

// Экспорт в глобальную область
window.setupFieldEvents = setupFieldEvents;
window.flipCourt = flipCourt;