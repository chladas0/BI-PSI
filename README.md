# Robot Navigation Server

## Task
Create a server for automatic control of remote robots. Robots autonomously log into the server, which then guides them to the center of the coordinate system. For testing purposes, each robot starts at random coordinates and tries to reach the coordinate [0,0]. At the target coordinate, the robot must pick up a secret. On the way to the goal, robots may encounter obstacles that they must navigate around. The server can navigate multiple robots simultaneously and implements a flawless communication protocol.

## Detailed Specification
Communication between the server and the robots is carried out using a fully text-based protocol. Each command ends with a pair of special symbols "\a\b". (These are two characters '\a' and '\b'.) The server must adhere to the communication protocol in detail, but must account for imperfect robot firmwares (see the Special Situations section).

## Special Situations
- **Handling Robot Disconnects:** The server must handle unexpected robot disconnects and ensure smooth reconnection.
- **Protocol Errors:** The server should be robust against minor deviations in protocol from the robots.
- **Obstacle Navigation:** The server must dynamically update the path for robots to avoid obstacles.

## Features
- **Multi-Robot Navigation:** Simultaneous guidance for multiple robots.
- **Obstacle Avoidance:** Dynamic path planning to avoid obstacles.
- **Robust Communication:** Fault-tolerant communication adhering to the specified protocol.

## Usage
1. Start the server.
2. Robots will connect and be assigned initial random coordinates.
3. The server will guide each robot to the coordinate [0,0].
4. Robots pick up the secret at the target coordinate.
