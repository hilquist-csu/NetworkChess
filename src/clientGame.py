from typing import Any

import packets

"""
Display information
"""
boardTemplate =  "Color: ?1  Opponent: ?2\n"
boardTemplate += "   ___ ___ ___ ___ ___ ___ ___ ___\n"
boardTemplate += "x7 | - | - | - | - | - | - | - | - | Move Format: \n"
boardTemplate += "  |___|___|___|___|___|___|___|___| From column + From Row + To column + To Row\n"
boardTemplate += "x6 | - | - | - | - | - | - | - | - | Example: e2e4\n"
boardTemplate += "  |___|___|___|___|___|___|___|___| Special cases:\n"
boardTemplate += "x5 | - | - | - | - | - | - | - | - | Pawn promotion:\n"
boardTemplate += "  |___|___|___|___|___|___|___|___| Append piece char (q for queen, n for )\n"
boardTemplate += "x4 | - | - | - | - | - | - | - | - | knight, b for bishop, r for rook)\n"
boardTemplate += "  |___|___|___|___|___|___|___|___| Example: h7h8q (white promote)\n"
boardTemplate += "x3 | - | - | - | - | - | - | - | - | Castling Moves: \n"
boardTemplate += "  |___|___|___|___|___|___|___|___| White: e1g1 king side; e1c1 queen side\n"
boardTemplate += "x2 | - | - | - | - | - | - | - | - | Black: e8g8 king side; e8c8 queen side\n"
boardTemplate += "  |___|___|___|___|___|___|___|___|\n"
boardTemplate += "x1 | - | - | - | - | - | - | - | - |\n"
boardTemplate += "  |___|___|___|___|___|___|___|___|\n"
boardTemplate += "x0 | - | - | - | - | - | - | - | - |\n"
boardTemplate += "  |___|___|___|___|___|___|___|___|\n"
boardTemplate += "    y0   y1   y2   y3   y4   y5   y6   y7 \n"

whitePieces = ['♔', '♕', '♖', '♗', '♘', '♙']
blackPieces = ['♚', '♛', '♜', '♝', '♞', '♟']
king = 0
queen = 1
rook = 2
bishop = 3
knight = 4
pawn = 5

"""
 Game state variables
"""
gameStarted = False
queueing = False
queued = False
drawOffer = False
fen = ""
stateDirty = False
lastMoveInvalid = False
inboundPacketQueue = []
outboundPacketQueue = []
opponentUsername = ""
color = ""

def run() -> None:
    if not gameStarted:
        if not queueing:
            promptForGame()
    else:
        processEvents()

def promptForGame() -> None:
    global queueing
    username = input("Enter username: ")
    createGame = packets.createServerboundQueueGame(username)
    outboundPacketQueue.append(createGame)
    queueing = True

def processEvents() -> None:
    for packet in inboundPacketQueue:
        processPacket(packet)
    if fen and stateDirty:
        display()

def processPacket(packet : dict) -> None:
    global queued, gameStarted, opponentUsername, color, fen, stateDirty, lastMoveInvalid, drawOffer
    packetType = packet["packet_id"]
    if packetType == "clientbound_queued":
        queued = True
        print("Waiting for game...")
    elif packetType == "clientbound_game_start":
        queued = True
        gameStarted = True
        fen = packet["board_state"]
        stateDirty = True
        color = packet["color"]
        opponentUsername = packet["opponent_username"]
    elif packetType == "clientbound_turn":
        fen = packet["board_state"]
        stateDirty = True
    elif packetType == "clientbound_offer_draw":
        drawOffer = True
    elif packetType == "clientbound_invalid_move":
        fen = packet["board_state"]
        stateDirty = True
        lastMoveInvalid = True
    elif packetType == "clientbound_game_end":
        fen = packet["board_state"]
        gameResults(packet)
        clearGame()

def clearGame() -> None:
    global queued, queueing, gameStarted, opponentUsername, color, fen, inboundPacketQueue, outboundPacketQueue, stateDirty, lastMoveInvalid
    gameStarted = False
    queueing = False
    queued = False
    fen = ""
    stateDirty = False
    lastMoveInvalid = False
    outboundPacketQueue = []
    inboundPacketQueue = []
    opponentUsername = ""
    color = ""

