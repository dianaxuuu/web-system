"""Utils package.

This package is for code shared by the Manager and the Worker.
"""

import socket
import json


def get_message(sock: socket.socket):
    """Get message from the TCP socket."""
    # Wait for a connection for 1s.  The socket library avoids
    # consuming CPU while waiting for a connection.
    connection_socket, _ = sock.accept()
    # Socket recv() will block for a maximum of 1 second.
    connection_socket.settimeout(1)
    # Receive data, one chunk at a time.
    # If recv() times out before we can read a chunk,
    # then go back to the top of the loop and
    # try again.  When the client closes the connection, recv()
    # returns empty data, which breaks out of the loop.  We make a
    # simplifying assumption that the client will always cleanly
    # close the connection.
    with connection_socket:
        message_chunks = []
        while True:
            data = connection_socket.recv(4096)
            if not data:
                break
            message_chunks.append(data)
    # Decode list-of-byte-strings to UTF8 and parse JSON data
    message_bytes = b''.join(message_chunks)
    message_str = message_bytes.decode("utf-8")
    return json.loads(message_str)
