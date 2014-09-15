REM this seems like a kludge but it is simple
REM all files are kept in latus and only use latusdoc to publish to the web
copy /Y doc\*.html ..\latusdoc
copy /Y doc\*.png ..\latusdoc
echo "now it is up to you do the repo commit and push on the latusdoc repo"