# COHERE — Two-Agent Research Prototype

COHERE is a two-agent Prisoner's Dilemma simulation that explores cooperation, defection, and decision-making between two agents.

## Project Components

- **Web Interface:** HTML-based interface for interacting with the simulation.
- **ESP32 Hardware:** Four physical buttons for selecting each agent's action.
- **Python Bridge:** Local server that connects hardware decisions to the web interface.

## Hardware

- ESP32-WROOM-32 development board
- Four push buttons
- Breadboard and jumper wires

## Software

- Arduino IDE
- Python 3
- HTML, CSS, and JavaScript

## How to Run

1. Install Python 3 and the Arduino IDE.
2. Start the Python bridge using `py cohere_wifi_bridge.py`.
3. Open `http://127.0.0.1:8000` in your browser on the same computer.
4. Configure the ESP32 sketch with the correct local server address and Wi-Fi credentials.
5. Upload the sketch to the ESP32 and test the buttons.

**Note:** The Python bridge must remain running for the local prototype to work. The website and bridge are not automatically hosted online by GitHub.

## Project Status

Hardware and software prototype in development.
