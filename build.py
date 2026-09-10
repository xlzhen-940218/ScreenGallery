import os
import subprocess
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtCore import Qt
from PIL import Image

def main():
    print("Converting SVG to ICO...")
    app = QApplication(sys.argv)
    
    svg_path = "相册.svg"
    png_path = "icon.png"
    ico_path = "icon.ico"
    
    if not os.path.exists(svg_path):
        print(f"Error: {svg_path} not found.")
        sys.exit(1)
        
    renderer = QSvgRenderer(svg_path)
    if not renderer.isValid():
        print(f"Error: Could not render {svg_path}. Make sure it's a valid SVG.")
        sys.exit(1)
        
    image = QImage(256, 256, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()
    
    if not image.save(png_path):
        print(f"Error: Failed to save {png_path}")
        sys.exit(1)
        
    print("PNG generated. Converting to ICO...")
    img = Image.open(png_path)
    img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])
    print("ICO generated successfully.")
    
    print("Building executable with PyInstaller...")
    # Add data files (QSS and db)
    # Using --windowed to hide console
    # Using --icon to set the executable icon
    cmd = [
        os.path.join(".venv", "Scripts", "pyinstaller"),
        "--noconfirm",
        "--windowed",
        "--icon=icon.ico",
        "--name=ScreenGallery",
        "--add-data=assets;assets",
        "main.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Build complete! The executable is in the 'dist' folder.")
    except Exception as e:
        print(f"Failed to build executable: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
