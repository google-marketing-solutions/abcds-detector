#!/bin/bash
# Quick test script for /api/evaluate_file endpoint

set -e

API_URL="${API_URL:-http://localhost:8080}"
VIDEO_FILE="${1:-}"

if [ -z "$VIDEO_FILE" ]; then
    echo "Usage: $0 <video_file.mp4>"
    echo ""
    echo "Example:"
    echo "  $0 my_video.mp4"
    echo ""
    echo "Environment variables:"
    echo "  API_URL - API base URL (default: http://localhost:8080)"
    exit 1
fi

if [ ! -f "$VIDEO_FILE" ]; then
    echo "❌ Error: Video file not found: $VIDEO_FILE"
    exit 1
fi

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         Testing /api/evaluate_file endpoint                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📹 Video: $VIDEO_FILE"
echo "🌐 API URL: $API_URL"
echo "⏱️  This will take several minutes..."
echo ""

# Create output directory
OUTPUT_DIR="test_output_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

# Make the request
echo "🚀 Sending request..."
RESPONSE_FILE="$OUTPUT_DIR/report.json"
HTTP_CODE=$(curl -w "%{http_code}" -o "$RESPONSE_FILE" \
    -X POST "$API_URL/api/evaluate_file" \
    -F "file=@$VIDEO_FILE" \
    -F "use_abcd=true" \
    -F "use_shorts=false" \
    -F "use_ci=true" \
    --progress-bar)

echo ""
echo "📥 HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✅ Success!"
    echo ""
    
    # Extract and display key metrics
    echo "═══════════════════════════════════════════════════════════════"
    echo "📊 REPORT SUMMARY"
    echo "═══════════════════════════════════════════════════════════════"
    
    # Use jq if available, otherwise use Python
    if command -v jq &> /dev/null; then
        echo ""
        echo "🏢 Brand: $(jq -r '.brand_name // "Unknown"' "$RESPONSE_FILE")"
        echo "🎬 Video: $(jq -r '.video_name // "Unknown"' "$RESPONSE_FILE")"
        echo "🆔 Report ID: $(jq -r '.report_id // "Unknown"' "$RESPONSE_FILE")"
        echo ""
        echo "📈 ABCD Score: $(jq -r '.abcd.score // 0' "$RESPONSE_FILE")%"
        echo "   Result: $(jq -r '.abcd.result // "Unknown"' "$RESPONSE_FILE")"
        echo "   Passed: $(jq -r '.abcd.passed // 0' "$RESPONSE_FILE")/$(jq -r '.abcd.total // 0' "$RESPONSE_FILE")"
        echo ""
        echo "🎯 Persuasion Density: $(jq -r '.persuasion.density // 0' "$RESPONSE_FILE")%"
        echo "   Detected: $(jq -r '.persuasion.detected // 0' "$RESPONSE_FILE")/$(jq -r '.persuasion.total // 0' "$RESPONSE_FILE")"
        echo ""
        echo "🎞️  Scenes: $(jq -r '.scenes | length' "$RESPONSE_FILE")"
        echo "   With keyframes: $(jq -r '[.scenes[] | select(.keyframe != "")] | length' "$RESPONSE_FILE")"
    else
        echo ""
        python3 << EOF
import json
with open('$RESPONSE_FILE', 'r') as f:
    report = json.load(f)

print(f"🏢 Brand: {report.get('brand_name', 'Unknown')}")
print(f"🎬 Video: {report.get('video_name', 'Unknown')}")
print(f"🆔 Report ID: {report.get('report_id', 'Unknown')}")
print()
if 'abcd' in report:
    abcd = report['abcd']
    print(f"📈 ABCD Score: {abcd.get('score', 0)}%")
    print(f"   Result: {abcd.get('result', 'Unknown')}")
    print(f"   Passed: {abcd.get('passed', 0)}/{abcd.get('total', 0)}")
print()
if 'persuasion' in report:
    pers = report['persuasion']
    print(f"🎯 Persuasion Density: {pers.get('density', 0)}%")
    print(f"   Detected: {pers.get('detected', 0)}/{pers.get('total', 0)}")
print()
scenes = report.get('scenes', [])
print(f"🎞️  Scenes: {len(scenes)}")
keyframes = sum(1 for s in scenes if s.get('keyframe'))
print(f"   With keyframes: {keyframes}")
EOF
    fi
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "💾 Full report saved to: $RESPONSE_FILE"
    echo ""
    echo "📖 To view the full report:"
    echo "   cat $RESPONSE_FILE | python -m json.tool | less"
    echo ""
    
else
    echo "❌ Failed!"
    echo ""
    echo "Error response:"
    cat "$RESPONSE_FILE"
    echo ""
    exit 1
fi
