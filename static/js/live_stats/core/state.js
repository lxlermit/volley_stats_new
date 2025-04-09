export const appState = {
    playersOnField: {},
    isFlipped: false,
    isOurServe: true,
    zoneMapping: {
        1: 4, 2: 5, 3: 6, 4: 1, 5: 2, 6: 3
    }
};

export const matchState = {
    currentSet: 1,
    maxSets: 5,
    ourScore: 0,
    opponentScore: 0,
    sets: {}
};

// Добавляем функцию инициализации состояния
export function initState(data) {
    if (data) {
        // Инициализация данных игроков (если переданы)
        if (data.playersData) {
            appState.playersData = data.playersData;
        }

        // Инициализация данных команды (если переданы)
        if (data.teamData) {
            matchState.teamData = data.teamData;
        }
    }

    // Возвращаем текущее состояние для удобства
    return { appState, matchState };
}

// Добавляем функцию получения состояния
export function getState() {
    return { appState, matchState };
}