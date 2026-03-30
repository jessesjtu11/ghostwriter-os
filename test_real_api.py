#!/usr/bin/env python3
"""
真实 API 测试 - 使用阮一峰的写作风格
"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace/ghostwriter-os')

from ghostwriter.llm import OpenAIProvider
from ghostwriter.memory import MemoryStore, SemanticRule, EpisodicMemory
from ghostwriter.composer import Composer
from ghostwriter.diff_learner import DiffLearner
import tempfile

# 配置
API_KEY = "sk-iuVjp21AqhBKycFrNzPbPOfiz6KsK51LUK8Hfp6rJsHvLJld"
BASE_URL = "https://openrouter.chipltech.com/v1"
MODEL = "gpt-4o-mini"  # 用便宜的模型测试

# 阮一峰风格的文章片段（作为"用户修改后"的参考）
RUANYIFENG_STYLE = """
很多人可能不知道，计算的本质是什么。

简单说，计算就是状态的变化。你有一个初始状态，经过一系列操作，变成最终状态。这就是计算。

举例来说，1 + 1 = 2。初始状态是"1和1"，最终状态是"2"，中间的操作是"加法"。

图灵机就是基于这个思想。它有一条无限长的纸带，上面写着符号。机器读取符号，根据规则改写符号，然后移动。就这么简单。

所以，任何可以描述为"状态变化"的问题，理论上都可以计算。这就是图灵的贡献。
"""

# AI 生成的中性版本（模拟）
AI_NEUTRAL = """
首先，我们来探讨计算的本质概念。

计算的定义可以理解为状态的转换过程。具体而言，从一个初始状态出发，通过一系列规定的操作，最终达到目标状态。这一过程即为计算的核心。

以加法运算为例：初始状态为两个数字1和1，经过加法操作后，得到最终状态2。这个简单的例子展示了计算的基本模式。

图灵机作为计算理论的重要模型，其设计思想正是基于上述原理。它由一条无限长的纸带组成，纸带上存储着符号。机器读取当前符号，依据预设规则进行改写，随后移动读写头。这种机制虽然简单，却能模拟任何计算过程。

综上所述，凡是能够被描述为"状态变化"的问题，在理论上都具有可计算性。这正是图灵在计算理论领域的重大贡献。
"""

def main():
    print("=" * 60)
    print("🖊️  Ghostwriter 真实 API 测试")
    print("=" * 60)
    print()
    
    # 创建临时数据目录
    temp_dir = tempfile.mkdtemp()
    
    # 初始化
    print("📡 连接 API...")
    llm = OpenAIProvider(api_key=API_KEY, base_url=BASE_URL, model=MODEL)
    memory = MemoryStore(data_dir=temp_dir)
    
    # 测试 API 连接
    try:
        test_response = llm.generate("说'测试成功'两个字")
        print(f"✅ API 连接成功: {test_response.content[:50]}...")
    except Exception as e:
        print(f"❌ API 连接失败: {e}")
        return
    
    print()
    print("=" * 60)
    print("📚 Step 1: 从阮一峰风格中学习")
    print("=" * 60)
    
    # 学习差异
    learner = DiffLearner(llm, memory)
    
    print("\n原文 (AI 中性生成):")
    print("-" * 40)
    print(AI_NEUTRAL[:200] + "...")
    
    print("\n修改后 (阮一峰风格):")
    print("-" * 40)
    print(RUANYIFENG_STYLE[:200] + "...")
    
    print("\n🔍 正在分析差异并提取规则...")
    result = learner.learn_from_edit(AI_NEUTRAL, RUANYIFENG_STYLE)
    
    print(f"\n✅ 学习完成!")
    print(f"   - 记录了 {result['episodes_added']} 个编辑案例")
    print(f"   - 提取了 {len(result['rules_extracted'])} 条风格规则")
    
    if result['rules_extracted']:
        print("\n📖 学到的规则:")
        for rule in result['rules_extracted']:
            print(f"   • {rule}")
    
    # 显示所有规则
    print("\n" + "=" * 60)
    print("📊 当前记忆状态")
    print("=" * 60)
    print(memory.get_all_rules_as_text())
    
    # 生成新文章
    print("\n" + "=" * 60)
    print("📝 Step 2: 用学到的风格生成新文章")
    print("=" * 60)
    
    composer = Composer(llm, memory)
    
    topic = "什么是神经网络"
    print(f"\n主题: {topic}")
    print("\n⏳ 正在生成...")
    
    result = composer.compose(topic, apply_style=True)
    
    print("\n📋 大纲:")
    print("-" * 40)
    print(result["outline"][:500] + "..." if len(result["outline"]) > 500 else result["outline"])
    
    print("\n📄 最终文章 " + ("(已应用风格)" if result["style_applied"] else "(中性)") + ":")
    print("-" * 40)
    print(result["styled"])
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print("=" * 60)
    
    # 清理
    import shutil
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
