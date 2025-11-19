#!/bin/bash
# Build script for MyCoder RocketChat Android App

set -e

echo "========================================="
echo "MyCoder RocketChat - Android Build Script"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
build_modern() {
    echo -e "${BLUE}Building Modern variant (Android 10+)...${NC}"
    ./gradlew assembleModernDebug
    echo -e "${GREEN}✓ Modern Debug built successfully${NC}"
    echo ""
}

build_legacy() {
    echo -e "${BLUE}Building Legacy variant (Android 4.4+)...${NC}"
    ./gradlew assembleLegacyDebug
    echo -e "${GREEN}✓ Legacy Debug built successfully${NC}"
    echo ""
}

build_release() {
    echo -e "${BLUE}Building Release variants...${NC}"
    ./gradlew assembleModernRelease assembleLegacyRelease
    echo -e "${GREEN}✓ Release builds completed${NC}"
    echo ""
}

install_modern() {
    echo -e "${BLUE}Installing Modern variant...${NC}"
    ./gradlew installModernDebug
    adb shell am start -n com.mycoder.rocketchat.debug/.ui.MainActivity
    echo -e "${GREEN}✓ Modern variant installed and launched${NC}"
    echo ""
}

install_legacy() {
    echo -e "${BLUE}Installing Legacy variant...${NC}"
    ./gradlew installLegacyDebug
    adb shell am start -n com.mycoder.rocketchat.debug/.ui.MainActivity
    echo -e "${GREEN}✓ Legacy variant installed and launched${NC}"
    echo ""
}

run_tests() {
    echo -e "${BLUE}Running tests...${NC}"
    ./gradlew testModernDebugUnitTest testLegacyDebugUnitTest
    echo -e "${GREEN}✓ Tests completed${NC}"
    echo ""
}

clean_build() {
    echo -e "${BLUE}Cleaning build...${NC}"
    ./gradlew clean
    echo -e "${GREEN}✓ Clean completed${NC}"
    echo ""
}

show_help() {
    echo "Usage: ./build.sh [OPTION]"
    echo ""
    echo "Options:"
    echo "  modern          Build modern variant (Android 10+)"
    echo "  legacy          Build legacy variant (Android 4.4+)"
    echo "  all             Build both variants"
    echo "  release         Build release variants"
    echo "  install-modern  Build and install modern variant"
    echo "  install-legacy  Build and install legacy variant"
    echo "  test            Run unit tests"
    echo "  clean           Clean build artifacts"
    echo "  help            Show this help message"
    echo ""
}

# Main
case "$1" in
    modern)
        build_modern
        ;;
    legacy)
        build_legacy
        ;;
    all)
        build_modern
        build_legacy
        ;;
    release)
        build_release
        ;;
    install-modern)
        build_modern
        install_modern
        ;;
    install-legacy)
        build_legacy
        install_legacy
        ;;
    test)
        run_tests
        ;;
    clean)
        clean_build
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo -e "${YELLOW}Unknown option: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac

echo -e "${GREEN}Done!${NC}"
