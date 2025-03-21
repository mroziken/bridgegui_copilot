#!/bin/bash

# Define the server address
CONTROL_SOCKET_ADDRESS="tcp://localhost:5555"
EVENT_SOCKET_ADDRESS="tcp://localhost:5555"

# Launch the first client to create the game
echo "Starting the first client to create the game..."
GAME_UUID=$(bridgegui -vv --create-game "$CONTROL_SOCKET_ADDRESS" | grep -oP '(?<=Game UUID: )[a-zA-Z0-9-]+')

if [ -z "$GAME_UUID" ]; then
  echo "Failed to retrieve the Game UUID. Exiting."
  exit 1
fi

echo "Game created with UUID: $GAME_UUID"

# Launch the other three clients in autopilot mode
for POSITION in "east" "south" "west"; do
  echo "Starting client at position: $POSITION"
  bridgegui -vv --autopilot --game "$GAME_UUID" "$CONTROL_SOCKET_ADDRESS" &
done

# Wait for all background processes to finish
wait

echo "All clients have been started."