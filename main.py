"""
Vexolve - 自我进化的 AI 智能体
入口文件
"""

from core.agent import VexolveAgent
import os
from dotenv import load_dotenv

load_dotenv()


def main():
    print("🔮 Vexolve 初始化中...")
    
    agent = VexolveAgent()
    
    print("✅ Vexolve 已就绪！开始对话（输入 'exit' 退出）：\n")
    
    while True:
        user_input = input("你: ").strip()
        
        if user_input.lower() in ["exit", "quit", "q"]:
            print("👋 再见！")
            break
        
        if not user_input:
            continue
        
        response = agent.run(user_input)
        print(f"Vexolve: {response}\n")


if __name__ == "__main__":
    main()