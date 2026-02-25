#!/usr/bin/env python3
"""
每日论文推荐主脚本
整合 fetcher 和 generator，自动获取并生成推荐
"""

import os
import sys
import json
from datetime import datetime

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetcher import ArxivFetcher
from generator import ReadmeGenerator


def main():
    """主函数"""
    print("=" * 60)
    print("  每日人脸识别/生成论文推荐系统")
    print(f"  运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 获取论文
    print("\n[1/3] 正在从 arXiv 获取论文...")
    fetcher = ArxivFetcher()
    papers = fetcher.fetch_all_papers()

    print(f"  - 人脸识别论文: {len(papers['face_recognition'])} 篇")
    print(f"  - 人脸生成论文: {len(papers['face_generation'])} 篇")
    print(f"  - 总计: {len(papers['all'])} 篇")

    if not papers["all"]:
        print("\n⚠️ 今日暂无新论文")
        return

    # 生成 README
    print("\n[2/3] 正在生成 README...")
    generator = ReadmeGenerator()

    # 获取项目根目录
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_path = os.path.join(repo_root, "README.md")

    readme_content = generator.generate_readme(papers)
    generator.save_readme(readme_content, readme_path)

    # 保存论文数据
    print("\n[3/3] 正在保存论文数据...")
    data_path = os.path.join(repo_root, "papers.json")
    generator.save_papers_json(papers, data_path)

    # 保存每日存档
    today = datetime.now().strftime("%Y-%m-%d")
    papers_dir = os.path.join(repo_root, "papers")
    os.makedirs(papers_dir, exist_ok=True)
    daily_path = os.path.join(papers_dir, f"{today}.md")

    # 生成每日存档
    daily_content = f"# {today} 论文推荐\n\n"
    for i, paper in enumerate(papers["all"], 1):
        daily_content += f"## {i}. {paper['title']}\n\n"
        daily_content += f"- **分类**: {paper.get('category')}\n"
        daily_content += f"- **作者**: {', '.join(paper['authors'])}\n"
        daily_content += f"- **日期**: {paper['published']}\n"
        daily_content += f"- **arXiv**: {paper['arxiv_link']}\n"
        daily_content += f"- **PDF**: {paper['pdf_link']}\n\n"
        daily_content += f"**简介**: {paper['summary']}\n\n---\n\n"

    with open(daily_path, "w", encoding="utf-8") as f:
        f.write(daily_content)
    print(f"  每日存档已保存到: {daily_path}")

    print("\n" + "=" * 60)
    print("  ✅ 完成! 论文推荐已生成")
    print("=" * 60)


if __name__ == "__main__":
    main()
