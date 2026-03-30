"""
双记忆系统 - 情景记忆 + 语义记忆
"""
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import hashlib


@dataclass
class EpisodicMemory:
    """情景记忆：具体的写作片段案例"""
    original: str           # AI 原始生成
    revised: str            # 用户修改后
    context: str            # 上下文（前后段落）
    diff_type: str          # 修改类型: replace, delete, insert, reorder
    level: str              # 粒度: sentence, paragraph
    topic: Optional[str] = None  # 相关主题
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def id(self) -> str:
        """生成唯一 ID"""
        content = f"{self.original}|{self.revised}|{self.created_at}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]


@dataclass 
class SemanticRule:
    """语义记忆：抽象的风格规则"""
    rule: str               # 自然语言描述的规则
    category: str           # 分类: vocabulary, structure, tone, formatting
    examples: List[str] = field(default_factory=list)  # 支撑案例
    confidence: float = 1.0  # 置信度 (基于出现频率)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def id(self) -> str:
        content = f"{self.rule}|{self.category}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]


class MemoryStore:
    """记忆存储引擎"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.episodic_file = self.data_dir / "episodic_memory.jsonl"
        self.semantic_file = self.data_dir / "semantic_rules.json"
        
        self._episodic_cache: List[EpisodicMemory] = []
        self._semantic_cache: List[SemanticRule] = []
        
        self._load()
    
    def _load(self):
        """加载已有记忆"""
        # 加载情景记忆
        if self.episodic_file.exists():
            with open(self.episodic_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        self._episodic_cache.append(EpisodicMemory(**data))
        
        # 加载语义规则
        if self.semantic_file.exists():
            with open(self.semantic_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._semantic_cache = [SemanticRule(**r) for r in data]
    
    def _save_episodic(self):
        """追加保存情景记忆"""
        with open(self.episodic_file, "w", encoding="utf-8") as f:
            for mem in self._episodic_cache:
                f.write(json.dumps(asdict(mem), ensure_ascii=False) + "\n")
    
    def _save_semantic(self):
        """保存语义规则"""
        with open(self.semantic_file, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in self._semantic_cache], f, ensure_ascii=False, indent=2)
    
    # --- 情景记忆操作 ---
    
    def add_episode(self, episode: EpisodicMemory):
        """添加情景记忆"""
        self._episodic_cache.append(episode)
        self._save_episodic()
    
    def get_episodes(self, limit: int = 10, level: Optional[str] = None) -> List[EpisodicMemory]:
        """获取最近的情景记忆"""
        episodes = self._episodic_cache
        if level:
            episodes = [e for e in episodes if e.level == level]
        return episodes[-limit:]
    
    def search_episodes(self, query: str, limit: int = 5) -> List[EpisodicMemory]:
        """简单关键词搜索（后续可换成向量检索）"""
        results = []
        query_lower = query.lower()
        for ep in self._episodic_cache:
            if query_lower in ep.original.lower() or query_lower in ep.revised.lower():
                results.append(ep)
        return results[-limit:]
    
    # --- 语义规则操作 ---
    
    def add_rule(self, rule: SemanticRule):
        """添加或更新语义规则"""
        # 检查是否已存在类似规则
        for i, existing in enumerate(self._semantic_cache):
            if existing.rule == rule.rule:
                # 更新已有规则
                existing.confidence = min(existing.confidence + 0.1, 2.0)
                existing.examples.extend(rule.examples)
                existing.examples = existing.examples[-10:]  # 保留最近10个例子
                existing.updated_at = datetime.now().isoformat()
                self._save_semantic()
                return
        
        # 添加新规则
        self._semantic_cache.append(rule)
        self._save_semantic()
    
    def get_rules(self, category: Optional[str] = None, min_confidence: float = 0.5) -> List[SemanticRule]:
        """获取语义规则"""
        rules = self._semantic_cache
        if category:
            rules = [r for r in rules if r.category == category]
        rules = [r for r in rules if r.confidence >= min_confidence]
        return sorted(rules, key=lambda x: x.confidence, reverse=True)
    
    def get_all_rules_as_text(self) -> str:
        """将所有规则格式化为文本（用于 prompt）"""
        if not self._semantic_cache:
            return "暂无学习到的风格规则。"
        
        lines = ["已学习的写作风格规则：", ""]
        for rule in sorted(self._semantic_cache, key=lambda x: x.confidence, reverse=True):
            lines.append(f"- [{rule.category}] {rule.rule}")
            if rule.examples:
                lines.append(f"  例：{rule.examples[0]}")
        
        return "\n".join(lines)
    
    # --- 统计 ---
    
    def stats(self) -> dict:
        """返回记忆统计"""
        return {
            "episodic_count": len(self._episodic_cache),
            "semantic_rules_count": len(self._semantic_cache),
            "categories": list(set(r.category for r in self._semantic_cache)),
        }
