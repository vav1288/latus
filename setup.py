import sys
import distutils
import py2exe
import cx_Freeze

# pick one
use_py2exe = False
use_cx_freeze = True

if use_cx_freeze:

    # GUI applications require a different base on Windows (the default is for a console application).
    base = None
    # Right now, we use the same .exe for CLI and GUI.  This is kind of a problem since it pops up a console window
    # for both.  Eventually we'll make 2 executables - one GUI, one CLI - so we'll do the below for the GUI.
    #if sys.platform == "win32":
    #    base = "Win32GUI"

    # make sure cx_freeze picks up these packages
    build_exe_options = {"packages": ["cryptography.fernet",
                                      "cryptography.hazmat",
                                      "distutils"]}

    cx_Freeze.setup(

        name="latus",
        version="0.0",
        author='James Abel',
        author_email='j@abel.co',
        url='www.lat.us',
        license='LICENSE', # points to the actual file
        description="secure file sync with low impact to cloud storage",
        options={"build_exe": build_exe_options},

        # make a single executable
        # PyQt version:
        #options = {'py2exe': {'bundle_files': 1,
        #                      'compressed': True,
        #                      'optimize': 0,
        #                      "includes" : ["sqlalchemy", "sip", "PyQt5.QtGui", "PyQt5.QtCore", "cryptography",
        #                                    "watchdog"]}},

        executables=[cx_Freeze.Executable("latus.py", base=base)],


    )

if use_py2exe:
    distutils.core.setup(

        console=['latus.py'],

        name="latus",
        version="0.0",
        author='James Abel',
        author_email='j@abel.co',
        url='www.lat.us',
        license='LICENSE', # points to the actual file
        description="secure file sync with low impact to cloud storage",

        # make a single executable
        # PyQt version:
        options = {'py2exe': {'bundle_files': 1,
                              'compressed': True,
                              'optimize': 0,
                              "includes" : ["sqlalchemy", "sip", "PyQt5.QtGui", "PyQt5.QtCore", "cryptography",
                                            "watchdog"]}},
        windows=['latus.py'],

        zipfile=None,  # a single executable
)
