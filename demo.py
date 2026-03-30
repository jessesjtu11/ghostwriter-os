#!/usr/bin/env python3
"""
Ghostwriter Demo - 不需要 API Key，展示核心流程
"""
from ghostwriter.memory import MemoryStore, EpisodicMemory, SemanticRule
from ghostwriter.diff_learner import DiffAnalyzer
import tempfile
import shutil


def main():
    print("=" * 60)
    print("🖊️  Ghostwriter OS Demo")
    print("=" * 60)
    print()
    
    # 使用临时目录
    temp_dir = tempfile.mkdtemp()
    memory = MemoryStore(data_dir=temp_dir)
    analyzer = DiffAnalyzer()
    
    # === 模拟用户修改 ===
    print("📝 模拟场景：用户修改了 AI 生成的文章")
    print("-" * 40)
    
    original = """首先，我们来看一下 Transformer 的基本概念。
Transformer 是一种用于自然语言处理的深度学习模型。
其次，让我们分析它的核心组件——自注意力机制。
最后，我们总结一下 Transformer 的优势。"""
    
    revised = """Transformer 的核心是什么？让我们直接切入正题。
Transformer 是 NLP 领域的核心架构，几乎统治了现代语言模型。
自注意力机制 (Self-Attention) 是它的灵魂——允许模型在处理每个词时"看到"整个句子。
简单说：Transformer 快、并行、能捕捉长距离依赖。这就是它赢的原因。"""
    
    print("原文 (AI 生成)：")
    print(original)
    print()
    print("用户修改后：")
    print(revised)
    print()
    
    # === 分析差异 ===
    print("🔍 分析差异...")
    print("-" * 40)
    
    segments = analyzer.compute_diff(original, revised, level="sentence")
    
    for i, seg in enumerate(segments):
        print(f"\n[{seg.diff_type.upper()}] {seg.level}")
        if seg.original:
            print(f"  原: {seg.original[:50]}...")
        if seg.revised:
            print(f"  改: {seg.revised[:50]}...")
        
        # 保存情景记忆
        memory.add_episode(EpisodicMemory(
            original=seg.original,
            revised=seg.revised,
            context="demo context",
            diff_type=seg.diff_type,
            level=seg.level,
        ))
    
    # === 模拟规则提取 (不调用 LLM，手动添加) ===
    print("\n\n📚 提取风格规则（模拟）...")
    print("-" * 40)
    
    rules = [
        SemanticRule(
            rule="开头用问句引入，激发读者思考",
            category="structure",
            examples=["Transformer 的核心是什么？"],
        ),
        SemanticRule(
            rule="避免使用「首先、其次、最后」等模板连接词",
            category="vocabulary",
            examples=["删除了「首先，我们来看一下」"],
        ),
        SemanticRule(
            rule="技术术语保留英文并加中文注释",
            category="vocabulary", 
            examples=["Self-Attention（自注意力机制）"],
        ),
        SemanticRule(
            rule="结尾用简洁有力的总结句",
            category="tone",
            examples=["这就是它赢的原因。"],
        ),
    ]
    
    for rule in rules:
        memory.add_rule(rule)
        print(f"  ✓ [{rule.category}] {rule.rule}")
    
    # === 展示记忆状态 ===
    print("\n\n📊 记忆状态")
    print("-" * 40)
    
    stats = memory.stats()
    print(f"  情景记忆: {stats['episodic_count']} 条")
    print(f"  风格规则: {stats['semantic_rules_count']} 条")
    print(f"  规则类别: {', '.join(stats['categories'])}")
    
    print("\n\n📖 所有规则（可直接用于 Prompt）：")
    print("-" * 40)
    print(memory.get_all_rules_as_text())
    
    # === 模拟风格重写 Prompt ===
    print("\n\n🎨 风格重写 Prompt 示例")
    print("-" * 40)
    
    new_topic_draft = """首先，CNN 和 RNN 都是深度学习中的重要架构。
其次，CNN 主要用于处理图像数据。
最后，RNN 适合处理序列数据。"""
    
    print("待重写的中性草稿：")
    print(new_topic_draft)
    print()
    print("重写指令（将发送给 LLM）：")
    print(f"""
你是一个写作风格调整专家。根据用户的风格偏好，重写给定的文章。

原文：
{new_topic_draft}

用户的风格规则：
{memory.get_all_rules_as_text()}

参考案例（用户之前的修改）：
原：首先，我们来看一下 Transformer 的基本概念。
改：Transformer 的核心是什么？让我们直接切入正题。

要求：
1. 保持原文的核心内容和逻辑不变
2. 按照风格规则调整表达方式

直接输出重写后的文章。
""")
    
    # 清理
    shutil.rmtree(temp_dir)
    
    print("\n" + "=" * 60)
    print("✅ Demo 完成！")
    print()
    print("下一步：配置你的 LLM API Key，然后运行：")
    print("  ghostwriter write \"你想写的主题\"")
    print("  ghostwriter learn original.md revised.md")
    print("=" * 60)


if __name__ == "__main__":
    main()
