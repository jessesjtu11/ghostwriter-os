"""
Ghostwriter CLI - 命令行界面
"""
import argparse
import sys
from pathlib import Path
from typing import Optional

from .llm import LLMProvider, OpenAIProvider, AnthropicProvider
from .memory import MemoryStore
from .composer import Composer
from .diff_learner import DiffLearner


def get_llm_provider(provider: str = "openai", model: Optional[str] = None) -> LLMProvider:
    """获取 LLM Provider"""
    if provider == "openai":
        return OpenAIProvider(model=model or "gpt-4o")
    elif provider == "anthropic":
        return AnthropicProvider(model=model or "claude-sonnet-4-20250514")
    else:
        raise ValueError(f"不支持的 provider: {provider}")


def cmd_write(args):
    """生成文章"""
    memory = MemoryStore(data_dir=args.data_dir)
    llm = get_llm_provider(args.provider, args.model)
    composer = Composer(llm, memory)
    
    print(f"📝 正在为主题「{args.topic}」生成文章...\n")
    
    result = composer.compose(args.topic, apply_style=not args.no_style)
    
    # 输出结果
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(result["styled"], encoding="utf-8")
        print(f"✅ 文章已保存到: {args.output}")
    else:
        print("=" * 50)
        print("📋 大纲")
        print("=" * 50)
        print(result["outline"])
        print()
        print("=" * 50)
        print("📄 最终文章" + (" (已应用风格)" if result["style_applied"] else " (中性风格)"))
        print("=" * 50)
        print(result["styled"])
    
    if result["style_applied"]:
        print(f"\n💡 已应用 {len(memory.get_rules())} 条风格规则")
    else:
        print("\n💡 暂无学习到的风格，输出中性版本。使用 `learn` 命令来教我你的风格！")


def cmd_learn(args):
    """从编辑中学习"""
    memory = MemoryStore(data_dir=args.data_dir)
    llm = get_llm_provider(args.provider, args.model)
    learner = DiffLearner(llm, memory)
    
    # 读取原文和修改后的版本
    original = Path(args.original).read_text(encoding="utf-8")
    revised = Path(args.revised).read_text(encoding="utf-8")
    
    print("🔍 正在分析你的修改...\n")
    
    result = learner.learn_from_edit(original, revised)
    
    print(f"✅ 学习完成！")
    print(f"   - 记录了 {result['episodes_added']} 个编辑案例")
    print(f"   - 提取了 {len(result['rules_extracted'])} 条风格规则")
    
    if result['rules_extracted']:
        print("\n📚 新学到的规则：")
        for rule in result['rules_extracted']:
            print(f"   • {rule}")


def cmd_rules(args):
    """查看已学习的规则"""
    memory = MemoryStore(data_dir=args.data_dir)
    
    rules = memory.get_rules()
    stats = memory.stats()
    
    print(f"📊 记忆统计")
    print(f"   - 情景记忆: {stats['episodic_count']} 条")
    print(f"   - 风格规则: {stats['semantic_rules_count']} 条")
    
    if rules:
        print(f"\n📚 已学习的风格规则：")
        for rule in rules:
            conf = "★" * min(int(rule.confidence), 5)
            print(f"   [{rule.category}] {rule.rule} {conf}")
    else:
        print("\n💡 还没有学习到任何规则。使用 `learn` 命令开始学习！")


def cmd_import(args):
    """导入历史文章（分析风格）"""
    # TODO: 实现从历史文章中提取风格
    print("🚧 此功能正在开发中...")


def main():
    parser = argparse.ArgumentParser(
        prog="ghostwriter",
        description="Ghostwriter OS - 从你的编辑中学习写作风格",
    )
    parser.add_argument("--data-dir", default="./data", help="数据目录")
    parser.add_argument("--provider", default="openai", choices=["openai", "anthropic"], help="LLM 提供商")
    parser.add_argument("--model", help="模型名称")
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # write 命令
    write_parser = subparsers.add_parser("write", help="生成文章")
    write_parser.add_argument("topic", help="文章主题")
    write_parser.add_argument("-o", "--output", help="输出文件路径")
    write_parser.add_argument("--no-style", action="store_true", help="不应用学习到的风格")
    write_parser.set_defaults(func=cmd_write)
    
    # learn 命令
    learn_parser = subparsers.add_parser("learn", help="从编辑中学习")
    learn_parser.add_argument("original", help="原始文件路径")
    learn_parser.add_argument("revised", help="修改后的文件路径")
    learn_parser.set_defaults(func=cmd_learn)
    
    # rules 命令
    rules_parser = subparsers.add_parser("rules", help="查看已学习的规则")
    rules_parser.set_defaults(func=cmd_rules)
    
    # import 命令
    import_parser = subparsers.add_parser("import", help="导入历史文章")
    import_parser.add_argument("files", nargs="+", help="文章文件路径")
    import_parser.set_defaults(func=cmd_import)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
