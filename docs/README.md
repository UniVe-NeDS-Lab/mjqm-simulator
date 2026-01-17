# MJQM simulator

Simulator for Multiserver Job Queueing Model (MJQM)

## Prerequisites

Depending on your system, different commands can be used to install the required tools. We'll use just Ubuntu and MacOS as examples.

### C++ toolchain

We ensure that the standard `g++` compiler, using the `C++20` standard, can be used to compile the project. Its minimum supported version is the latest in the 10 series.

```sh
sudo apt install build-essential # Ubuntu
brew install gcc # MacOS
```

> [!Note]
  On MacOS, if in the past you run the `xcode-select --install` command, you will find two versions of the compiler installed. \
  To manually use the standard `gcc` version, you can refer to the `g++-{main-version}` binary. \
  Using the `configure` and `rebuild` scripts, we try to select the correct version.

### CMake

The project uses the `CMake` build system, we tested it with version `3.16` and higher.

```sh
sudo apt install cmake # Ubuntu
brew install --cask cmake # MacOS
```

### Boost

The project uses the `Boost` library, we tested it with version `1.71` and higher.

```sh
sudo apt install libboost-all-dev # Ubuntu
brew install boost # MacOS
```

### Python3

To run the tests, you need to have `Python3` installed on your system, in addition to the previous requirements.

We recommend using [`uv`](https://docs.astral.sh/uv/) as Python package manager, for which we provide the pyproject.toml configuration file.

## Build

To prepare and compile the project with `cmake`, use the following command from the project root directory:

```sh
./configure [--debug] [--clean] [--test] [--no-build]
```

This will create an executable named `<file>` for each configured `<file>.cpp` in the root directory.
It will also prepare the Python environment with `uv`, installing it for the current user if missing.

The additional parameters work as such:

- `--debug` to build with debug symbols (useful for IDEs).
- `--clean` to remove the cmake directory before configuring the project, effectively doing a _full fresh restart_.
- `--test` to also run tests.
- `--no-build` to only configure the project without building it.
- `--no-uv` to skip the installation of `uv` and the Python environment.

> [!Note]
  To dig deeper into the details, in the output of the `configure` script you can find the actual commands used to configure and build the project, prepended with `+`.

### Rebuild

If you change some code and want to rebuild the project, you can use the `rebuild` script:

```sh
./rebuild [--debug] [--clean] [--test]
```

The additional parameters work as such:

- `--debug` to rebuild with debug symbols (you need to have configured the project with the `--debug` parameter already).
- `--clean` to add the `--clean-first` parameter to cmake, that will remove all prebuilt symbols and objects before rebuilding the project, without doing a _full fresh restart_.
- `--test` to also run tests.

## Test

> [!Note]
  The test suite will be completely reworked soon.

To run the test suite, use the following command after configuration is done:

```sh
cmake --build . --preset test
```

This will run all the simulation tests for which results are available in the `test/expected` folder.

Their run parameters are configured in the `CMakeLists.txt` file.
