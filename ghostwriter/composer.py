"""
Composer - 生成 + 风格重写
"""
from typing import Optional, List
from .llm import LLMProvider
from .memory import MemoryStore


class Composer:
    """内容生成 + 风格重写"""
    
    OUTLINE_PROMPT = """你是一个技术写作专家。根据给定主题，生成一篇技术文章的大纲。

主题：{topic}

要求：
1. 结构清晰，逻辑连贯
2. 包含引言、正文（3-5个要点）、结论
3. 每个要点用一句话描述核心内容

输出 Markdown 格式的大纲。
"""
    
    DRAFT_PROMPT = """你是一个技术写作专家。根据大纲，写一篇完整的技术文章。

大纲：
{outline}

要求：
1. 内容准确、逻辑清晰
2. 保持中立的写作风格（后续会进行风格调整）
3. 每段控制在 3-5 句话
4. 输出 Markdown 格式

直接输出文章内容，不要额外说明。
"""
    
    STYLE_REWRITE_PROMPT = """你是一个写作风格调整专家。根据用户的风格偏好，重写给定的文章。

原文：
{draft}

用户的风格规则：
{style_rules}

参考案例（用户之前的修改）：
{examples}

要求：
1. 保持原文的核心内容和逻辑不变
2. 按照风格规则调整表达方式
3. 参考案例中的修改风格
4. 如果没有足够的风格信息，保持原文风格

直接输出重写后的文章，不要额外说明。
"""
    
    def __init__(self, llm: LLMProvider, memory: MemoryStore):
        self.llm = llm
        self.memory = memory
    
    def generate_outline(self, topic: str) -> str:
        """生成大纲"""
        prompt = self.OUTLINE_PROMPT.format(topic=topic)
        response = self.llm.generate(prompt)
        return response.content
    
    def generate_draft(self, outline: str) -> str:
        """根据大纲生成中性草稿"""
        prompt = self.DRAFT_PROMPT.format(outline=outline)
        response = self.llm.generate(prompt)
        return response.content
    
    def rewrite_with_style(self, draft: str) -> str:
        """用学习到的风格重写"""
        # 获取风格规则
        style_rules = self.memory.get_all_rules_as_text()
        
        # 获取最近的情景记忆作为参考
        episodes = self.memory.get_episodes(limit=5)
        examples = ""
        if episodes:
            examples_list = []
            for ep in episodes:
                if ep.diff_type == "replace":
                    examples_list.append(f"原：{ep.original}\n改：{ep.revised}")
            examples = "\n\n".join(examples_list[-3:]) if examples_list else "暂无参考案例"
        else:
            examples = "暂无参考案例"
        
        prompt = self.STYLE_REWRITE_PROMPT.format(
            draft=draft,
            style_rules=style_rules,
            examples=examples,
        )
        
        response = self.llm.generate(prompt)
        return response.content
    
    def compose(self, topic: str, apply_style: bool = True) -> dict:
        """完整的生成流程"""
        # 1. 生成大纲
        outline = self.generate_outline(topic)
        
        # 2. 生成中性草稿
        draft = self.generate_draft(outline)
        
        # 3. 风格重写（如果有学习到的风格）
        styled = draft
        if apply_style and self.memory.get_rules():
            styled = self.rewrite_with_style(draft)
        
        return {
            "topic": topic,
            "outline": outline,
            "draft": draft,
            "styled": styled,
            "style_applied": apply_style and bool(self.memory.get_rules()),
        }
