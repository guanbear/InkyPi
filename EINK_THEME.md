# E-Ink 主题使用说明

## 概述
已为 InkyPi 天气插件添加了专为 E6 彩色墨水屏（800x480 分辨率）优化的新主题。

## 主要特性

### 1. 字体优化
- **QWeather Icons 字体**: 集成和风天气官方图标字体，支持所有天气状态
- **中文字体**: 使用 Noto Sans SC（思源黑体 Google 版）作为主字体
- **字体 fallback**: Microsoft YaHei, PingFang SC, Hiragino Sans GB 等
- **字重增强**: 标题和数据使用更粗的字重（600-700），提升可读性
- **字号调整**: 所有文字都相应放大，适应墨水屏的显示特点
- **抗锯齿**: 添加字体平滑渲染，减少锯齿感

### 2. 图标系统
- **图标来源**: [QWeather Icons 1.8.0](https://icons.qweather.com) 官方图标库
- **格式**: SVG 矢量图标，支持任意缩放
- **位置**: `src/plugins/qweather/icons/eink/`
- **颜色**: 纯色设计，适合 E6 墨水屏的 6 色显示（黑、白、红、黄、绿、蓝）
- **许可**: CC BY 4.0 (Creative Commons Attribution)
- **图标映射**: 直接使用和风天气 API 返回的 icon 代码（如 100.svg, 101.svg 等）

### 3. CSS 样式优化
针对 E-Ink 显示特性的样式调整：
- SVG 图像自动渲染优化
- 对比度和饱和度增强（contrast 1.2, saturate 1.3）
- 字体平滑处理
- 更大的字号以提升可读性
- 增加字重确保笔画清晰

## 使用方法

1. 进入天气插件设置页面
2. 找到 **"显示风格"** (Display Style) 选项
3. 选择 **"墨水屏优化（E6彩色）"** (E-Ink Optimized)
4. 保存设置并刷新显示

## 主题选项对比

| 主题 | 字体 | 图标风格 | 图标格式 | 适用场景 |
|------|------|----------|----------|----------|
| Default | Jost | 渐变彩色 | PNG | 常规显示屏 |
| Nothing Weather | Dogica 像素字体 | 像素黑白 | PNG | 复古像素风 |
| **E-Ink Optimized** | QWeather Icons + Noto Sans SC | QWeather官方纯色 | SVG | E6 彩色墨水屏 |

## 技术细节

### 修改的文件
1. `src/plugins/qweather/settings.html` - 添加了 eink 主题选项
2. `src/plugins/qweather/render/qweather.css` - 新增 eink 样式类和 QWeather 字体
3. `src/plugins/qweather/render/qweather.html` - 添加 eink 样式支持
4. `src/plugins/qweather/qweather.py` - 更新图标映射逻辑，直接使用 QWeather 图标代码
5. `src/plugins/qweather/icons/eink/` - QWeather 官方 SVG 图标
6. `src/static/fonts/` - QWeather Icons 字体文件（ttf, woff, woff2）

### 字体配置
```css
@font-face {
  font-family: "qweather-icons";
  src: url("../../../static/fonts/qweather-icons.woff2") format("woff2"),
       url("../../../static/fonts/qweather-icons.woff") format("woff"),
       url("../../../static/fonts/qweather-icons.ttf") format("truetype");
}

.weather-dashboard.eink-style {
  font-family: "qweather-icons", "Noto Sans SC", "Microsoft YaHei", sans-serif;
  font-weight: 500;
  image-rendering: -webkit-optimize-contrast;
  -webkit-font-smoothing: antialiased;
}
```

### 图标优化
```css
.weather-dashboard.eink-style .current-icon,
.weather-dashboard.eink-style .forecast-icon {
  image-rendering: auto;
  filter: contrast(1.2) saturate(1.3);
}
```

### 分辨率适配
所有尺寸使用响应式单位（cqh, cqi, dvh, vw），自动适应 800x480 分辨率。

## QWeather Icons 资源

- **官方网站**: https://icons.qweather.com
- **GitHub**: https://github.com/qwd/Icons
- **版本**: 1.8.0
- **许可**: 
  - 代码: MIT License
  - 图标: CC BY 4.0
- **图标数量**: 500+ 天气相关图标
- **格式支持**: SVG, Web Font

## 后续优化建议

1. **字体加载优化**: 考虑将 Google Fonts 改为本地字体以加快加载速度
2. **图标缓存**: SVG 图标可以通过浏览器缓存提升性能
3. **颜色调整**: 根据实际 E6 显示效果微调对比度和饱和度参数
4. **刷新优化**: 考虑墨水屏的刷新特性，实现局部刷新

## 故障排除

### 图标不显示
- 检查 `src/plugins/qweather/icons/eink/` 目录是否有 SVG 文件
- 验证和风天气 API 返回的 icon 代码是否正确
- 查看浏览器控制台是否有 404 错误

### 字体显示异常
- 确保 `src/static/fonts/` 目录包含 qweather-icons 字体文件
- 检查 CSS 字体路径是否正确
- 清除浏览器缓存

### 样式未生效
- 清除浏览器缓存
- 重启 InkyPi 服务
- 检查设置中是否正确选择了 "E-Ink Optimized" 主题
- 查看浏览器开发者工具确认 CSS 类已正确应用

## 贡献

如有任何建议或改进，欢迎提交 issue 或 pull request！

## 鸣谢

- [QWeather](https://www.qweather.com/) - 提供优秀的天气图标库
- [Noto Sans SC](https://fonts.google.com/noto/specimen/Noto+Sans+SC) - Google 提供的开源中文字体
