#!/bin/bash
# Generate streams-manifest.json from the public/data/streams directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STREAMS_DIR="tim-tams-viewer/public/data/streams"
MANIFEST_FILE="tim-tams-viewer/public/data/streams-manifest.json"

# Run json_convert_timestamps.py first
echo "Running json_convert_timestamps.py..."
python3 "$SCRIPT_DIR/json_convert_timestamps.py"
if [ $? -ne 0 ]; then
  echo "Error: json_convert_timestamps.py failed"
  exit 1
fi

# Run update_tracks_stats.py next
echo "Running update_tracks_stats.py..."
python3 "$SCRIPT_DIR/update_tracks_stats.py"
if [ $? -ne 0 ]; then
  echo "Error: update_tracks_stats.py failed"
  exit 1
fi

if [ ! -d "$STREAMS_DIR" ]; then
  echo "Error: $STREAMS_DIR directory not found"
  exit 1
fi

# Generate JSON array of filenames, sorted
files=($(ls "$STREAMS_DIR"/*.json 2>/dev/null | xargs -n1 basename | sort))

# Write as JSON array
echo "[" > "$MANIFEST_FILE"
for i in "${!files[@]}"; do
  if [ $i -lt $((${#files[@]} - 1)) ]; then
    echo "  \"${files[$i]}\"," >> "$MANIFEST_FILE"
  else
    echo "  \"${files[$i]}\"" >> "$MANIFEST_FILE"
  fi
done
echo "]" >> "$MANIFEST_FILE"

echo "Generated manifest with ${#files[@]} files"

# Ask if the user wants to deploy to GitHub
read -r -p "Upload to GitHub? [y/N] " response
if [[ "$response" =~ ^[Yy]$ ]]; then
  echo "Deploying to GitHub..."
  npm run deploy --prefix tim-tams-viewer
fi