"""
Vietnam Sovereignty Tile Server
Proxies OSM tiles and adds Vietnamese labels for Hoang Sa & Truong Sa
"""
from flask import Flask, Response, send_file, jsonify
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os

app = Flask(__name__)

# Tile sources
OSM_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

# Vietnam Islands coordinates
HOANG_SA = {"lat": 16.5, "lon": 112.0, "name": "Quần đảo Hoàng Sa", "name_en": "Paracel Islands"}
TRUONG_SA = {"lat": 10.0, "lon": 114.0, "name": "Quần đảo Trường Sa", "name_en": "Spratly Islands"}

# Chinese characters to filter (common ones found on disputed territory labels)
CHINESE_FILTER = [
    "西沙群岛", "南沙群岛", "中沙群岛",  # Xisha, Nansha, Zhongsha
    "永兴岛", "太平岛", "中业岛",  # Yongxing, Taiping, Zhongye
    "黄岩岛", "美济礁", "渚碧礁",  # Huangyan, Meiji, Zhubi
    "南海", "中国"  # South China Sea, China
]

def lon_to_tile_x(lon, zoom):
    """Convert longitude to tile X coordinate"""
    import math
    return int((lon + 180.0) / 360.0 * (2 ** zoom))

def lat_to_tile_y(lat, zoom):
    """Convert latitude to tile Y coordinate"""
    import math
    lat_rad = math.radians(lat)
    n = 2 ** zoom
    return int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)

def tile_to_coords(x, y, zoom):
    """Convert tile coordinates back to lat/lon"""
    import math
    n = 2 ** zoom
    lon = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return lat, lon

def get_pixel_position(lat, lon, tile_x, tile_y, zoom):
    """Get pixel position within a tile for given coordinates"""
    import math
    
    # Get tile bounds
    n = 2 ** zoom
    
    # Calculate position within tile (0-256)
    x_pos = ((lon + 180.0) / 360.0 * n - tile_x) * 256
    lat_rad = math.radians(lat)
    y_pos = ((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n - tile_y) * 256
    
    return int(x_pos), int(y_pos)

def should_add_label(tile_x, tile_y, zoom, island):
    """Check if island label should be added to this tile"""
    expected_x = lon_to_tile_x(island["lon"], zoom)
    expected_y = lat_to_tile_y(island["lat"], zoom)
    
    # Allow some margin for label
    margin = max(1, 3 - zoom // 4)
    return (abs(tile_x - expected_x) <= margin and 
            abs(tile_y - expected_y) <= margin)

def add_vietnam_label(img, island, tile_x, tile_y, zoom):
    """Add Vietnamese sovereignty label to tile"""
    try:
        draw = ImageDraw.Draw(img)
        
        # Get pixel position
        px, py = get_pixel_position(island["lat"], island["lon"], tile_x, tile_y, zoom)
        
        # Check if position is within tile bounds
        if not (0 <= px <= 256 and 0 <= py <= 256):
            return img
            
        # Adjust font size based on zoom
        font_size = max(8, min(14, zoom - 2))
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size - 2)
        except:
            font = ImageFont.load_default()
            font_small = font
        
        # Only show label at certain zoom levels
        if zoom < 5:
            return img
            
        # Draw background
        text1 = f"🇻🇳 {island['name']}"
        text2 = island['name_en']
        
        # Calculate text sizes
        bbox1 = draw.textbbox((0, 0), island['name'], font=font)
        bbox2 = draw.textbbox((0, 0), text2, font=font_small)
        
        text_width = max(bbox1[2] - bbox1[0], bbox2[2] - bbox2[0]) + 30
        text_height = (bbox1[3] - bbox1[1]) + (bbox2[3] - bbox2[1]) + 15
        
        # Background rectangle
        x1 = px - text_width // 2
        y1 = py - text_height // 2
        x2 = px + text_width // 2
        y2 = py + text_height // 2
        
        # White background with red border
        draw.rectangle([x1-2, y1-2, x2+2, y2+2], fill=(255, 255, 255, 230), outline=(220, 38, 38), width=2)
        
        # Vietnamese name (red)
        draw.text((px - (bbox1[2]-bbox1[0])//2, y1 + 5), island['name'], fill=(220, 38, 38), font=font)
        
        # English name (gray)
        draw.text((px - (bbox2[2]-bbox2[0])//2, y1 + (bbox1[3]-bbox1[1]) + 8), text2, fill=(100, 100, 100), font=font_small)
        
    except Exception as e:
        print(f"Error adding label: {e}")
        
    return img

@app.route('/tile/<int:z>/<int:x>/<int:y>.png')
def get_tile(z, x, y):
    """Proxy OSM tile and add Vietnamese labels"""
    try:
        # Fetch original tile from OSM
        url = OSM_URL.format(z=z, x=x, y=y)
        headers = {
            'User-Agent': 'OpenInfra-TileServer/1.0 (https://openinfra.space)'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return Response(status=response.status_code)
        
        # Open image
        img = Image.open(BytesIO(response.content)).convert('RGBA')
        
        # Add Vietnamese labels if tile contains islands
        for island in [HOANG_SA, TRUONG_SA]:
            if should_add_label(x, y, z, island):
                img = add_vietnam_label(img, island, x, y, z)
        
        # Save to buffer
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return Response(buffer.getvalue(), mimetype='image/png')
        
    except Exception as e:
        print(f"Error fetching tile: {e}")
        return Response(status=500)

@app.route('/style.json')
def get_style():
    """Return MapLibre style JSON"""
    return jsonify({
        "version": 8,
        "name": "Vietnam Sovereignty Map",
        "sources": {
            "vietnam-tiles": {
                "type": "raster",
                "tiles": ["/tile/{z}/{x}/{y}.png"],
                "tileSize": 256,
                "attribution": "© OpenStreetMap contributors | 🇻🇳 Hoàng Sa, Trường Sa thuộc Việt Nam"
            }
        },
        "layers": [
            {
                "id": "vietnam-base",
                "type": "raster",
                "source": "vietnam-tiles"
            }
        ]
    })

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "Vietnam Sovereignty Tile Server"})

@app.route('/')
def index():
    return """
    <html>
    <head><title>Vietnam Sovereignty Tile Server</title></head>
    <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
        <h1>🇻🇳 Vietnam Sovereignty Tile Server</h1>
        <p>This tile server provides OpenStreetMap tiles with Vietnamese sovereignty labels for:</p>
        <ul>
            <li><strong>Quần đảo Hoàng Sa</strong> (Paracel Islands)</li>
            <li><strong>Quần đảo Trường Sa</strong> (Spratly Islands)</li>
        </ul>
        <h2>Endpoints</h2>
        <ul>
            <li><code>/tile/{z}/{x}/{y}.png</code> - Tile endpoint</li>
            <li><code>/style.json</code> - MapLibre style</li>
            <li><code>/health</code> - Health check</li>
        </ul>
        <h2>Usage</h2>
        <pre>
// Leaflet
L.tileLayer('/tile/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap | 🇻🇳 Hoàng Sa, Trường Sa thuộc Việt Nam'
})
        </pre>
        <p><em>Built for OpenInfra - VKU.OneLove © 2025</em></p>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
