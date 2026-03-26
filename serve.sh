#!/bin/bash
# Simple dev server for the roadtrip visualization
cd "$(dirname "$0")"
echo "Serving at http://localhost:8090"
python3 -m http.server 8090
