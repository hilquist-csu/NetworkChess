def getValidMoves(fen : str) -> list[str]:
    fenParts = fen.split(" ")
    board = toBoard(fenParts[0])
    turn = fenParts[1]
    castlingRights = fenParts[2]
    enPassantTarget = fenParts[3]

    visibleSquares = []
    for i in range(0, 8):
        for j in range(0, 8):
            pieceVisibleSquares = visibleSquaresForPiece(i, j, board, turn, castlingRights, enPassantTarget)
            for visibleSquare in pieceVisibleSquares:
                visibleSquares.append(visibleSquare)

    legalMoves = []
    for move in visibleSquares:
        newFen = doMove(fen, move).split(" ")
        if colorInCheck(toBoard(newFen[0]), turn, newFen[2], newFen[3]):
            continue
        legalMoves.append(move)
    print(f"State: {fen} -> Legal Moves: {legalMoves}")
    return legalMoves

def moveIsValid(fen : str, move : str) -> bool:
    if len(move) < 4: return False
    fromRow = ord(move[1]) - ord('1')
    fromColumn = ord(move[0]) - ord('a')
    toRow = ord(move[3]) - ord('1')
    toColumn = ord(move[2]) - ord('a')
    return (fromRow, fromColumn, toRow, toColumn) in getValidMoves(fen)

def doMoveString(fen: str, move: str) -> str:
    fromRow = ord(move[1]) - ord('1')
    fromColumn = ord(move[0]) - ord('a')
    toRow = ord(move[3]) - ord('1')
    toColumn = ord(move[2]) - ord('a')
    return doMove(fen, (fromRow, fromColumn, toRow, toColumn), None)

def doMove(fen : str, move : tuple[int, int, int, int], promoteTo = None) -> str:
    fenParts = fen.split(" ")
    board = toBoard(fenParts[0])
    turn = fenParts[1]
    castlingRights = fenParts[2]
    enPassantTarget = fenParts[3]
    halfMove = int(fenParts[4])
    fullMove = int(fenParts[5])

    fromRow, fromColumn, toRow, toColumn = move
    sourceSquare = board[fromRow][fromColumn]
    targetSquare = board[toRow][toColumn]

    board[toRow][toColumn] = sourceSquare
    board[fromRow][fromColumn] = ' '

    castlingRights = updateCastlingRights(castlingRights, board, move)

    #todo: en passant

    fullMove += 1
    turn = "w" if turn == "b" else "b"
    if targetSquare != " ":
        halfMove = 0
    else:
        halfMove += 1

    castlingRights = '-' if castlingRights == '' else castlingRights

    return f"{fromBoard(board)} {turn} {castlingRights} {enPassantTarget} {halfMove} {fullMove}"

def updateCastlingRights(castlingRights : str, board : list[list[str]], move : tuple[int, int, int, int]) -> str:
    fromRow, fromColumn, toRow, toColumn = move
    if fromRow == 0 and fromColumn == 4 and toRow == 0 and (toColumn == 6 or toColumn == 2):
        if toColumn == 6:
            board[0][5] = board[0][7]
            board[0][7] = " "
        if toColumn == 2:
            board[0][3] = board[0][0]
            board[0][0] = " "
        castlingRights = castlingRights.replace("K", "").replace("Q", "")

    if fromRow == 7 and fromColumn == 4 and toRow == 7 and (toColumn == 6 or toColumn == 2):
        if toColumn == 6:
            board[7][5] = board[7][7]
            board[7][7] = " "
        elif toColumn == 2:
            board[7][3] = board[7][0]
            board[7][0] = " "
        castlingRights = castlingRights.replace("k", "").replace("q", "")

    if fromRow == 0 and fromColumn == 4:
        castlingRights = castlingRights.replace("K", "").replace("Q", "")
    if fromRow == 7 and fromColumn == 4:
        castlingRights = castlingRights.replace("k", "").replace("q", "")
    if fromRow == 0 and fromColumn == 0:
        castlingRights = castlingRights.replace("Q", "")
    if fromRow == 0 and fromColumn == 7:
        castlingRights = castlingRights.replace("K", "")
    if fromRow == 7 and fromColumn == 0:
        castlingRights = castlingRights.replace("q", "")
    if fromRow == 7 and fromColumn == 7:
        castlingRights = castlingRights.replace("k", "")

    return castlingRights

def isCheck(fen : str) -> bool:
    fenParts = fen.split(" ")
    board = toBoard(fenParts[0])
    turn = fenParts[1]
    castlingRights = fenParts[2]
    enPassantTarget = fenParts[3]
    return colorInCheck(board, turn, castlingRights, enPassantTarget)

