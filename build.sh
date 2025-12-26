#!/bin/bash

# Színek
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Konfiguráció
IMAGE_NAME="speech-service"
VERSION=$(cat VERSION)

echo -e "${BLUE}Building ${IMAGE_NAME} version ${VERSION}...${NC}"

# Segédfüggvény a buildeléshez és tageléshez
build_and_tag() {
    local variant=$1
    local dockerfile=$2
    local platform_arg=$3

    echo -e "${GREEN}Building [${variant}] image...${NC}"
    
    # Build parancs összeállítása
    cmd="docker build"
    if [ -n "$platform_arg" ]; then
        cmd="$cmd --platform $platform_arg"
    fi
    
    # Tagek: variant-verzió és variant-latest
    tag_ver="${IMAGE_NAME}:${variant}-${VERSION}"
    tag_latest="${IMAGE_NAME}:${variant}-latest"
    
    cmd="$cmd -f $dockerfile -t $tag_ver -t $tag_latest ."
    
    echo -e "Executing: $cmd"
    eval $cmd
}

# 1. GPU Build (x86_64)
build_and_tag "gpu" "Dockerfile.gpu" ""

# 2. CPU Build (x86_64)
build_and_tag "cpu" "Dockerfile.cpu" ""

# 3. ARM Build (linux/arm64)
# Megjegyzés: Cross-compilation x86 gépen
build_and_tag "arm" "Dockerfile.arm" "linux/arm64"

echo -e "${BLUE}---------------------------------------${NC}"
echo -e "${BLUE}Build Complete! Images created:${NC}"
docker images | grep "${IMAGE_NAME}" | head -n 10
