# Vexolve

> 一个能够自我进化的 AI 智能体

## 目标

让 Vexolve 连上 AI，能说话、能思考、能进化。

## 核心能力

- 🔮 连接大语言模型（支持 OpenAI / MiniMax / 本地模型）
- 🧠 多轮对话记忆
- 📚 知识库检索（RAG）
- 🔄 自我反思与进化
- 🌐 工具调用（搜索、代码执行等）

## 快速开始

```bash
pip install -r requirements.txt
cp .env.example .env  # 填写 API Key
python main.py
```

## 项目结构

```
vexolve/
├── .env              # API 密钥配置
├── main.py           # 智能体入口
├── requirements.txt  # 依赖
└── core/
    └── agent.py      # 智能体核心
```

## License

MIT