def colorInCheck(board : list[list[str]], color : str, castlingRights : str, enPassantTarget : str) -> bool:
    visibleSquares = []
    visibleForColor = "w" if color == "b" else "b"
    for i in range(0, 8):
        for j in range(0, 8):
            pieceVisibleSquares = visibleSquaresForPiece(i, j, board, visibleForColor, castlingRights, enPassantTarget)
            for visibleSquare in pieceVisibleSquares:
                visibleSquares.append(visibleSquare)
    king = "k" if color == "b" else "K"
    for fromRow, fromColumn, toRow, toColumn in visibleSquares:
        if board[toRow][toColumn] == king:
            return True
    return False

def insufficientMaterial(fen : str) -> bool:
    fenParts = fen.split(" ")
    board = toBoard(fenParts[0])
    whiteOnlyHasKing = True
    blackOnlyHasKing = True
    for i in range(0, 8):
        for j in range(0, 8):
            piece = board[i][j]
            if piece == " ":
                continue
            elif piece.lower() == piece and piece != 'k':
                blackOnlyHasKing = False
            elif piece.upper() == piece and piece != 'K':
                whiteOnlyHasKing = False
    return whiteOnlyHasKing and blackOnlyHasKing

def visibleSquaresForPiece(row : int, column : int, board : list[list[str]], turnsColor : str, castlingRights : str, enPassantTarget : str) -> list[tuple[int, int, int, int]]:
    piece = board[row][column]
    if piece == " ":
        return []
    color = 'w' if piece.lower() != piece else 'b'
    if color != turnsColor:
        return []
    squares = []
    if piece.lower() == "p":
        squares =  pawnVisibleSquares(row, column, color, board, enPassantTarget)
    elif piece.lower() == "k":
        squares =  kingVisibleSquares(row, column, color, board, castlingRights)
    elif piece.lower() == "q":
        squares = queenVisibleSquares(row, column, color, board)
    elif piece.lower() == "r":
        squares = rookVisibleSquares(row, column, color, board)
    elif piece.lower() == "n":
        squares = knightVisibleSquares(row, column, color, board)
    elif piece.lower() == "b":
        squares = bishopVisibleSquares(row, column, color, board)
    moves = []
    for square in squares:
        toRow, toColumn = square
        moves.append((row, column, toRow, toColumn))
    return moves

def pawnVisibleSquares(row : int, column : int, pieceColor : str, board : list[list[str]], enPassantTarget : str) -> list[tuple[int, int]]:
    visibleSquares = []
    direction = 1 if pieceColor == "w" else -1
    targetRow = row + direction
    startRow = 1 if pieceColor == "w" else 6
    genericMoveDirection(row, column, direction, 0, pieceColor, board, visibleSquares, 2 if row == startRow else 1, pawn=True)
    leftColumn = column - 1
    rightColumn = column + 1

    for i in [leftColumn, rightColumn]:
        if inRange(targetRow, i):
            pieceAtTarget = board[targetRow][i]
            if pieceAtTarget != " ":
                if getPieceColor(pieceAtTarget) != pieceColor:
                    visibleSquares.append((targetRow, i))

    # todo: en passant

    return visibleSquares

def bishopVisibleSquares(row : int, column : int, pieceColor : str, board : list[list[str]]) -> list[tuple[int, int]]:
    visibleSquares = []
    genericMoveDirection(row, column, 1, 1, pieceColor, board, visibleSquares, 8)
    genericMoveDirection(row, column, 1, -1, pieceColor, board, visibleSquares, 8)
    genericMoveDirection(row, column, -1, 1, pieceColor, board, visibleSquares, 8)
    genericMoveDirection(row, column, -1, -1, pieceColor, board, visibleSquares, 8)
    return visibleSquares

def kingVisibleSquares(row : int, column : int, pieceColor : str, board : list[list[str]], castlingRights : str) -> list[tuple[int, int]]:
    visibleSquares = []
    genericMoveDirection(row, column, 1, 0, pieceColor, board, visibleSquares, 1)
    genericMoveDirection(row, column, -1, 0, pieceColor, board, visibleSquares, 1)
    genericMoveDirection(row, column, 0, 1, pieceColor, board, visibleSquares, 1)
    genericMoveDirection(row, column, 0, -1, pieceColor, board, visibleSquares, 1)
    genericMoveDirection(row, column, 1, 1, pieceColor, board, visibleSquares, 1)
    genericMoveDirection(row, column, -1, 1, pieceColor, board, visibleSquares, 1)
    genericMoveDirection(row, column, 1, -1, pieceColor, board, visibleSquares, 1)
    genericMoveDirection(row, column, -1, -1, pieceColor, board, visibleSquares, 1)
    if pieceColor == 'w':
        if board[0][5] == " " and board[0][6] == " " and 'K' in castlingRights:
            visibleSquares.append((0, 6))
        if board[0][1] == " " and board[0][2] == " " and board[0][3] == " " and 'Q' in castlingRights:
            visibleSquares.append((0, 2))
    if pieceColor == 'b':
        if board[7][5] == " " and board[7][6] == " " and 'k' in castlingRights:
            visibleSquares.append((7, 6))
        if board[7][1] == " " and board[7][2] == " " and board[0][3] == " " and 'q' in castlingRights:
            visibleSquares.append((7, 2))
    return visibleSquares

