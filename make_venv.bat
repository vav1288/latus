REM
REM Python must already be installed
REM
c:\Python34\python c:\Python34\Tools\Scripts\pyvenv.py --clear lvenv
lvenv\Scripts\activate.bat
lvenv\Scripts\pip.exe install cryptography
lvenv\Scripts\pip.exe install sqlalchemy
lvenv\Scripts\pip.exe install send2trash
lvenv\Scripts\pip.exe install pathtools
lvenv\Scripts\pip.exe install watchdog
lvenv\Scripts\pip.exe install rsa
lvenv\Scripts\pip.exe install pytest
lvenv\Scripts\pip.exe install PySide
REM
REM packages not in pypi (can not be installed with pip):
lvenv\Scripts\easy_install.exe third_party_installers\pywin32-219.win-amd64-py3.4.exe

