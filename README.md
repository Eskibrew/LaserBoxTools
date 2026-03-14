# LaserBoxTools

A FreeCAD workbench for designing laser-cut boxes and enclosures. Create parametric tabs, slots, and living hinges on your 3D models for easy laser cutting and assembly.

![Laser Boxes Workbench](Resources/icons/LBLogo.svg)

**Video tutorial:** [How to use basic features](https://youtu.be/j17BoXwl58k)

## Features

- **Basic Box** — Create rectangular box pieces with configurable dimensions
- **Tabs** — Add parametric finger tabs along edges for joining panels. Supports tab count, width, depth, taper, margins, and optional hook profiles
- **Slots** — Generate slots along edges to receive tabs from other panels. Configurable slot count, length, depth, and gap width
- **Living Hinge** — Create flexible hinge patterns (e.g. straight elements) along edges for foldable designs

All features work on selected faces and edges of your Part or PartDesign bodies, with optional auto-update when parameters change.

## Requirements

- [FreeCAD](https://www.freecad.org/) (tested with FreeCAD 1.x)
- PySide (included with FreeCAD)

## Installation

### Option 1: Addon Manager (recommended)

1. Open FreeCAD
2. Go to **Tools → Addon Manager**
3. Search for "LaserBoxTools" or "Laser Boxes"
4. Click **Install**

> If this workbench is not yet in the Addon Manager repository, use manual installation below.

### Option 2: Manual installation

1. Clone or download this repository
2. Copy the entire `LaserBoxTools` folder into your FreeCAD Mod directory:
   - **Linux**: `~/.local/share/FreeCAD/Mod/` (or `~/.local/share/FreeCAD/v1-2/Mod/` for FreeCAD 1.2)
   - **Windows**: `%APPDATA%\FreeCAD\Mod\`
   - **macOS**: `~/Library/Application Support/FreeCAD/Mod/`
3. Restart FreeCAD
4. Select the **Laser Boxes** workbench from the workbench dropdown

## Usage

1. Create or open a Part or PartDesign model
2. Switch to the **Laser Boxes** workbench
3. Select a face or edge on your model
4. Use one of the tools:
   - **LBBasicBox** — Create a new box piece
   - **LBTabs** — Add tabs to the selected edge
   - **LBSlots** — Add slots to the selected edge
   - **LBLivingHinge** — Add a living hinge along the selected edge

Adjust parameters in the property panel or task panel. Enable **Auto Update** to refresh the geometry when you change values.

## Project Structure

```
LaserBoxTools/
├── Init.py              # Module initialization
├── InitGui.py           # Workbench registration
├── laser_boxes_locator.py
├── src/
│   ├── lasermakebox.py  # Basic box creation
│   ├── lasertabs.py     # Tab generation
│   ├── laserslots.py    # Slot generation
│   ├── laserlivinghinge.py
│   └── laserhelper.py   # Shared utilities
├── dialogs/             # Qt UI files
├── Resources/icons/     # Tool icons
└── LICENSE
```

## License

This project is licensed under the **GNU Lesser General Public License v2.1** (LGPL-2.1). See the [LICENSE](LICENSE) file for details.

## Credits

- Copyright (c) 2022 EskiBrew
