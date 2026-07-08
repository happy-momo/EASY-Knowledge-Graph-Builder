import pandas as pd
from pypdf import PdfReader
from docx import Document
import io
import re
import math


def smart_text_segmentation(text, max_chunk_size=2000, min_chunk_size=500):
    """
    智能文本切分：保持语义完整性，控制处理时间
    
    Args:
        text: 原始文本
        max_chunk_size: 最大块大小（字符数）
        min_chunk_size: 最小块大小（字符数）
    
    Returns:
        切分后的文本块列表
    """
    # 1. 预处理：清理特殊符号，保留语义关系
    # 保留中文字符、英文字母、数字、基本标点（逗号、句号、冒号、分号）
    cleaned_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s,，.。:：;；!！?？]', '', text)
    
    # 2. 按段落分割（基于换行符）
    paragraphs = [p.strip() for p in cleaned_text.split('\n') if p.strip()]
    
    # 3. 如果文本较短，直接返回
    if len(cleaned_text) <= max_chunk_size:
        return [cleaned_text]
    
    # 4. 智能合并段落，构建语义块
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # 如果当前段落过长，单独处理
        if len(paragraph) > max_chunk_size:
            # 将长段落按句子分割，但保持语义关系
            sentences = re.split(r'[。！？!?]', paragraph)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 1 > max_chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk)
                        current_chunk = ""
                
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # 正常段落处理
        elif len(current_chunk) + len(paragraph) + 1 > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                chunks.append(paragraph)
                current_chunk = ""
        else:
            if current_chunk:
                current_chunk += " " + paragraph
            else:
                current_chunk = paragraph
    
    # 添加最后一个块
    if current_chunk:
        chunks.append(current_chunk)
    
    # 5. 合并过小的块（避免过多小请求）
    merged_chunks = []
    temp_chunk = ""
    
    for chunk in chunks:
        if len(temp_chunk) + len(chunk) + 1 <= max_chunk_size:
            if temp_chunk:
                temp_chunk += " " + chunk
            else:
                temp_chunk = chunk
        else:
            if temp_chunk:
                merged_chunks.append(temp_chunk)
                temp_chunk = chunk
            else:
                merged_chunks.append(chunk)
    
    if temp_chunk:
        merged_chunks.append(temp_chunk)
    
    # 6. 确保每个块都有足够的语义内容
    final_chunks = []
    for chunk in merged_chunks:
        if len(chunk) >= min_chunk_size:
            final_chunks.append(chunk)
        else:
            # 如果块太小，尝试与相邻块合并
            if final_chunks:
                final_chunks[-1] += " " + chunk
            else:
                final_chunks.append(chunk)
    
    return final_chunks


def clean_special_characters(text):
    """
    清理特殊符号，保留语义关系
    """
    # 保留中文字符、英文字母、数字、基本标点
    cleaned = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s,，.。:：;；!！?？\-\—（）()【】\[\]《》]', '', text)
    
    # 标准化空格：多个连续空格替换为单个空格
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    return cleaned.strip()


def load_document(uploaded_file, max_chunk_size=2000, min_chunk_size=500):
    """
    根据文件类型加载内容，返回智能切分的文本块列表
    
    Args:
        uploaded_file: 上传的文件对象
        max_chunk_size: 最大块大小（字符数）
        min_chunk_size: 最小块大小（字符数）
    
    Returns:
        (文本块列表, 错误信息)
    """
    file_type = uploaded_file.name.split('.')[-1].lower()
    text_content = ""

    try:
        if file_type in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file)
            # 按行处理，保持行间语义关系
            text_list = []
            for index, row in df.iterrows():
                row_text = " ".join([str(cell) for cell in row if pd.notna(cell)])
                if row_text.strip():
                    text_list.append(row_text)
            text_content = "\n".join(text_list)

        elif file_type == 'pdf':
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text.strip():
                    text_content += page_text + "\n"

        elif file_type in ['docx', 'doc']:
            doc = Document(uploaded_file)
            for para in doc.paragraphs:
                if para.text.strip():
                    text_content += para.text + "\n"

        elif file_type == 'txt':
            raw_bytes = uploaded_file.read()
            # 尝试多种编码解码，优先 UTF-8
            for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']:
                try:
                    text_content = raw_bytes.decode(encoding)
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            else:
                return None, "无法解码文本文件，请确认文件编码"

        else:
            return None, "不支持的文件格式"

    except Exception as e:
        return None, f"解析失败: {str(e)}"

    # 清理特殊符号并智能切分
    cleaned_text = clean_special_characters(text_content)
    if not cleaned_text:
        return None, "文档内容为空或无法解析"
    
    chunks = smart_text_segmentation(cleaned_text, max_chunk_size, min_chunk_size)
    return chunks, None