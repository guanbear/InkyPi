#!/usr/bin/env python3
from PIL import Image, ImageDraw
import os

# E6彩色墨水屏的6色色板（使用饱和度适中的颜色以适应墨水屏）
E6_COLORS = {
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'red': (200, 0, 0),      # 暗红色，避免过亮
    'yellow': (255, 200, 0),  # 金黄色
    'green': (0, 150, 0),     # 深绿色
    'blue': (0, 80, 180),     # 深蓝色
}

# 图标尺寸
SIZE = 200
CENTER = SIZE // 2

def create_icon(filename, draw_func):
    """创建图标"""
    img = Image.new('RGBA', (SIZE, SIZE), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw_func(draw)
    output_path = f'src/plugins/qweather/icons/eink/{filename}'
    img.save(output_path, 'PNG')
    print(f'Created: {output_path}')

# 01d - 晴天（黄色太阳）
def draw_01d(draw):
    # 太阳圆盘
    draw.ellipse([60, 60, 140, 140], fill=E6_COLORS['yellow'])
    # 太阳光芒（8条）
    rays = [
        # 上
        [(CENTER, 20), (CENTER, 50)],
        # 下
        [(CENTER, 150), (CENTER, 180)],
        # 左
        [(20, CENTER), (50, CENTER)],
        # 右
        [(150, CENTER), (180, CENTER)],
        # 左上
        [(40, 40), (65, 65)],
        # 右上
        [(160, 40), (135, 65)],
        # 左下
        [(40, 160), (65, 135)],
        # 右下
        [(160, 160), (135, 135)],
    ]
    for ray in rays:
        draw.line(ray, fill=E6_COLORS['yellow'], width=10)

# 02d - 少云（黄色太阳+白色云）
def draw_02d(draw):
    # 太阳（较小）
    draw.ellipse([30, 30, 90, 90], fill=E6_COLORS['yellow'])
    # 简单的太阳光芒
    for angle in [0, 45, 90, 135]:
        import math
        rad = math.radians(angle)
        x1 = 60 + 35 * math.cos(rad)
        y1 = 60 + 35 * math.sin(rad)
        x2 = 60 + 55 * math.cos(rad)
        y2 = 60 + 55 * math.sin(rad)
        draw.line([(x1, y1), (x2, y2)], fill=E6_COLORS['yellow'], width=8)
    
    # 云（白色带黑边）
    cloud_y = 110
    draw.ellipse([70, cloud_y, 130, cloud_y+40], fill=E6_COLORS['white'], outline=E6_COLORS['black'], width=3)
    draw.ellipse([90, cloud_y-15, 150, cloud_y+25], fill=E6_COLORS['white'], outline=E6_COLORS['black'], width=3)
    draw.ellipse([110, cloud_y, 170, cloud_y+40], fill=E6_COLORS['white'], outline=E6_COLORS['black'], width=3)

# 03d - 多云（灰色云）
def draw_03d(draw):
    # 多个云
    for offset in [(40, 50), (90, 80)]:
        x, y = offset
        draw.ellipse([x, y, x+50, y+35], fill=(180, 180, 180), outline=E6_COLORS['black'], width=3)
        draw.ellipse([x+15, y-10, x+65, y+25], fill=(180, 180, 180), outline=E6_COLORS['black'], width=3)
        draw.ellipse([x+30, y, x+80, y+35], fill=(180, 180, 180), outline=E6_COLORS['black'], width=3)

# 04d - 阴天（深灰云）
def draw_04d(draw):
    # 大片乌云
    for offset in [(30, 60), (70, 50), (30, 100)]:
        x, y = offset
        draw.ellipse([x, y, x+60, y+40], fill=(100, 100, 100), outline=E6_COLORS['black'], width=3)
        draw.ellipse([x+20, y-15, x+80, y+25], fill=(100, 100, 100), outline=E6_COLORS['black'], width=3)
        draw.ellipse([x+40, y, x+100, y+40], fill=(100, 100, 100), outline=E6_COLORS['black'], width=3)

# 09d - 小雨（蓝色雨滴）
def draw_09d(draw):
    # 云
    draw.ellipse([50, 40, 110, 80], fill=(180, 180, 180), outline=E6_COLORS['black'], width=3)
    draw.ellipse([70, 30, 130, 70], fill=(180, 180, 180), outline=E6_COLORS['black'], width=3)
    draw.ellipse([90, 40, 150, 80], fill=(180, 180, 180), outline=E6_COLORS['black'], width=3)
    
    # 雨滴（蓝色）
    for x in [60, 85, 110, 135]:
        for y_offset in [0, 25]:
            y = 100 + y_offset
            draw.line([(x, y), (x, y+20)], fill=E6_COLORS['blue'], width=4)

# 10d - 雨（蓝色雨滴，更多）
def draw_10d(draw):
    # 云
    draw.ellipse([50, 40, 110, 80], fill=(150, 150, 150), outline=E6_COLORS['black'], width=3)
    draw.ellipse([70, 30, 130, 70], fill=(150, 150, 150), outline=E6_COLORS['black'], width=3)
    draw.ellipse([90, 40, 150, 80], fill=(150, 150, 150), outline=E6_COLORS['black'], width=3)
    
    # 更多雨滴
    for x in [55, 75, 95, 115, 135]:
        for y_offset in [0, 20, 40]:
            y = 95 + y_offset
            draw.line([(x, y), (x, y+15)], fill=E6_COLORS['blue'], width=4)

# 11d - 雷暴（黄色闪电）
def draw_11d(draw):
    # 乌云
    draw.ellipse([50, 30, 110, 70], fill=(80, 80, 80), outline=E6_COLORS['black'], width=3)
    draw.ellipse([70, 20, 130, 60], fill=(80, 80, 80), outline=E6_COLORS['black'], width=3)
    draw.ellipse([90, 30, 150, 70], fill=(80, 80, 80), outline=E6_COLORS['black'], width=3)
    
    # 闪电（黄色）
    lightning = [(CENTER, 80), (CENTER-10, 110), (CENTER+5, 110), (CENTER-5, 150)]
    draw.polygon(lightning, fill=E6_COLORS['yellow'], outline=E6_COLORS['black'])

# 13d - 雪（白色雪花）
def draw_13d(draw):
    # 云
    draw.ellipse([50, 40, 110, 80], fill=(200, 200, 200), outline=E6_COLORS['black'], width=3)
    draw.ellipse([70, 30, 130, 70], fill=(200, 200, 200), outline=E6_COLORS['black'], width=3)
    draw.ellipse([90, 40, 150, 80], fill=(200, 200, 200), outline=E6_COLORS['black'], width=3)
    
    # 雪花（简化的六角形）
    for pos in [(65, 110), (100, 120), (135, 110), (80, 145), (120, 145)]:
        x, y = pos
        # 六角星形雪花
        for angle in [0, 60, 120]:
            import math
            rad = math.radians(angle)
            draw.line([
                (x + 12*math.cos(rad), y + 12*math.sin(rad)),
                (x - 12*math.cos(rad), y - 12*math.sin(rad))
            ], fill=E6_COLORS['white'], width=4)
        # 雪花外轮廓
        draw.ellipse([x-3, y-3, x+3, y+3], outline=E6_COLORS['black'], width=2)

# 50d - 雾（灰色波浪线）
def draw_50d(draw):
    # 多层雾气（波浪线）
    for y in [60, 90, 120, 150]:
        import math
        points = []
        for x in range(30, 171, 5):
            wave_y = y + 10 * math.sin(x / 10)
            points.append((x, wave_y))
        draw.line(points, fill=(120, 120, 120), width=6)

# 创建所有图标
if __name__ == '__main__':
    os.chdir('/Users/guanzhicheng/Downloads/InkyPi')
    
    icons = {
        '01d.png': draw_01d,
        '02d.png': draw_02d,
        '03d.png': draw_03d,
        '04d.png': draw_04d,
        '09d.png': draw_09d,
        '10d.png': draw_10d,
        '11d.png': draw_11d,
        '13d.png': draw_13d,
        '50d.png': draw_50d,
    }
    
    for filename, draw_func in icons.items():
        create_icon(filename, draw_func)
    
    print(f'\n成功创建 {len(icons)} 个E6墨水屏适配图标！')
