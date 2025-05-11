# 🎮 AI-Powered Dynamic Pacman: Two-Player Edition

<div align="center">
  <img src="![image](https://github.com/user-attachments/assets/1a8449a1-121d-4f6c-8d64-10612e82318c)
  
  [![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
  [![Pygame](https://img.shields.io/badge/Pygame-2.0+-green)](https://www.pygame.org/)

</div>

## 🌟 Project Overview
A modern twist on classic Pacman featuring:
- **Competitive two-player mode** with score tracking
- **Dynamic map regeneration** every 30 seconds
- **Intelligent ghosts** using multiple AI algorithms (A*, BFS, Min-Max, Genetic Algorithm)
- **New power-ups** like ghost freezing
- **Adaptive gameplay** with multiple win conditions

## 🚀 Key Features
| Feature | Description |
|---------|-------------|
| 🕹️ Dual Players | Compete head-to-head as Pacman characters |
| 🧠 Smart Ghosts | AI-driven enemies with pathfinding strategies |
| 🗺️ Living Maze | Map reshapes dynamically during gameplay |
| ⏳ Ghost Freeze | Temporary power-up to evade capture |
| 🏆 Multiple Win Conditions | Score-based or survival-based victory |

## 📊 Program Architecture
```mermaid
graph TD
    A[Game Start] --> B[Initialize Map]
    B --> C[Player Spawn]
    C --> D{Gameloop}
    D --> E[Ghost AI Movement]
    E --> F[Player Input]
    F --> G[Collision Detection]
    G --> H[Score Update]
    H --> I{Map Timer >30s?}
    I -->|Yes| J[Regenerate Map]
    I -->|No| D
    J --> K[Reposition Entities]
    K --> D
    G --> L{Game End?}
    L -->|Yes| M[Display Winner]
