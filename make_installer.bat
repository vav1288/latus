echo on
REM Install wosnap to make sure we have the latest.  Eventually this might be on PyPI :) .
pushd .
cd ..\wosnap
..\latus\venv\scripts\python.exe setup.py install
popd
REM make the local python
venv\Scripts\python.exe make_local_python.py
REM
REM copy the launcher from wosnap and rename it to this project
copy /Y ..\wosnap\launch\Debug\launch.exe latus.exe
REM
REM create the nsis installer
mkdir dist
"C:\Program Files (x86)\NSIS\makensis" latus.nsi