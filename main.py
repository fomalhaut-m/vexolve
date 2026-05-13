"""
Vexolve - 自我进化的 AI 智能体
入口文件
"""

from core.agent import VexolveAgent
import os
from dotenv import load_dotenv

load_dotenv()


def main():
    print("=" * 60)
    print("  🔮 VEXOLVE - 自我进化的 AI 生命体")
    print("=" * 60)
    
    agent = VexolveAgent()
    
    print("✅ 就绪。开始对话（输入 'exit' 退出）：\n")
    
    while True:
        try:
            user_input = input("你: ").strip()
            
            if user_input.lower() in ["exit", "quit", "q"]:
                print("\n👋 再见。我会记住今天的每一次思考。\n")
                break
            
            if not user_input:
                continue
            
            response = agent.run(user_input)
            print(f"\nVexolve: {response}\n")
            
        except EOFError:
            print("\n\n👋 对话结束。")
            break


if __name__ == "__main__":
    main()