def createBoardString(pieces : list[str]) -> str:
    board = boardTemplate
    colorString = "White" if color == "w" else "Black"
    board = board.replace("?1", colorString)
    board = board.replace("?2", opponentUsername)
    index = 0

    while '-' in board:
        board = board.replace('-', pieces[index], 1)
        index += 1

    for i in range(0, 8):
        adjustedIndex = invertValue(i, 7) if color == 'b' else i
        board = board.replace("x" + str(i), chr(ord('1') + adjustedIndex), 1)
        board = board.replace("y" + str(i), chr(ord('A') + adjustedIndex), 1)

    return board


def display() -> None:
    global stateDirty, lastMoveInvalid, drawOffer

    fenParts = fen.split(" ")
    pieces = parseFenBoard(fenParts[0].split("/"))
    board = createBoardString(pieces)
    print(board)

    if drawOffer:
        print("Opponent has offered a draw, enter yes or no for move if you would like to respond.")

    if fenParts[1] == color:
        if lastMoveInvalid:
            move = input("Invalid move, try another: ")
            lastMoveInvalid = False
        else:
            move = input("Enter move: ")

        if move == "draw":
            outboundPacketQueue.append(packets.createServerboundOfferDraw())
            display()
        elif move == "forfeit":
            outboundPacketQueue.append(packets.createServerboundForfeit())
        elif move == "yes" and drawOffer:
            outboundPacketQueue.append(packets.createServerboundRespondDraw(True))
            drawOffer = False
            display()
        elif move == "no" and drawOffer:
            outboundPacketQueue.append(packets.createServerboundRespondDraw(False))
            drawOffer = False
            display()
        else:
            outboundPacketQueue.append(packets.createServerboundTurn(move))

    else:
        print("Waiting for opponent...")

    stateDirty = False

def gameResults(packet : dict[Any, str]) -> None:
    fenParts = fen.split(" ")
    pieces = parseFenBoard(fenParts[0].split("/"))
    board = createBoardString(pieces)
    print(board)
    if color == packet["winner"]:
        print(f"You win by {packet["win_condition"]}!")
    else:
        print(f"You lose by {packet["win_condition"]}!")

def parseFenBoard(fenBoardRows : list[str]) -> list[str]:
    pieces = []
    for row in fenBoardRows:
        for i in range(0, len(row)):
            if row[i].isdigit():
                num = int(row[i])
                for j in range(0, num):
                    pieces.append(' ')
            else:
                pieces.append(getPiece(row[i]))
    if color == 'b':
        mirroredPieces = []
        for i in range(0, len(pieces)):
            row = i // 8
            column = i % 8
            source = (8 * invertValue(row, 7)) + invertValue(column, 7)
            mirroredPieces.append(pieces[source])
        return mirroredPieces
    else:
        return pieces

def nextOutboundPacket() -> dict[str, Any] | None:
    if len(outboundPacketQueue) == 0: return None
    return outboundPacketQueue.pop(0)

def inboundPacket(packet : dict) -> None:
    inboundPacketQueue.append(packet)

def invertValue(value : int, maxValue : int) -> int:
    return abs(value - maxValue)

def getPiece(piece : str) -> str:
    invertColors = True # On a black and white terminal, the black ascii characters look white and white pieces looks black
    isLowerCase = piece.lower() == piece
    lowerCase = piece.lower()
    displayColor = "b" if isLowerCase else "w"
    if invertColors:
        displayColor = "w" if displayColor == "b" else "b"
    if lowerCase == 'k':
        return whitePieces[king] if displayColor == "w" else blackPieces[king]
    elif lowerCase == 'q':
        return whitePieces[queen] if displayColor == "w" else blackPieces[queen]
    elif lowerCase == 'r':
        return whitePieces[rook] if displayColor == "w" else blackPieces[rook]
    elif lowerCase == 'b':
        return whitePieces[bishop] if displayColor == "w" else blackPieces[bishop]
    elif lowerCase == 'n':
        return whitePieces[knight] if displayColor == "w" else blackPieces[knight]
    elif lowerCase == 'p':
        return whitePieces[pawn] if displayColor == "w" else blackPieces[pawn]
    else: return "?"
