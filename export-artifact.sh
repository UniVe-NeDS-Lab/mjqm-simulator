#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

TAG="${1:-latest}"
OUTDIR="docker-artifact"
IMAGE="mjqm-simulator"

echo "=== MJQM Simulator — Docker Artifact Export ==="
echo "Tag: ${TAG}"
echo ""

# Ensure buildx builder exists
docker buildx inspect mjqm-builder >/dev/null 2>&1 || \
    docker buildx create --name mjqm-builder
docker buildx use mjqm-builder
docker buildx inspect --bootstrap >/dev/null 2>&1

# Build both architectures
echo "Building linux/amd64..."
docker buildx build --platform linux/amd64 -t "${IMAGE}:amd64" --load .

echo ""
echo "Building linux/arm64..."
docker buildx build --platform linux/arm64 -t "${IMAGE}:arm64" --load .

# Prepare output directory
rm -rf "${OUTDIR}"
mkdir -p "${OUTDIR}/configs"

# Export images
echo ""
echo "Exporting images..."
docker save "${IMAGE}:amd64" | gzip > "${OUTDIR}/${IMAGE}-amd64.tar.gz"
docker save "${IMAGE}:arm64" | gzip > "${OUTDIR}/${IMAGE}-arm64.tar.gz"

# Bundle configs and docs
cp Inputs/validation_mm1.toml "${OUTDIR}/configs/"
[ -f Inputs/cellA_Sorted_4096.toml ] && \
    cp Inputs/cellA_Sorted_4096.toml "${OUTDIR}/configs/"
cp docker-README.md "${OUTDIR}/README.md"

# Create INSTRUCTIONS.md
cat > "${OUTDIR}/INSTRUCTIONS.md" <<'INSTR'
# Loading and Running the MJQM Simulator

## 1. Load the Docker image

Pick the image matching your architecture:

```sh
# Intel/AMD — most Windows PCs, Linux servers, older Macs
docker load < mjqm-simulator-amd64.tar.gz

# ARM — Apple Silicon Macs, Windows on ARM (e.g. Surface Pro X), ARM servers
docker load < mjqm-simulator-arm64.tar.gz
```

**Note:** The examples below assume Docker is running on your local machine.
If you are running on a remote host, replace `localhost` with the host's address
and ensure the relevant ports are reachable.

## 2. Run a simulation

If you use Linux or similar machines
```sh
docker run --rm -v "$(pwd)/results:/app/Results" mjqm-simulator:amd64 \
    ./simulator validation_mm1 --repetitions 5
```

or if you use Apple/ARM machines
```sh
docker run --rm -v "$(pwd)/results:/app/Results" mjqm-simulator:arm64 \
    ./simulator validation_mm1 --repetitions 5
```

Results are written to the `results/` directory on the host.

## 3. Explore results with the web UI

```sh
docker run --rm -p 8050:8050 -v "$(pwd)/results:/app/Results" mjqm-simulator:amd64 \
    uv run --no-dev scripts/plotly_app.py
```

Open http://localhost:8050 in your browser.

## 4. Custom configurations

Example configs are in the `configs/` directory. Mount one into the container:

```sh
docker run --rm \
    -v "$(pwd)/configs/cellA_Sorted_4096.toml:/app/Inputs/cellA_Sorted_4096.toml" \
    -v "$(pwd)/results:/app/Results" \
    mjqm-simulator:amd64 ./simulator cellA_Sorted_4096
```

## 5. Override parameters

Any TOML parameter can be overridden from the command line:

```sh
docker run --rm -v "$(pwd)/results:/app/Results" mjqm-simulator:amd64 \
    ./simulator validation_mm1 --arrival.lambda 0.5 --repetitions 10
```
INSTR

# Package
ZIPNAME="${IMAGE}-docker-$(date +%Y%m%d).zip"
(cd "${OUTDIR}" && zip -r "../${ZIPNAME}" .)

echo ""
echo "Done! Artifact: ${ZIPNAME}"
echo ""
echo "Contents:"
ls -lh "${OUTDIR}/"
echo ""
echo "Total zip size: $(du -h "${ZIPNAME}" | cut -f1)"
