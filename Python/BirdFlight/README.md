# BirdFlight 🐦

A small, colorful 3D flight game about crossing a chain of island cliffs. Your bird flies itself forward; steer between islands, reach the glowing nest checkpoints, and shake the predators that pursue you.

## Run in VS Code

BirdFlight uses Ursina, which depends on Panda3D. The virtual environment currently in `.venv` was created with Python 3.15, for which Panda3D does not currently publish a Windows wheel. Use standard 64-bit CPython 3.13 for this project.

1. Install Python 3.13 (64-bit) from [python.org](https://www.python.org/downloads/).
2. Open this folder in VS Code.
3. In the integrated PowerShell terminal, create a Python 3.13 environment and install the game engine:

   ```powershell
   py -3.13 -m venv .venv313
   .\.venv313\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. Select `.venv313` as the Python interpreter (`Ctrl+Shift+P` → **Python: Select Interpreter**).
5. Press **F5** and choose **BirdFlight**, or run `python main.py`.

If the `py` launcher is unavailable, create `.venv313` using the full path to your Python 3.13 executable, for example:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m venv .venv313
```

Then activate `.venv313` and continue with the install steps above. The existing `.venv` is left in place.

## Controls

- **Tap or hold WASD** or **arrow keys**: steer left/right and climb/dive
- **Space**: flap boost and fly faster
- **R**: restart

Reach the gold nest marker on each island to save your progress. Nests restore one heart, up to three. Three predator strikes end the flight; your current nest is your respawn point.

The world and birds are drawn from Ursina's built-in 3D primitives, so there are no external art assets to download.

