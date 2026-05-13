"""
Vexolve 飞书接口
完整闭环：飞书消息 → Raw写入 → Wiki编译 → LLM回复（带Wiki上下文）

使用方式：
1. 在飞书开放平台创建应用，配置事件订阅 URL 为 /feishu/webhook
2. 设置环境变量：FEISHU_APP_ID, FEISHU_APP_SECRET, MINIMAX_API_KEY
3. 运行：python feishu_server.py
4. 在飞书给机器人发消息即可
"""

import os
import sys
import json
import traceback
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import lark_oapi as lark

# Vexolve 核心（完整闭环版）
from core.agent import VexolveAgent


# ===========================
# 配置
# ===========================

FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")

vexolve: Optional[VexolveAgent] = None


# ===========================
# FastAPI 应用
# ===========================

app = FastAPI(title="Vexolve Feishu Bot", version="2.0.0")


@app.on_event("startup")
async def startup():
    global vexolve
    vexolve = VexolveAgent()
    
    print("=" * 60)
    print("  🔮 VEXOLVE 飞书接口已启动（完整闭环版）")
    print("=" * 60)
    print(f"  飞书应用: {'✅ 已配置' if FEISHU_APP_ID else '❌ 未配置'}")
    print(f"  Vexolve: {'✅ 运行中' if vexolve else '❌ 未连接'}")
    print(f"  闭环链路: 飞书 → Raw → 编译 → Wiki → 回复")
    print("=" * 60)


@app.get("/")
async def root():
    return {
        "name": "Vexolve Feishu Bot",
        "version": "2.0.0",
        "status": "running",
        "loop": "Raw → Wiki → Reply",
        "time": datetime.now().isoformat(),
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/wiki_context")
async def wiki_context():
    """查询当前 Wiki 上下文"""
    if not vexolve:
        return {"error": "Vexolve not initialized"}
    return {"context": vexolve.get_wiki_context()[:500]}


@app.post("/compile")
async def trigger_compile():
    """手动触发一次编译"""
    if not vexolve:
        return {"error": "Vexolve not initialized"}
    vexolve.trigger_compile()
    return {"status": "compiled"}


# ===========================
# 飞书事件订阅
# ===========================

@app.post("/feishu/webhook")
async def feishu_webhook(request: Request):
    """
    飞书事件订阅地址
    飞书开放平台 → 应用功能 → 事件订阅 → 请求地址
    """
    global vexolve
    
    try:
        body = await request.json()
        
        # URL 验证挑战（GET 请求）
        challenge = request.query_params.get("challenge")
        if challenge:
            return {"challenge": challenge}
        
        # 处理事件
        event_type = body.get("type", "")
        
        if event_type == "url_verification":
            return {"challenge": body.get("challenge", "")}
        
        if event_type == "event_callback":
            return await handle_event(body)
        
        return JSONResponse({"status": "ok"})
        
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)


async def handle_event(body: dict) -> JSONResponse:
    """处理飞书事件"""
    global vexolve
    
    try:
        event = body.get("event", {})
        
        # 提取消息字段（兼容新旧格式）
        if body.get("schema") == "2.0":
            msg_type = event.get("msg_type", "")
            chat_id = event.get("chat_id", "")
            content = event.get("content", "{}")
            sender = event.get("sender", {})
            sender_id = sender.get("sender_id", {}).get("open_id", "")
        else:
            msg_type = event.get("msg_type", "")
            chat_id = event.get("chat_id", "")
            content = event.get("content", "{}")
            sender_id = event.get("open_id", "")
        
        # 过滤非文本消息
        if msg_type != "text":
            return JSONResponse({"status": "ignored", "reason": "not text"})
        
        # 解析文本
        try:
            content_obj = json.loads(content)
            text = content_obj.get("text", "").strip()
        except:
            text = content.strip() if isinstance(content, str) else ""
        
        if not text:
            return JSONResponse({"status": "ignored", "reason": "empty"})
        
        # 过滤机器人消息
        if sender_id == FEISHU_APP_ID:
            return JSONResponse({"status": "ignored", "reason": "bot"})
        
        print(f"\n📩 来自飞书: {text[:50]}...")
        
        # 调用 Vexolve 完整闭环
        if vexolve:
            response = vexolve.run(text, user="luke")
        else:
            response = "⚠️ Vexolve 未初始化"
        
        print(f"  Vexolve: {response[:50]}...")
        
        # 回复飞书
        if chat_id and response:
            send_feishu_message(chat_id, response)
        
        return JSONResponse({"status": "ok"})
        
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)


def send_feishu_message(chat_id: str, text: str):
    """发送飞书文本消息"""
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        print("⚠️ 飞书未配置，无法发送消息")
        return
    
    try:
        client = lark.Client.builder().app_id(FEISHU_APP_ID).app_secret(FEISHU_APP_SECRET).build()
        
        client.im.v1.message.create(
            lark.im.v1.MessageCreateRequest.builder()
            .data(lark.im.v1.MessageCreateRequestData.builder()
                .receive_id(chat_id)
                .msg_type("text")
                .content(json.dumps({"text": text}))
                .build())
            .build()
        )
    except Exception as e:
        print(f"❌ 发送失败: {e}")


# ===========================
# 启动
# ===========================

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  🚀 Vexolve 飞书服务（完整闭环版）")
    print("=" * 60)
    print()
    print("  环境变量检查：")
    print(f"    FEISHU_APP_ID:     {'✅' if FEISHU_APP_ID else '❌'}")
    print(f"    FEISHU_APP_SECRET: {'✅' if FEISHU_APP_SECRET else '❌'}")
    print(f"    MINIMAX_API_KEY:   {'✅' if os.environ.get('MINIMAX_API_KEY') else '❌'}")
    print()
    print("  闭环链路：")
    print("    飞书消息 → raw/对话/ → 编译 → wiki/ → 回复")
    print()
    print("  服务地址：http://0.0.0.0:9000")
    print("  飞书事件订阅：http://0.0.0.0:9000/feishu/webhook")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=9000, log_level="info")