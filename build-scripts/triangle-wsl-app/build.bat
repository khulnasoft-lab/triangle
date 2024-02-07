@echo off

rem Default variables
set _MSBUILD=()
set _MSBUILD_VERSION=()
set _MSBUILD_TARGET=Build
set _MSBUILD_CONFIG=Debug
set _MSBUILD_PLATFORM=x64
set _MSBUILD_APPX_BUNDLE_PLATFORMS="x64|ARM64"
set _MSBUILD_NOSIGN_ARG=
set _MSBUILD_NOSIGN=true



rem Add path to MSBuild Binaries
rem Visual Studio Build Tools 2015
if exist "%ProgramFiles(x86)%\MSBuild\14.0\bin" (
    set _MSBUILD="%ProgramFiles(x86)%\MSBuild\14.0\bin\msbuild.exe"
    set _MSBUILD_VERSION=Build Tools 2015 x86
)
if exist "%ProgramFiles%\MSBuild\14.0\bin" (
    set _MSBUILD="%ProgramFiles%\MSBuild\14.0\bin\msbuild.exe"
    set _MSBUILD_VERSION=Build Tools 2015 x64
)
rem Visual Studio Community 2017
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2017\Community\MSBuild\15.0\Bin\msbuild.exe" (
    set _MSBUILD="%ProgramFiles(x86)%\Microsoft Visual Studio\2017\Community\MSBuild\15.0\Bin\msbuild.exe"
    set _MSBUILD_VERSION=Community 2017 x86
)
if exist "%ProgramFiles%\Microsoft Visual Studio\2017\Community\MSBuild\15.0\Bin\msbuild.exe" (
    set _MSBUILD="%ProgramFiles%\Microsoft Visual Studio\2017\Community\MSBuild\15.0\Bin\msbuild.exe"
    set _MSBUILD_VERSION=Community 2017 x64
)
rem Visual Studio Professional 2017
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\msbuild.exe" (
    set _MSBUILD="%ProgramFiles(x86)%\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\msbuild.exe"
    set _MSBUILD_VERSION=Professional 2017 x86
)
if exist "%ProgramFiles%\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\msbuild.exe" (
    set _MSBUILD="%ProgramFiles%\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\msbuild.exe"
    set _MSBUILD_VERSION=Professional 2017 x64
)
rem Visual Studio Enterprise 2017
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2017\Enterprise\MSBuild\15.0\Bin\msbuild.exe" (
	set _MSBUILD="%ProgramFiles(x86)%\Microsoft Visual Studio\2017\Enterprise\MSBuild\15.0\Bin\msbuild.exe"
    set _MSBUILD_VERSION=Enterprise 2017 x86
)
if exist "%ProgramFiles%\Microsoft Visual Studio\2017\Enterprise\MSBuild\15.0\Bin\msbuild.exe" (
	set _MSBUILD="%ProgramFiles%\Microsoft Visual Studio\2017\Enterprise\MSBuild\15.0\Bin\msbuild.exe"
    set _MSBUILD_VERSION=Enterprise 2017 x64
)
rem Visual Studio Preview 2019
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2019\Preview\MSBuild\Current\Bin\MSBuild.exe" (
    set _MSBUILD="%ProgramFiles(x86)%\Microsoft Visual Studio\2019\Preview\MSBuild\Current\Bin\MSBuild.exe"
    set _MSBUILD_VERSION=Preview 2017 x86
)
if exist "%ProgramFiles%\Microsoft Visual Studio\2019\Preview\MSBuild\Current\Bin\MSBuild.exe" (
    set _MSBUILD="%ProgramFiles%\Microsoft Visual Studio\2019\Preview\MSBuild\Current\Bin\MSBuild.exe"
    set _MSBUILD_VERSION=Preview 2017 x64
)
REM Visual Studio Community 2019
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe" (
    set _MSBUILD="%ProgramFiles(x86)%\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe"
    set _MSBUILD_VERSION=Community 2019 x86
)
if exist "%ProgramFiles%\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe" (
    set _MSBUILD="%ProgramFiles%\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe"
    set _MSBUILD_VERSION=Community 2019 x64
)
rem Visual Studio Build Tools 2019
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe" (
    set _MSBUILD="%ProgramFiles(x86)%\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
    set _MSBUILD_VERSION=Build Tools 2019 x86
)
if exist "%ProgramFiles%\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe" (
    set _MSBUILD=""%ProgramFiles%\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
    set _MSBUILD_VERSION=Build Tools 2019 x64
)
REM Visual Studio Community 2022
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe" (
    set _MSBUILD="%ProgramFiles(x86)%\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"
    set _MSBUILD_VERSION=Community 2022 x86
)
if exist "%ProgramFiles%\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe" (
    set _MSBUILD="%ProgramFiles%\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"
    set _MSBUILD_VERSION=Community 2022 x64
)
rem Visual Studio Professional 2022
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe" (
    set _MSBUILD="%ProgramFiles(x86)%\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe"
    set _MSBUILD_VERSION=Community 2022 x86
)
if exist "%ProgramFiles%\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe" (
    set _MSBUILD="%ProgramFiles%\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe"
    set _MSBUILD_VERSION=Community 2022 x64
)
rem Visual Studio Enterprise 2022
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe" (
    set _MSBUILD="%ProgramFiles(x86)%\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe"
    set _MSBUILD_VERSION=Enterprise 2022 x86
)
if exist "%ProgramFiles%\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe" (
    set _MSBUILD="%ProgramFiles%\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe"
    set _MSBUILD_VERSION=Enterprise 2022 x64
)
rem Visual Studio Build Tools 2022
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe" (
    set _MSBUILD="%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
    set _MSBUILD_VERSION=Build Tools 2022 x86
)
if exist "%ProgramFiles%\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe" (
    set _MSBUILD="%ProgramFiles%\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
    set _MSBUILD_VERSION=Build Tools 2022 x64
)



