"""
Vexolve Agent - 智能体核心
"""

from typing import List, Dict
from dotenv import load_dotenv
import os

load_dotenv()


class Message:
    """对话消息"""
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
    
    def to_dict(self) -> Dict:
        return {"role": self.role, "content": self.content}


class VexolveAgent:
    """Vexolve 智能体"""
    
    def __init__(self):
        self.model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.messages: List[Message] = []
        
        print(f"  模型: {self.model}")
        print(f"  API Key: {'✅ 已配置' if self.api_key else '❌ 未配置'}")
    
    def run(self, user_input: str) -> str:
        """处理用户输入"""
        self.messages.append(Message("user", user_input))
        response = self._think(user_input)
        self.messages.append(Message("assistant", response))
        return response
    
    def _think(self, user_input: str) -> str:
        """思考逻辑 - 待实现"""
        if not self.api_key:
            return "⚠️ 还未配置 API Key，请填入 .env 文件"
        return f"🔮 我收到: {user_input}\n\n（LLM 接入后这里会返回真正的智能回复）"
    
    def reset(self):
        """重置对话历史"""
        self.messages = []