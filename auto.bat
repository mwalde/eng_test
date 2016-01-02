@echo off

set count=0
set /p count="Enter number of tests: "

if %count% == 0 (
    echo "Loop count required"
    goto continue
    
)
echo %count%
for /l %%x in (1,1,%count%) do (
    echo %%x
    5xsweep.py
)
:continue
pause
