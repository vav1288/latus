
import distutils
import py2exe

distutils.core.setup(
    console=['latus.py'],

    name="latus sync",
    version="0.0",
    author='James Abel',
    author_email='j@abel.co',
    url='www.lat.us',
    license='LICENSE', # points to the actual file
    description="secure file sync with low impact to cloud storage",

    # make a single executable
    # PyQt version:
    # options = {'py2exe': {'bundle_files': 1, 'compressed': True, "includes" : ["sip", "PyQt5.QtGui", "PyQt5.QtCore"]}},
    # CLI version:
    options={'py2exe': {'bundle_files': 1, 'compressed': True, }},

    zipfile=None,
)
