# QWeather Official Theme

## 概述
为 InkyPi 天气插件添加了使用和风天气官方图标的主题风格。

## 主要特性

- **图标来源**: [QWeather Icons 1.8.0](https://icons.qweather.com) 官方图标库
- **格式**: SVG 矢量图标，支持任意缩放
- **位置**: `src/plugins/qweather/icons/qweather/`
- **许可**: CC BY 4.0 (Creative Commons Attribution)
- **适配**: 针对 E6 墨水屏优化（对比度和饱和度增强）

## 使用方法

1. 进入天气插件设置页面
2. 找到 **"显示风格"** (Display Style) 选项
3. 选择 **"和风天气官方"** (QWeather Official)
4. 保存设置并刷新显示

## 主题选项对比

| 主题 | 字体 | 图标风格 | 图标格式 | 适用场景 |
|------|------|----------|----------|----------|
| Default | Jost | 渐变彩色 | PNG | 常规显示屏 |
| Nothing Weather | Dogica 像素字体 | 像素黑白 | PNG | 复古像素风 |
| **QWeather Official** | 原设 | QWeather官方纯色 | SVG | E6 彩色墨水屏 |

## 技术细节

- 保持原主题布局和字体设置不变
- 仅优化图标渲染（对比度 1.2x，饱和度 1.3x）
- 直接使用和风天气 API 返回的 icon 代码图标

## QWeather Icons 资源

- **官方网站**: https://icons.qweather.com
- **GitHub**: https://github.com/qwd/Icons
- **版本**: 1.8.0
- **许可**: CC BY 4.0

## 鸣谢

- [QWeather](https://www.qweather.com/) - 提供优秀的天气图标库