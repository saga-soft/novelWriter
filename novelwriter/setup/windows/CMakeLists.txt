cmake_minimum_required(VERSION 3.14)
project(novelWriter LANGUAGES CXX)
add_executable(novelWriter main.cpp launcher.rc)
set_target_properties(novelWriter PROPERTIES WIN32_EXECUTABLE True)
