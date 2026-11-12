# 中文课程提交稿

提交文件为 `陈佳旭_多核上下文聚焦融合_课程论文.pdf`：A4 双栏中文正文，含中英文题目、作者单位、摘要与关键词。首页左下角仅放一个可点击的 GitHub 网址。

当前稿为 6 页，采用“引言—相关工作—方法—实验与结果分析—讨论—结论”的结构。正文为 9.4 pt、行距 14.8 pt；允许段落和表格按栏接续，避免标题整段绑定造成栏末大块空白。统计分析以归档的 22 次运行记录为依据，未增加未执行的实验。

## 字体与符号

- 中文正文采用基于 Noto Serif CJK SC 制作的 CourseSerif 字体子集，标题采用基于 Noto Sans CJK SC 制作的 CourseHei 黑体子集。
- 英文和数字采用 Liberation Serif（Times 风格），正确区分常规、粗体和斜体。
- 数学公式使用 STIX 字体绘制为 PDF 矢量文本；指标下标和上下标采用统一字号与基线。
- 中文字体子集随源文件提供，许可证见 `fonts/LICENSES.txt`。字体嵌入 PDF，阅读时不依赖本机字体。

## 源文件

- `main_zh.html`：可编辑的正文、表格与参考文献。
- `build_course_pdf.py`：生成双栏课程 PDF。
- `build_zh_pdf.py`：共享 HTML 解析与排版辅助代码。
- `course_typography.py`：中英文混排、字体选择与矢量公式。
- `prepare_course_fonts.py`：中文字体子集转换；正常重建直接使用随包字体。
- `fonts/`：已准备的中文字体、内容签名、哈希与许可说明。
- PNG 图片：结构图和实验曲线；单栏统计图位于 `../figures/robustness_summary_column.png`。

## 重建 PDF

在 Debian/Ubuntu 安装构建依赖及英文字体：

```bash
sudo apt-get install python3-reportlab python3-pil python3-matplotlib fonts-liberation2
MPLCONFIGDIR=/tmp/course-matplotlib python3 build_course_pdf.py
```

当前成品使用 Python 3.8、ReportLab 3.5.34、Matplotlib 3.7.5 构建。中文子集随包提供，无需安装全部 Noto 字库。如果修改正文后新增了子集中没有的字，需安装 `python3-fonttools fonts-noto-cjk`；辅助脚本会按新字符集重建子集。数学字形来自 Matplotlib 的 STIX 字体。字体路径在脚本中列明，其他系统可调整对应路径。

复现步骤见 [指南](../../docs/REPRODUCTION.md)，数据和权重下载清单见 [ASSETS.json](../../reproduction/ASSETS.json)。其中包含 baseline、FDPN 及对照/消融的全部 22 个权重。构建 PDF 不运行模型训练或推理。
