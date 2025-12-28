#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

REGISTRY="dlaszlo/speech-service"
VERSION=$(cat VERSION)

echo -e "${BLUE}Pushing ${REGISTRY} version ${VERSION}...${NC}"

# Ensure we are logged in
docker login

# --- Helper Function ---
push_image() {
    local tag=$1
    echo -e "Pushing ${tag}..."
    docker push "${tag}"
}

# --- 1. Push Base Images ---

echo -e "${BLUE}Pushing CPU variants...${NC}"
push_image "${REGISTRY}:cpu-amd64-${VERSION}"
push_image "${REGISTRY}:cpu-amd64-latest"
push_image "${REGISTRY}:cpu-arm64-${VERSION}"
push_image "${REGISTRY}:cpu-arm64-latest"

echo -e "${BLUE}Pushing GPU variant...${NC}"
push_image "${REGISTRY}:gpu-${VERSION}"
push_image "${REGISTRY}:gpu-latest"


# --- 2. Create and Push Manifests (CPU only) ---

create_push_manifest() {
    local target_tag=$1
    local src_amd64=$2
    local src_arm64=$3

    echo -e "${BLUE}Creating manifest for ${target_tag}...${NC}"
    
    # Create the manifest
    docker manifest rm "${target_tag}" 2>/dev/null || true
    docker manifest create "${target_tag}" \
        "${src_amd64}" \
        "${src_arm64}"

    # Annotate explicitly (good practice)
    # This tells Docker explicitly that cpu-arm64 is for arm64
    docker manifest annotate "${target_tag}" "${src_arm64}" --os linux --arch arm64
    docker manifest annotate "${target_tag}" "${src_amd64}" --os linux --arch amd64

    # Push the manifest
    echo -e "Pushing manifest ${target_tag}..."
    docker manifest push "${target_tag}"
    echo -e "${GREEN}✓ Manifest ${target_tag} pushed.${NC}"
}

echo -e "${BLUE}Processing CPU Multi-arch Manifests...${NC}"

# Create/Push :cpu-VERSION
create_push_manifest \
    "${REGISTRY}:cpu-${VERSION}" \
    "${REGISTRY}:cpu-amd64-${VERSION}" \
    "${REGISTRY}:cpu-arm64-${VERSION}"

# Create/Push :cpu-latest
create_push_manifest \
    "${REGISTRY}:cpu-latest" \
    "${REGISTRY}:cpu-amd64-latest" \
    "${REGISTRY}:cpu-arm64-latest"

echo -e "${BLUE}---------------------------------------${NC}"
echo -e "${BLUE}Push complete!${NC}"
echo -e "${GREEN}Usage:${NC}"
echo "  CPU (Multi-arch): docker pull ${REGISTRY}:cpu-${VERSION}"
echo "  GPU (AMD64 Only): docker pull ${REGISTRY}:gpu-${VERSION}"