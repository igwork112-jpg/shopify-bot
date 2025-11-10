"""
Color Detection Test Suite
Tests multiple methods for accurate product color identification
"""

import cv2
import numpy as np
import requests
from io import BytesIO
from PIL import Image
import base64
from typing import Dict, Optional, Tuple

class ColorDetectionTester:
    """Test suite for product color detection methods"""
    
    def __init__(self):
        self.test_results = []
    
    # ========== METHOD 1: TEXT EXTRACTION ==========
    def test_text_extraction(self, product_name: str, description: str, html: str = "") -> str:
        """Method 1: Extract color from text (most reliable)"""
        print("\n" + "="*60)
        print("METHOD 1: TEXT EXTRACTION")
        print("="*60)
        
        combined_text = f"{product_name} {description} {html}".lower()
        
        color_keywords = {
            'black': ['black', 'noir', 'schwarz', 'negro'],
            'white': ['white', 'blanc', 'weiß', 'blanco'],
            'grey': ['grey', 'gray', 'gris'],
            'red': ['red', 'rouge', 'rot', 'rojo'],
            'blue': ['blue', 'bleu', 'blau', 'azul'],
            'green': ['green', 'vert', 'grün', 'verde'],
            'yellow': ['yellow', 'jaune', 'gelb', 'amarillo'],
            'brown': ['brown', 'brun', 'braun', 'marrón'],
        }
        
        found_colors = []
        for color, keywords in color_keywords.items():
            for keyword in keywords:
                if keyword in combined_text:
                    found_colors.append((color, keyword))
                    print(f"✅ Found: '{keyword}' → {color}")
        
        if found_colors:
            result = found_colors[0][0]  # First match wins
            print(f"\n🎯 TEXT RESULT: {result.upper()}")
            return result
        else:
            print("❌ No color found in text")
            return "unknown"
    
    # ========== METHOD 2: HISTOGRAM ANALYSIS ==========
    def test_histogram_analysis(self, image_url: str) -> str:
        """Method 2: Brightness-based histogram analysis"""
        print("\n" + "="*60)
        print("METHOD 2: HISTOGRAM ANALYSIS")
        print("="*60)
        
        try:
            # Download image
            response = requests.get(image_url, timeout=15)
            img = Image.open(BytesIO(response.content)).convert('RGB')
            
            # Convert to grayscale
            gray = img.convert('L')
            pixels = list(gray.getdata())
            
            # Calculate metrics
            avg_brightness = sum(pixels) / len(pixels)
            histogram = gray.histogram()
            
            # Count dark vs light pixels
            dark_pixels = sum(histogram[0:86])      # 0-85: dark
            light_pixels = sum(histogram[170:256])  # 170-255: light
            mid_pixels = sum(histogram[86:170])     # 86-169: mid
            
            total = len(pixels)
            dark_ratio = dark_pixels / total
            light_ratio = light_pixels / total
            mid_ratio = mid_pixels / total
            
            print(f"📊 Average Brightness: {avg_brightness:.1f} / 255")
            print(f"📊 Dark pixels (0-85): {dark_ratio:.1%}")
            print(f"📊 Mid pixels (86-169): {mid_ratio:.1%}")
            print(f"📊 Light pixels (170-255): {light_ratio:.1%}")
            
            # Decision logic
            if dark_ratio > 0.4 or avg_brightness < 85:
                result = "black"
                print(f"\n🎯 HISTOGRAM RESULT: {result.upper()} (High dark ratio or low brightness)")
            elif light_ratio > 0.4 or avg_brightness > 170:
                result = "white"
                print(f"\n🎯 HISTOGRAM RESULT: {result.upper()} (High light ratio or high brightness)")
            elif avg_brightness < 130:
                result = "dark grey"
                print(f"\n🎯 HISTOGRAM RESULT: {result.upper()} (Medium-low brightness)")
            else:
                result = "grey"
                print(f"\n🎯 HISTOGRAM RESULT: {result.upper()} (Medium brightness)")
            
            return result
            
        except Exception as e:
            print(f"❌ Histogram analysis failed: {e}")
            return "unknown"
    
    # ========== METHOD 3: DOMINANT COLOR (OpenCV + KMeans) ==========
    def test_dominant_color_extraction(self, image_url: str) -> Tuple[str, Optional[Dict]]:
        """Method 3: Extract dominant color using KMeans clustering"""
        print("\n" + "="*60)
        print("METHOD 3: DOMINANT COLOR EXTRACTION (OpenCV + KMeans)")
        print("="*60)
        
        try:
            # Download and convert image
            response = requests.get(image_url, timeout=15)
            img_pil = Image.open(BytesIO(response.content)).convert('RGB')
            img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
            
            # Convert to HSV for glare detection
            hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
            v = hsv[:, :, 2]  # Value channel (brightness)
            s = hsv[:, :, 1]  # Saturation channel
            
            # Create mask to remove glossy reflections
            # Glare = very bright (v > 220) + low saturation (s < 40)
            gloss_mask = (v > 220) & (s < 40)
            gloss_mask = gloss_mask.astype(np.uint8) * 255
            
            print(f"📊 Glare pixels detected: {np.sum(gloss_mask > 0)} / {gloss_mask.size}")
            
            # Invert mask to keep non-glossy areas
            non_gloss_mask = cv2.bitwise_not(gloss_mask)
            
            # Apply mask
            masked = cv2.bitwise_and(img_cv, img_cv, mask=non_gloss_mask)
            
            # Reshape for clustering
            pixels = masked.reshape(-1, 3)
            pixels = pixels[np.any(pixels != [0, 0, 0], axis=1)]  # Remove black pixels
            
            if len(pixels) == 0:
                print("❌ No valid pixels after masking")
                return "unknown", None
            
            print(f"📊 Valid pixels for analysis: {len(pixels)}")
            
            # KMeans clustering to find dominant colors
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10).fit(pixels)
            
            # Get cluster centers and their sizes
            labels = kmeans.labels_
            centers = kmeans.cluster_centers_
            
            # Count pixels in each cluster
            unique, counts = np.unique(labels, return_counts=True)
            
            # Find the largest cluster (most dominant color)
            dominant_idx = np.argmax(counts)
            dominant_bgr = centers[dominant_idx]
            
            # Convert BGR to RGB
            b, g, r = [int(c) for c in dominant_bgr]
            hex_color = '#%02x%02x%02x' % (r, g, b)
            
            print(f"\n🎨 Dominant Color (RGB): ({r}, {g}, {b})")
            print(f"🎨 Dominant Color (HEX): {hex_color}")
            print(f"🎨 Pixel count: {counts[dominant_idx]} ({counts[dominant_idx]/len(pixels)*100:.1f}%)")
            
            # Interpret color name from RGB
            color_name = self._rgb_to_color_name(r, g, b)
            print(f"\n🎯 DOMINANT COLOR RESULT: {color_name.upper()}")
            
            color_info = {
                "r": r,
                "g": g,
                "b": b,
                "hex": hex_color,
                "name": color_name,
                "percentage": counts[dominant_idx]/len(pixels)*100
            }
            
            return color_name, color_info
            
        except Exception as e:
            print(f"❌ Dominant color extraction failed: {e}")
            return "unknown", None
    
    def _rgb_to_color_name(self, r: int, g: int, b: int) -> str:
        """Convert RGB to approximate color name"""
        # Calculate brightness
        brightness = (r + g + b) / 3
        
        # Check if grayscale (low color variation)
        color_diff = max(r, g, b) - min(r, g, b)
        
        if color_diff < 30:  # Grayscale
            if brightness < 50:
                return "black"
            elif brightness < 100:
                return "dark grey"
            elif brightness < 180:
                return "grey"
            else:
                return "white"
        
        # Color detection
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
        else:
            return "mixed color"
    
    # ========== COMPREHENSIVE TEST ==========
    def run_all_tests(self, product_name: str, product_description: str, 
                     image_url: str, page_html: str = ""):
        """Run all three methods and compare results"""
        print("\n" + "🔬"*30)
        print("COMPREHENSIVE COLOR DETECTION TEST")
        print("🔬"*30)
        print(f"\n📦 Product: {product_name}")
        print(f"🔗 Image URL: {image_url[:60]}...")
        
        # Test all methods
        text_color = self.test_text_extraction(product_name, product_description, page_html)
        histogram_color = self.test_histogram_analysis(image_url)
        dominant_color, color_info = self.test_dominant_color_extraction(image_url)
        
        # Summary
        print("\n" + "="*60)
        print("FINAL RESULTS SUMMARY")
        print("="*60)
        print(f"Method 1 (Text):            {text_color.upper()}")
        print(f"Method 2 (Histogram):       {histogram_color.upper()}")
        print(f"Method 3 (Dominant Color):  {dominant_color.upper()}")
        
        # Determine final color with priority
        if text_color != "unknown":
            final = text_color
            source = "Text (Priority 1)"
        elif dominant_color != "unknown":
            final = dominant_color
            source = "Dominant Color (Priority 2)"
        elif histogram_color != "unknown":
            final = histogram_color
            source = "Histogram (Priority 3)"
        else:
            final = "black"
            source = "Default Fallback"
        
        print("\n" + "🎯"*30)
        print(f"FINAL COLOR: {final.upper()} (from {source})")
        print("🎯"*30)
        
        return {
            "text_color": text_color,
            "histogram_color": histogram_color,
            "dominant_color": dominant_color,
            "color_info": color_info,
            "final_color": final,
            "source": source
        }


# ========== USAGE EXAMPLE ==========
if __name__ == "__main__":
    # Test with the rubber sheet product
    tester = ColorDetectionTester()
    
    # Example 1: Black rubber sheet
    print("\n🧪 TEST 1: Black Rubber Sheet")
    results1 = tester.run_all_tests(
        product_name="Commercial Grade Rubber Sheet - Black",
        product_description="Heavy duty black rubber sheeting for commercial use",
        image_url="https://rubberco.co.uk/cdn/shop/files/raw_1817d421-298c-416f-984d-c5f1c869d440_720x.png?v=1755808224",
        page_html="<h1>Commercial Grade Rubber Sheet 1.5mm-25mm, 1.4m Wide Heavy Duty Black</h1>"
    )
    
    print("\n" + "="*60)
    print("Test 1 Complete!")
    print(f"Detected Color: {results1['final_color']}")
    print(f"Color Info: {results1['color_info']}")
    
    # You can add more test cases here
    # Example 2: Test with another product
    # results2 = tester.run_all_tests(...)