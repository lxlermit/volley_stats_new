import { appState, matchState } from './core/state.js';
import { LONG_PRESS_DURATION } from './core/constants.js';


import { initSubstitutions } from './features/substitutions.js';
import { initTeamManagement } from './features/team_management.js';
import { initPlayerTags, clearAllPlayers } from './features/players.js';
import { initZoneFields, flipCourt, setupActionButtonsForAllZones, setupFieldEvents } from './features/court.js';
import { initModal, initSettingsModal } from './ui/modals.js';
import { initScoreControls } from './features/score.js';
import { updateServeUI, updateZone1Actions } from './ui/serve-ui.js';


// Для ----- Модальное окно замены игроков в зонах на площадке
import { initPlayers } from './features/players.js';
import { modalManager } from './features/modals.js';

// Экспортируем функции в глобальную область
window.setupFieldEvents = setupFieldEvents;
window.flipCourt = flipCourt;
window.clearAllPlayers = clearAllPlayers;

document.addEventListener('DOMContentLoaded', function() {
    initSubstitutions();
    initTeamManagement();
    initPlayerTags();
    initZoneFields();
    initModal();
    initScoreControls();
    updateServeUI();
    updateZone1Actions();
    initSettingsModal();
    setupActionButtonsForAllZones();

    window.modalManager = modalManager; // Делаем доступным глобально ----- Модальное окно замены игроков в зонах на площадке
});