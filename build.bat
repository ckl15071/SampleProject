@echo off
set PATH=%PATH%

if "%1"=="clean" (
    rmdir /s /q build
    exit /b 0
)

cmake -S . -B build -G "MinGW Makefiles" -DCMAKE_C_COMPILER=gcc
cmake --build build
