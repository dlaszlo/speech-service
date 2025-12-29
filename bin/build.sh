#!/bin/bash

REGISTRY="dlaszlo/speech-service"
VERSION=$(cat VERSION)

echo "Building images version ${VERSION}..."

# Setup buildx just in case (needed for --platform with --load sometimes, or for caching optimization)
docker buildx create --use --name speech-builder 2>/dev/null || docker buildx use speech-builder

# --- CPU Builds ---

# 1. CPU AMD64 (using Dockerfile.cpu)
echo "Building CPU AMD64 variant (Dockerfile.cpu)..."
docker buildx build \
    --platform linux/amd64 \
    --load \
    -f Dockerfile.cpu \
    -t "${REGISTRY}:cpu-amd64-${VERSION}" \
    -t "${REGISTRY}:cpu-amd64-latest" \
    .
echo "[OK] CPU AMD64 built."

# 2. CPU ARM64 (using Dockerfile.arm)
echo "Building CPU ARM64 variant (Dockerfile.arm)..."
docker buildx build \
    --platform linux/arm64 \
    --load \
    -f Dockerfile.arm \
    -t "${REGISTRY}:cpu-arm64-${VERSION}" \
    -t "${REGISTRY}:cpu-arm64-latest" \
    .
echo "[OK] CPU ARM64 built."

# --- GPU Build ---

# 3. GPU AMD64 (using Dockerfile.gpu)
echo "Building GPU variant (Dockerfile.gpu)..."
docker buildx build \
    --platform linux/amd64 \
    --load \
    -f Dockerfile.gpu \
    -t "${REGISTRY}:gpu-${VERSION}" \
    -t "${REGISTRY}:gpu-latest" \
    .
echo "[OK] GPU built."

echo "---------------------------------------"
echo "Build complete! Images are loaded into your local Docker daemon."
echo "Run ./bin/push.sh to push images and manifests to Docker Hub."