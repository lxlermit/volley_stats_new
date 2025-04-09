import { appState, matchState, initState, getState } from './core/state.js';
import { LONG_PRESS_DURATION } from './core/constants.js';

import { initSubstitutions } from './features/substitutions.js';
import { initTeamManagement } from './features/team_management.js';
import { initPlayerTags, clearAllPlayers } from './features/players.js';
import { initZoneFields, flipCourt, setupActionButtonsForAllZones, setupFieldEvents } from './features/court.js';
import { initModal, initSettingsModal } from './ui/modals.js';
import { initScoreControls } from './features/score.js';
import { updateServeUI, updateZone1Actions } from './ui/serve-ui.js';
import { modalManager } from './features/modals.js';

export function initApp(data) {
    initState(data);

    // Инициализируем модальное окно настроек с явной передачей зависимостей
    initSettingsModal({
        clearAllPlayers: clearAllPlayers,
        flipCourt: flipCourt,
        updateServeUI: updateServeUI,
        updateZone1Actions: updateZone1Actions
    });

    // Остальная инициализация
    initSubstitutions();
    initTeamManagement();
    initPlayerTags();
    initZoneFields();
    initModal();
    initScoreControls();
    updateServeUI();
    updateZone1Actions();
    setupActionButtonsForAllZones();

    // Глобальные переменные для обратной совместимости
    window.setupFieldEvents = setupFieldEvents;
    window.flipCourt = flipCourt;
    window.modalManager = modalManager;
    if (typeof clearAllPlayers !== 'function') {
        console.error('clearAllPlayers is not defined!(main.js-40)');
    }
    window.clearAllPlayers = clearAllPlayers; // Добавляем для совместимости
}

document.addEventListener('DOMContentLoaded', function() {
    const state = getState();
    if (state.appState.playersData || state.matchState.teamData) {
        initApp({
            playersData: state.appState.playersData,
            teamData: state.matchState.teamData
        });
    }

    if (window.playersData) {
        initApp({
            playersData: window.playersData,
            teamData: window.teamData || {}
        });
    }
});