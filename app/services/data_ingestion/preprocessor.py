"""
数据预处理模块
负责清洗和标准化来自各种渠道的用户反馈数据
"""
import re
import html
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

from bs4 import BeautifulSoup
import pandas as pd

logger = logging.getLogger(__name__)


class FeedbackPreprocessor:
    """用户反馈预处理器"""
    
    def __init__(self):
        # 常见的无用模板文本模式
        self.template_patterns = [
            r"发送自\s*iPhone",
            r"Sent from my iPhone",
            r"发送自\s*我的\s*\w+手机",
            r"获取\s*Outlook.*",
            r"Get Outlook.*",
            r"此邮件.*保密.*",
            r"This email.*confidential.*",
            r"版权所有.*",
            r"Copyright.*",
            r"免责声明.*",
            r"Disclaimer.*"
        ]
        
        # 表情符号正则模式
        self.emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
    
    def clean_html_tags(self, text: str) -> str:
        """移除HTML标签"""
        if not text:
            return ""
        
        # 使用BeautifulSoup移除HTML标签
        soup = BeautifulSoup(text, "html.parser")
        cleaned_text = soup.get_text()
        
        # 解码HTML实体
        cleaned_text = html.unescape(cleaned_text)
        
        return cleaned_text
    
    def remove_template_text(self, text: str) -> str:
        """移除模板化文本"""
        if not text:
            return ""
        
        cleaned_text = text
        for pattern in self.template_patterns:
            cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE)
        
        return cleaned_text.strip()
    
    def normalize_whitespace(self, text: str) -> str:
        """标准化空白字符"""
        if not text:
            return ""
        
        # 替换多个连续空格为单个空格
        text = re.sub(r'\s+', ' ', text)
        
        # 移除行首行尾空格
        text = text.strip()
        
        return text
    
    def remove_excessive_punctuation(self, text: str) -> str:
        """移除过多的标点符号"""
        if not text:
            return ""
        
        # 移除连续的感叹号和问号（保留最多3个）
        text = re.sub(r'[!]{4,}', '!!!', text)
        text = re.sub(r'[?]{4,}', '???', text)
        text = re.sub(r'[.]{4,}', '...', text)
        
        return text
    
    def handle_emojis(self, text: str, keep_emojis: bool = True) -> str:
        """处理表情符号"""
        if not text:
            return ""
        
        if keep_emojis:
            # 保留表情符号，但在前后添加空格以便处理
            text = self.emoji_pattern.sub(r' \g<0> ', text)
        else:
            # 移除表情符号
            text = self.emoji_pattern.sub('', text)
        
        return text
    
    def detect_language(self, text: str) -> str:
        """简单的语言检测"""
        if not text:
            return "unknown"
        
        # 检测中文字符
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        english_chars = re.findall(r'[a-zA-Z]', text)
        
        chinese_ratio = len(chinese_chars) / len(text) if text else 0
        english_ratio = len(english_chars) / len(text) if text else 0
        
        if chinese_ratio > 0.3:
            return "zh"
        elif english_ratio > 0.5:
            return "en"
        else:
            return "unknown"
    
    def extract_keywords(self, text: str) -> List[str]:
        """提取基础关键词"""
        if not text:
            return []
        
        # 简单的关键词提取（可以后续用更复杂的NLP方法替换）
        # 移除标点符号
        text_clean = re.sub(r'[^\w\s]', ' ', text)
        
        # 分词
        words = text_clean.lower().split()
        
        # 过滤停用词和短词
        stop_words = {'的', '了', '是', '在', '有', '和', '对', '我', '你', '他', '她', '它',
                     'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an', 'as', 'are',
                     'was', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does',
                     'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must'}
        
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # 返回前10个关键词
        return keywords[:10]
    
    def preprocess_feedback(self, 
                          original_text: str, 
                          source: str = "unknown",
                          metadata: Optional[Dict] = None) -> Dict:
        """预处理单条反馈"""
        
        processing_steps = []
        
        # 1. 基础清理
        text = original_text or ""
        processing_steps.append(f"原始长度: {len(text)}")
        
        # 2. 清理HTML标签
        text = self.clean_html_tags(text)
        processing_steps.append(f"清理HTML后长度: {len(text)}")
        
        # 3. 移除模板文本
        text = self.remove_template_text(text)
        processing_steps.append(f"移除模板后长度: {len(text)}")
        
        # 4. 处理表情符号
        text = self.handle_emojis(text, keep_emojis=True)
        
        # 5. 标准化空白字符
        text = self.normalize_whitespace(text)
        
        # 6. 移除过多标点符号
        text = self.remove_excessive_punctuation(text)
        processing_steps.append(f"最终长度: {len(text)}")
        
        # 7. 语言检测
        language = self.detect_language(text)
        
        # 8. 提取关键词
        keywords = self.extract_keywords(text)
        
        # 9. 质量评估
        quality_score = self._assess_quality(text)
        
        result = {
            "original_text": original_text,
            "processed_text": text,
            "source": source,
            "language": language,
            "keywords": keywords,
            "quality_score": quality_score,
            "processing_steps": processing_steps,
            "metadata": metadata or {},
            "processed_at": datetime.now().isoformat()
        }
        
        return result
    
    def _assess_quality(self, text: str) -> float:
        """评估文本质量"""
        if not text or len(text.strip()) < 5:
            return 0.0
        
        score = 1.0
        
        # 长度评分
        if len(text) < 10:
            score *= 0.3
        elif len(text) < 20:
            score *= 0.6
        elif len(text) > 2000:
            score *= 0.8
        
        # 字符种类评分
        has_letters = bool(re.search(r'[a-zA-Z\u4e00-\u9fff]', text))
        if not has_letters:
            score *= 0.2
        
        # 重复字符评分
        repeated_chars = len(re.findall(r'(.)\1{5,}', text))
        if repeated_chars > 0:
            score *= 0.5
        
        # 大写字母比例评分
        if text.isupper() and len(text) > 20:
            score *= 0.7
        
        return max(0.0, min(1.0, score))
    
    def preprocess_batch(self, feedback_list: List[Dict]) -> List[Dict]:
        """批量预处理反馈"""
        results = []
        
        for i, feedback_data in enumerate(feedback_list):
            try:
                text = feedback_data.get("text", "")
                source = feedback_data.get("source", "unknown")
                metadata = feedback_data.get("metadata", {})
                
                result = self.preprocess_feedback(text, source, metadata)
                results.append(result)
                
            except Exception as e:
                logger.error(f"预处理第{i+1}条反馈失败: {e}")
                # 添加错误结果
                results.append({
                    "original_text": feedback_data.get("text", ""),
                    "processed_text": "",
                    "source": feedback_data.get("source", "unknown"),
                    "language": "unknown",
                    "keywords": [],
                    "quality_score": 0.0,
                    "processing_steps": [f"预处理失败: {str(e)}"],
                    "metadata": feedback_data.get("metadata", {}),
                    "processed_at": datetime.now().isoformat()
                })
        
        return results
    
    def get_processing_stats(self, results: List[Dict]) -> Dict:
        """获取预处理统计信息"""
        if not results:
            return {}
        
        total_count = len(results)
        
        # 语言分布
        languages = [r.get("language", "unknown") for r in results]
        language_counts = pd.Series(languages).value_counts().to_dict()
        
        # 质量分布
        quality_scores = [r.get("quality_score", 0.0) for r in results]
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        # 长度统计
        text_lengths = [len(r.get("processed_text", "")) for r in results]
        avg_length = sum(text_lengths) / len(text_lengths)
        
        # 来源统计
        sources = [r.get("source", "unknown") for r in results]
        source_counts = pd.Series(sources).value_counts().to_dict()
        
        return {
            "total_count": total_count,
            "language_distribution": language_counts,
            "average_quality_score": round(avg_quality, 3),
            "average_text_length": round(avg_length, 1),
            "source_distribution": source_counts,
            "quality_distribution": {
                "high_quality": len([s for s in quality_scores if s >= 0.8]),
                "medium_quality": len([s for s in quality_scores if 0.5 <= s < 0.8]),
                "low_quality": len([s for s in quality_scores if s < 0.5])
            }
        }


# 创建全局预处理器实例
preprocessor = FeedbackPreprocessor() 