c:\Python34\python c:\Python34\Tools\Scripts\pyvenv.py --clear venv
venv\Scripts\python -m pip install --upgrade pip
call venv\Scripts\activate.bat
pip install setuptools -U
pip install sqlalchemy
pip install cryptography
pip install watchdog
pip install send2trash
pip install requests
pip install python-dateutil
pip install pytest
pip install dirsync
pip install appdirs
REM packages that can not be installed with pip:
easy_install.exe third_party_installers\pywin32-220.win-amd64-py3.4.exe
pip.exe install third_party_installers\PySide-1.2.2-cp34-none-win_amd64.whl
deactivate