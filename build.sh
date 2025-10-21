#!/bin/bash

# Exit on error
set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create build directory
mkdir -p build

# Navigate to build directory
cd build

# Configure with CMake
echo "Configuring project..."
cmake ..

# Build
echo "Building project..."
cmake --build . -j$(sysctl -n hw.ncpu)

echo "Build complete!"
echo "Output files:"
ls -lh *.so *.dylib 2>/dev/null || echo "No shared libraries found"

# Return to project root and run test
cd "$SCRIPT_DIR"
echo "\nRunning test_ssynth.py..."
python test_ssynth.py