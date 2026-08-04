#!/usr/bin/env python3
"""
PDF 完整提取脚本 - 文本和嵌入图表提取（无表格）
"""
import os
import sys
import argparse
import re
import io

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import pypdfium2 as pdfium
except ImportError:
    pdfium = None

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import fitz
except ImportError:
    try:
        import pymupdf as fitz
    except ImportError:
        fitz = None


def clean_filename(name, max_len=50):
    if not name:
        return None
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', '_', name)
    return name[:max_len]


def get_page_text(page):
    try:
        textpage = page.get_textpage()
        text = textpage.get_text_bounded()
        return text
    except Exception:
        return ""


def extract_figure_captions(pdf_path):
    captions = {}
    try:
        if not pdfium:
            return captions
        pdf = pdfium.PdfDocument(pdf_path)
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            text = get_page_text(page)
            if not text:
                continue
            
            page_captions = []
            patterns = [
                r'Fig(?:ure)?\.?\s*(\d+[a-zA-Z]?)(?:[:\s]+([^.].*))?',
                r'图\s*(\d+)(?:\s*[-–:]\s*([^\n]{0,60}))?',
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    fig_id = match.group(1)
                    desc = match.group(2) if match.lastindex and match.lastindex >= 2 else ""
                    caption = f"Fig{fig_id}"
                    if desc:
                        desc = clean_filename(desc.strip(), 30)
                        caption += f"_{desc}"
                    if caption not in page_captions:
                        page_captions.append(caption)
            
            if page_captions:
                captions[page_num + 1] = page_captions
        
        pdf.close()
    except Exception:
        pass
    return captions


def extract_text_with_pdfplumber(pdf_path):
    if not pdfplumber:
        return None, "pdfplumber 未安装"
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"=== 第 {i+1} 页 ===\n{page_text}\n\n"
        return text, None
    except Exception as e:
        return None, str(e)


def extract_embedded_images(pdf_path, output_dir, min_size=(500, 500)):
    if not fitz:
        return [], "PyMuPDF (fitz) 未安装"
    
    figure_captions = extract_figure_captions(pdf_path)
    images_info = []
    seen_hashes = set()
    
    try:
        doc = fitz.open(pdf_path)
        fig_count = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)
            
            page_captions = figure_captions.get(page_num + 1, [])
            caption_idx = 0
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                width = base_image["width"]
                height = base_image["height"]
                
                if width < min_size[0] or height < min_size[1]:
                    continue
                
                aspect_ratio = max(width, height) / min(width, height) if min(width, height) > 0 else 0
                if aspect_ratio > 10:
                    continue
                
                if width * height < 90000:
                    continue
                
                image_hash = hash(image_bytes)
                if image_hash in seen_hashes:
                    continue
                seen_hashes.add(image_hash)
                
                fig_count += 1
                
                fig_name = None
                if page_captions and caption_idx < len(page_captions):
                    fig_name = page_captions[caption_idx]
                    caption_idx += 1
                
                try:
                    img_obj = Image.open(io.BytesIO(image_bytes))
                    if img_obj.mode not in ('RGB', 'RGBA', 'L'):
                        img_obj = img_obj.convert('RGB')
                    
                    if fig_name:
                        filename = f"fig_{fig_name}.png"
                    else:
                        filename = f"fig_p{page_num+1:02d}_{fig_count:02d}.png"
                    
                    image_path = os.path.join(output_dir, filename)
                    img_obj.save(image_path, "PNG")
                    img_obj.close()
                    
                    images_info.append({
                        "page": page_num + 1,
                        "file": image_path,
                        "name": fig_name,
                        "width": width,
                        "height": height
                    })
                except Exception:
                    continue
        
        doc.close()
        return images_info, None
        
    except Exception as e:
        return [], str(e)


def get_pdf_title(pdf_path):
    try:
        if pdfium:
            pdf = pdfium.PdfDocument(pdf_path)
            meta = pdf.metadata
            title = meta.get("title", "")
            pdf.close()
            if title and len(title) > 3:
                return clean_filename(title, 80)
    except Exception:
        pass
    
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    return base_name


def extract_pdf(pdf_path, output_dir=None, extract_images=True):
    if not os.path.exists(pdf_path):
        return {"error": f"文件不存在: {pdf_path}"}
    
    pdf_title = get_pdf_title(pdf_path)
    
    if not output_dir:
        output_dir = os.path.join(os.path.dirname(pdf_path), f"{pdf_title}_extracted")
    
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    figures_dir = os.path.join(output_dir, "extracted_figures")
    os.makedirs(figures_dir, exist_ok=True)
    
    result = {
        "pdf_path": pdf_path,
        "output_dir": output_dir,
        "pdf_title": pdf_title,
        "text": None,
        "images": [],
        "metadata": {},
        "stats": {},
        "errors": []
    }
    
    print(f"开始提取 PDF: {pdf_path}")
    print(f"论文标题: {pdf_title}")
    print(f"输出目录: {output_dir}")
    
    print("\n[1/2] 提取文本...")
    text, error = extract_text_with_pdfplumber(pdf_path)
    if error:
        result["errors"].append(f"文本提取失败: {error}")
        print(f"  失败: {error}")
    else:
        result["text"] = text
        result["stats"]["text_length"] = len(text)
        print(f"  文本长度: {len(text)} 字符")
    
    if extract_images:
        print("\n[2/2] 提取嵌入图表...")
        
        if fitz:
            images, error = extract_embedded_images(pdf_path, figures_dir)
            if error:
                print(f"  提取失败: {error}")
                result["errors"].append(f"图片提取失败: {error}")
            else:
                result["images"] = images
                print(f"  提取 {len(images)} 个图表图片")
        else:
            print("  PyMuPDF 未安装，跳过图片提取")
            result["errors"].append("PyMuPDF 未安装，无法提取图片")
    
    result["stats"]["images_count"] = len(result["images"])
    result["stats"]["errors"] = result["errors"]
    
    print("\n" + "=" * 50)
    print("提取完成!")
    print(f"  输出目录: {output_dir}")
    print(f"  文本字符数: {result['stats'].get('text_length', 0)}")
    print(f"  嵌入图表数量: {result['stats'].get('images_count', 0)}")
    if result["errors"]:
        print(f"  警告: {len(result['errors'])} 个")
    print("=" * 50)
    
    return result


def main():
    parser = argparse.ArgumentParser(description="PDF 完整提取工具 - 文本、嵌入图表（无表格）")
    parser.add_argument("pdf_path", help="PDF 文件路径")
    parser.add_argument("-o", "--output", help="输出目录（默认：{论文标题}_extracted）")
    
    args = parser.parse_args()
    result = extract_pdf(args.pdf_path, args.output)
    return 0 if not result.get("errors") else 1


if __name__ == "__main__":
    sys.exit(main())