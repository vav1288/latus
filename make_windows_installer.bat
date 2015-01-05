REM todo make this a python script
mkdir dist\platforms
copy /Y C:\Python34\Lib\site-packages\PyQt5\plugins\platforms\*.dll dist\platforms
copy /Y C:\Python34\Lib\site-packages\PyQt5\libEGL.dll dist
c:\python34\python.exe setup.py py2exe
"C:\Program Files (x86)\NSIS\makensis.exe" latus.nsi
REM copy the exe and installer to dropbox - just so I don't have to push to github and take it back down
REM for user's other than me (the author) these need to be changed and/or made parameters (best when I convert this to Python)
mkdir E:\Documents\Dropbox\.latus\dist
copy /Y dist\*.exe E:\Documents\Dropbox\.latus\dist
