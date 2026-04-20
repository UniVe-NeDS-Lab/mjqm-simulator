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
mkdir -p "${OUTDIR}/src"


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
cp docker-prerun/custom/*.toml "${OUTDIR}/configs/"
cp docker-prerun/results/tools_B_dist/*.csv "${OUTDIR}/results/prerun/tools_B_dist/"
cp docker-prerun/results/tools_B_pol/*.csv "${OUTDIR}/results/prerun/tools_B_pol/"
cp docker-prerun/scripts/*.py "${OUTDIR}/scripts/"
cp docker-prerun/mg/*.csv "${OUTDIR}/scripts/mg/"
cp docker-prerun/sre/*.csv "${OUTDIR}/scripts/sre/"

# Bundle source code for native build
cp CMakeLists.txt CMakePresets.json configure rebuild simulator.cpp toml_loader_test.cpp "${OUTDIR}/src/"
cp -r libs/ "${OUTDIR}/src/libs/"
mkdir -p "${OUTDIR}/src/scripts"
cp scripts/select-g++.sh "${OUTDIR}/src/scripts/"

# Bundle files needed for Docker image build from artifact root
cp pyproject.toml uv.lock run-examples.sh "${OUTDIR}/"
cp scripts/*.py "${OUTDIR}/scripts/"

# Generate Dockerfile adjusted for artifact directory layout
sed \
    -e 's|COPY CMakeLists.txt CMakePresets.json \./|COPY src/CMakeLists.txt src/CMakePresets.json ./|' \
    -e 's|COPY libs/ \./libs/|COPY src/libs/ ./libs/|' \
    -e 's|COPY simulator.cpp toml_loader_test.cpp \./|COPY src/simulator.cpp src/toml_loader_test.cpp ./|' \
    -e 's|COPY Inputs/ \./Inputs/|COPY configs/ ./Inputs/|' \
    -e 's|COPY docker-prerun/results/ \./Results/prerun/|COPY results/prerun/ ./Results/prerun/|' \
    Dockerfile > "${OUTDIR}/Dockerfile"

# Generate .dockerignore for artifact layout
cat > "${OUTDIR}/.dockerignore" <<'DIGNORE'
mjqm-simulator.tar.gz
README.md
*.zip
.DS_Store
__pycache__/
DIGNORE

# Extract image ID from the OCI archive
IMAGE_ID=$(tar -xf "${OUTDIR}/${IMAGE}.tar" -O index.json \
    | grep -o '"sha256:[a-f0-9]*"' | head -1 | tr -d '"')

# Copy versioned instructions and patch in the image digest
sed -e '/<!-- artifact-only-begin -->/d' -e '/<!-- artifact-only-end -->/d' \
    -e "s|IMAGE_ID_PLACEHOLDER|${IMAGE_ID}|" \
    INSTRUCTIONS.md > "${OUTDIR}/README.md"

# Compress the image
echo ""
echo "Compressing image..."
gzip "${OUTDIR}/${IMAGE}.tar"

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

# SHA-256 checksum
shasum -a 256 "${ZIPNAME}" | tee "${ZIPNAME}.sha256"