def queenVisibleSquares(row : int, column : int, pieceColor : str, board : list[list[str]]) -> list[tuple[int, int]]:
    visibleSquares = []
    genericMoveDirection(row, column, 1, 0, pieceColor, board, visibleSquares, 8)
    genericMoveDirection(row, column, -1, 0, pieceColor, board, visibleSquares, 8)
    genericMoveDirection(row, column, 0, 1, pieceColor, board, visibleSquares, 8)
    genericMoveDirection(row, column, 0, -1, pieceColor, board, visibleSquares, 8)
    genericMoveDirection(row, column, 1, 1, pieceColor, board, visibleSquares, 8)
    genericMoveDirection(row, column, -1, 1, pieceColor, board, visibleSquares, 8)
    genericMoveDirection(row, column, 1, -1, pieceColor, board, visibleSquares, 8)
    genericMoveDirection(row, column, -1, -1, pieceColor, board, visibleSquares, 8)
    return visibleSquares

def knightVisibleSquares(row : int, column : int, pieceColor : str, board : list[list[str]]) -> list[tuple[int, int]]:
    visibleSquares = []
    genericMoveDirection(row, column, 1, 2, pieceColor, board, visibleSquares, 1)
    genericMoveDirection(row, column, 1, -2, pieceColor, board, visibleSquares, 1)
    genericMoveDirection(row, column, -1, 2, pieceColor, board, visibleSquares, 1)
    genericMoveDirection(row, column, -1, -2, pieceColor, board, visibleSquares, 1)
    genericMoveDirection(row, column, 2, 1, pieceColor, board, visibleSquares, 1)
    genericMoveDirection(row, column, 2, -1, pieceColor, board, visibleSquares, 1)
    genericMoveDirection(row, column, -2, 1, pieceColor, board, visibleSquares, 1)
    genericMoveDirection(row, column, -2, -1, pieceColor, board, visibleSquares, 1)
    return visibleSquares

def rookVisibleSquares(row : int, column : int, pieceColor : str, board : list[list[str]]) -> list[tuple[int, int]]:
    visibleSquares = []
    genericMoveDirection(row, column, 1, 0, pieceColor, board, visibleSquares, 8)
    genericMoveDirection(row, column, 0, 1, pieceColor, board, visibleSquares, 8)
    genericMoveDirection(row, column, -1, 0, pieceColor, board, visibleSquares, 8)
    genericMoveDirection(row, column, 0, -1, pieceColor, board, visibleSquares, 8)
    return visibleSquares

def genericMoveDirection(row : int, column : int, rowIncrement : int, columnIncrement : int, color : str, board : list[list[str]], visibleSquares : list[tuple[int, int]], maxIterations : int = 64, pawn=False) -> None:
    nextRow = row + rowIncrement
    nextColumn = column + columnIncrement
    count = 0
    while inRange(nextRow, nextColumn) and count < maxIterations:
        targetSquare = board[nextRow][nextColumn]
        if targetSquare == " ":
            visibleSquares.append((nextRow, nextColumn))
        elif getPieceColor(targetSquare) != color and not pawn:
            visibleSquares.append((nextRow, nextColumn))
            return None
        else:
            return None
        nextRow += rowIncrement
        nextColumn += columnIncrement
        count += 1
    return None

def inRange(row : int, column : int) -> bool:
    return 0 <= row <= 7 and 0 <= column <= 7

def getPieceColor(piece : str) -> str:
    return 'w' if piece.lower() != piece else 'b'

def toBoard(boardString: str) -> list[list[str]]:
    board = []
    for rowString in boardString.split("/"):
        row = []
        for i in range(0, len(rowString)):
            if rowString[i].isdigit():
                for j in range(0, int(rowString[i])):
                    row.append(' ')
            else:
                row.append(rowString[i])
        board.append(row)
    board.reverse()
    return board

def fromBoard(board : list[list[str]]) -> str:
    fenBoard = ""
    rows = []
    for i in range(0, 8):
        gap = 0
        row = ""
        for column in range(0, 8):
            piece = board[i][column]
            if piece == " ":
                gap += 1
            else:
                if gap > 0:
                    row = row + str(gap)
                    gap = 0
                row = row + piece
        if gap > 0:
            row = row + str(gap)
        i -= 1
        rows.append(row)
    rows.reverse()
    for i in range(0, 8):
        fenBoard += rows[i]
        if i != 7: fenBoard += "/"
    return fenBoard