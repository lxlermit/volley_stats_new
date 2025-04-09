import { matchState } from '../core/state.js';

export function initScoreControls() {
    document.getElementById('our-point-btn')?.addEventListener('click', () => {
        matchState.ourScore++;
        updateScoreDisplay();
    });

    document.getElementById('opponent-point-btn')?.addEventListener('click', () => {
        matchState.opponentScore++;
        updateScoreDisplay();
    });
}

export function updateScoreDisplay() {
    document.querySelector('.our-score').textContent = matchState.ourScore;
    document.querySelector('.opponent-score').textContent = matchState.opponentScore;
}