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
pip.exe install dirsync
pip.exe install python-dateutil
pip.exe install requests
pip.exe install pex
pip.exe install PyAutoGUI
popd
REM packages not in pypi (can not be installed with pip):
venv\Scripts\easy_install.exe third_party_installers\pywin32-219.win-amd64-py3.4.exe
REM
REM PySide not installing this way so use PySide-1.2.2.win-amd64-py3.4.exe
REM pip.exe install PySide
venv\Scripts\easy_install.exe third_party_installers\PySide-1.2.2-py3.4-win-amd64.egg
