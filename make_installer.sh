#!/usr/bin/env bash
venv/bin/python3 make_installer.py
#
# In this example we are making both a .dmg and a .pkg .  In general you would make one or the other only.
hdiutil create -volname test_example -srcfolder /Users/james/projects/latus/dist -ov -format UDZO latus_install.dmg
# Create the .pkkproj with Packages tool ( http://s.sudre.free.fr/Software/Packages/about.html )
/usr/local/bin/packagesbuild latus_install.pkgproj
