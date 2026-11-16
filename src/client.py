import json
import selectors
import socket
import struct
import sys

import networkUtils
import clientGame

selector = selectors.DefaultSelector()

hostname = None
port = None

def createSocket() -> bool:
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        ip = socket.gethostbyname(hostname)
        clientSocket.connect((ip, port))
        print(f"Connected to server {ip}:{port}")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        selector.register(clientSocket, events)
        return True
    except socket.gaierror as e:
        print(f"Unable to resolve DNS hostname: {hostname}\n{e}")
        return False
    except OSError:
        clientSocket.close()
        return False

def loop() -> None:
    try:
        while True:
            events = selector.select(timeout=1)
            if events:
                for key, mask in events:
                    serviceConnection(key, mask)
            if not selector.get_map():
                break
    except KeyboardInterrupt:
        print("caught keyboard interrupt, exiting")
    finally:
        selector.close()

def serviceConnection(key : selectors.SelectorKey, mask : int) -> None:
    clientSocket = key.fileobj
    clientGame.run()
    if mask & selectors.EVENT_READ:
        headerBytes = networkUtils.receiveBytes(clientSocket, 4)
        if headerBytes:
            payloadLength = struct.unpack("!I", headerBytes)[0]
            payloadBytes = networkUtils.receiveBytes(clientSocket, payloadLength)
            message = json.loads(payloadBytes.decode("utf-8"))
            #print(f"Received packet: {message}")
            clientGame.processPacket(message)
        else:
            print("closing client connection")
            selector.unregister(clientSocket)
            clientSocket.close()
    if mask & selectors.EVENT_WRITE:
        message = clientGame.nextOutboundPacket()
        if message:
            #print(f"Sending packet: {message}")
            networkUtils.send(clientSocket, message)

def main():
    global hostname, port
    argLength = len(sys.argv)
    for i in range(0, argLength):
        arg = sys.argv[i]
        if arg.startswith("-"):
            if arg == "-i":
                if i < argLength - 1:
                    hostname = sys.argv[i + 1]
            elif arg == "-p":
                if i < argLength - 1:
                    try:
                        port = int(sys.argv[i + 1])
                    except ValueError:
                        print("Port must be an integer.")
                        sys.exit(-1)
            elif arg == "-h":
                print(f"Usage: python3 server.py -i <hostname> -p <port>")
                return
        else:
            continue

    if hostname and port:
        if createSocket():
            loop()
        else: print("Erroring connecting to server")
    else:
        print(f"Usage: python3 server.py -i <hostname> -p <port>")

if __name__ == "__main__":
    main()