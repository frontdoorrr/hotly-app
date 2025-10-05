#!/bin/bash
# ==============================================================================
# Docker Build Script for hotly-app
# ==============================================================================
# This script builds optimized Docker images for different environments
# ==============================================================================

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
DOCKERFILE="Dockerfile.optimized"
IMAGE_NAME="hotly-app"
TARGET="runtime"
VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "latest")

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dev|--development)
            TARGET="development"
            shift
            ;;
        --prod|--production)
            TARGET="runtime"
            shift
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --tag)
            IMAGE_NAME="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dev, --development     Build development image"
            echo "  --prod, --production     Build production image (default)"
            echo "  --version VERSION        Set image version tag (default: git tag or 'latest')"
            echo "  --tag NAME               Set custom image name (default: 'hotly-app')"
            echo "  --help                   Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}===============================================================================${NC}"
echo -e "${GREEN}Building Docker Image for hotly-app${NC}"
echo -e "${GREEN}===============================================================================${NC}"
echo -e "Target:      ${YELLOW}$TARGET${NC}"
echo -e "Image:       ${YELLOW}$IMAGE_NAME:$VERSION${NC}"
echo -e "Dockerfile:  ${YELLOW}$DOCKERFILE${NC}"
echo -e "${GREEN}===============================================================================${NC}"
echo ""

# Build the Docker image
echo -e "${GREEN}▶ Building Docker image...${NC}"
docker build \
    --file "$DOCKERFILE" \
    --target "$TARGET" \
    --tag "$IMAGE_NAME:$VERSION" \
    --tag "$IMAGE_NAME:latest" \
    --progress=plain \
    .

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}===============================================================================${NC}"
    echo -e "${GREEN}✓ Build successful!${NC}"
    echo -e "${GREEN}===============================================================================${NC}"
    echo -e "Image: ${GREEN}$IMAGE_NAME:$VERSION${NC}"
    echo -e "Also tagged as: ${GREEN}$IMAGE_NAME:latest${NC}"
    echo ""
    echo -e "${YELLOW}Image size:${NC}"
    docker images "$IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    if [ "$TARGET" == "development" ]; then
        echo -e "  docker run -p 8000:8000 $IMAGE_NAME:$VERSION"
    else
        echo -e "  docker-compose -f docker-compose.prod.yml up -d"
    fi
else
    echo -e "${RED}✗ Build failed!${NC}"
    exit 1
fi
