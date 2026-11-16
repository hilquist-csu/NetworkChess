import json
import socket
import struct

from typing import Any

def receiveBytes(socketInstance : socket.socket, numberOfBytes : int) -> bytes | None:
    buffer = bytearray()
    while len(buffer) < numberOfBytes:
        chunk = socketInstance.recv(numberOfBytes - len(buffer))
        if not chunk:
            return None
        buffer.extend(chunk)
    return bytes(buffer)

def send(socketInstance : socket.socket, messageDictionary : dict[str, Any]) -> None:
    payloadBytes = json.dumps(messageDictionary).encode("utf-8")
    header = struct.pack("!I", len(payloadBytes))
    socketInstance.sendall(header + payloadBytes)
