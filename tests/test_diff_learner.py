"""
测试 Diff Learner 模块
"""
import pytest

from ghostwriter.diff_learner import DiffAnalyzer, DiffSegment


class TestDiffAnalyzer:
    """Diff 分析器测试"""
    
    @pytest.fixture
    def analyzer(self):
        return DiffAnalyzer()
    
    def test_split_sentences_chinese(self, analyzer):
        text = "这是第一句。这是第二句！这是第三句？"
        sentences = analyzer.split_sentences(text)
        
        assert len(sentences) == 3
        assert sentences[0] == "这是第一句。"
        assert sentences[1] == "这是第二句！"
        assert sentences[2] == "这是第三句？"
    
    def test_split_sentences_english(self, analyzer):
        text = "This is first. This is second! This is third?"
        sentences = analyzer.split_sentences(text)
        
        assert len(sentences) == 3
    
    def test_split_paragraphs(self, analyzer):
        text = "第一段内容。\n\n第二段内容。\n\n第三段内容。"
        paragraphs = analyzer.split_paragraphs(text)
        
        assert len(paragraphs) == 3
        assert paragraphs[0] == "第一段内容。"
    
    def test_compute_diff_replace(self, analyzer):
        original = "首先，我们来看问题。然后分析原因。"
        revised = "问题的核心在于什么？然后分析原因。"
        
        segments = analyzer.compute_diff(original, revised, level="sentence")
        
        # 应该有一个 replace
        replace_segments = [s for s in segments if s.diff_type == "replace"]
        assert len(replace_segments) >= 1
    
    def test_compute_diff_delete(self, analyzer):
        original = "第一句。第二句。第三句。"
        revised = "第一句。第三句。"
        
        segments = analyzer.compute_diff(original, revised, level="sentence")
        
        delete_segments = [s for s in segments if s.diff_type == "delete"]
        assert len(delete_segments) >= 1
    
    def test_compute_diff_insert(self, analyzer):
        original = "第一句。第三句。"
        revised = "第一句。新增的句子。第三句。"
        
        segments = analyzer.compute_diff(original, revised, level="sentence")
        
        insert_segments = [s for s in segments if s.diff_type == "insert"]
        assert len(insert_segments) >= 1
    
    def test_compute_diff_no_change(self, analyzer):
        text = "完全相同的内容。没有任何修改。"
        
        segments = analyzer.compute_diff(text, text, level="sentence")
        
        assert len(segments) == 0
    
    def test_paragraph_level_diff(self, analyzer):
        original = "第一段。\n\n第二段要删除。\n\n第三段。"
        revised = "第一段。\n\n第三段。"
        
        segments = analyzer.compute_diff(original, revised, level="paragraph")
        
        assert len(segments) >= 1
        assert any(s.diff_type == "delete" for s in segments)


class TestDiffSegment:
    """DiffSegment 数据类测试"""
    
    def test_create_segment(self):
        seg = DiffSegment(
            original="原文",
            revised="修改后",
            diff_type="replace",
            level="sentence",
            context_before="前文",
            context_after="后文",
        )
        
        assert seg.original == "原文"
        assert seg.revised == "修改后"
        assert seg.diff_type == "replace"
        assert seg.level == "sentence"
