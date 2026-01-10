"""
LLM utility functions
"""
import json
import re
from typing import Dict, List, Any, Optional


def extract_json(text: str) -> Optional[Dict]:
    """
    Extract JSON from text

    Args:
        text: text that may contain a JSON object

    Returns:
        Dict: Parsed JSON object if found, otherwise None
    """
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # 尝试查找 JSON 块
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text)
    
    if matches:
        # Return the longest match
        longest_match = max(matches, key=len)
        try:
            return json.loads(longest_match)
        except json.JSONDecodeError:
            pass
    
    return None


def format_list(items: List[str], separator: str = ", ") -> str:
    """
    Format a list of items into a string

    Args:
        items: list of items
        separator: separator string

    Returns:
        str: formatted string
    """
    if not items:
        return ""
    
    return separator.join(str(item) for item in items)


def extract_keywords(text: str) -> List[str]:
    """
    Extract keywords from text (simple implementation)

    Args:
        text: input text

    Returns:
        List[str]: list of keywords
    """
    # 简单的词频分析
    words = text.lower().split()
    
    # 过滤停用词和短词
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
        'of', 'by', 'with', 'from', 'as', 'this', 'that', 'these', 'those',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who'
    }
    
    keywords = [w for w in words if w not in stopwords and len(w) > 3]
    
    # 返回前 10 个最常见的词
    from collections import Counter
    return [word for word, _ in Counter(keywords).most_common(10)]


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and non-text characters

    Args:
        text: input text

    Returns:
        str: cleaned text
    """
    # 移除多余空格
    text = re.sub(r'\s+', ' ', text)
    # 移除特殊字符
    text = re.sub(r'[^\w\s\.\,\!\?\-\']', '', text)
    return text.strip()


def truncate_text(text: str, max_length: int = 500) -> str:
    """
    Truncate text to a maximum length, trying to cut at sentence boundary

    Args:
        text: input text
        max_length: maximum length

    Returns:
        str: truncated text
    """
    if len(text) <= max_length:
        return text
    
    # Try to truncate at a period
    truncated = text[:max_length]
    last_period = truncated.rfind('.')
    
    if last_period > max_length * 0.8:
        return text[:last_period + 1]
    
    return truncated + "..."
