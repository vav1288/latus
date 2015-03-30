
import os
import sys
import shutil
import glob

import latus.const
import latus.util

import nsist

installer_string = 'installer'
config_path = 'installer.cfg'
nsis_build_dir = os.path.join('build', 'nsis')
dist_dir = 'dist'
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

          # use this Python's version for the build version
          'py_version': sys.version.split()[0],
         }

# make the requirements list out of requirements.txt
kwargs['packages'] = requirements = []
with open('requirements.txt') as f:
    for l in f:
        l = l.strip()
        if len(l) > 0:
            requirements.append(l)
requirements.append(latus.const.NAME)  # we need to include ourselves too
requirements.append('icons')  # and the icons code

shutil.copy(os.path.join('icons', 'glossyorb.ico'), nsis_build_dir)  # there should be a cleaner way to do this ...

# Call pynsist to build the installer
ib = nsist.InstallerBuilder(**kwargs)
ib.run()

# copy the installer over to the dist folder
installer_path = latus.const.NAME + '_' + version + '.exe'
shutil.copy(os.path.join(nsis_build_dir, installer_path), dist_dir)