#!/usr/bin/env bash
set -euo pipefail

# new-resource.sh — scaffold a new data resource skeleton
#
# Creates resources/<identifier>/ from the template at
# examples/templates/resource/, substituting template variables.
#
# This script does NOT register the resource with FERRY.
# After reviewing and populating the skeleton, run:
#
#   make register-resources
#
# Usage: ./scripts/new-resource.sh <identifier> <name> <provider>
#
#   identifier  — stable institutional ID (e.g. "uk-biobank-serum")
#   name        — display name (e.g. "UK Biobank Serum Biomarkers")
#   provider    — one of: csv, duckdb, postgres, excel, parquet

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE_DIR="$REPO_ROOT/examples/templates/resource"
RESOURCES_DIR="$REPO_ROOT/resources"

if [ $# -lt 3 ]; then
    echo "Usage: $0 <identifier> <name> <provider>"
    echo ""
    echo "  identifier  — stable institutional ID (e.g. uk-biobank-serum)"
    echo "  name        — display name (e.g. UK Biobank Serum Biomarkers)"
    echo "  provider    — one of: csv, duckdb, postgres, excel, parquet"
    echo ""
    echo "Example:"
    echo "  $0 uk-biobank-serum \"UK Biobank Serum Biomarkers\" csv"
    exit 1
fi

ID="$1"
NAME="$2"
PROVIDER="$3"
ALIAS="${4:-$ID}"

if [ ! -d "$TEMPLATE_DIR" ]; then
    echo "ERROR: Template directory not found at $TEMPLATE_DIR"
    exit 1
fi

TARGET_DIR="$RESOURCES_DIR/$ID"
if [ -d "$TARGET_DIR" ]; then
    echo "ERROR: Resource directory already exists: $TARGET_DIR"
    exit 1
fi

echo "Creating resource skeleton at $TARGET_DIR ..."
mkdir -p "$TARGET_DIR/data" "$TARGET_DIR/representative"

for template in "$TEMPLATE_DIR"/* "$TEMPLATE_DIR"/data/.gitkeep "$TEMPLATE_DIR"/representative/.gitkeep; do
    rel="${template#$TEMPLATE_DIR/}"
    target="$TARGET_DIR/$rel"

    if [ -f "$template" ]; then
        case "$rel" in
            .gitkeep)
                touch "$target"
                ;;
            *)
                sed -e "s/{{ID}}/$ID/g" \
                    -e "s/{{NAME}}/$NAME/g" \
                    -e "s/{{ALIAS}}/$ALIAS/g" \
                    -e "s/{{PROVIDER}}/$PROVIDER/g" \
                    "$template" > "$target"
                echo "  created: resources/$ID/$rel"
                ;;
        esac
    fi
done

echo ""
echo "Resource skeleton created at resources/$ID/"
echo ""
echo "Next steps:"
echo "  1. Place data files in resources/$ID/data/"
echo "  2. Review and edit the manifest: resources/$ID/manifest.yaml"
echo "  3. Add representative data to resources/$ID/representative/"
echo "  4. Edit documentation: resources/$ID/SCHEMA.md, DOCUMENTATION.md"
echo "  5. Register with FERRY: make register-resources"
echo ""
