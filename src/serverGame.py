import random
import time
import types

from typing import Any

import packets
import gameLogic

# queue structure: { address: <address>, username: <username>, packet: <packet> }
# packet is the queue acknowledgement packet, which is set to none once sent
# is a list, but length should not exceed one, two players -> start game
queue = []

# games: List of dictionaries of structure {
# white: {address: <white_address>, username: <white_username>, queue: []}},
# black: {address: <black_address>, username: <black_username>, queue: []}}
# fen: <fen_string>}
games = []

# Starting Game state
initialState = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
#initialState = "3r1rk1/1pp1bppp/p1n5/4p2Q/3PP1q1/2NBP2b/PPP5/R4RK1 w - - 2 31"

# castle test
#initialState = "rnbqkbnr/pppp1pp1/8/4p2p/2B1P3/7N/PPPP1PPP/RNBQK2R w KQkq - 6 7"

# mate test
#initialState = "rnbqkb1r/1ppp1pR1/5B2/4p2p/p1B1P3/3P3N/PPP2PPP/RN1Q1RK1 w kq - 1 15"

# Time in seconds that a user is assumed gone and can no longer reconnect to game
disconnectTime = 10

def processPacket(data : types.SimpleNamespace, packet : dict[str, Any]) -> None:
    packetType = packet["packet_id"]
    if packetType == "serverbound_queue_game":
        queuePlayer(data, packet["username"])
    elif packetType == "serverbound_turn":
        handlePlayerTurn(packet, data.address)
    elif packetType == "serverbound_offer_draw":
        userRequestDraw(data.address)
    elif packetType == "serverbound_respond_draw":
        userRespondDraw(data.address, packet)
    elif packetType == "serverbound_forfeit":
        userForfeit(data.address)

def checkForDisconnectForfeit():
    for game in games:
        timeDisconnect = game["white"]["time_disconnect_ms"]
        if timeDisconnect:
            now = int(time.time() * 1000)
            if now - timeDisconnect > disconnectTime * 1000:
                game["black"]["packet_queue"].append(packets.createClientboundEndGame("b", "Opponent disconnected", game["fen"]))
                game["white"]["time_disconnect_ms"] = None
        else:
            timeDisconnect = game["black"]["time_disconnect_ms"]
            if timeDisconnect:
                now = int(time.time() * 1000)
                if now - timeDisconnect > disconnectTime * 1000:
                    game["white"]["packet_queue"].append(packets.createClientboundEndGame("w", "Opponent disconnected", game["fen"]))
                    game["black"]["time_disconnect_ms"] = None

def getGameForUser(address : str) -> dict[str, Any] | None:
    for game in games:
        if game["white"]["address"] == address or game["black"]["address"] == address:
            return game
    return None

def queuePlayer(data : types.SimpleNamespace, username : str) -> None:
    # Try to reconnect user if previously disconnected
    for game in games:
        if game["white"]["username"] == username:
            if not game["white"]["address"]:
                game["white"]["address"] = data.address
                game["white"]["time_disconnect_ms"] = None
                game["white"]["packet_queue"].append(packets.createClientboundGameStart(game["fen"], "w", game["black"]["username"]))
                return
        elif game["black"]["username"] == username:
            if not game["black"]["address"]:
                game["black"]["address"] = data.address
                game["black"]["time_disconnect_ms"] = None
                game["black"]["packet_queue"].append(packets.createClientboundGameStart(game["fen"], "b", game["white"]["username"]))
                return

    if len(queue) > 0:
        newGameDictionary = {}
        otherQueued = queue.pop(0)
        newGameDictionary["fen"] = initialState
        randomInt = random.randint(0, 1)

        # randomly assign white/black player
        player1 = otherQueued
        player1["packet_queue"].append(packets.createClientboundGameStart(initialState, "w" if randomInt == 0 else "b", username))
        player2 = {"address": data.address, "username": username, "packet_queue": [packets.createClientboundGameStart(initialState, "b" if randomInt == 0 else "w", otherQueued["username"])], "time_disconnect_ms": None}
        newGameDictionary["white"] = player1 if randomInt == 0 else player2
        newGameDictionary["black"] = player2 if randomInt == 0 else player1

        games.append(newGameDictionary)
        print(f"Starting game: {newGameDictionary}")
    else:
        queue.append({"address": data.address, "username": username, "packet_queue": [packets.createClientboundQueued()], "time_disconnect_ms": None})

