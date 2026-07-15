#!/bin/bash
# Generate streams-manifest.json from the public/data/streams directory

STREAMS_DIR="public/data/streams"
MANIFEST_FILE="public/data/streams-manifest.json"

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
