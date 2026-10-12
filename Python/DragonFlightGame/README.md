# DragonFlight 🐉

A small 3D flight game about guiding a young dragon through a forest beneath its leafy canopy. Weave between tree trunks, keep ahead of the dragons chasing you, and reach the glowing forest beacon.

## Run in VS Code

DragonFlight uses Ursina and Panda3D. Use 64-bit Python 3.13, which has the Windows Panda3D wheel required by Ursina.

1. Install Python 3.13 (64-bit) from [python.org](https://www.python.org/downloads/).
2. Open this folder in VS Code and select `.venv313` as the Python interpreter (`Ctrl+Shift+P` → **Python: Select Interpreter**).
3. Press **F5** and choose **DragonFlight**, or run `python main.py` in the integrated terminal.

To create the environment and install the engine dependencies:

```powershell
py -3.13 -m venv .venv313
.\.venv313\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Controls

- **WASD** or **arrow keys**: steer left, right, up, and down
- **Space**: fly faster for a short burst while held
- **R**: restart the run

Steer through gaps between trunks and adjust your altitude as tree crowns vary in height. The route has alternating high and low clearances: climb above the brush, then dive under low branches. A tree or chaser strike costs one of your three hearts. Reach the beacon in the forest clearing to teleport into a blank white room with your dragon. Choose **Thank you!** or **OK** when the other dragon congratulates you, then hear about its next challenge.
