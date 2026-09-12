cmake_minimum_required(VERSION 3.10)
set(CMAKE_C_COMPILER "C:/bin/mingw64/bin/gcc.exe")
project(test_app C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED True)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include_directories(
    "C:/bin/mingw64/include"
    "C:/bin/mingw64/x86_64-w64-mingw32/include"
    ${CMAKE_CURRENT_SOURCE_DIR}/src/test
    ${CMAKE_CURRENT_SOURCE_DIR}/src/cmd
)

add_executable(test_app
    src/main.c
    src/test/test.c
    src/cmd/cmd.c
)

target_include_directories(test_app PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src/test
    ${CMAKE_CURRENT_SOURCE_DIR}/src/cmd
)
