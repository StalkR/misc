@echo off
rem Requirements:
rem - Visual Studio 2022 (PlatformToolset v143, otherwise just change that field)
rem - windivert include path: mklink /J include "path to github.com/basil00/Divert/include"
rem - WinDivert.dll, WinDivert.lib & WinDivert.sys from latest WinDivert release
rem - Find your binary in x64\Release\winnat.exe
rem - Run it with WinDivert.{dll,sys} in the current working directory
msbuild winnat.vcxproj /p:Configuration=Release /p:Platform=x64
