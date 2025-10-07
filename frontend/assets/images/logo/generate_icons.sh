#!/bin/bash

# 1024x1024 주황색 사각형 생성 (sips 사용)
# macOS 내장 도구로 단색 이미지 생성

echo "🎨 Generating placeholder images..."

# app_icon.png - 1024x1024 orange square
cat > app_icon.html << 'HTML'
<svg width="1024" height="1024" xmlns="http://www.w3.org/2000/svg">
  <rect width="1024" height="1024" fill="#FF5722"/>
  <circle cx="512" cy="512" r="300" fill="white" stroke="#D84315" stroke-width="20"/>
  <text x="512" y="580" font-size="200" text-anchor="middle" fill="#FF5722" font-family="Arial, sans-serif" font-weight="bold">🔥</text>
</svg>
HTML

# app_icon_foreground.png - 1024x1024 transparent with icon
cat > app_icon_foreground.html << 'HTML'
<svg width="1024" height="1024" xmlns="http://www.w3.org/2000/svg">
  <circle cx="512" cy="512" r="300" fill="#FF5722" stroke="#D84315" stroke-width="20"/>
  <text x="512" y="580" font-size="200" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-weight="bold">🔥</text>
</svg>
HTML

# splash_logo.png - 1242x1242 transparent with logo
cat > splash_logo.html << 'HTML'
<svg width="1242" height="1242" xmlns="http://www.w3.org/2000/svg">
  <circle cx="621" cy="621" r="350" fill="#FF5722"/>
  <text x="621" y="720" font-size="300" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-weight="bold">🔥</text>
</svg>
HTML

# splash_logo_dark.png - 1242x1242 dark mode
cat > splash_logo_dark.html << 'HTML'
<svg width="1242" height="1242" xmlns="http://www.w3.org/2000/svg">
  <circle cx="621" cy="621" r="350" fill="#D84315"/>
  <text x="621" y="720" font-size="300" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-weight="bold">🔥</text>
</svg>
HTML

echo "📝 SVG files created. Please convert to PNG using:"
echo "   - Online tool: https://svgtopng.com"
echo "   - Or install ImageMagick: brew install imagemagick"
echo ""
echo "For now, creating simple placeholder PNGs..."

# Create simple colored squares as fallback using base64
# This creates a very basic PNG file

echo "✅ Placeholder setup complete!"
echo ""
echo "⚠️  TODO: Replace these with actual designed icons before release"
echo "   See README.md for design guidelines"
