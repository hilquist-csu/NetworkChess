## Transport Layer & Packet Framing Mechanism
- Transport Protocol: TCP
- Serialization Format: JSON 

#### Packet Framing: Length-Prefixed Encoding
The length of the packet is sent as a header, and the rest of the bytes are sent after.
```py
payload_bytes = json.dumps(message_dict).encode("utf-8")
header = struct.pack("!I", len(payload_bytes)) 
sock.sendall(header + payload_bytes)
```

On the receiving end, length is read first, then the rest is read into json using the length.
```py
header_bytes = recv_exact(sock, 4)
if header_bytes:
    payload_len = struct.unpack("!I", header_bytes)[0]
    payload_bytes = recv_exact(sock, payload_len)
    message = json.loads(payload_bytes.decode("utf-8"))
```

## Application Message Types
Packet data is encoded in json and sent with a 4-byte fixed-length header containing the packet length
The packet will contain the packet type (packet_id) and any fields associated with the packet type.

```json
{
  "packet_id": "serverbound_queue_game",
  "username": "ben"
}
```

- board_state will be a FEN (Forsyth-Edwards Notation) string of the chess board. 
This contains board placement, turn, castling availability, 
en passant targets, half-move clock, and  full-move counter


| Packet Type              | Description                                                       | Json Fields              |
|--------------------------|-------------------------------------------------------------------|--------------------------|
| serverbound_queue_game   | Client requests to join a game                                    | username                 |
| clientbound_queued       | Server lets client know they are waiting for a game               | none                     |
| clientbound_game_start   | Server tells clients a game has started                           | opponent_username, color |
| serverbound_turn         | Client sends server it moves                                      | turn                     |
| clientbound_turn         | Server sends clients new state after move                         | last_move, board_state   |
| serverbound_offer_draw   | Client tells server it would like to offer a draw                 | none                     |
| clientbound_offer_draw   | Server tells client opponent request draw                         | none                     |
| serverbound_respond_draw | Clients tells server if or if not it accepts opponents draw offer | accept (boolean)         |
| serverbound_forfeit      | Client tells server it forfeits                                   | none                     |
| clientbound_invalid_move | Server tells client it rejects their move                         | board_state              |
| clientbound_game_end     | Server tells clients game is over                                 | winner, win_condition    |

*assume json fields are string unless specified otherwise*

## Connection termination handling
#### Application-Layer Disconnect
When the client wants to leave, it can send a serverbound_forfeit packet to end the game, close the socket, and all is handled cleanly.
#### Transport-Layer Teardown 
When BrokenPipeError occurs, a client socket has closed and server tried to send data through it. 
The server way weight a small amount of time (5-20 seconds) to see 
if the user tries to start a new connection (serverbound_queue_game). 
If this happens, the server can attach this connection to the game,
otherwise end the game by user forfeit.
#### Abrupt Termination
When ConnectionResetError occurs, treat this the same way as a Transport-Layer Teardown; Wait a little bit to see if client rejoins, 
otherwise terminate game.