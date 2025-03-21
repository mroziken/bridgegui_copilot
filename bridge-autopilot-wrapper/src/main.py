from bridgegui import BridgeWindow
import sys
import zmq
from multiprocessing import Process
from PyQt5.QtWidgets import QApplication
import logging

logging.basicConfig(level=logging.DEBUG)

def run_client(control_socket_address, event_socket_address, position, game_uuid=None):
    # Create a QApplication instance in the main thread of the process
    app = QApplication([])

    # Create ZMQ sockets
    context = zmq.Context()
    control_socket = context.socket(zmq.REQ)
    control_socket.connect(control_socket_address)

    event_socket = context.socket(zmq.SUB)
    event_socket.connect(event_socket_address)

    logging.debug(f"Client {position} connected to control socket at {control_socket_address}")
    logging.debug(f"Client {position} connected to event socket at {event_socket_address}")

    # Create the BridgeWindow instance
    client = BridgeWindow(
        control_socket,
        event_socket,
        position,
        game_uuid,
        create_game=(game_uuid is None),
        player_uuid=None,
        copilot=False,
        autopilot=True
    )
    client.show()

    # Start the Qt event loop
    app.exec_()

def main():
    control_socket_address = "tcp://localhost:5555"
    event_socket_address = "tcp://localhost:5555"

    # Start the first client to create a game
    first_client_process = Process(
        target=run_client,
        args=(control_socket_address, event_socket_address, 'north', None)
    )
    first_client_process.start()
    first_client_process.join()  # Wait for the first client to finish creating the game

    # Retrieve the game UUID from the first client (this part needs to be implemented in the BridgeWindow class)
    game_uuid = None  # Placeholder: Replace with actual game UUID retrieval logic

    # Start the other three clients to join the game
    for position in ['east', 'south', 'west']:
        client_process = Process(
            target=run_client,
            args=(control_socket_address, event_socket_address, position, game_uuid)
        )
        client_process.start()

if __name__ == "__main__":
    main()