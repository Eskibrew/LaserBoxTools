# SPDX-License-Identifier: LGPL-2.1-or-later

"""
Entry point for the addon (headless mode).

This file is loaded once during FreeCAD initialization if the addon is not disabled.
It runs in headless mode, so no Gui imports or calls are allowed here.

FreeCAD discovers addons using the native namespace package structure:
    freecad/<module_name>/

The parent `freecad/` package uses native namespace packaging (no __init__.py),
allowing multiple addons to coexist under the same freecad namespace.

Loading sequence:
    1. FreeCAD imports freecad.<module_name> (this file) during startup
    2. If FreeCAD is running with GUI, it later imports init_gui.py in the same package
    3. GUI-related code (workbenches, toolbars, etc.) belongs in init_gui.py

Keep this file fast - it runs on every FreeCAD startup.
"""

# Old files store proxies as src.lasertabs.*. During document restore FreeCAD
# allows that import only if the module is already loaded, or if its file path
# matches an entry in FreeCAD.__ModDirs__. Importing
# here marks the module as loaded by the addon before any document opens.
try:
    import src.lasertabs
except ImportError as ex:
    import FreeCAD as App

    App.Console.PrintWarning(
        f"LaserBoxTools: could not preload src.lasertabs ({ex}). Old documents will not migrate.\n"
    )

try:
    import src.laserslots
except ImportError as ex:
    import FreeCAD as App

    App.Console.PrintWarning(
        f"LaserBoxTools: could not preload src.laserslots ({ex}). Old documents will not migrate.\n"
    )

try:
    import src.laserlivinghinge
except ImportError as ex:
    import FreeCAD as App

    App.Console.PrintWarning(
        f"LaserBoxTools: could not preload src.laserlivinghinge ({ex}). Old documents will not migrate.\n"
    )
