#!/bin/bash

IMAGE_NAME="speech-service"
VERSION=$(cat VERSION)
REGISTRY="gitea.max.lan/dlaszlo/speech-service"
VARIANTS=("gpu" "cpu" "arm")

echo "Logging in to registry..."
docker login gitea.max.lan

for variant in "${VARIANTS[@]}"; do
    LOCAL_TAG_VER="${IMAGE_NAME}:${variant}-${VERSION}"
    LOCAL_TAG_LATEST="${IMAGE_NAME}:${variant}-latest"

    if docker image inspect "$LOCAL_TAG_VER" >/dev/null 2>&1; then
        echo "--- Pushing: ${variant} ---"

        REMOTE_TAG_VER="${REGISTRY}:${variant}-${VERSION}"
        REMOTE_TAG_LATEST="${REGISTRY}:${variant}-latest"

        docker tag "$LOCAL_TAG_VER" "$REMOTE_TAG_VER"
        docker tag "$LOCAL_TAG_LATEST" "$REMOTE_TAG_LATEST"

        docker push "$REMOTE_TAG_VER"
        docker push "$REMOTE_TAG_LATEST"
    else
        echo "Info: ${LOCAL_TAG_VER} not found locally, skipping."
    fi
done

echo "Done!"
