# SVG转PNG转换器使用说明

这个工具用于批量转换和风天气SVG图标为PNG格式，支持深色/浅色主题适配。

## 安装依赖

```bash
pip install cairosvg lxml tinycss2
```

## 使用方法

### 方法1: 批量转换所有图标（推荐）

```bash
# 转换所有SVG到PNG，生成多个尺寸和主题
python scripts/convert_svg_icons.py

# 指定自定义参数
python scripts/convert_svg_icons.py \
  --input src/plugins/qweather/icons/qweather \
  --output src/plugins/qweather/icons/converted \
  --sizes 64x64 48x48 32x32 \
  --themes light dark
```

### 方法2: 插件内置转换（自动）

插件会自动在运行时转换SVG为PNG，无需手动预处理。转换后的文件会被缓存在系统临时目录中，避免重复转换。

## 特性

1. **主题适配**: 自动为深色/浅色主题调整图标颜色
2. **缓存机制**: 避免重复转换相同图标
3. **降级方案**: 转换失败时自动回退到PNG图标
4. **透明背景**: 生成的PNG保持透明背景

## 文件结构

转换后的文件结构：
```
src/plugins/qweather/icons/converted/
├── light/
│   ├── 64x64/
│   │   ├── 100_64x64_light.png
│   │   └── 101_64x64_light.png
│   └── 48x48/
└── dark/
    ├── 64x64/
    └── 48x48/
```

## 配置

在插件设置中选择 `displayStyle: "qweather"` 来使用和风天气SVG图标。转换会自动进行。

## 故障排除

1. **转换失败**: 检查是否安装了所有依赖库
2. **图标不显示**: 查看日志中的错误信息
3. **颜色问题**: SVG中使用 `currentColor` 的会自动适配主题