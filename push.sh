#!/bin/bash

# Konfiguráció
IMAGE_NAME="speech-service"
VERSION=$(cat VERSION)
REGISTRY="gitea.max.lan/dlaszlo"
VARIANTS=("gpu" "cpu" "arm")

echo "Bejelentkezés a regisztridbe..."
docker login gitea.max.lan

for variant in "${VARIANTS[@]}"; do
    LOCAL_TAG_VER="${IMAGE_NAME}:${variant}-${VERSION}"
    LOCAL_TAG_LATEST="${IMAGE_NAME}:${variant}-latest"
    
    # Ellenőrizzük, hogy létezik-e a helyi image
    if docker image inspect "$LOCAL_TAG_VER" >/dev/null 2>&1; then
        echo "--- Pusholás: ${variant} ---"
        
        REMOTE_TAG_VER="${REGISTRY}/${IMAGE_NAME}:${variant}-${VERSION}"
        REMOTE_TAG_LATEST="${REGISTRY}/${IMAGE_NAME}:${variant}-latest"

        # Tagelés a távoli regisztrihez
        docker tag "$LOCAL_TAG_VER" "$REMOTE_TAG_VER"
        docker tag "$LOCAL_TAG_LATEST" "$REMOTE_TAG_LATEST"

        # Feltöltés (Push)
        docker push "$REMOTE_TAG_VER"
        docker push "$REMOTE_TAG_LATEST"
    else
        echo "Info: ${LOCAL_TAG_VER} nem található helyben, kihagyás."
    fi
done

echo "Kész!"
