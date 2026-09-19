cmake_minimum_required(VERSION 3.10)
set(CMAKE_C_COMPILER "gcc.exe")
project(test_app C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED True)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_executable(test_app
    src/main.c
    src/test/test.c
    src/cmd/cmd.c
)

set_target_properties(test_app PROPERTIES
    C_STANDARD 11
    C_STANDARD_REQUIRED ON
    C_EXTENSIONS OFF
)

target_include_directories(test_app PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src/test
    ${CMAKE_CURRENT_SOURCE_DIR}/src/cmd
)
