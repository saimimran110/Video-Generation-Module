@echo off
REM This script launches Chrome with remote debugging enabled
REM It uses your existing Chrome profile with all your logins and extensions

echo Starting Chrome with Remote Debugging on port 9222...
echo Your existing profile will be used - all logins preserved!
echo.

REM Use your actual Chrome profile (not temporary)
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-allow-origins=* ^
  --no-first-run ^
  --no-default-browser-check

echo.
echo Chrome debugger stopped.
pause
