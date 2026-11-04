"""
Generate retro 16-bit pixel-art badges for the 5 crystal morph states:
1. Quartz (Cyan Diamond)
2. Cloud (Cloud + Lightning)
3. NPM (Crimson Hexagon with 'npm')
4. PHP (Royal Blue/Purple with 'php')
5. Meta (Electric Blue/Magenta Infinity Loop)
"""
from PIL import Image, ImageDraw
import os

OUT_DIR = "website/assets"
os.makedirs(OUT_DIR, exist_ok=True)

def create_quartz():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    def px(x, y, w, h, col):
        draw.rectangle([x*2, y*2, (x+w)*2 - 1, (y+h)*2 - 1], fill=col)

    # Outline
    px(10, 2, 12, 2, "#000")
    px(6, 4, 4, 4, "#000")
    px(22, 4, 4, 4, "#000")
    px(3, 8, 3, 6, "#000")
    px(26, 8, 3, 6, "#000")
    px(3, 14, 2, 2, "#000")
    px(27, 14, 2, 2, "#000")
    px(5, 16, 3, 3, "#000")
    px(24, 16, 3, 3, "#000")
    px(8, 19, 4, 4, "#000")
    px(20, 19, 4, 4, "#000")
    px(12, 23, 8, 3, "#000")

    # Facets
    px(10, 4, 12, 4, "#ffffff")
    px(6, 8, 8, 6, "#cffafe")
    px(14, 8, 8, 6, "#67e8f9")
    px(22, 8, 4, 6, "#06b6d4")
    px(5, 14, 6, 2, "#38bdf8")
    px(11, 14, 10, 5, "#0284c7")
    px(21, 14, 6, 2, "#0369a1")
    px(12, 19, 8, 4, "#0f172a")

    img.save(os.path.join(OUT_DIR, "badge_quartz.png"))
    return img

def create_cloud():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    def px(x, y, w, h, col):
        draw.rectangle([x*2, y*2, (x+w)*2 - 1, (y+h)*2 - 1], fill=col)

    # Cloud outline
    px(11, 4, 10, 2, "#000")
    px(8, 6, 3, 3, "#000")
    px(21, 6, 3, 3, "#000")
    px(4, 9, 4, 3, "#000")
    px(24, 9, 4, 3, "#000")
    px(2, 12, 3, 8, "#000")
    px(28, 12, 3, 8, "#000")
    px(4, 20, 24, 3, "#000")

    # Cloud body fill
    px(11, 6, 10, 3, "#ffffff")
    px(8, 9, 16, 4, "#ffffff")
    px(5, 12, 23, 4, "#f0f9ff")
    px(5, 16, 23, 4, "#bae6fd")

    # Lightning spark at bottom
    px(15, 19, 3, 3, "#facc15")
    px(13, 22, 3, 3, "#facc15")
    px(16, 22, 2, 2, "#eab308")
    px(14, 25, 2, 4, "#facc15")
    px(14, 25, 2, 4, "#000") # outline edge
    px(15, 24, 2, 3, "#facc15")

    img.save(os.path.join(OUT_DIR, "badge_cloud.png"))
    return img

def create_npm():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    def px(x, y, w, h, col):
        draw.rectangle([x*2, y*2, (x+w)*2 - 1, (y+h)*2 - 1], fill=col)

    # NPM Hexagon / Cube outline
    px(10, 3, 12, 2, "#000")
    px(5, 5, 5, 2, "#000")
    px(22, 5, 5, 2, "#000")
    px(3, 7, 2, 16, "#000")
    px(27, 7, 2, 16, "#000")
    px(5, 23, 5, 2, "#000")
    px(22, 23, 5, 2, "#000")
    px(10, 25, 12, 2, "#000")

    # Crimson body fill
    px(10, 5, 12, 2, "#ef4444")
    px(5, 7, 22, 16, "#cb3837")
    px(10, 23, 12, 2, "#991b1b")

    # Pixel letters 'npm' in white and black
    # 'n'
    px(6, 11, 2, 8, "#ffffff")
    px(8, 11, 3, 2, "#ffffff")
    px(10, 13, 2, 6, "#ffffff")

    # 'p'
    px(13, 11, 2, 8, "#ffffff")
    px(15, 11, 3, 2, "#ffffff")
    px(17, 13, 2, 4, "#ffffff")
    px(15, 16, 3, 2, "#ffffff")

    # 'm'
    px(20, 11, 2, 8, "#ffffff")
    px(22, 11, 2, 2, "#ffffff")
    px(23, 13, 2, 6, "#ffffff")
    px(24, 11, 2, 2, "#ffffff")
    px(25, 11, 2, 8, "#ffffff")

    img.save(os.path.join(OUT_DIR, "badge_npm.png"))
    return img

