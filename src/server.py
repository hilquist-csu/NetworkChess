import socket
import selectors
import sys
import types
import struct
import json

import networkUtils
import serverGame

selector = selectors.DefaultSelector()

port = None

def createServerSocket() -> None:
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        ip = socket.gethostbyname("0.0.0.0")
        serverSocket.bind((ip, port))
        serverSocket.listen()
        serverSocket.setblocking(False)
        selector.register(serverSocket, selectors.EVENT_READ, data=None)
    except socket.gaierror as e:
        print(f"Unable to resolve DNS hostname: {hostname}\n{e}")
        sys.exit(-1)

def acceptConnection(clientSocket : socket.socket) -> None:
    connection, address = clientSocket.accept()
    print("Accepted connection from: ", address)
    connection.setblocking(False)
    data = types.SimpleNamespace(address=address)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    selector.register(connection, events, data=data)

def serviceConnection(key : selectors.SelectorKey, mask : int) -> None:
    clientSocket = key.fileobj
    data = key.data

    serverGame.checkForDisconnectForfeit()

    if mask & selectors.EVENT_READ:
        message = read(clientSocket, data)
        if not message:
            return
        print(f"Received packet: {message}")
        serverGame.processPacket(data, message)

    if mask & selectors.EVENT_WRITE:
        outboundMessage = serverGame.getQueuedPacket(data.address)
        if outboundMessage:
            print(f"Sending packet: {outboundMessage}")
            networkUtils.send(clientSocket, outboundMessage)

def read(clientSocket : socket.socket, data : types.SimpleNamespace) -> dict | None:
    try:
        headerBytes = networkUtils.receiveBytes(clientSocket, 4)
    except OSError:
        return None
    if headerBytes:
        payloadLength = struct.unpack("!I", headerBytes)[0]
        try:
            payloadBytes = networkUtils.receiveBytes(clientSocket, payloadLength)
        except OSError:
            return None
        message = json.loads(payloadBytes.decode("utf-8"))
        return message
    else:
        print("Closing connection to ", data.address)
        selector.unregister(clientSocket)
        clientSocket.close()
        serverGame.clientDisconnected(data.address)
        return None

def loop() -> None:
    try:
        while True:
            events = selector.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    acceptConnection(key.fileobj)
                else:
                    serviceConnection(key, mask)
    except KeyboardInterrupt:
        print("Stoping server")
    finally:
        selector.close()

def main():
    global port
    argLength = len(sys.argv)
    for i in range(0, argLength):
        arg = sys.argv[i]
        if arg.startswith("-"):
            if arg == "-p":
                if i < argLength - 1:
                    try:
                        port = int(sys.argv[i + 1])
                    except ValueError:
                        print("Port must be an integer.")
                        sys.exit(-1)
            elif arg == "-h":
                print(f"Usage: python3 server.py -p <port>")
                return
        else:
            continue

    if port:
        print("Starting server")
        createServerSocket()
        print(f"Started server on port {port}")
        loop()
    else:
        print(f"Usage: python3 server.py -p <port>")

if __name__ == "__main__":
    main()

