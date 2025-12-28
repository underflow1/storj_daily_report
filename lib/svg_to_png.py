#!/usr/bin/env python3
"""
Скрипт для конвертации SVG в PNG
"""
import subprocess
import sys
import os

def svg_to_png(svg_path, png_path=None, width=None, height=None):
    """
    Конвертирует SVG файл в PNG используя rsvg-convert (более точная передача цветов)
    
    Args:
        svg_path: путь к SVG файлу
        png_path: путь для сохранения PNG (если None, создается автоматически)
        width: ширина PNG в пикселях (если None, используется из SVG)
        height: высота PNG в пикселях (если None, используется из SVG)
    """
    if not os.path.exists(svg_path):
        print(f"Ошибка: файл {svg_path} не найден")
        return False
    
    if png_path is None:
        png_path = svg_path.replace('.svg', '.png')
    
    try:
        # rsvg-convert команда для конвертации (более точная передача цветов)
        cmd = ['rsvg-convert', '-o', png_path]
        
        # Если указаны размеры, добавляем их
        if width and height:
            cmd.extend(['--width', str(width), '--height', str(height)])
        
        cmd.append(svg_path)
        
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        print(f"✓ Успешно конвертировано: {svg_path} -> {png_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Ошибка при конвертации: {e}")
        if e.stderr:
            print(f"Детали: {e.stderr}")
        return False
    except FileNotFoundError:
        print("✗ Ошибка: rsvg-convert не найден. Установите: apt-get install librsvg2-bin")
        return False

if __name__ == "__main__":
    svg_file = "storj_card_v1.svg"
    
    if len(sys.argv) > 1:
        svg_file = sys.argv[1]
    
    # Размеры берутся из SVG
    svg_to_png(svg_file)

