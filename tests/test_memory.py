"""
测试 Memory 模块
"""
import pytest
import tempfile
import shutil
from pathlib import Path

from ghostwriter.memory import MemoryStore, EpisodicMemory, SemanticRule


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def memory_store(temp_data_dir):
    """创建测试用的 MemoryStore"""
    return MemoryStore(data_dir=temp_data_dir)


class TestEpisodicMemory:
    """情景记忆测试"""
    
    def test_add_and_retrieve_episode(self, memory_store):
        episode = EpisodicMemory(
            original="首先，我们来看一下这个问题。",
            revised="这个问题的核心在于...",
            context="上一段讨论了背景",
            diff_type="replace",
            level="sentence",
        )
        
        memory_store.add_episode(episode)
        episodes = memory_store.get_episodes()
        
        assert len(episodes) == 1
        assert episodes[0].original == "首先，我们来看一下这个问题。"
        assert episodes[0].revised == "这个问题的核心在于..."
    
    def test_episode_persistence(self, temp_data_dir):
        """测试持久化"""
        # 写入
        store1 = MemoryStore(data_dir=temp_data_dir)
        store1.add_episode(EpisodicMemory(
            original="test original",
            revised="test revised",
            context="ctx",
            diff_type="replace",
            level="sentence",
        ))
        
        # 重新加载
        store2 = MemoryStore(data_dir=temp_data_dir)
        episodes = store2.get_episodes()
        
        assert len(episodes) == 1
        assert episodes[0].original == "test original"
    
    def test_filter_by_level(self, memory_store):
        memory_store.add_episode(EpisodicMemory(
            original="s1", revised="s2", context="", diff_type="replace", level="sentence"
        ))
        memory_store.add_episode(EpisodicMemory(
            original="p1", revised="p2", context="", diff_type="replace", level="paragraph"
        ))
        
        sentences = memory_store.get_episodes(level="sentence")
        paragraphs = memory_store.get_episodes(level="paragraph")
        
        assert len(sentences) == 1
        assert len(paragraphs) == 1
        assert sentences[0].original == "s1"
        assert paragraphs[0].original == "p1"
    
    def test_search_episodes(self, memory_store):
        memory_store.add_episode(EpisodicMemory(
            original="Transformer 架构很重要",
            revised="Transformer 是核心架构",
            context="", diff_type="replace", level="sentence"
        ))
        memory_store.add_episode(EpisodicMemory(
            original="CNN 用于图像",
            revised="CNN 擅长处理图像",
            context="", diff_type="replace", level="sentence"
        ))
        
        results = memory_store.search_episodes("Transformer")
        assert len(results) == 1
        assert "Transformer" in results[0].original


class TestSemanticRules:
    """语义规则测试"""
    
    def test_add_and_retrieve_rule(self, memory_store):
        rule = SemanticRule(
            rule="技术术语保留英文",
            category="vocabulary",
            examples=["Transformer 不翻译为"变换器""],
        )
        
        memory_store.add_rule(rule)
        rules = memory_store.get_rules()
        
        assert len(rules) == 1
        assert rules[0].rule == "技术术语保留英文"
        assert rules[0].category == "vocabulary"
    
    def test_rule_confidence_increases(self, memory_store):
        """重复添加相同规则应增加置信度"""
        rule1 = SemanticRule(rule="避免长句", category="structure")
        rule2 = SemanticRule(rule="避免长句", category="structure")
        
        memory_store.add_rule(rule1)
        memory_store.add_rule(rule2)
        
        rules = memory_store.get_rules()
        assert len(rules) == 1
        assert rules[0].confidence > 1.0  # 初始1.0，增加后>1.0
    
    def test_filter_by_category(self, memory_store):
        memory_store.add_rule(SemanticRule(rule="r1", category="vocabulary"))
        memory_store.add_rule(SemanticRule(rule="r2", category="structure"))
        memory_store.add_rule(SemanticRule(rule="r3", category="tone"))
        
        vocab_rules = memory_store.get_rules(category="vocabulary")
        assert len(vocab_rules) == 1
        assert vocab_rules[0].rule == "r1"
    
    def test_get_all_rules_as_text(self, memory_store):
        memory_store.add_rule(SemanticRule(
            rule="技术术语保留英文",
            category="vocabulary",
            examples=["Transformer 不翻译"],
        ))
        
        text = memory_store.get_all_rules_as_text()
        assert "技术术语保留英文" in text
        assert "vocabulary" in text
    
    def test_empty_rules_text(self, memory_store):
        text = memory_store.get_all_rules_as_text()
        assert "暂无" in text


class TestMemoryStats:
    """统计测试"""
    
    def test_stats(self, memory_store):
        memory_store.add_episode(EpisodicMemory(
            original="a", revised="b", context="", diff_type="replace", level="sentence"
        ))
        memory_store.add_rule(SemanticRule(rule="r1", category="vocabulary"))
        memory_store.add_rule(SemanticRule(rule="r2", category="structure"))
        
        stats = memory_store.stats()
        
        assert stats["episodic_count"] == 1
        assert stats["semantic_rules_count"] == 2
        assert set(stats["categories"]) == {"vocabulary", "structure"}
