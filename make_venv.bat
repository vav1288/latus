c:\Python34\python c:\Python34\Tools\Scripts\pyvenv.py --clear venv
pushd .
cd venv\Scripts
pip.exe install cryptography
pip.exe install sqlalchemy
pip.exe install send2trash
pip.exe install pathtools
pip.exe install pathlib
pip.exe install watchdog
pip.exe install rsa
pip.exe install pytest
pip.exe install PySide
pip.exe install dirsync
pip.exe install python-dateutil
pip.exe install requests
popd
REM packages not in pypi (can not be installed with pip):
venv\Scripts\easy_install.exe third_party_installers\pywin32-219.win-amd64-py3.4.exe