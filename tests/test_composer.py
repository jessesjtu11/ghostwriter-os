"""
测试 Composer 模块（不需要真实 LLM 调用）
"""
import pytest
from unittest.mock import MagicMock

from ghostwriter.composer import Composer
from ghostwriter.memory import MemoryStore, SemanticRule
from ghostwriter.llm import LLMResponse


@pytest.fixture
def mock_llm():
    """模拟 LLM Provider"""
    llm = MagicMock()
    llm.generate.return_value = LLMResponse(
        content="这是模拟的 LLM 输出内容。",
        model="mock-model",
    )
    llm.get_model_name.return_value = "mock-model"
    return llm


@pytest.fixture
def memory_store(tmp_path):
    return MemoryStore(data_dir=str(tmp_path))


class TestComposer:
    """Composer 测试"""
    
    def test_generate_outline(self, mock_llm, memory_store):
        composer = Composer(mock_llm, memory_store)
        
        outline = composer.generate_outline("测试主题")
        
        mock_llm.generate.assert_called_once()
        assert outline == "这是模拟的 LLM 输出内容。"
    
    def test_generate_draft(self, mock_llm, memory_store):
        composer = Composer(mock_llm, memory_store)
        
        draft = composer.generate_draft("# 大纲\n1. 引言\n2. 正文")
        
        mock_llm.generate.assert_called_once()
        assert draft == "这是模拟的 LLM 输出内容。"
    
    def test_compose_without_style(self, mock_llm, memory_store):
        """没有学习规则时，不应用风格"""
        composer = Composer(mock_llm, memory_store)
        
        result = composer.compose("测试主题", apply_style=True)
        
        assert result["topic"] == "测试主题"
        assert result["outline"] is not None
        assert result["draft"] is not None
        assert result["styled"] is not None
        assert result["style_applied"] is False  # 没有规则，不应用风格
    
    def test_compose_with_style(self, mock_llm, memory_store):
        """有规则时，应用风格重写"""
        # 添加一条规则
        memory_store.add_rule(SemanticRule(
            rule="技术术语保留英文",
            category="vocabulary",
        ))
        
        composer = Composer(mock_llm, memory_store)
        result = composer.compose("测试主题", apply_style=True)
        
        assert result["style_applied"] is True
        # 应该调用3次: outline, draft, style_rewrite
        assert mock_llm.generate.call_count == 3
    
    def test_compose_skip_style(self, mock_llm, memory_store):
        """显式跳过风格"""
        memory_store.add_rule(SemanticRule(rule="test", category="test"))
        
        composer = Composer(mock_llm, memory_store)
        result = composer.compose("测试主题", apply_style=False)
        
        assert result["style_applied"] is False
        # 只调用2次: outline, draft (跳过 style_rewrite)
        assert mock_llm.generate.call_count == 2
    
    def test_rewrite_includes_rules(self, mock_llm, memory_store):
        """风格重写时应包含已学习的规则"""
        memory_store.add_rule(SemanticRule(
            rule="避免使用首先其次最后",
            category="vocabulary",
        ))
        
        composer = Composer(mock_llm, memory_store)
        composer.rewrite_with_style("原始草稿内容")
        
        # 检查 prompt 中包含规则
        call_args = mock_llm.generate.call_args
        prompt = call_args[0][0]  # 第一个位置参数
        assert "避免使用首先其次最后" in prompt
