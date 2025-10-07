#!/bin/bash

# Hotly App - Android Build Script
# Usage: ./scripts/build-android.sh [dev|staging|prod] [debug|release]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-dev}
BUILD_TYPE=${2:-debug}

echo -e "${GREEN}======================================"
echo "Hotly Android Build Script"
echo "Environment: $ENVIRONMENT"
echo "Build Type: $BUILD_TYPE"
echo -e "======================================${NC}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo -e "${RED}Error: Invalid environment. Use dev, staging, or prod${NC}"
    exit 1
fi

# Validate build type
if [[ ! "$BUILD_TYPE" =~ ^(debug|release)$ ]]; then
    echo -e "${RED}Error: Invalid build type. Use debug or release${NC}"
    exit 1
fi

# Set environment file
ENV_FILE=".env.$ENVIRONMENT"
if [ "$ENVIRONMENT" == "dev" ]; then
    ENV_FILE=".env.dev"
fi

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: Environment file $ENV_FILE not found${NC}"
    exit 1
fi

echo -e "${YELLOW}Using environment file: $ENV_FILE${NC}"

# Check for Firebase config
if [ ! -f "android/app/google-services.json" ]; then
    echo -e "${RED}Warning: google-services.json not found!${NC}"
    echo -e "${YELLOW}Please download from Firebase Console and place in android/app/${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Clean previous builds
echo -e "${GREEN}Cleaning previous builds...${NC}"
flutter clean

# Get dependencies
echo -e "${GREEN}Getting dependencies...${NC}"
flutter pub get

# Run code generation
echo -e "${GREEN}Running code generation...${NC}"
flutter pub run build_runner build --delete-conflicting-outputs

# Build APK/AAB
if [ "$BUILD_TYPE" == "release" ]; then
    echo -e "${GREEN}Building release AAB (App Bundle)...${NC}"
    flutter build appbundle \
        --release \
        --flavor $ENVIRONMENT \
        --dart-define-from-file=$ENV_FILE \
        --obfuscate \
        --split-debug-info=build/app/outputs/symbols

    echo -e "${GREEN}Building release APK...${NC}"
    flutter build apk \
        --release \
        --flavor $ENVIRONMENT \
        --dart-define-from-file=$ENV_FILE \
        --obfuscate \
        --split-debug-info=build/app/outputs/symbols
else
    echo -e "${GREEN}Building debug APK...${NC}"
    flutter build apk \
        --debug \
        --flavor $ENVIRONMENT \
        --dart-define-from-file=$ENV_FILE
fi

# Output location
echo -e "${GREEN}======================================"
echo "Build complete!"
if [ "$BUILD_TYPE" == "release" ]; then
    echo -e "AAB: ${YELLOW}build/app/outputs/bundle/${ENVIRONMENT}Release/app-${ENVIRONMENT}-release.aab${NC}"
    echo -e "APK: ${YELLOW}build/app/outputs/apk/${ENVIRONMENT}/release/app-${ENVIRONMENT}-release.apk${NC}"
else
    echo -e "APK: ${YELLOW}build/app/outputs/apk/${ENVIRONMENT}/debug/app-${ENVIRONMENT}-debug.apk${NC}"
fi
echo -e "======================================${NC}"
