## Concurrency Design
#### Server Concurrency Model: Selectors
For this project, I will use Non-blocking I/O multiplexing with selectors.
Instead of having multiple threads, 
the sockets are set to non-blocking and a single event loop checks the read/write availability of the sockets.


### Server listening socket
This is how a server socket will be setup and registered with the selector:
```py
# Create a server socket and listen for connections
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind(('0.0.0.0', <some port>))
lsock.listen()

lsock.setblocking(False) # prevent IO calls from blocking the current thread

# Register socket with select
sel = selectors.DefaultSelector()
sel.register(lsock, selectors.EVENT_READ, data=None)

```

### Server main event loop
Once the selector is registered and the server starts listening for connections, the main event loop should start.
The main event loop loops through all the sockets registered in the selector, and performs any necessary functions.
```py
try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                pass
                """
                This block is reached when the server
                gets a new client connection request.
                 
                Upon receiving a connection request, the server
                should accept the connection, set the socket to
                non-blocking, set data to some initial value,
                and register the socket with the selector.
                """    
            else:
                pass
                """
                This block is reached when the socket selected
                is already registered with the server and 
                is ready to read or write.
                 
                This should call some method to read or write
                to the socket as needed.
                """   
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()
```


### Score & Leaderboard Synchronization Design
The chess board state will be stored in a Forsyth-Edwards Notation (FEN) string.
The FEN string contains the entire state of the board, including board placement, turn, castling availability, en passant targets, half-move clock, and full-move counter.
When a client makes a move, the board is updated, the new FEN string is created, and sent to the client in a "clientbound_turn" packet.