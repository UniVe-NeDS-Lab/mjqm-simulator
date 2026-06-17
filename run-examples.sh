#!/usr/bin/env bash
set -e

echo "=== MJQM Simulator — Example Run ==="
echo ""
echo "Running M/M/1 validation experiment (5 repetitions)..."
./simulator validation_mm1 --repetitions 5
echo ""
echo "Done! Results written to Results/"
echo ""
echo "To explore results interactively, launch the web UI from the host:"
echo ""
echo "  docker run --rm -p 8050:8050 -v \$(pwd)/Results:/app/Results mjqm-simulator \\"
echo "      uv run --no-dev scripts/plotly_app.py"
echo ""
echo "  Then open http://localhost:8050"
