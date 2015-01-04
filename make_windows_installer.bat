REM for PyQt
mkdir dist\platforms
copy /Y C:\Python34\Lib\site-packages\PyQt5\plugins\platforms\*.dll dist\platforms
copy /Y C:\Python34\Lib\site-packages\PyQt5\libEGL.dll dist
REM mkdir dist\icons
REM copy /Y icons\*.ico dist\icons
c:\python34\python.exe setup.py py2exe
"C:\Program Files (x86)\NSIS\makensis.exe" latus.nsi
