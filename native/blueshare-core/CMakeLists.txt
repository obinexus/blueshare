set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS ON)

# The public header describes a future library API. No source in the current
# repository implements that API, so this remains an interface target rather
# than a falsely advertised binary library.
add_library(blueshare_core_api INTERFACE)
target_include_directories(
    blueshare_core_api
    INTERFACE
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include/blueshare>
)

# Existing sources are independent executable demonstrations with their own
# main() functions. Keep them separate until a real library implementation
# exists.
add_executable(blueshare_demo src/blueshare.c)
if(NOT MSVC)
    target_compile_options(blueshare_demo PRIVATE -Wall -Wextra)
endif()
if(UNIX OR MINGW)
    target_link_libraries(blueshare_demo PRIVATE m)
endif()

find_package(OpenSSL QUIET)
if(OpenSSL_FOUND)
    add_executable(blueshare_node_zero_demo src/zero.c)
    target_link_libraries(blueshare_node_zero_demo PRIVATE OpenSSL::Crypto)
    if(NOT MSVC)
        target_compile_options(blueshare_node_zero_demo PRIVATE -Wall -Wextra)
    endif()
else()
    message(STATUS "OpenSSL not found: skipping blueshare_node_zero_demo")
endif()

if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    add_executable(blueshare_nsigii_demo src/nsiggi.c)
    target_link_libraries(blueshare_nsigii_demo PRIVATE m)
    target_compile_options(blueshare_nsigii_demo PRIVATE -Wall -Wextra)
else()
    message(STATUS "Linux getrandom() unavailable: skipping blueshare_nsigii_demo")
endif()

if(BUILD_TESTING)
    # The retained demo deliberately supplies a mixed consent set and returns
    # nonzero when NSIGII rejects the session. Treat that rejection as the
    # expected constitutional outcome rather than as a build failure.
    add_test(NAME blueshare_demo_rejects_mixed_consent COMMAND blueshare_demo)
    set_tests_properties(blueshare_demo_rejects_mixed_consent PROPERTIES WILL_FAIL TRUE)
    if(TARGET blueshare_nsigii_demo)
        add_test(NAME blueshare_nsigii_demo_runs COMMAND blueshare_nsigii_demo)
    endif()
endif()

install(
    FILES
        include/blueshare_core.h
        include/platform_interface.h
    DESTINATION include/blueshare
)
