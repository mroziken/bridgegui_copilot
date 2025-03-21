# BridgeGUI Wrapper

This project is a wrapper for the BridgeGUI application, designed to facilitate the initiation of multiple clients in autopilot mode. The wrapper allows for the creation of a game by one client and the joining of that game by additional clients.

## Project Structure

```
bridgegui-wrapper
├── src
│   ├── main.py          # Entry point for the wrapper application
│   └── utils
│       └── __init__.py  # Utility functions and classes
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```

## Installation

To set up the project, clone the repository and install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

To run the wrapper application, execute the following command:

```bash
python src/main.py
```

This will start four clients in autopilot mode, where the first client creates a game and the other three clients join using the game UUID.

## Dependencies

The project requires the following Python packages:

- PyQt5
- Other necessary libraries for the BridgeGUI application

Make sure to check the `requirements.txt` file for the complete list of dependencies.

## Contributing

Contributions to the project are welcome. Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.