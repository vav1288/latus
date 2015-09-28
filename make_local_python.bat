REM
REM base Python must already be installed
REM
c:\Python34\python c:\Python34\Tools\Scripts\pyvenv.py --clear venv
REM
cd venv\Scripts
pip.exe install cryptography
pip.exe install sqlalchemy
pip.exe install send2trash
pip.exe install pathtools
pip.exe install watchdog
pip.exe install rsa
pip.exe install pytest
pip.exe install PySide
pip.exe install dirsync
REM
REM install wosnap.  eventually this might be on PyPI :)
pushd .
cd ..\wosnap
..\latus\venv\scripts\python.exe setup.py install
popd
REM
REM packages not in pypi (can not be installed with pip):
venv\Scripts\easy_install.exe third_party_installers\pywin32-219.win-amd64-py3.4.exe
venv\Scripts\python.exe make_local_python.py