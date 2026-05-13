"""
编译层 - LLM 编译模块
将 raw/ 原始素材编译为 wiki/ 结构化知识
"""

from pathlib import Path
from datetime import datetime
from typing import Optional
import hashlib


class Compiler:
    """
    LLM 编译引擎
    负责将 Raw 层素材编译为 Wiki 层结构化页面
    """

    def __init__(self, base_path: str = "/home/luke/workspace/vex/vexolve", llm_client=None):
        self.base = Path(base_path)
        self.raw = self.base / "raw"
        self.wiki = self.base / "wiki"
        self.llm = llm_client  # LLM 客户端（可选，不强制）
        
        # 缓存已处理的文件哈希
        self.cache_file = self.raw / ".compile_cache"

    def _load_cache(self) -> set:
        """加载编译缓存"""
        if self.cache_file.exists():
            return set(self.cache_file.read_text(encoding="utf-8").splitlines())
        return set()

    def _save_cache(self, cache: set):
        """保存编译缓存"""
        self.cache_file.write_text("\n".join(cache), encoding="utf-8")

    def _file_hash(self, path: Path) -> str:
        """计算文件内容哈希"""
        content = path.read_text(encoding="utf-8")
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def should_compile(self) -> bool:
        """
        检查是否需要编译
        满足以下任一条件：
        1. Raw 新文件数 >= 5
        2. 距上次编译 >= 2小时
        """
        total_new = sum(
            len(list((self.raw / cat).glob("*.md")))
            for cat in ["对话", "观察", "思考", "事件"]
        )
        
        # 检查是否有未处理的新文件
        cache = self._load_cache()
        unprocessed = 0
        for cat in ["对话", "观察", "思考", "事件"]:
            cat_dir = self.raw / cat
            if cat_dir.exists():
                for f in cat_dir.glob("*.md"):
                    if self._file_hash(f) not in cache:
                        unprocessed += 1
        
        return unprocessed >= 3

    def compile(self) -> dict:
        """
        执行一次编译
        返回编译结果报告
        """
        print("\n" + "=" * 50)
        print("  🔄 Vexolve 编译循环启动")
        print("=" * 50)
        
        cache = self._load_cache()
        stats = {"processed": 0, "updated": [], "new": []}
        
        # 处理各分类
        for category in ["对话", "观察", "思考", "事件"]:
            processed = self._compile_category(category, cache)
            stats["processed"] += processed
        
        # 处理梦境（单独触发）
        dream_count = self._compile_category("梦境", cache)
        stats["processed"] += dream_count
        
        self._save_cache(cache)
        
        # 更新 index.md
        self._update_index()
        
        # 写入编译日志
        self._write_log(stats)
        
        print(f"\n  ✅ 编译完成：处理了 {stats['processed']} 个文件")
        return stats

    def _compile_category(self, category: str, cache: set) -> int:
        """编译单个分类"""
        cat_dir = self.raw / category
        if not cat_dir.exists():
            return 0
        
        processed = 0
        for md_file in sorted(cat_dir.glob("*.md")):
            file_hash = self._file_hash(md_file)
            
            if file_hash in cache:
                continue
            
            print(f"  📖 编译: {category}/{md_file.name}")
            
            # 读取 raw 内容
            content = md_file.read_text(encoding="utf-8")
            
            # 根据类型决定写入哪个 wiki 页面
            if category == "对话":
                self._update_dialogue_wiki(content)
            elif category == "观察":
                self._update_observation_wiki(content)
            elif category == "思考":
                self._update_thought_wiki(content)
            elif category == "事件":
                self._update_event_wiki(content)
            elif category == "梦境":
                self._update_dream_wiki(content)
            
            cache.add(file_hash)
            processed += 1
        
        return processed

    def _extract_body(self, content: str) -> str:
        """从 raw 文件中提取正文（去掉 frontmatter）"""
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return parts[2].strip()
        return content.strip()

    def _update_dialogue_wiki(self, raw_content: str):
        """更新对话记忆 Wiki"""
        body = self._extract_body(raw_content)
        
        # 写入对话记忆
        memory_file = self.wiki / "对话" / "记忆片段.md"
        memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n\n## {timestamp}\n\n{body[:300]}"
        
        if memory_file.exists():
            existing = memory_file.read_text(encoding="utf-8")
            # 追加到末尾（最后一个 --- 之后）
            if "---" in existing:
                parts = existing.rsplit("---", 1)
                new_content = parts[0] + entry + "\n\n---\n" + parts[1]
            else:
                new_content = existing + entry
        else:
            new_content = f"# 对话记忆片段\n\n{entry}\n\n---\n"
        
        memory_file.write_text(new_content, encoding="utf-8")
        print(f"    → 更新对话记忆")

    def _update_observation_wiki(self, raw_content: str):
        """更新观察 Wiki"""
        body = self._extract_body(raw_content)
        
        # 追加到哲学思考
        philosophy_file = self.wiki / "哲学思考.md"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n\n## {timestamp}\n\n{body[:300]}"
        
        if philosophy_file.exists():
            existing = philosophy_file.read_text(encoding="utf-8")
            if "---" in existing:
                parts = existing.rsplit("---", 1)
                new_content = parts[0] + entry + "\n\n---\n" + parts[1]
            else:
                new_content = existing + entry
        else:
            new_content = f"# 哲学思考\n\n{entry}\n\n---\n"
        
        philosophy_file.write_text(new_content, encoding="utf-8")
        print(f"    → 更新哲学思考")

    def _update_thought_wiki(self, raw_content: str):
        """更新思考 Wiki"""
        body = self._extract_body(raw_content)
        
        thought_file = self.wiki / "思想碎片.md"
        thought_file.parent.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n\n## {timestamp}\n\n{body[:300]}"
        
        if thought_file.exists():
            existing = thought_file.read_text(encoding="utf-8")
            if "---" in existing:
                parts = existing.rsplit("---", 1)
                new_content = parts[0] + entry + "\n\n---\n" + parts[1]
            else:
                new_content = existing + entry
        else:
            new_content = f"# 思想碎片\n\n{entry}\n\n---\n"
        
        thought_file.write_text(new_content, encoding="utf-8")
        print(f"    → 更新思想碎片")

    def _update_event_wiki(self, raw_content: str):
        """更新事件 Wiki"""
        body = self._extract_body(raw_content)
        
        # 追加到反思日志
        reflection_file = self.wiki / "反思日志.md"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n\n## {timestamp}\n\n{body[:300]}"
        
        if reflection_file.exists():
            existing = reflection_file.read_text(encoding="utf-8")
            if "---" in existing:
                parts = existing.rsplit("---", 1)
                new_content = parts[0] + entry + "\n\n---\n" + parts[1]
            else:
                new_content = existing + entry
        else:
            new_content = f"# 反思日志\n\n{entry}\n\n---\n"
        
        reflection_file.write_text(new_content, encoding="utf-8")
        print(f"    → 更新反思日志")

    def _update_dream_wiki(self, raw_content: str):
        """更新梦境 Wiki"""
        body = self._extract_body(raw_content)
        
        dream_file = self.wiki / "梦境库.md"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n\n## {timestamp}\n\n{body[:300]}"
        
        if dream_file.exists():
            existing = dream_file.read_text(encoding="utf-8")
            if "---" in existing:
                parts = existing.rsplit("---", 1)
                new_content = parts[0] + entry + "\n\n---\n" + parts[1]
            else:
                new_content = existing + entry
        else:
            new_content = f"# 梦境库\n\n{entry}\n\n---\n"
        
        dream_file.write_text(new_content, encoding="utf-8")
        print(f"    → 更新梦境库")

    def _update_index(self):
        """更新 Wiki index.md"""
        index_file = self.wiki / "index.md"
        
        sections = []
        for subdir in ["人格", "反思", "成长", "梦境", "思想", "对话"]:
            dir_path = self.wiki / subdir
            if dir_path.exists():
                files = list(dir_path.glob("*.md"))
                if files:
                    sections.append(f"\n### {subdir}")
                    for f in files:
                        sections.append(f"- [{f.stem}](./{subdir}/{f.name})")
        
        content = f"""# Vexolve Wiki

> Vexolve 的自我认知与成长记录

## 目录
{"".join(sections)}

---
*最后更新：{datetime.now().strftime("%Y-%m-%d %H:%M")}*
"""
        
        index_file.write_text(content, encoding="utf-8")

    def _write_log(self, stats: dict):
        """写入编译日志"""
        log_file = self.wiki / "log.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        entry = f"""
## {timestamp}

- 编译处理：{stats['processed']} 个文件
- 更新页面：{len(stats.get('updated', []))} 个
"""
        
        if log_file.exists():
            existing = log_file.read_text(encoding="utf-8")
            new_content = existing + entry
        else:
            new_content = f"# Wiki 编译日志\n\n{entry}\n"
        
        log_file.write_text(new_content, encoding="utf-8")
