#!/usr/bin/env python3
"""
SVG转PNG工具脚本
用于批量转换和风天气SVG图标为PNG格式，支持主题适配
"""

import os
import sys
import argparse
from pathlib import Path
import tempfile
import hashlib

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from plugins.qweather.qweather import QWeather
    import cairosvg
    import lxml
    print("✓ All dependencies available")
except ImportError as e:
    print(f"✗ Missing dependency: {e}")
    print("Please install: pip install cairosvg lxml")
    sys.exit(1)

def convert_all_svg_icons(input_dir, output_dir, sizes=[(64, 64), (48, 48), (24, 24)], themes=['light', 'dark']):
    """
    批量转换所有SVG图标为PNG格式
    
    Args:
        input_dir: SVG图标目录
        output_dir: PNG输出目录  
        sizes: 需要生成的尺寸列表
        themes: 需要生成的主题列表
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        print(f"Input directory does not exist: {input_path}")
        return
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 初始化转换器
    converter = QWeather()
    
    svg_files = list(input_path.glob("*.svg"))
    if not svg_files:
        print(f"No SVG files found in {input_path}")
        return
    
    print(f"Found {len(svg_files)} SVG files")
    
    converted_count = 0
    error_count = 0
    
    for svg_file in svg_files:
        print(f"\nProcessing: {svg_file.name}")
        
        for size in sizes:
            for theme in themes:
                is_dark = theme == 'dark'
                
                # 生成输出文件名
                size_str = f"{size[0]}x{size[1]}"
                output_name = f"{svg_file.stem}_{size_str}_{theme}.png"
                output_file = output_path / theme / size_str / output_file
                
                # 创建输出目录
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    # 转换SVG
                    converted_path = converter.convert_svg_to_png(
                        svg_file, 
                        output_size=size, 
                        is_dark_mode=is_dark
                    )
                    
                    if converted_path and os.path.exists(converted_path):
                        # 复制到目标目录
                        import shutil
                        shutil.copy2(converted_path, output_file)
                        print(f"  ✓ {output_name}")
                        converted_count += 1
                    else:
                        print(f"  ✗ {output_name} (conversion failed)")
                        error_count += 1
                        
                except Exception as e:
                    print(f"  ✗ {output_name} - Error: {e}")
                    error_count += 1
    
    print(f"\nConversion complete:")
    print(f"  Converted: {converted_count}")
    print(f"  Errors: {error_count}")

def main():
    parser = argparse.ArgumentParser(description='Convert QWeather SVG icons to PNG')
    parser.add_argument('--input', '-i', 
                       default='src/plugins/qweather/icons/qweather',
                       help='Input directory containing SVG files')
    parser.add_argument('--output', '-o',
                       default='src/plugins/qweather/icons/converted',
                       help='Output directory for PNG files')
    parser.add_argument('--sizes', '-s',
                       nargs='+',
                       default=['64x64', '48x48', '24x24'],
                       help='Output sizes (e.g., 64x64 48x48)')
    parser.add_argument('--themes', '-t',
                       nargs='+', 
                       default=['light', 'dark'],
                       help='Themes to generate (light, dark)')
    
    args = parser.parse_args()
    
    # 解析尺寸
    sizes = []
    for size_str in args.sizes:
        try:
            w, h = map(int, size_str.split('x'))
            sizes.append((w, h))
        except ValueError:
            print(f"Invalid size format: {size_str}. Use WxH format (e.g., 64x64)")
            return
    
    print("QWeather SVG to PNG Converter")
    print("=" * 40)
    print(f"Input:  {args.input}")
    print(f"Output: {args.output}")
    print(f"Sizes:  {args.sizes}")
    print(f"Themes: {args.themes}")
    print("=" * 40)
    
    convert_all_svg_icons(args.input, args.output, sizes, args.themes)

if __name__ == "__main__":
    main()