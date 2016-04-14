@echo off

rem This is apparently required with Windows/Python 3.x to avoid errors when using debug mode
set WERKZEUG_DEBUG_PIN=off
start /B python src\fileserve.py