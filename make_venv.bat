REM minimum needed for osnap to run from this venv
c:\Python35\python c:\Python35\Tools\Scripts\pyvenv.py --clear venv
venv\Scripts\python -m pip install --upgrade pip
call venv\Scripts\activate.bat
pip install appdirs
deactivate