echo on
venv\scripts\python.exe make_installer.py
REM
REM create the nsis installer
mkdir dist
"C:\Program Files (x86)\NSIS\makensis" latus.nsis