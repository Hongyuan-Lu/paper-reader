# PDF 处理详细参考

本文件是 paper-reader skill 的 PDF 处理子模块，提供论文 PDF 解析所需的完整技术参考。

## 核心依赖

```bash
pip install pypdf pdfplumber pypdfium2 Pillow
```

## 1. 文本提取

### 方法一：pypdf（基础文本提取）

```python
from pypdf import PdfReader

reader = PdfReader("论文.pdf")
text = ""
for page in reader.pages:
    text += page.extract_text() or ""

print(f"共 {len(reader.pages)} 页")
```

### 方法二：pdfplumber（推荐，用于保留布局和表格）

```python
import pdfplumber

with pdfplumber.open("论文.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        tables = page.extract_tables()
        print(f"第 {i+1} 页：{len(text)} 字符，{len(tables)} 个表格")
```

### 方法三：pypdfium2（高性能渲染和文本提取）

```python
import pypdfium2 as pdfium

pdf = pdfium.PdfDocument("论文.pdf")
for i, page in enumerate(pdf):
    text = page.get_text()
    print(f"第 {i+1} 页：{len(text)} 字符")
```

## 2. 图表与图片提取

### 提取 PDF 中的图片

```bash
pdfimages -j input.pdf output_prefix
```

### 使用 pypdfium2 将 PDF 页面渲染为图片

```python
import pypdfium2 as pdfium
from PIL import Image

pdf = pdfium.PdfDocument("论文.pdf")
for i, page in enumerate(pdf):
    bitmap = page.render(scale=2.0)
    img = bitmap.to_pil()
    img.save(f"page_{i+1}.png")
```

### 提取图表并保存

```python
import os
import pdfplumber

def extract_figures_and_tables(pdf_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    with pdfplumber.open(pdf_path) as pdf:
        fig_count = 0
        table_count = 0
        
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for table in tables:
                if table:
                    table_count += 1
                    # 保存表格数据
                    with open(f"{output_dir}/table_{table_count:03d}.txt", "w", encoding="utf-8") as f:
                        for row in table:
                            f.write("\t".join(str(cell) if cell else "" for cell in row) + "\n")
    
    return fig_count, table_count
```

## 3. 元信息提取

```python
from pypdf import PdfReader

reader = PdfReader("论文.pdf")
meta = reader.metadata

print(f"标题: {meta.title}")
print(f"作者: {meta.author}")
print(f"主题: {meta.subject}")
print(f"创建者: {meta.creator}")
print(f"页数: {len(reader.pages)}")
```

## 4. 命令行工具

### pdftotext（保留布局）

```bash
pdftotext -r 300 -layout "论文.pdf" "输出.txt"
```

### pdfimages（提取图片）

```bash
# 提取所有图片为 JPEG
pdfimages -j "论文.pdf" "fig"

# 提取为 PNG
pdfimages -png "论文.pdf" "fig"
```

## 5. 表格详细提取

```python
import pdfplumber
import pandas as pd

def extract_all_tables(pdf_path):
    all_tables = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for j, table in enumerate(tables):
                if table:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    df['source_page'] = i + 1
                    df['table_index'] = j + 1
                    all_tables.append(df)
    
    return all_tables

tables = extract_all_tables("论文.pdf")
if tables:
    combined = pd.concat(tables, ignore_index=True)
    combined.to_csv("all_tables.csv", index=False)
```

## 6. 快速参考表

| 任务 | 推荐方法 | 代码 |
|------|----------|------|
| 基本文本提取 | pypdf | `page.extract_text()` |
| 保留布局提取 | pdftotext | `pdftotext -layout file.pdf -` |
| 表格提取 | pdfplumber | `page.extract_tables()` |
| 图表渲染 | pypdfium2 | `page.render(scale=2.0)` |
| 图片提取 | pdfimages | `pdfimages -j file.pdf prefix` |
| 元信息 | pypdf | `reader.metadata` |