# MJQM Simulator — Docker Image

## Quick Start

**Note:** The examples below assume Docker is running on your local machine.
If you are running on a remote host, replace `localhost` with the host's address
and ensure the relevant ports are reachable.

### 1. Run a simulation

```sh
docker run --rm -v "$(pwd)/results:/app/Results" mjqm-simulator \
    ./simulator validation_mm1
```

Results are written to the mounted `results/` directory on the host.

Or run the bundled example (shorter, 5 repetitions):

```sh
docker run --rm -v "$(pwd)/results:/app/Results" mjqm-simulator \
    ./run-examples.sh
```

### 2. Explore results with the web UI

```sh
docker run --rm -p 8050:8050 -v "$(pwd)/results:/app/Results" mjqm-simulator \
    uv run --no-dev scripts/plotly_app.py
```

Open http://localhost:8050 in your browser.

## Overriding Parameters

Any TOML parameter can be overridden from the command line:

```sh
docker run --rm -v "$(pwd)/results:/app/Results" mjqm-simulator \
    ./simulator validation_mm1 --arrival.lambda 0.5
```

## Custom Configurations

Mount your own TOML config file into the `Inputs/` directory:

```sh
docker run --rm \
    -v "$(pwd)/my_config.toml:/app/Inputs/my_config.toml" \
    -v "$(pwd)/results:/app/Results" \
    mjqm-simulator ./simulator my_config
```

The simulator looks for configs in the `Inputs/` directory and appends `.toml` automatically.

## Bundled Experiment Configs

- `validation_mm1` — M/M/1 validation (quick, ~1 min)
- `cellA_Sorted_4096` — Google Borg Cell A workload, 29 job classes, 9 policies, 39 arrival rates (long run)

## Environment Variables

The web UI (`plotly_app.py`) supports:

- `DASH_HOST` — bind address (default: `0.0.0.0`)
- `DASH_PORT` — port (default: `8050`)
- `DASH_DEBUG` — enable debug mode (default: `false`)
