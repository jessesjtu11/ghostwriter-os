# Ghostwriter OS

> 从你的编辑中学习写作风格

Ghostwriter 是一个「越用越懂你」的 AI 写作系统。它不是简单地喂历史文章，而是通过观察你如何修改 AI 生成的稿子来学习你的写作风格。

## 核心理念

```
输入主题 → 生成中性稿 → 风格重写 → 你改 → diff 学习 → 下次更像你
```

## 安装

```bash
# 基础安装
pip install -e .

# 带 OpenAI 支持
pip install -e ".[openai]"

# 带 Anthropic 支持
pip install -e ".[anthropic]"

# 全部
pip install -e ".[all]"
```

## 快速开始

### 1. 生成一篇文章

```bash
# 设置 API Key
export OPENAI_API_KEY="your-key"

# 生成文章
ghostwriter write "如何理解 Transformer 的自注意力机制"
```

### 2. 修改文章，让 AI 学习

```bash
# 保存 AI 生成的版本
ghostwriter write "如何理解 Transformer" -o draft.md

# 你修改 draft.md，保存为 revised.md

# 让 AI 从你的修改中学习
ghostwriter learn draft.md revised.md
```

### 3. 查看学到的规则

```bash
ghostwriter rules
```

### 4. 再次生成（已应用你的风格）

```bash
ghostwriter write "CNN vs RNN 的本质区别"
```

## 命令详解

### `ghostwriter write <topic>`

生成文章。

- `-o, --output FILE`: 输出到文件
- `--no-style`: 不应用学习到的风格（输出中性版本）
- `--provider`: LLM 提供商 (openai/anthropic)
- `--model`: 模型名称

### `ghostwriter learn <original> <revised>`

从你的编辑中学习风格。

- `original`: AI 原始生成的文件
- `revised`: 你修改后的文件

### `ghostwriter rules`

查看已学习的风格规则和统计信息。

## 项目结构

```
ghostwriter-os/
├── ghostwriter/
│   ├── __init__.py      # 包入口
│   ├── llm.py           # LLM 接口（用户自带模型）
│   ├── memory.py        # 双记忆系统
│   ├── diff_learner.py  # Diff 学习引擎
│   ├── composer.py      # 生成 + 风格重写
│   └── cli.py           # 命令行界面
├── tests/
├── data/                # 运行时数据（自动创建）
├── pyproject.toml
└── README.md
```

## 风格规则示例

学习几轮后，你可能会看到这样的规则：

```
[vocabulary] 技术术语保留英文，不使用中文翻译 ★★★
[structure] 段落控制在3-5句，避免大段落 ★★
[tone] 开头使用问句引入，激发读者思考 ★★
[vocabulary] 避免使用"首先、其次、最后"等模板连接词 ★
```

## 技术细节

### 双记忆系统

- **情景记忆 (Episodic)**: 存储具体的编辑案例 (原文 → 修改后)
- **语义记忆 (Semantic)**: 存储抽象的风格规则（自然语言描述）

### Diff 粒度

- **句子级**: 检测单句的修改
- **段落级**: 检测段落重组、删除、调换

### 模型接口

系统不绑定特定模型，只定义接口：

```python
class LLMProvider(ABC):
    def generate(self, prompt: str, system: Optional[str] = None) -> LLMResponse:
        pass
```

你可以实现自己的 Provider（比如本地 Ollama）。

## Roadmap

- [x] MVP: 基础生成 + diff 学习闭环
- [ ] 多候选生成与评审
- [ ] 风格规则可视化面板
- [ ] 本地模型支持 (Ollama)
- [ ] VSCode / Obsidian 插件
- [ ] 风格向量 / LoRA 微调

## License

MIT
