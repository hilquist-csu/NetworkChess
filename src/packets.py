from typing import Any

def createServerboundQueueGame(username : str) -> dict[str, Any]:
    packet = createBasePacket("serverbound_queue_game")
    packet["username"] = username
    return packet

def createClientboundQueued() -> dict[str, Any]:
    return createBasePacket("clientbound_queued")

def createClientboundGameStart(board_state : str, color : str, opponentUsername : str) -> dict[str, Any]:
    packet = createBasePacket("clientbound_game_start")
    packet["board_state"] = board_state
    packet["color"] = color
    packet["opponent_username"] = opponentUsername
    return packet

def createServerboundTurn(move : str) -> dict[str, Any]:
    packet = createBasePacket("serverbound_turn")
    packet["move"] = move
    return packet

def createClientboundTurn(board_state : str, last_move: str) -> dict[str, Any]:
    packet = createBasePacket("clientbound_turn")
    packet["board_state"] = board_state
    packet["last_move"] = last_move
    return packet

def createServerboundOfferDraw() -> dict[str, Any]:
    return createBasePacket("serverbound_offer_draw")

def createClientboundOfferDraw() -> dict[str, Any]:
    return createBasePacket("clientbound_offer_draw")

def createServerboundRespondDraw(accept : bool) -> dict[str, Any]:
    packet = createBasePacket("serverbound_respond_draw")
    packet["accept"] = accept
    return packet

def createServerboundForfeit() -> dict[str, Any]:
    return createBasePacket("serverbound_forfeit")

def createClientboundInvalidMove(board_state : str) -> dict[str, Any]:
    packet = createBasePacket("clientbound_invalid_move")
    packet["board_state"] = board_state
    return packet

def createClientboundEndGame(colorOfWinner : str, winCondition: str, fen : str) -> dict[str, Any]:
    packet = createBasePacket("clientbound_game_end")
    packet["winner"] = colorOfWinner
    packet["win_condition"] = winCondition
    packet["board_state"] = fen
    return packet

def createBasePacket(packetType : str) -> dict[str, Any]:
    return {"packet_id": packetType}