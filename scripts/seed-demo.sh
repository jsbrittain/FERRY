#!/usr/bin/env bash

# seed-demo.sh — print evaluation welcome message and pointer to Quick Start
#
# Prerequisite: seed-personas.sh must have completed (accounts exist).
# This script does not manipulate platform state. It prints guidance only.
# It is owned by the evaluation layer (make seed-demo), not the installation layer.

echo ""
echo "=== FERRY Demo ==="
echo ""
echo "Evaluation accounts:"
echo "  Maintainer  maintainer@ferry.local  / maintainer"
echo "  Researcher  researcher@ferry.local  / researcher"
echo "  Moderator   moderator@ferry.local   / moderator"
echo ""
echo "Institutional publications:"
echo "  - Demonstration Surveillance Dataset"
echo "  - Example Analysis (Demonstration Surveillance Summary)"
echo ""
echo "Quick Start:  docs/quickstart.md"
echo ""
echo "Next steps:"
echo "  1. Open https://localhost/ and accept the self-signed certificate"
echo "  2. Log in as researcher@ferry.local / researcher"
echo "  3. Follow the Quick Start tutorial at docs/quickstart.md"
echo ""
echo "Platform terms will be presented at first login."
echo "================================"