rem Check for Visual Studio / MSBuild
if %_MSBUILD%==() (
    echo Couldn't find MSBuild
    echo Make sure Visual Studio is installed.   Supported: 2015 - 2022
    goto :EXIT
)



rem Command line argument loop
:FOUND_MSBUILD
if (%1) == () (
    goto :POST_ARGS_LOOP
)
if (%1) == (clean) (
    goto :MSBUILD_CLEAN
)
if (%1) == (rel) (
    goto :MSBUILD_RELEASE
)
if (%1) == (release) (
    goto :MSBUILD_RELEASE
)
if (%1) == (x64) (
    goto :MSBUILD_AMD64
)
if (%1) == (amd64) (
    goto :MSBUILD_AMD64
)
if (%1) == (AMD64) (
    goto :MSBUILD_AMD64
)
if (%1) == (arm64) (
    goto :MSBUILD_ARM64
)
if (%1) == (ARM64) (
    goto :MSBUILD_ARM64
)
if (%1) == (nosign) (
    goto :MSBUILD_NOSIGN
)

echo Unknown option: %1
goto :EXIT

:ARGS_LOOP
shift
goto :FOUND_MSBUILD



rem Functions for command line argument loop
:MSBUILD_CLEAN
    set _MSBUILD_TARGET=Clean,Build
goto :ARGS_LOOP

:MSBUILD_RELEASE
    set _MSBUILD_CONFIG=Release
goto :ARGS_LOOP

:MSBUILD_AMD64
    set _MSBUILD_PLATFORM=x64
    set _MSBUILD_APPX_BUNDLE_PLATFORMS=x64
goto :ARGS_LOOP

:MSBUILD_ARM64
    set _MSBUILD_PLATFORM=ARM64
    set _MSBUILD_APPX_BUNDLE_PLATFORMS=ARM64
goto :ARGS_LOOP

:MSBUILD_NOSIGN
    set _MSBUILD_NOSIGN_ARG=/property:AppxPackageSigningEnabled=false
    set _MSBUILD_NOSIGN=false
goto :ARGS_LOOP



rem Build solution
:POST_ARGS_LOOP
echo [i] MSBuild: Visual Studio %_MSBUILD_VERSION%
echo [i] Target: %_MSBUILD_TARGET%
echo [i] Config: %_MSBUILD_CONFIG%
echo [i] Build platform: %_MSBUILD_PLATFORM%
echo [i] Appx platform: %_MSBUILD_APPX_BUNDLE_PLATFORMS%
echo [i] Sign output: %_MSBUILD_NOSIGN%

%_MSBUILD% %~dp0DistroLauncher.sln ^
    /maxcpucount ^
    /nodeReuse:true ^
    /target:%_MSBUILD_TARGET% ^
    /property:Configuration=%_MSBUILD_CONFIG% ^
    /property:Platform=%_MSBUILD_PLATFORM% ^
    /property:AppxBundlePlatforms=%_MSBUILD_APPX_BUNDLE_PLATFORMS% ^
    /property:UseSubFolderForOutputDirDuringMultiPlatformBuild=false ^
    %_MSBUILD_NOSIGN_ARG%

if (%ERRORLEVEL%) == (0) (
    echo.
    echo Created appx in: %~dp0AppPackages\DistroLauncher-Appx\
    echo.
    EXIT /B 0
)



rem End
:EXIT
EXIT /B 1
