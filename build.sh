#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

REGISTRY="dlaszlo/speech-service"
VERSION=$(cat VERSION)

echo -e "${BLUE}Building images version ${VERSION}...${NC}"

# Setup buildx just in case (needed for --platform with --load sometimes, or for caching optimization)
docker buildx create --use --name speech-builder 2>/dev/null || docker buildx use speech-builder

# --- CPU Builds ---

# 1. CPU AMD64 (using Dockerfile.cpu)
echo -e "${BLUE}Building CPU AMD64 variant (Dockerfile.cpu)...${NC}"
docker buildx build \
    --platform linux/amd64 \
    --load \
    -f Dockerfile.cpu \
    -t "${REGISTRY}:cpu-amd64-${VERSION}" \
    -t "${REGISTRY}:cpu-amd64-latest" \
    .
echo -e "${GREEN}✓ CPU AMD64 built.${NC}"

# 2. CPU ARM64 (using Dockerfile.arm)
echo -e "${BLUE}Building CPU ARM64 variant (Dockerfile.arm)...${NC}"
docker buildx build \
    --platform linux/arm64 \
    --load \
    -f Dockerfile.arm \
    -t "${REGISTRY}:cpu-arm64-${VERSION}" \
    -t "${REGISTRY}:cpu-arm64-latest" \
    .
echo -e "${GREEN}✓ CPU ARM64 built.${NC}"

# --- GPU Build ---

# 3. GPU AMD64 (using Dockerfile.gpu)
echo -e "${BLUE}Building GPU variant (Dockerfile.gpu)...${NC}"
docker buildx build \
    --platform linux/amd64 \
    --load \
    -f Dockerfile.gpu \
    -t "${REGISTRY}:gpu-${VERSION}" \
    -t "${REGISTRY}:gpu-latest" \
    .
echo -e "${GREEN}✓ GPU built.${NC}"

echo -e "${BLUE}---------------------------------------${NC}"
echo -e "${BLUE}Build complete! Images are loaded into your local Docker daemon.${NC}"
echo -e "${GREEN}Run ./push.sh to push images and manifests to Docker Hub.${NC}"