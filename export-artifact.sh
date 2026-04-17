#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

OUTDIR="docker-artifact"
IMAGE="mjqm-simulator"

echo "=== MJQM Simulator — Docker Artifact Export ==="
echo ""

# Ensure buildx builder exists
docker buildx inspect mjqm-builder >/dev/null 2>&1 || \
    docker buildx create --name mjqm-builder
docker buildx use mjqm-builder
docker buildx inspect --bootstrap >/dev/null 2>&1

# Prepare output directory
rm -rf "${OUTDIR}"
mkdir -p "${OUTDIR}/configs"
mkdir -p "${OUTDIR}/results"
mkdir -p "${OUTDIR}/results/prerun/"
mkdir -p "${OUTDIR}/results/prerun/tools_B_pol"
mkdir -p "${OUTDIR}/results/prerun/tools_B_dist"
mkdir -p "${OUTDIR}/scripts"
mkdir -p "${OUTDIR}/scripts/mg"
mkdir -p "${OUTDIR}/scripts/sre"


# Build multi-arch OCI image
echo "Building linux/amd64 + linux/arm64..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -o "type=oci,dest=${OUTDIR}/${IMAGE}.tar" \
    .

# Bundle configs and docs
cp Inputs/tools_B_pol.toml "${OUTDIR}/configs/"
cp Inputs/tools_B_dist.toml "${OUTDIR}/configs/"
cp Inputs/tools_oneOrT.toml "${OUTDIR}/configs/"
cp Inputs/tools_five_bpar.toml "${OUTDIR}/configs/"
cp Inputs/tools_five_exp.toml "${OUTDIR}/configs/"
cp docker-prerun/results/tools_B_dist/*.csv "${OUTDIR}/results/prerun/tools_B_dist/"
cp docker-prerun/results/tools_B_pol/*.csv "${OUTDIR}/results/prerun/tools_B_pol/"
cp docker-prerun/scripts/*.py mkdir "${OUTDIR}/scripts/"
cp docker-prerun/scripts/mg/*.csv "${OUTDIR}/scripts/mg/"
cp docker-prerun/scripts/sre/*.csv "${OUTDIR}/scripts/sre/"

#[ -f Inputs/cellA_Sorted_4096.toml ] && \
#    cp Inputs/cellA_Sorted_4096.toml "${OUTDIR}/configs/"
cp docker-README.md "${OUTDIR}/README.md"

# Extract image ID from the OCI archive
IMAGE_ID=$(tar -xf "${OUTDIR}/${IMAGE}.tar" -O index.json \
    | grep -o '"sha256:[a-f0-9]*"' | head -1 | tr -d '"')

# Create INSTRUCTIONS.md
cat > "${OUTDIR}/INSTRUCTIONS.md" <<'INSTR'
# Loading and Running the MJQM Simulator

## Prerequisites

You need [Docker Desktop](https://www.docker.com/products/docker-desktop/)
installed on your machine (available for Linux, macOS, and Windows).

## 1. Load the Docker image

```sh
docker load -i mjqm-simulator.tar.gz
docker tag IMAGE_ID_PLACEHOLDER mjqm-simulator
```

The image supports both Intel/AMD and Apple Silicon/ARM machines.
Docker will automatically use the right version for your system.

> **Note:** The examples below assume Docker is running on your local machine.
> If you are running on a remote server, replace `localhost` with the server's
> address and make sure the relevant ports are accessible.
>
> **Windows users:** Replace `$(pwd)` with `%cd%` in Command Prompt,
> or `${PWD}` in PowerShell.

## 2. Run a simulation

```sh
docker run --rm --cpus=2 \
    -v "$(pwd)/results:/app/Results" \
    mjqm-simulator \
    ./simulator validation_mm1 --repetitions 5
```

Results are written to the `results/` directory on the host.

## 3. Explore results with the web UI

Once a simulation has produced results, you can visualise them interactively:

```sh
docker run --rm --cpus=2 -p 8050:8050 \
    -v "$(pwd)/results:/app/Results" \
    mjqm-simulator \
    uv run --no-dev scripts/plotly_app.py
```

Open http://localhost:8050 in your browser.

## 4. Custom configurations

Example configs are in the `configs/` directory. Mount one into the container:

```sh
docker run --rm --cpus=2 \
    -v "$(pwd)/configs/cellA_Sorted_4096.toml:/app/Inputs/cellA_Sorted_4096.toml" \
    -v "$(pwd)/results:/app/Results" \
    mjqm-simulator \
    ./simulator cellA_Sorted_4096
```

## 5. Override parameters

Any TOML parameter can be overridden from the command line:

```sh
docker run --rm --cpus=2 \
    -v "$(pwd)/results:/app/Results" \
    mjqm-simulator \
    ./simulator validation_mm1 --arrival.lambda 0.5 --repetitions 10
```
INSTR

# Embed the actual image ID
sed -i '' "s|IMAGE_ID_PLACEHOLDER|${IMAGE_ID}|" "${OUTDIR}/INSTRUCTIONS.md"

# Compress the image
echo ""
echo "Compressing image..."
gzip "${OUTDIR}/${IMAGE}.tar"

# Package
ZIPNAME="${IMAGE}-docker-$(date +%Y%m%d).zip"
(cd "${OUTDIR}" && zip -0 -r "../${ZIPNAME}" .)

echo ""
echo "Done! Artifact: ${ZIPNAME}"
echo ""
echo "Contents:"
ls -lh "${OUTDIR}/"
echo ""
echo "Total zip size: $(du -h "${ZIPNAME}" | cut -f1)"
