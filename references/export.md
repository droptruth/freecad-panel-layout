# 保存和 AutoCAD 互用

只按用户本次要求导出。优先保留 FCStd；DWG 是额外的可编辑图形副本。以用户指定目录为准，使用清楚的新版本文件名，避免覆盖现有源图。

## DXF / DWG

- 将完整板件和板料框各导出一次，排除隐藏旧版、重复父容器和不属于排版的辅助对象。
- 保留真实 LINE、ARC（或具有正确 bulge 的闭合多段线）。不能把 R3 圆弧打散成大量短线，也不能只导出当前视口的截图。
- FreeCAD 自带 Python 中先 `import FreeCAD` 再 `import Import`；可用 `Import.writeDXFObject(objects, output_dxf, 14, False)` 输出真实 LINE/ARC。检测输出的 ARC 半径、角度及闭合关系。
- DWG 需要实际转换器：优先已连接 CAD MCP、现有 ODA/LibreDWG，或已安装 AutoCAD 的 `accoreconsole.exe`。无转换能力时先交付可用 DXF，并明确尚未得到 DWG；不要仅改扩展名，也不要为此擅自安装软件。
- 已安装 AutoCAD 时可在独立后台会话中用 `/i input.dxf /s export.scr` 读取 DXF 并 SAVEAS。对输出设置 `INSUNITS=4`（毫米），必要时 `MEASUREMENT=1`；数值尺寸不缩放。查当前安装或官方文档确认选项。
- 在可能支持的情况下用独立配置运行转换，避免影响用户正在编辑的图纸。进程调用用文件/API/命令行，不通过界面输入终端命令。

## 最终验证

用 AutoCAD 或真实 DWG 读取器重新打开成品，核对实际单位、实体数、圆弧半径、端点、孔槽和闭合关系。仅看到文件存在或 SAVEAS 日志不代表转换正确。

AutoCAD Core Console 退出时可能再次保存成当前格式。因此按**最终文件头或实际读取结果**报告 DWG 版本，不仅看脚本中请求的版本：`AC1027` 是 2013 格式，`AC1032` 是 2018 格式。读回验证可加 `/readonly`，避免验收过程改变成品格式。后台输出可能为 UTF-16，按正确编码解读，不能把中文乱码当作转换成功或失败的证据。

对二维图元可从 AutoCAD 的 `entget` 读取 LINE 端点、ARC 圆心/半径/起终角/法向，再与 FreeCAD 源几何逐一比较。注意 ARC 的 OCS 坐标与方向，不因法向为 -Z 而误判轮廓。

输出复制到目标目录后，核对文件大小或哈希一致，并向用户给出可点击的完整路径；无需自动在 AutoCAD 新开图纸，除非用户要求。
