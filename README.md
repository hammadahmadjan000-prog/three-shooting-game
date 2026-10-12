# three-shooting-game

A futuristic OpenGL-based first-person shooter prototype built in Python without a game engine.

Features:
- First-person camera with mouse look
- WASD movement, sprint, jump, and crouch
- Reloading, weapon cooldown, and ammo management
- Enemy drones that chase and fire projectiles
- Health, armor, score, and wave progression
- Sci-fi arena with modular buildings and floor grid
- Pickups for health, armor, and ammo
- Particle bursts and projectile effects
- Clean HUD overlay with status and mission messages

Run locally:

```bash
cd three-shooting-game
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Controls:
- W/A/S/D: movement
- Mouse: look around
- Left mouse: shoot
- Shift: sprint
- Space: jump
- Ctrl: crouch
- R: reload
- Esc: exit

This project is intentionally structured as a realistic, extensible FPS prototype so it can be expanded with weapon switching, sound effects, menus, more AI, and richer maps.
