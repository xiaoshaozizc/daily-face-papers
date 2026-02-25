#!/usr/bin/env python3
"""
README 生成脚本
根据获取的论文数据生成 Markdown 格式的每日推荐
"""

import os
import json
from datetime import datetime
from typing import Dict, List


class ReadmeGenerator:
    """README 生成器"""

    def __init__(self, repo_name: str = "daily-face-papers"):
        self.repo_name = repo_name
        self.today = datetime.now().strftime("%Y-%m-%d")

    def generate_readme(self, papers: Dict[str, List[Dict]]) -> str:
        """
        生成 README 内容

        Args:
            papers: 论文数据字典

        Returns:
            Markdown 格式的 README 内容
        """
        all_papers = papers.get("all", [])

        # 生成头部
        content = self._generate_header()

        # 统计信息
        content += self._generate_stats(papers)

        # 论文列表
        content += self._generate_paper_list(all_papers)

        # 归档链接
        content += self._generate_archive_section()

        # 更新日志
        content += self._generate_changelog()

        return content

    def _generate_header(self) -> str:
        """生成头部信息"""
        return f"""# 每日人脸识别/生成论文推荐

![Last Updated](https://img.shields.io/badge/last_updated-{self.today}-blue)
![Paper Count](https://img.shields.io/badge/papers_today-6+-green)

本项目每日自动从 [arXiv](https://arxiv.org) 抓取人脸识别和人脸生成领域的最新论文。

## 📌 今日推荐 ({self.today})

---

"""

    def _generate_stats(self, papers: Dict[str, List[Dict]]) -> str:
        """生成统计信息"""
        rec_count = len(papers.get("face_recognition", []))
        gen_count = len(papers.get("face_generation", []))
        sources = papers.get("sources", {})

        # 生成来源统计
        source_lines = []
        for source, count in sources.items():
            if count > 0:
                source_lines.append(f"- **{source}**: {count} 篇")

        source_str = "\n".join(source_lines) if source_lines else "- arXiv: 0 篇"

        return f"""### 📊 今日统计

**论文分类:**
- **人脸识别论文**: {rec_count} 篇
- **人脸生成论文**: {gen_count} 篇
- **总计**: {rec_count + gen_count} 篇

**来源统计:**
{source_str}

> 📡 数据来源: arXiv, CVPR, ICCV, ECCV, NeurIPS 等会议/预印本

---

"""

    def _generate_paper_list(self, papers: List[Dict]) -> str:
        """生成论文列表"""
        if not papers:
            return "今日暂无新论文。\n"

        content = "### 📄 论文列表\n\n"

        for i, paper in enumerate(papers, 1):
            content += self._format_paper(i, paper)

        return content

    def _format_paper(self, index: int, paper: Dict) -> str:
        """格式化单个论文"""
        # 分类标签
        category_emoji = "🔍" if paper.get("category") == "人脸识别" else "🎨"
        category_color = "识别" if paper.get("category") == "人脸识别" else "生成"

        # 格式化作者
        authors = ", ".join(paper["authors"]) if paper["authors"] else "Unknown"

        return f"""{index}. **{paper['title']}**

   - 🏷️ 分类: {category_emoji} {paper.get('category', '人脸生成')}
   - 👤 作者: {authors}
   - 📅 发布日期: {paper['published']}
   - 📖 简介: {paper['summary']}

   **链接**: [arXiv]({paper['arxiv_link']}) | [PDF]({paper['pdf_link']})

---

"""

    def _generate_archive_section(self) -> str:
        """生成归档部分"""
        year = datetime.now().year

        return f"""## 📁 历史归档

- [{year} 年论文归档](./papers/{year}.md)

---

## 🤝 贡献

欢迎提交 Issue 推荐优质论文！

## 📄 License

MIT License

---

*本项目由 GitHub Actions 自动更新*
"""

    def _generate_changelog(self) -> str:
        """生成更新日志"""
        return f"""

---
## 📝 更新日志

### {self.today}
- 每日论文推荐更新
- 共收录 {self.today} 发布的论文
"""

    def generate_archive(self, papers: List[Dict], year: int) -> str:
        """生成归档文件"""
        content = f"""# {year} 年人脸识别/生成论文汇总

本文件收录了 {year} 年发布的所有人脸相关论文。

## 目录

"""

        # 按月份分组
        by_month = {}
        for paper in papers:
            month = paper["published"][:7]  # YYYY-MM
            if month not in by_month:
                by_month[month] = []
            by_month[month].append(paper)

        # 生成月份链接
        for month in sorted(by_month.keys(), reverse=True):
            content += f"- [{month}](./{month}.md)\n"

        # 添加每月详情
        for month in sorted(by_month.keys(), reverse=True):
            content += f"\n## {month}\n\n"
            for i, paper in enumerate(by_month[month], 1):
                content += f"{i}. [{paper['title']}]({paper['arxiv_link']}) - {paper['published']}\n"

        return content

    def save_readme(self, content: str, output_path: str = "README.md"):
        """保存 README 文件"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"README 已保存到: {output_path}")

    def save_papers_json(self, papers: Dict[str, List[Dict]], output_path: str = "papers.json"):
        """保存论文数据为 JSON"""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)
        print(f"论文数据已保存到: {output_path}")


def main():
    """测试生成器"""
    # 模拟数据
    sample_papers = {
        "face_recognition": [
            {
                "id": "2401.12345",
                "title": "Sample Face Recognition Paper",
                "authors": ["Author One", "Author Two"],
                "summary": "This is a sample paper about face recognition...",
                "arxiv_link": "https://arxiv.org/abs/2401.12345",
                "pdf_link": "https://arxiv.org/pdf/2401.12345.pdf",
                "published": "2024-01-15",
                "category": "人脸识别",
            }
        ],
        "face_generation": [
            {
                "id": "2401.67890",
                "title": "Sample Face Generation Paper",
                "authors": ["Author Three", "Author Four"],
                "summary": "This is a sample paper about face generation...",
                "arxiv_link": "https://arxiv.org/abs/2401.67890",
                "pdf_link": "https://arxiv.org/pdf/2401.67890.pdf",
                "published": "2024-01-14",
                "category": "人脸生成",
            }
        ],
        "all": [
            {
                "id": "2401.12345",
                "title": "Sample Face Recognition Paper",
                "authors": ["Author One", "Author Two"],
                "summary": "This is a sample paper about face recognition...",
                "arxiv_link": "https://arxiv.org/abs/2401.12345",
                "pdf_link": "https://arxiv.org/pdf/2401.12345.pdf",
                "published": "2024-01-15",
                "category": "人脸识别",
            },
            {
                "id": "2401.67890",
                "title": "Sample Face Generation Paper",
                "authors": ["Author Three", "Author Four"],
                "summary": "This is a sample paper about face generation...",
                "arxiv_link": "https://arxiv.org/abs/2401.67890",
                "pdf_link": "https://arxiv.org/pdf/2401.67890.pdf",
                "published": "2024-01-14",
                "category": "人脸生成",
            }
        ]
    }

    generator = ReadmeGenerator()
    readme_content = generator.generate_readme(sample_papers)

    print(readme_content)


if __name__ == "__main__":
    main()
