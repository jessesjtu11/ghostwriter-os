"""
LLM Provider Interface - 用户自带模型
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: Optional[dict] = None


class LLMProvider(ABC):
    """LLM 接口基类，用户实现自己的 provider"""
    
    @abstractmethod
    def generate(self, prompt: str, system: Optional[str] = None) -> LLMResponse:
        """生成文本"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """返回模型名称"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API Provider（示例实现）"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o", base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            from openai import OpenAI
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = OpenAI(**kwargs)
        return self._client
    
    def generate(self, prompt: str, system: Optional[str] = None) -> LLMResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            }
        )
    
    def get_model_name(self) -> str:
        return self.model


class AnthropicProvider(LLMProvider):
    """Anthropic API Provider（示例实现）"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=self.api_key)
        return self._client
    
    def generate(self, prompt: str, system: Optional[str] = None) -> LLMResponse:
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        
        response = self.client.messages.create(**kwargs)
        
        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        )
    
    def get_model_name(self) -> str:
        return self.model
