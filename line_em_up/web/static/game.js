function update_board(board) {
    for(let i = 0; i < board.length; i++) {
        for(let j = 0; j < board[i].length; j++) {
            let id = `game_board_${i}_${j}`;
            let td = document.getElementById(id);

            td.innerHTML = board[i][j];
        }
    }
}

function set_message(text) {
    let message = document.getElementById("message");
    message.innerText = text;
}

function handle_error({ error }) {
    if(error === "No game with game_id.") {
        window.location.replace("/");
    } else if(error === "Could not join game.") {
        PLAYER_NAME = null;
    }

    set_message(error);
}

function join(player_name, game_id) {
    socket.emit("join", { player_name, player_type: "human", game_id });
}

function play(move) {
    socket.emit("play", { move });
}

function addTileClick(handler) {
    document.querySelectorAll("[id^=game_board_]").forEach(node => {
        node.onclick = handler;
        node.classList.add("cursor-pointer");
    });
}

function removeTileClick() {
    document.querySelectorAll("[id^=game_board_]").forEach(node => {
        node.onclick = null;
        node.classList.remove("cursor-pointer");
    });
}