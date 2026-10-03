@echo off
title FINTELLIGENCE Pytest Verification Suite
echo ========================================================
echo Running FINTELLIGENCE 16/16 Pytest Verification Suite...
echo ========================================================
set PYTHONPATH=backend
py -m pytest backend\tests\ -v
pause
