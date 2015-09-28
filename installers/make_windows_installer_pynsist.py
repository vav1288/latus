
import os
import sys
import shutil
import glob
import datetime
import pprint

import latus.const
import latus.util

import nsist

start_time = datetime.datetime.now()

installer_string = 'installer'
config_path = 'installer.cfg'
nsis_build_dir = os.path.join('build', 'nsis')
dist_dir = 'dist'
python_root = os.path.join('c:', os.sep, 'Python34')

if not os.path.exists(dist_dir):
    os.mkdir (dist_dir)

# 'automatically' create the version based on the date.
# A day granularity is an (arbitrary) balance between version length and expected frequency of updates.
# In other words, I don't expect to release more than one version in a day and that will all live on.
# Also, the repo management gets too difficult if we have too many file names.  And nsist doesn't seem
# to like super frequent version string updates either.
version = installer_string + '_' + latus.util.version_string()

# get rid of all existing installers
existing_installers = []
# I'm not sure if I should delete these for nsist's benefit or not ...
# existing_installers += glob.glob(os.path.join(nsis_build_dir, '*.exe'))
existing_installers += glob.glob(os.path.join(dist_dir, '*.exe'))
print('existing installers %s' % existing_installers)
for existing_installer in existing_installers:
    print('removing %s' % existing_installer)
    os.remove(existing_installer)

kwargs = {'appname': latus.const.NAME,
          'version': version,
          'shortcuts': {
              latus.const.NAME: {'entry_point': 'latus_main:main',
                                 'console': False,
                                 'icon': os.path.join('icons', 'latus.ico'),
                                },
          },
          'packages': ['latus', 'cryptography', 'win32api', 'win32con', 'sqlalchemy', 'PyQt5', 'send2trash',
                       'pathtools', 'watchdog', 'rsa', 'icons',
                       # Special cryptography packages ... I don't know why just specifying 'cryptography' doesn't
                       # pick these up.
                       'six', 'cffi', '_cffi_backend',
                       #
                       'sip',  # needed for PyQt, apparently
                       ],
          # use this Python's version for the build version
          'py_version': sys.version.split()[0],
         }

if not os.path.exists(nsis_build_dir):
    os.makedirs(nsis_build_dir)

shutil.copy(os.path.join('icons', 'glossyorb.ico'), nsis_build_dir)  # there should be a cleaner way to do this ...

# Qt platform plugin "windows"
shutil.copy(os.path.join(python_root, 'Lib', 'site-packages', 'PyQt5', 'libEGL.dll'), nsis_build_dir)

pprint.pprint(kwargs)

# Call pynsist to build the installer
ib = nsist.InstallerBuilder(**kwargs)
ib.run()

# copy the installer over to the dist folder
installer_path = latus.const.NAME + '_' + version + '.exe'
shutil.copy(os.path.join(nsis_build_dir, installer_path), dist_dir)

print()
print("time to create installer : %s" % str(datetime.datetime.now() - start_time))