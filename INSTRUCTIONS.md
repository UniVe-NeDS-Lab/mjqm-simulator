# MJQM Simulator — Docker Artifact

After extracting the zip, all commands below should be run from the
artifact root directory (the folder containing `README.md`,
`mjqm-simulator.tar.gz`, `configs/`, `scripts/`, etc.).

## Prerequisites

You need [Docker Desktop](https://www.docker.com/products/docker-desktop/)
installed on your machine (available for Linux, macOS, and Windows).

> **Note:** The examples below assume Docker is running on your local machine.
> If you are running on a remote server, replace `localhost` with the server's
> address and make sure the relevant ports are accessible.
>
> **Windows users:** Replace `$(pwd)` with `%cd%` in Command Prompt,
> or `${PWD}` in PowerShell.
>
## Load the Docker image

```sh
docker load -i mjqm-simulator.tar.gz
```

Expected output: `Loaded image: mjqm-simulator:latest`.
Apple Silicon/ARM machines run the image transparently via
Docker Desktop's Rosetta emulation.

## Quick check (Phase I)

Run the bundled example script to verify the simulator works correctly:

```sh
docker run --rm \
    -v "$(pwd)/Results:/app/Results" \
    mjqm-simulator \
    ./run-examples.sh
```

This runs the M/M/1 validation experiment with 5 repetitions (~30 s).
The simulator prints `"Repetition N Done"` after each repetition and
`"All threads joined"` when the experiment completes. The output CSV
files are written to `Results/validation_mm1/`.

## Simulator CLI

The simulator accepts a TOML configuration file and optional parameter overrides:

```
./simulator <config> [--key value ...] [--pivot --key value ...]
```

To see the available options:

```sh
docker run --rm mjqm-simulator ./simulator --help
```

The simulator loads the configuration from `Inputs/`, runs the specified
number of discrete events for each repetition, and writes aggregated CSV
results to `Results/<config_name>/`.

## Run a simulation

To run a simulation, for example:

```sh
docker run --rm \
    -v "$(pwd)/Results:/app/Results" \
    mjqm-simulator \
    ./simulator tools_oneOrT
```

Results are written to the `Results/` directory on the host.

### Reproducing the paper figures

The following configurations reproduce the figures in the paper:

| Figure(s)     | Configuration                                     |
|---------------|----------------------------------------------------|
| Figures 2a, 3 | `tools_B_pol`                                      |
| Figure 2b     | `tools_B_dist`                                     |
| Figure 4a     | `tools_five_exp` and `tools_five_bpar`             |
| Figure 4b     | `tools_oneOrT`                                     |

### Runtime estimates

<span style="color:red">IMPORTANT</span>

Configurations based on the Google Borg Cell B dataset (`tools_B_*`)
require a large number of events (30–60 million) to produce reliable
results. The table below lists runtimes measured on a high-capacity
cluster node (20-core Intel Xeon Gold 6148 CPU @ 2.40 GHz, 200 GB ECC RAM):

| Configuration      | Events | Arrival rates | Total runtime |
|--------------------|--------|---------------|---------------|
| `validation_mm1`   | 1 M    | 11            | ~30 s         |
| `tools_B_dist`     | 30 M   | 16            | ~95 min       |
| `tools_B_pol`      | 30–60 M| 28–59         | ~11.5 h       |

Precomputed results for the Cell B experiments are included both in
the Docker image and in the artifact at `Results/prerun/`, and can be
used directly for figure generation and
visualisation without re-running the simulations. New simulation results
are written to `Results/<config_name>/` and do not overwrite the
precomputed data. We also provide an alternative to run shorter experiments in the next section.


### Reduced experiments

Any TOML parameter can be overridden from the command line using
dot-notation paths that mirror the configuration structure. Overrides
modify an in-memory copy of the configuration; the file on disk is never
changed. When a configuration file defines `[[pivot]]` sections that
iterate over values for a parameter, a CLI override for the same key
replaces those values entirely (the iteration continues, but over the
CLI-provided values). Non-overlapping pivot keys are preserved.

For the Cell B configurations that exceed 8 hours in full, override the
event count to produce results in a shorter time with only 1 million events:

```sh
docker run --rm \
    -v "$(pwd)/Results:/app/Results" \
    mjqm-simulator \
    ./simulator tools_B_pol --events 1000000
```

```sh
docker run --rm \
    -v "$(pwd)/Results:/app/Results" \
    mjqm-simulator \
    ./simulator tools_B_dist --events 1000000
```

On a Mac Mini M1, this reduced simulation takes approximately 45 minutes.
The results will be noisier than the full run but sufficient to verify
that the simulator operates correctly. To reproduce the exact paper
figures, use the precomputed results in `Results/prerun/`.

### Figure generation scripts

Two scripts in the `scripts/` directory generate figures matching those
in the paper. These scripts run on the host (not inside Docker) and
require Python 3 with `matplotlib` and `pandas`. From the artifact root:

```sh
cd scripts
python3 figure_B.py
```

The script prompts whether to use precomputed results or freshly
generated simulation outputs. Output: `figure_2a.pdf`, `figure_2b.pdf`,
`figure_3.pdf`.

```sh
cd scripts
python3 figure_4.py
```

Output: `figure_4a.pdf`, `figure_4b.pdf`.

## Explore results with the web UI

The image ships with precomputed results in `Results/prerun/`. The
interactive web dashboard is available immediately without running any
simulation first since we have already provided some precomputed results:

```
docker run --rm -p 8050:8050 \
    -v $(pwd)/Results:/app/Results mjqm-simulator \
    uv run --no-dev scripts/plotly_app.py
```

Open http://localhost:8050 in your browser. Press Ctrl+C in the
terminal to stop the server. The dashboard provides:

- A **dropdown** to select an experiment from the available results.
- **Tabs** for different metrics: response time, waiting time, throughput,
  queue length, wasted servers, and Kleinrock's Power (knee metric).
- A **log-log plot** of the selected metric against arrival rate, with one
  line per scheduling policy or distribution.
- A **stability toggle** to filter out unstable operating points.
- A **data table** view with CSV export.

The web UI (`plotly_app.py`) also supports:

- `DASH_HOST` — bind address (default: `0.0.0.0`)
- `DASH_PORT` — port (default: `8050`)
- `DASH_DEBUG` — enable debug mode (default: `false`)

For example, to run on port 9000:

```
docker run --rm -p 9000:9000 \
    -e DASH_PORT=9000 \
    -v $(pwd)/Results:/app/Results mjqm-simulator \
    uv run --no-dev scripts/plotly_app.py
```

## Custom configurations

Configuration files use the [TOML](https://toml.io/) format. A minimal
example:

```toml
identifier = "my_config"
events = 1000000
repetitions = 20
cores = 1
policy = "fifo"

arrival.distribution = "exponential"
service.distribution = "exponential"

[[class]]
cores = 1
arrival.prob = 1.0
service.mean = 1.0

[[pivot]]
arrival.rate = [0.1, 0.2, 0.3, 0.5, 0.7, 0.9]
```

The `[[class]]` sections define job classes with their resource
requirements and service characteristics. The `[[pivot]]` sections
define parameter sweeps: the simulator iterates over all listed values.
Full documentation of all supported fields is available in the
[online documentation](https://unive-neds-lab.github.io/mjqm-simulator/user-guide/running).

Mount your own config file into the `Inputs/` directory:

```sh
docker run --rm \
    -v "$(pwd)/my_config.toml:/app/Inputs/my_config.toml" \
    -v "$(pwd)/Results:/app/Results" \
    mjqm-simulator \
    ./simulator my_config
```

The simulator looks for configs in the `Inputs/` directory (inside the
Docker image) and appends `.toml` automatically. The same configs are
also available in the `configs/` directory of the artifact zip for
reference and editing.

## Bundled experiment configs

The image ships with several configs in `Inputs/`:

- `validation_mm1` — M/M/1 validation (~30 s)
- `tools_B_pol` — Google Borg Cell B, multiple scheduling policies
- `tools_B_dist` — Google Borg Cell B, multiple service distributions
- `tools_oneOrT` — one-or-T configuration for Matrix Geometric validation
- `tools_five_bpar` — 5-class system with Bounded Pareto service times
- `tools_five_exp` — 5-class system with Exponential service times

## Building from source

The artifact includes the full source code in the `src/` directory.

### Native build

Requirements: CMake >= 3.16, GCC >= 10 (with C++20 support), Boost >= 1.71.
External libraries (toml++ and RngStreams) are fetched automatically by
CMake during configuration.

```sh
cd src
cmake -DCMAKE_BUILD_TYPE=Release -S . -B build
cmake --build build --target simulator -j
```

The compiled binary is placed in `build/simulator`. On Linux/macOS, the
included `./configure` script wraps these commands with sensible defaults.

### Docker image build

From the artifact root directory:

```sh
docker build -t mjqm-simulator .
```

The source code is also available on [GitHub](https://github.com/unive-neds-lab/mjqm-simulator).
