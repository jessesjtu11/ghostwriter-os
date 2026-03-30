"""
Diff Learner - 从用户编辑中学习风格规则
"""
import difflib
from dataclasses import dataclass
from typing import List, Optional, Tuple
from .memory import EpisodicMemory, SemanticRule, MemoryStore
from .llm import LLMProvider, LLMResponse


@dataclass
class DiffSegment:
    """差异片段"""
    original: str
    revised: str
    diff_type: str  # replace, delete, insert, equal
    level: str      # sentence, paragraph
    context_before: str = ""
    context_after: str = ""


class DiffAnalyzer:
    """分析原文和修改后的差异"""
    
    @staticmethod
    def split_sentences(text: str) -> List[str]:
        """简单的句子分割"""
        import re
        # 按中英文句号、问号、感叹号分割
        sentences = re.split(r'([。！？\.!?])', text)
        result = []
        for i in range(0, len(sentences) - 1, 2):
            result.append(sentences[i] + sentences[i + 1] if i + 1 < len(sentences) else sentences[i])
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            result.append(sentences[-1])
        return [s.strip() for s in result if s.strip()]
    
    @staticmethod
    def split_paragraphs(text: str) -> List[str]:
        """段落分割"""
        paragraphs = text.split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]
    
    def compute_diff(self, original: str, revised: str, level: str = "sentence") -> List[DiffSegment]:
        """计算差异"""
        if level == "sentence":
            orig_units = self.split_sentences(original)
            rev_units = self.split_sentences(revised)
        else:
            orig_units = self.split_paragraphs(original)
            rev_units = self.split_paragraphs(revised)
        
        segments = []
        matcher = difflib.SequenceMatcher(None, orig_units, rev_units)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            
            orig_text = ' '.join(orig_units[i1:i2]) if i1 < i2 else ""
            rev_text = ' '.join(rev_units[j1:j2]) if j1 < j2 else ""
            
            # 获取上下文
            ctx_before = orig_units[max(0, i1-1)] if i1 > 0 else ""
            ctx_after = orig_units[min(len(orig_units)-1, i2)] if i2 < len(orig_units) else ""
            
            diff_type = tag  # replace, delete, insert
            
            segments.append(DiffSegment(
                original=orig_text,
                revised=rev_text,
                diff_type=diff_type,
                level=level,
                context_before=ctx_before,
                context_after=ctx_after,
            ))
        
        return segments


class DiffLearner:
    """从差异中学习风格规则"""
    
    RULE_EXTRACTION_PROMPT = """你是一个写作风格分析专家。根据用户的修改行为，提取出可复用的风格规则。

原文：
{original}

用户修改为：
{revised}

修改类型：{diff_type}
上下文：{context}

请分析这个修改，提取出 1-2 条风格规则。每条规则应该：
1. 是可泛化的（不是针对具体内容的）
2. 用自然语言描述
3. 指明类别（vocabulary/structure/tone/formatting）

输出格式（JSON）：
[
  {{"rule": "规则描述", "category": "类别", "example": "这次修改的简短说明"}}
]

如果这个修改是内容修正（比如错别字、事实错误）而非风格调整，返回空数组 []。
"""
    
    def __init__(self, llm: LLMProvider, memory: MemoryStore):
        self.llm = llm
        self.memory = memory
        self.analyzer = DiffAnalyzer()
    
    def learn_from_edit(self, original: str, revised: str) -> dict:
        """从一次编辑中学习"""
        results = {
            "episodes_added": 0,
            "rules_extracted": [],
        }
        
        # 分析句子级和段落级差异
        for level in ["sentence", "paragraph"]:
            segments = self.analyzer.compute_diff(original, revised, level)
            
            for seg in segments:
                # 1. 保存情景记忆
                episode = EpisodicMemory(
                    original=seg.original,
                    revised=seg.revised,
                    context=f"前：{seg.context_before}\n后：{seg.context_after}",
                    diff_type=seg.diff_type,
                    level=seg.level,
                )
                self.memory.add_episode(episode)
                results["episodes_added"] += 1
                
                # 2. 用 LLM 提取规则（仅对有实质修改的情况）
                if seg.diff_type == "replace" and seg.original and seg.revised:
                    rules = self._extract_rules(seg)
                    for rule_data in rules:
                        rule = SemanticRule(
                            rule=rule_data["rule"],
                            category=rule_data.get("category", "general"),
                            examples=[rule_data.get("example", "")],
                        )
                        self.memory.add_rule(rule)
                        results["rules_extracted"].append(rule.rule)
        
        return results
    
    def _extract_rules(self, segment: DiffSegment) -> List[dict]:
        """用 LLM 从差异中提取规则"""
        prompt = self.RULE_EXTRACTION_PROMPT.format(
            original=segment.original,
            revised=segment.revised,
            diff_type=segment.diff_type,
            context=f"{segment.context_before} [...] {segment.context_after}",
        )
        
        try:
            response = self.llm.generate(prompt)
            # 解析 JSON
            import json
            import re
            # 尝试提取 JSON 数组
            match = re.search(r'\[.*\]', response.content, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            print(f"规则提取失败: {e}")
        
        return []
