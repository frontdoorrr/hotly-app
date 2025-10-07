#!/bin/bash

# Hotly App - iOS Build Script
# Usage: ./scripts/build-ios.sh [dev|staging|prod] [debug|release]

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
echo "Hotly iOS Build Script"
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
if [ ! -f "ios/Runner/GoogleService-Info.plist" ]; then
    echo -e "${RED}Warning: GoogleService-Info.plist not found!${NC}"
    echo -e "${YELLOW}Please download from Firebase Console and place in ios/Runner/${NC}"
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

# Install CocoaPods
echo -e "${GREEN}Installing iOS dependencies (CocoaPods)...${NC}"
cd ios
pod install --repo-update
cd ..

# Run code generation
echo -e "${GREEN}Running code generation...${NC}"
flutter pub run build_runner build --delete-conflicting-outputs

# Build IPA
if [ "$BUILD_TYPE" == "release" ]; then
    echo -e "${GREEN}Building release IPA...${NC}"
    flutter build ipa \
        --release \
        --flavor $ENVIRONMENT \
        --dart-define-from-file=$ENV_FILE \
        --obfuscate \
        --split-debug-info=build/ios/symbols

    echo -e "${GREEN}======================================"
    echo "Build complete!"
    echo -e "IPA: ${YELLOW}build/ios/ipa/*.ipa${NC}"
    echo -e "Archive: ${YELLOW}build/ios/archive/Runner.xcarchive${NC}"
    echo -e "======================================${NC}"
    echo -e "${YELLOW}Note: Upload to App Store Connect using:${NC}"
    echo -e "  xcrun altool --upload-app --type ios --file build/ios/ipa/*.ipa --username YOUR_APPLE_ID --password YOUR_APP_SPECIFIC_PASSWORD"
else
    echo -e "${GREEN}Building debug app...${NC}"
    flutter build ios \
        --debug \
        --flavor $ENVIRONMENT \
        --dart-define-from-file=$ENV_FILE

    echo -e "${GREEN}======================================"
    echo "Build complete!"
    echo -e "App: ${YELLOW}build/ios/Debug-iphonesimulator/Runner.app${NC}"
    echo -e "======================================${NC}"
    echo -e "${YELLOW}Note: Install on simulator or device using:${NC}"
    echo -e "  flutter install"
fi
