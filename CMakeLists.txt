cmake_minimum_required(VERSION 3.16)
#cmake_policy(SET CMP0167 NEW)
#set(CMAKE_VERBOSE_MAKEFILE ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

option(BUILD_SHARED_LIBS "Build using shared libraries" OFF)
option(COMPILE_NATIVE "Build optimizing for the current machine" ON)

# Set the C++ standard to C++20
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

project(mjqm-simulator
    VERSION 0.1.0
    DESCRIPTION "Simulator for Multiserver Job Queuing Model (MJQM)"
    HOMEPAGE_URL "https://github.com/UniVe-NeDS-Lab/mjqm-simulator"
    LANGUAGES CXX
)

# Link and compile time optimization
add_link_options(   -flto=auto -O3)
add_compile_options(-flto=auto -O3)
# Safe math improvements for the project
add_link_options(   -ffinite-math-only -fno-signed-zeros -fno-math-errno)
add_compile_options(-ffinite-math-only -fno-signed-zeros -fno-math-errno)

if (CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    # CLang has issues on darwin
    add_link_options(   -ffat-lto-objects)
    add_compile_options(-ffat-lto-objects)
else ()
    add_link_options(   -Wno-ignored-optimization-argument)
    add_compile_options(-Wno-ignored-optimization-argument)
endif()
if (COMPILE_NATIVE)
    message(STATUS "Compiling for the current machine")
    add_link_options(   -march=native)
    add_compile_options(-march=native)
endif ()
if (CMAKE_BUILD_TYPE STREQUAL "Debug")
    message(STATUS "Compiling in Debug mode")
    add_link_options(   -g)
    add_compile_options(-g)
    add_compile_options(-Wall -Wextra -Wpedantic -Wno-unused-parameter)
endif()

# Include the Boost library
if (CMAKE_BUILD_TYPE STREQUAL "Debug")
    set(Boost_USE_DEBUG_LIBS     ON)  # only find debug libs
else ()
    set(Boost_USE_DEBUG_LIBS    OFF)  # ignore debug libs
endif ()
set(Boost_USE_RELEASE_LIBS       ON)  # only find release libs
set(Boost_USE_MULTITHREADED     OFF)  # each thread is reserved for one experiment each
if (BUILD_SHARED_LIBS)
    set(Boost_USE_STATIC_LIBS   OFF)  # only find shared libs
else ()
    set(Boost_USE_STATIC_LIBS    ON)  # only find static libs
endif ()
find_package(Boost 1.71 REQUIRED)
include_directories(${Boost_INCLUDE_DIR})

include_directories(
    libs/policies/include
    libs/samplers/include
    libs/simulator/include
    libs/utils/include
)

add_subdirectory(libs/policies)
add_subdirectory(libs/samplers)
add_subdirectory(libs/simulator)
add_subdirectory(libs/utils)

add_executable(simulator simulator.cpp)
target_compile_options(simulator PRIVATE -fwhole-program)
target_link_libraries(simulator toml_loader)

add_executable(toml_loader_test toml_loader_test.cpp)
target_compile_options(toml_loader_test PRIVATE -fwhole-program)
target_link_libraries(toml_loader_test toml_loader)

foreach (target simulator toml_loader_test)
    add_custom_command(
        TARGET ${target} POST_BUILD
        BYPRODUCTS ${CMAKE_CURRENT_SOURCE_DIR}/${target}
        COMMAND ${CMAKE_COMMAND} -E copy
        ${CMAKE_CURRENT_BINARY_DIR}/${target}
        ${CMAKE_CURRENT_SOURCE_DIR}/${target}
    )
endforeach ()

add_custom_command(
    TARGET simulator POST_BUILD
    BYPRODUCTS ${CMAKE_CURRENT_SOURCE_DIR}/Results/simulator
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMAND mkdir -p Results/simulator
)

enable_testing()

set(TOML_TEST_CMD $<TARGET_FILE:toml_loader_test>)
set(TOML_TEST_DIR ${CMAKE_SOURCE_DIR})

foreach(name sa_det sa_equal sa_warn sa_unordered)
    string(REPLACE "sa_" "test_shared_arrival_" toml_name ${name})
    add_test(NAME ${name} COMMAND ${TOML_TEST_CMD} tests/${toml_name} WORKING_DIRECTORY ${TOML_TEST_DIR})
    set_tests_properties(${name} PROPERTIES FAIL_REGULAR_EXPRESSION "Error reading experiment config")
endforeach()

add_test(NAME sa_neg_prob    COMMAND ${TOML_TEST_CMD} tests/test_shared_arrival_negative_prob    WORKING_DIRECTORY ${TOML_TEST_DIR})
add_test(NAME sa_partial     COMMAND ${TOML_TEST_CMD} tests/test_shared_arrival_partial_prob     WORKING_DIRECTORY ${TOML_TEST_DIR})
add_test(NAME sa_bad_dist    COMMAND ${TOML_TEST_CMD} tests/test_shared_arrival_bad_distribution WORKING_DIRECTORY ${TOML_TEST_DIR})
add_test(NAME sa_conflict    COMMAND ${TOML_TEST_CMD} tests/test_shared_arrival_conflict         WORKING_DIRECTORY ${TOML_TEST_DIR})

set_tests_properties(sa_neg_prob PROPERTIES PASS_REGULAR_EXPRESSION "arrival.prob for class 0 is negative")
set_tests_properties(sa_partial  PROPERTIES PASS_REGULAR_EXPRESSION "Not all classes have the prob property defined")
set_tests_properties(sa_bad_dist PROPERTIES PASS_REGULAR_EXPRESSION "Unsupported distribution")
set_tests_properties(sa_conflict PROPERTIES PASS_REGULAR_EXPRESSION "Unsupported arrival.mode")

add_test(NAME ind_mode COMMAND ${TOML_TEST_CMD} tests/test_independent_arrival WORKING_DIRECTORY ${TOML_TEST_DIR})
set_tests_properties(ind_mode PROPERTIES FAIL_REGULAR_EXPRESSION "Error reading experiment config")