def getQueuedPacket(address : str) -> dict[str, Any] | None:
    for queued in queue:
        if queued["address"] == address:
            packetQueue = queued["packet_queue"]
            if len(packetQueue) > 0:
                packet = packetQueue.pop(0)
                if packet:
                    queued["packet_queue"] = []
                    return packet
                else:
                    return None

    game = getGameForUser(address)
    packet = None
    if game:
        clientColor = "white" if game["white"]["address"] == address else "black"
        queuedPackets = game[clientColor]["packet_queue"]
        if len(queuedPackets) > 0:
            packet = queuedPackets.pop(0)
        else:
            return None

    # Check if game can be removed
    if packet is None: return None
    if packet["packet_id"] == "clientbound_game_end":
        if len(game["white"]["packet_queue"]) > 0 or len(game["black"]["packet_queue"]) > 0:
            return packet
        if game["white"]["time_disconnect_ms"] is not None or game["black"]["time_disconnect_ms"] is not None:
            return packet
        games.remove(game)
    return packet

def handlePlayerTurn(packet : dict[str, Any], address : str) -> None:
    game = getGameForUser(address)
    if not game:
        print(f"Error: could not find game for user {address}")
        return

    fen = game["fen"]
    senderColor = "white" if game["white"]["address"] == address else "black"
    opponentColor = "black" if game["white"]["address"] == address else "white"
    move = packet["move"]

    if gameLogic.moveIsValid(fen, move.lower()):
        newFen = gameLogic.doMoveString(fen, move.lower())
        fenParts = newFen.split(" ")
        halfMove = int(fenParts[4])
        game["fen"] = newFen
        endPacket = None

        # Check for win conditions, if none, send client update packet
        if len(gameLogic.getValidMoves(newFen)) == 0:
            if gameLogic.isCheck(newFen):
                winner = "w" if senderColor == "white" else "b"
                endPacket = packets.createClientboundEndGame(winner, "Checkmate", newFen)
            else:
                endPacket = packets.createClientboundEndGame("-", "Stalemate", newFen)

        elif halfMove > 100:
            endPacket = packets.createClientboundEndGame("-", "50 move rule", newFen)

        elif gameLogic.insufficientMaterial(newFen):
            endPacket = packets.createClientboundEndGame("-", "Insufficient Material", newFen)

        if endPacket:
            game[senderColor]["packet_queue"].append(endPacket)
            game[opponentColor]["packet_queue"].append(endPacket)
            return

        updatePacket = packets.createClientboundTurn(newFen, move.lower())
        game[senderColor]["packet_queue"].append(updatePacket)
        game[opponentColor]["packet_queue"].append(updatePacket)

    else:
        game[senderColor]["packet_queue"].append(packets.createClientboundInvalidMove(fen))

def userForfeit(address : str) -> None:
    game = getGameForUser(address)
    forfeitingUser = "w" if game["white"]["address"] == address else "b"
    endPacket = packets.createClientboundEndGame(forfeitingUser, "Forfeit", game["fen"])
    game["white"]["packet_queue"].append(endPacket)
    game["black"]["packet_queue"].append(endPacket)

def userRequestDraw(address : str) -> None:
    game = getGameForUser(address)
    requestee = "white" if game["black"]["address"] == address else "black"
    game[requestee]["packet_queue"].append(packets.createClientboundOfferDraw())

def userRespondDraw(address : str, packet : dict[str, Any]) -> None:
    game = getGameForUser(address)
    if packet["accept"]:
        endPacket = packets.createClientboundEndGame("-", "Draw", game["fen"])
        game["white"]["packet_queue"].append(endPacket)
        game["white"]["packet_queue"].append(endPacket)

def clientDisconnected(address : str) -> None:
    game = getGameForUser(address)
    if not game:
        return
    disconnectedUser = "white" if game["white"]["address"] == address else "black"
    print(f"User disconnected: {disconnectedUser}")
    game[disconnectedUser]["address"] = None
    game[disconnectedUser]["time_disconnect_ms"] = int(time.time() * 1000)
