
import os
import sys
import shutil
import glob
import datetime
import subprocess
import configparser

import latus.const
import latus.util

installer_string = 'installer'
config_path = 'installer.cfg'
nsis_build_dir = os.path.join('build', 'nsis')
dist_dir = 'dist'
# 'automatically' create the version based on the date.
# A day granularity is an (arbitrary) balance between version length and expected frequency of updates.
# In other words, I don't expect to release more than one version in a day and that will all live on.
# Also, the repo management gets too difficult if we have too many file names.  And nsist doesn't seem
# to like super frequent version string updates either.
version = installer_string + '_' + datetime.datetime.utcnow().strftime("%y%m%d")

# get rid of all existing installers
existing_installers = []
# I'm not sure if I should delete these for nsist's benefit or not ...
# existing_installers += glob.glob(os.path.join(nsis_build_dir, '*.exe'))
existing_installers += glob.glob(os.path.join(dist_dir, '*.exe'))
print('existing installers %s' % existing_installers)
for existing_installer in existing_installers:
    print('removing %s' % existing_installer)
    os.remove(existing_installer)

config = configparser.ConfigParser()
config['Application'] = {'name': latus.const.NAME,
                         'version': version,
                         # 'icon': os.path.join('icons', 'latus.ico'),
                         # 'console': 'True',
                         'entry_point': 'latus_main:main'}

# use this Python's version for the build version
config['Python'] = {'version': sys.version.split()[0]}

# make the requirements list out of requirements.txt
requirements = []
with open('requirements.txt') as f:
    for l in f:
        l = l.strip()
        if len(l) > 0:
            requirements.append(l)
requirements.append(latus.const.NAME)  # we need to include ourselves too
requirements.append('icons')  # and the icons code
requirements_string = None
for requirement in requirements:
    if len(requirement) > 0:
        if requirements_string is None:
            requirements_string = requirement
        else:
            requirements_string += '\n' + requirement
config['Include'] = {'packages': requirements_string}

if True:
    # write out the config
    with open(config_path, 'w') as configfile:
        config.write(configfile, space_around_delimiters=False)
        configfile.write('files = LICENSE\n')
        configfile.write(' README.md')

# finally execute nsist to create the installer
subprocess.call([sys.executable, '-m', 'nsist', config_path])

# copy the installer over to the dist folder
installer_path = latus.const.NAME + '_' + version + '.exe'
shutil.copy(os.path.join(nsis_build_dir, installer_path), dist_dir)