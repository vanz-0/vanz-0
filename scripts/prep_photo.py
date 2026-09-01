#!/usr/bin/env python3
"""
Prepare a portrait photo for clean ASCII conversion:
  1. Remove the background (rembg) so the subject is isolated
  2. Boost LOCAL contrast (CLAHE) so a flatly-lit face gains highlights/shadows
  3. Composite the subject onto pure white so the background maps to blank

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.
Run once whenever the source photo changes.

    python scripts/prep_photo.py [input.jpg] [output.png]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.jpg")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

# 1. cut out the subject
print(f"Removing background from {INP}...")
cut = remove(Image.open(INP).convert("RGBA"))

# 2. composite onto pure white background
white_bg = Image.new("RGBA", cut.size, (255, 255, 255, 255))
composite = Image.alpha_composite(white_bg, cut)
gray = composite.convert("L")

# 3. boost local contrast with CLAHE
arr = np.array(gray)
clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
arr = clahe.apply(arr)

# save
result = Image.fromarray(arr)
result.save(OUT)
print(f"Wrote prepped photo to {OUT}")
