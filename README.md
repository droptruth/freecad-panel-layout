# 拆板排版与 R3 让刀

一个用于 FreeCAD 木工拆板图的 Codex 技能：把板件紧凑排入外框，检查 6 mm 间距，并在材料内凹直角生成单条 R3 圆弧让刀。

## 功能

- 默认按 1200 × 2400 mm 板材、板件间距 6 mm、板件到外框边距 6 mm 排列；具体尺寸按当前图纸和用户要求调整。
- 保持板件尺寸、数量和方向；只有在允许旋转时才尝试转向排版。
- 对材料内凹直角生成经过原角点的单条 R3 圆弧；不修改外凸角。
- 可按要求另存 FreeCAD 文件并导出 AutoCAD 可用的 DWG。

技能还包含用于保守矩形排版估算和 R3 几何处理的辅助脚本。排版脚本采用启发式算法，无法放入的报告不代表数学上绝对无解。

## 在 Codex 中安装

在 Codex 中让 `skill-installer` 从本仓库安装根目录的技能：

```text
https://github.com/droptruth/freecad-panel-layout
```

安装后，在新对话中这样调用：

```text
使用 $freecad-panel-layout 帮我整理当前 FreeCAD 拆板图。
```

也可以把本仓库内容放到 Codex 的技能目录 `skills/freecad-panel-layout/` 中；该目录下应直接包含 `SKILL.md`。

## 目录

- `SKILL.md`：技能入口和工作流程。
- `references/`：R3 几何规则、验证与导出说明。
- `scripts/`：可复用的排版与圆弧处理辅助脚本。
- `assets/`：单圆弧参考示意图。
- `agents/openai.yaml`：Codex 界面显示名称和默认提示。
