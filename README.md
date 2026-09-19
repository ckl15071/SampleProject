# Overview
A sample project for verifying the development environment setup.
Written in C/C++.

# Prerequisites
## gcc (MinGW-w64)
This project is built with gcc (MinGW-w64).

Install with MSYS2:
```
$ pacman -S mingw-w64-ucrt-x86_64-gcc
```

Or download a standalone build (e.g. WinLibs) and extract it to `C:\bin\mingw64`.

Add the bin directory to PATH. Note that build.bat expects `C:\bin\mingw64\bin`. Edit build.bat if you installed it elsewhere.
```
C:\bin\mingw64\bin
```

Verify the installation:
```
$ gcc --version
```

## clangd
clangd is used as the language server (completion, go-to-definition, references).

Install with winget (LLVM):
```
$ winget install LLVM.LLVM
```

Or install with MSYS2:
```
$ pacman -S mingw-w64-ucrt-x86_64-clang-tools-extra
```

If you use VS Code, you can install the clangd extension (`llvm-vs-code-extensions.vscode-clangd`) instead, which downloads clangd automatically.

This project generates `compile_commands.json` in the build directory. Point clangd to it:
```
--compile-commands-dir=${workspaceFolder}/build
```

Verify the installation:
```
$ clangd --version
```

# How to build
Run build.bat in the project root.

To build the project:
```
$ build
```

To clean the build directory:
```
$ build clean
```