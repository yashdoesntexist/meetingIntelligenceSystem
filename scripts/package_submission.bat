@echo off
set OUT=submission_%DATE:~10,4%-%DATE:~4,2%-%DATE:~7,2%.zip
echo Packaging to %OUT%
powershell -Command "Compress-Archive -Path README.md,AI_USAGE.md,LICENSES.txt,references.docx,references.md,images,logs,data\processed,src,scripts -DestinationPath %OUT% -Force"
echo Done: %OUT%
