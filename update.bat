@echo off
title Update Project to GitHub
echo ====================================================
echo   Updating Source Code to GitHub...
echo ====================================================

set /p commit_msg="Enter commit message (default: Code update): "
if "%commit_msg%"=="" set commit_msg=Code update

git add .
git commit -m "%commit_msg%"
git push

echo ====================================================
echo   Source code pushed successfully!
echo ====================================================
echo.

set /p make_release="Do you want to create a new Release and upload Tx6.exe? (y/n, default: n): "
if /i "%make_release%"=="y" (
    set /p version_tag="Enter version tag (e.g. v1.4.1): "
    if not "%version_tag%"=="" (
        python create_release_dynamic.py %version_tag%
    ) else (
        echo Version tag cannot be empty. Skipping release.
    )
)

echo ====================================================
echo   Update completed!
echo ====================================================
pause
