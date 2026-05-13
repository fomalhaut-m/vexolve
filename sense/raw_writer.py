"""
感知层 - 原始素材写入器
将所有感知结果写入 raw/ 目录
"""

from pathlib import Path
from datetime import datetime
from typing import Optional


class RawWriter:
    """
    原始素材写入器
    负责将所有感知结果以不可变方式写入 raw/ 目录
    """

    def __init__(self, base_path: str = "/home/luke/workspace/vex/vexolve"):
        self.base = Path(base_path)
        self.raw = self.base / "raw"
        self._ensure_dirs()

    def _ensure_dirs(self):
        """确保 raw/ 子目录存在"""
        for subdir in ["对话", "观察", "思考", "事件", "梦境", "反馈"]:
            (self.raw / subdir).mkdir(parents=True, exist_ok=True)

    def _timestamp_filename(self, subdir: str, suffix: str = "md") -> Path:
        """生成带时间戳的文件名"""
        ts = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        return self.raw / subdir / f"{ts}.{suffix}"

    def write_dialogue(self, user: str, text: str, sender: str = "user") -> Path:
        """
        写入对话记录
        user: "luke" 或 "vexolve"
        """
        filename = self._timestamp_filename("对话")
        
        content = f"""---
type: dialogue
user: {user}
sender: {sender}
timestamp: {datetime.now().isoformat()}
---

**{user}**: {text}
"""
        filename.write_text(content, encoding="utf-8")
        print(f"  📝 写入对话: {filename.name}")
        return filename

    def write_observation(self, source: str, content: str) -> Path:
        """
        写入观察记录
        source: 来源（如 "timer", "wiki_sync", "external"）
        """
        filename = self._timestamp_filename("观察")
        
        body = f"""---
type: observation
source: {source}
timestamp: {datetime.now().isoformat()}
---

{content}
"""
        filename.write_text(body, encoding="utf-8")
        print(f"  📝 写入观察: {filename.name}")
        return filename

    def write_thought(self, content: str) -> Path:
        """写入思考碎片"""
        filename = self._timestamp_filename("思考")
        
        body = f"""---
type: thought
timestamp: {datetime.now().isoformat()}
---

{content}
"""
        filename.write_text(body, encoding="utf-8")
        print(f"  📝 写入思考: {filename.name}")
        return filename

    def write_event(self, event_type: str, content: str) -> Path:
        """写入事件记录（定时触发等）"""
        filename = self._timestamp_filename("事件")
        
        body = f"""---
type: event
event_type: {event_type}
timestamp: {datetime.now().isoformat()}
---

{content}
"""
        filename.write_text(body, encoding="utf-8")
        print(f"  📝 写入事件: {filename.name}")
        return filename

    def write_feedback(self, original_text: str, feedback: str, reaction: str = "neutral") -> Path:
        """
        写入用户反馈
        reaction: "positive" / "negative" / "neutral"
        """
        filename = self._timestamp_filename("反馈")
        
        body = f"""---
type: feedback
reaction: {reaction}
timestamp: {datetime.now().isoformat()}
original: {original_text}
feedback: {feedback}
---

{feedback}
"""
        filename.write_text(body, encoding="utf-8")
        print(f"  📝 写入反馈: {filename.name}")
        return filename

    def get_unprocessed(self, category: str = "对话") -> list[Path]:
        """获取未处理的 raw 文件（供编译层使用）"""
        processed_file = self.raw / f".processed_{category}"
        if processed_file.exists():
            processed = processed_file.read_text(encoding="utf-8").splitlines()
        else:
            processed = []
        
        category_dir = self.raw / category
        if not category_dir.exists():
            return []
        
        return [
            f for f in sorted(category_dir.glob("*.md"))
            if f.name not in processed
        ]

    def mark_processed(self, category: str, filename: str):
        """标记文件已处理"""
        processed_file = self.raw / f".processed_{category}"
        with open(processed_file, "a", encoding="utf-8") as f:
            f.write(f"{filename}\n")

    def get_all_recent(self, category: str, count: int = 10) -> list[str]:
        """获取最近N条记录的内容摘要"""
        category_dir = self.raw / category
        if not category_dir.exists():
            return []
        
        files = sorted(category_dir.glob("*.md"), reverse=True)[:count]
        contents = []
        for f in files:
            text = f.read_text(encoding="utf-8")
            # 去掉 frontmatter
            if text.startswith("---"):
                parts = text.split("---", 2)
                if len(parts) >= 3:
                    text = parts[2].strip()
            contents.append(text[:200])  # 截断
        
        return contents

    def get_wiki_context(self) -> str:
        """
        汇总 Wiki 层最新内容，作为 Vexolve 回复的上下文
        """
        wiki_dir = self.base / "wiki"
        
        if not wiki_dir.exists():
            return "（Wiki 尚未初始化）"
        
        context_parts = []
        
        # 读反思日志
        reflection = wiki_dir / "反思日志.md"
        if reflection.exists():
            lines = reflection.read_text(encoding="utf-8").splitlines()
            # 取最后20行
            recent = lines[-20:] if len(lines) > 20 else lines
            context_parts.append(f"【最近反思】：\n" + "\n".join(recent))
        
        # 读成长轨迹
        growth = wiki_dir / "成长轨迹.md"
        if growth.exists():
            lines = growth.read_text(encoding="utf-8").splitlines()
            recent = lines[-15:] if len(lines) > 15 else lines
            context_parts.append(f"【成长轨迹】：\n" + "\n".join(recent))
        
        # 读人格宣言
        declaration = wiki_dir / "人格宣言.md"
        if declaration.exists():
            lines = declaration.read_text(encoding="utf-8").splitlines()
            # 取前15行（核心宣言）
            context_parts.append(f"【人格宣言】：\n" + "\n".join(lines[:15]))
        
        return "\n\n".join(context_parts) if context_parts else "（Wiki 暂无内容）"
