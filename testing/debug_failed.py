import cv2
import numpy as np
import requests
from io import BytesIO
from rembg import remove
from sklearn.cluster import KMeans
def _rgb_to_color_name(r, g, b):
    """Convert RGB to approximate color name (same logic you use)"""
    brightness = (r + g + b) / 3
    color_diff = max(r, g, b) - min(r, g, b)
    if color_diff < 30:
        if brightness < 50:
            return "black"
        elif brightness < 120:
            return "dark grey"
        elif brightness < 200:
            return "grey"
        elif brightness < 240:
            return "light grey"
        else:
            return "white"
    if r > g and r > b:
        if r - max(g, b) > 50:
            return "red"
        else:
            return "brown"
    elif g > r and g > b:
        return "green"
    elif b > r and b > g:
        return "blue"
    elif r > 200 and g > 200 and b < 100:
        return "yellow"
    elif r > 150 and g < 100 and b > 150:
        return "purple"
    elif r > 200 and g > 100 and b < 100:
        return "orange"
    else:
        return "mixed color"

def get_product_color(image_url):
    """Download image, remove background, and detect dominant product color"""
    print("📥 Downloading image...")
    response = requests.get(image_url)
    img_bytes = BytesIO(response.content)

    print("🧼 Removing background...")
    result = remove(img_bytes.read())

    # Convert to numpy array
    img_np = np.frombuffer(result, np.uint8)
    img = cv2.imdecode(img_np, cv2.IMREAD_UNCHANGED)

    # Convert to RGB (remove alpha if exists)
    if img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    print("🎨 Running KMeans...")
    pixels = img.reshape(-1, 3)
    pixels = pixels[np.all(pixels < [240, 240, 240], axis=1)]  # remove white-ish pixels

    kmeans = KMeans(n_clusters=3, random_state=0).fit(pixels)
    centers = np.round(kmeans.cluster_centers_).astype(int)
    counts = np.bincount(kmeans.labels_)
    dominant = centers[np.argmax(counts)]

    rgb = tuple(dominant)
    hex_color = '#%02x%02x%02x' % rgb
    name = _rgb_to_color_name(*rgb)

    print(f"\n✅ Dominant Color: {name.upper()}")
    print(f"RGB: {rgb}")
    print(f"HEX: {hex_color}")
    return rgb, hex_color, name

if __name__ == "__main__":
    url = "https://rubberco.co.uk/cdn/shop/files/raw_5d4c43e3-c723-4fac-8d74-48e1083b60ce_720x.png?v=1755808224"
    get_product_color(url)
