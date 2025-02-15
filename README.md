# gimp-screenshot-grim-plugin

This [GIMP](https://www.gimp.org/) plug-in lets the user select a region of a
Wayland desktop and then creates an image from the selected region.  The
plug-in adds the menu item "Screenshot with grim..." to the File > Create menu.

## DEPENDENCIES

Requires GIMP 3.0, Python 3.7, a wlroots-based Wayland compositor and the
utilities grim and slurp.

## INSTALLATION

Run the following commands to install the plug-in:

    mkdir -p ~/.config/GIMP/3.0/plug-ins
    git clone https://github.com/voegelas/gimp-screenshot-grim-plugin.git \
        ~/.config/GIMP/3.0/plug-ins/screenshot-grim

Restart GIMP to enable the plug-in.

In GIMP, select Filters > Development > Python-Fu > Python Console.  Then press
"Browse..." and enter "plug-in-screenshot-grim" to see the usage information.

## LICENSE AND COPYRIGHT

Copyright (C) 2025 Andreas Vögele

This program is free software; you can redistribute and modify it under the
terms of the ISC license.
