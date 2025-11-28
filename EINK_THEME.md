# E-Ink 主题使用说明

## 概述
已为 InkyPi 天气插件添加了专为 E6 彩色墨水屏（800x480 分辨率）优化的新主题。

## 主要特性

### 1. 字体优化
- **字体选择**: 使用 Noto Sans SC 作为主要字体，fallback 到系统中文字体
- **字重增强**: 标题和数据使用更粗的字重（600-700），提升可读性
- **字号调整**: 所有文字都相应放大，适应墨水屏的显示特点
- **抗锯齿**: 添加了字体平滑渲染，减少锯齿感

### 2. 图标系统
- **位置**: `src/plugins/qweather/icons/eink/`
- **风格**: 使用简洁的像素风格图标，带纯色填充
- **适配**: 针对 E6 墨水屏的 6 色显示进行优化（黑、白、红、黄、绿、蓝）
- **图标映射**:
  - 晴天 (01d/02d): k0.png - 太阳+云
  - 多云 (03d): Pf.png - 云朵
  - 阴天 (04d): Hx.png - 厚云
  - 大雨 (09d): uu.png - 云+大雨
  - 雨 (10d): xc.png - 云+雨
  - 雷暴 (11d): gk.png - 云+闪电
  - 雪 (13d): nt.png - 云+雪
  - 雾 (50d): p8.png - 雾气

### 3. CSS 样式优化
针对 E-Ink 显示特性的样式调整：
- 图像渲染优化（crisp-edges）
- 字体平滑处理
- 更大的字号以提升可读性
- 增加字重确保笔画清晰

## 使用方法

1. 进入天气插件设置页面
2. 找到 **"显示风格"** (Display Style) 选项
3. 选择 **"墨水屏优化（E6彩色）"** (E-Ink Optimized)
4. 保存设置并刷新显示

## 主题选项对比

| 主题 | 字体 | 图标风格 | 适用场景 |
|------|------|----------|----------|
| Default | Jost | 渐变彩色 | 常规显示屏 |
| Nothing Weather | Dogica 像素字体 | 像素黑白 | 复古像素风 |
| **E-Ink Optimized** | Noto Sans SC | 纯色像素 | E6 彩色墨水屏 |

## 技术细节

### 修改的文件
1. `src/plugins/qweather/settings.html` - 添加了 eink 主题选项
2. `src/plugins/qweather/render/qweather.css` - 新增 eink 样式类
3. `src/plugins/qweather/render/qweather.html` - 添加 eink 样式支持
4. `src/plugins/qweather/qweather.py` - 更新图标映射逻辑
5. `src/plugins/qweather/icons/eink/` - 新增图标目录

### 字体配置
```css
.weather-dashboard.eink-style {
  font-family: "Noto Sans SC", "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", sans-serif;
  font-weight: 500;
  image-rendering: -webkit-optimize-contrast;
  -webkit-font-smoothing: antialiased;
}
```

### 分辨率适配
所有尺寸使用响应式单位（cqh, cqi, dvh, vw），自动适应 800x480 分辨率。

## 后续优化建议

1. **更多彩色图标**: 可以创建更多专门为 E6 设计的纯色图标
2. **对比度增强**: 根据实际显示效果调整颜色对比度
3. **刷新优化**: 考虑墨水屏的刷新特性，减少不必要的全屏刷新
4. **字体替换**: 如需更好效果，可下载思源黑体等专业字体文件到 `static/fonts/`

## 故障排除

### 图标不显示
- 检查 `src/plugins/qweather/icons/eink/` 目录是否有图标文件
- 验证文件权限是否正确

### 字体显示异常
- 确保设备已安装 Noto Sans SC 字体
- 或系统有 Microsoft YaHei / PingFang SC 等中文字体

### 样式未生效
- 清除浏览器缓存
- 重启 InkyPi 服务
- 检查设置中是否正确选择了 "E-Ink Optimized" 主题

## 贡献

如有任何建议或改进，欢迎提交 issue 或 pull request！
