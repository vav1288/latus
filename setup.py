
import distutils.core

import latus.const
import latus.util

use_distutils = False
use_py2exe = True
use_cx_freeze = False

if use_cx_freeze:

    import cx_Freeze
    import sys

    # GUI applications require a different base on Windows (the default is for a console application).
    #base = None
    # Right now, we use the same .exe for CLI and GUI.  This is kind of a problem since it pops up a console window
    # for both.  Eventually we'll make 2 executables - one GUI, one CLI - so we'll do the below for the GUI.
    if sys.platform == "win32":
        base = "Win32GUI"

    # make sure cx_freeze picks up these packages
    build_exe_options = {"packages": ["cryptography.fernet",
                                      "cryptography.hazmat",
                                      "distutils"]}

    cx_Freeze.setup(

        name=latus.const.NAME,
        version=latus.util.version_string(),
        author=latus.const.AUTHOR,
        author_email=latus.const.EMAIL,
        url=latus.const.URL,
        license='LICENSE', # points to the actual file
        description=latus.const.DESCRIPTION,

        #options={"build_exe": build_exe_options},

        # make a single executable
        # PyQt version:
        options = {'py2exe': {'bundle_files': 1,
                              'compressed': True,
                              'optimize': 0,
                              "includes" : ["sqlalchemy", "sip", "PyQt5.QtGui", "PyQt5.QtCore", "cryptography",
                                            "watchdog"]}},

        executables=[cx_Freeze.Executable(latus.const.MAIN_FILE, base=base)],


    )

if use_py2exe:
    import py2exe

    distutils.core.setup(

        name=latus.const.NAME,
        version=latus.util.version_string(),
        author=latus.const.AUTHOR,
        author_email=latus.const.EMAIL,
        url=latus.const.URL,
        license='LICENSE',  # points to the actual file
        description=latus.const.DESCRIPTION,

        # make a single executable
        # PyQt version:
        options = {'py2exe': {'bundle_files': 1,
                              'compressed': True,
                              'optimize': 0,
                              "includes" : ["latus", "sqlalchemy", "sip", "PyQt5.QtGui", "PyQt5.QtCore", "cryptography",
                                            "watchdog"]}},
        console=[latus.const.MAIN_FILE],
        #windows=[latus.const.MAIN_FILE],
        zipfile=None,  # a single executable
    )

if use_distutils:
    distutils.core.setup(
        name=latus.const.NAME,
        version=latus.util.version_string(),
        author=latus.const.AUTHOR,
        author_email=latus.const.EMAIL,
        url=latus.const.URL,
        license='LICENSE',  # points to the actual file
        description=latus.const.DESCRIPTION,
    )