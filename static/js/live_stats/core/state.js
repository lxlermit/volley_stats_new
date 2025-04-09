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