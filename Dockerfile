# syntax=docker/dockerfile:1

# Build stage — compile the simulator with static linking
FROM gcc:15 AS builder

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends cmake libboost-all-dev

WORKDIR /build
COPY CMakeLists.txt CMakePresets.json ./
COPY libs/ ./libs/
COPY simulator.cpp toml_loader_test.cpp ./

RUN cmake -DCMAKE_BUILD_TYPE=Release \
          -DCOMPILE_NATIVE=OFF \
          -DBUILD_SHARED_LIBS=OFF \
          -DCMAKE_CXX_COMPILER=g++ \
          -S . -B build && \
    cmake --build build --target simulator -j "$(nproc)"


# Runtime stage — slim image with simulator + Python tooling
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

COPY --from=builder /build/build/simulator ./
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --no-dev --link-mode=copy

COPY scripts/ ./scripts/
COPY Inputs/ ./Inputs/
COPY docker-README.md ./README.md
COPY run-examples.sh ./

RUN mkdir -p Results && chmod +x run-examples.sh

ENV DASH_HOST=0.0.0.0
EXPOSE 8050
CMD ["cat", "README.md"]
