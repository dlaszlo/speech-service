#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

IMAGE_NAME="speech-service"
VERSION=$(cat VERSION)

echo -e "${BLUE}Building ${IMAGE_NAME} version ${VERSION}...${NC}"

build_and_tag() {
    local variant=$1
    local dockerfile=$2
    local platform_arg=$3

    echo -e "${GREEN}Building [${variant}] image...${NC}"

    cmd="docker build"
    if [ -n "$platform_arg" ]; then
        cmd="$cmd --platform $platform_arg"
    fi

    tag_ver="${IMAGE_NAME}:${variant}-${VERSION}"
    tag_latest="${IMAGE_NAME}:${variant}-latest"

    cmd="$cmd -f $dockerfile -t $tag_ver -t $tag_latest ."

    echo -e "Executing: $cmd"
    eval $cmd
}

build_and_tag "gpu" "Dockerfile.gpu" ""
build_and_tag "cpu" "Dockerfile.cpu" ""

echo -e "${BLUE}Setting up QEMU for ARM cross-compilation...${NC}"
docker run --privileged --rm tonistiigi/binfmt --install all

build_and_tag "arm" "Dockerfile.arm" "linux/arm64"

echo -e "${BLUE}---------------------------------------${NC}"
echo -e "${BLUE}Build Complete! Images created:${NC}"
docker images | grep "${IMAGE_NAME}" | head -n 10