def create_php():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    def px(x, y, w, h, col):
        draw.rectangle([x*2, y*2, (x+w)*2 - 1, (y+h)*2 - 1], fill=col)

    # Oval silhouette outline
    px(8, 5, 16, 2, "#000")
    px(4, 7, 4, 3, "#000")
    px(24, 7, 4, 3, "#000")
    px(2, 10, 2, 10, "#000")
    px(28, 10, 2, 10, "#000")
    px(4, 20, 4, 3, "#000")
    px(24, 20, 4, 3, "#000")
    px(8, 23, 16, 2, "#000")

    # Royal Blue fill
    px(8, 7, 16, 3, "#818cf8")
    px(4, 10, 24, 10, "#4f46e5")
    px(8, 20, 16, 3, "#3730a3")

    # Pixel letters 'php' in white
    # 'p'
    px(6, 12, 2, 7, "#ffffff")
    px(8, 12, 2, 2, "#ffffff")
    px(9, 13, 2, 3, "#ffffff")
    px(8, 15, 2, 2, "#ffffff")

    # 'h'
    px(13, 10, 2, 9, "#ffffff")
    px(15, 13, 2, 2, "#ffffff")
    px(17, 14, 2, 5, "#ffffff")

    # 'p'
    px(21, 12, 2, 7, "#ffffff")
    px(23, 12, 2, 2, "#ffffff")
    px(24, 13, 2, 3, "#ffffff")
    px(23, 15, 2, 2, "#ffffff")

    img.save(os.path.join(OUT_DIR, "badge_php.png"))
    return img

def create_meta():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    def px(x, y, w, h, col):
        draw.rectangle([x*2, y*2, (x+w)*2 - 1, (y+h)*2 - 1], fill=col)

    # Circular/rounded badge outline
    px(9, 4, 14, 2, "#000")
    px(5, 6, 4, 3, "#000")
    px(23, 6, 4, 3, "#000")
    px(2, 9, 3, 14, "#000")
    px(27, 9, 3, 14, "#000")
    px(5, 23, 4, 3, "#000")
    px(23, 23, 4, 3, "#000")
    px(9, 26, 14, 2, "#000")

    # Gradient fill: Electric Blue to Magenta
    px(9, 6, 14, 3, "#38bdf8")
    px(5, 9, 22, 7, "#0084ff")
    px(5, 16, 22, 7, "#7c3aed")
    px(9, 23, 14, 3, "#4c1d95")

    # Meta Infinity loop / figure 8 in glowing white/cyan
    # Left loop
    px(6, 14, 3, 4, "#ffffff")
    px(8, 12, 4, 2, "#ffffff")
    px(8, 18, 4, 2, "#ffffff")
    # Center crossover
    px(12, 13, 3, 2, "#cffafe")
    px(14, 15, 4, 2, "#ffffff")
    px(17, 17, 3, 2, "#cffafe")
    # Right loop
    px(20, 12, 4, 2, "#ffffff")
    px(20, 18, 4, 2, "#ffffff")
    px(23, 14, 3, 4, "#ffffff")

    img.save(os.path.join(OUT_DIR, "badge_meta.png"))
    return img

if __name__ == "__main__":
    create_quartz()
    create_cloud()
    create_npm()
    create_php()
    create_meta()
    print("All 5 badges generated successfully in website/assets/")
