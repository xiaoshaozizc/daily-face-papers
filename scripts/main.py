#!/usr/bin/env python3
"""
每日论文推荐主脚本
"""

import os
import sys
import json

# 添加脚本目录到路径
scripts_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, scripts_dir)

from fetcher import PaperAggregator


def main():
    from datetime import datetime
    print("=" * 60)
    print("  每日人脸论文推荐系统")
    print(f"  运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 获取论文
    print("\n[1/2] 正在获取论文...")
    aggregator = PaperAggregator()
    papers = aggregator.fetch_all(days=30)

    # 确保数据格式正确
    all_papers = papers.get("all", [])
    recognition = [p for p in all_papers if isinstance(p, dict) and p.get("category") == "人脸识别"]
    generation = [p for p in all_papers if isinstance(p, dict) and p.get("category") == "人脸生成"]

    print(f"\n  📊 统计:")
    print(f"     - 人脸识别: {len(recognition)} 篇")
    print(f"     - 人脸生成: {len(generation)} 篇")
    print(f"     - 总计: {len(all_papers)} 篇")

    # 如果没有论文，使用默认数据
    if not all_papers:
        print("\n⚠️ 暂无新论文，使用现有数据")
        # 读取现有的 papers.json
        repo_root = os.path.dirname(scripts_dir)
        json_path = os.path.join(repo_root, "papers.json")
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
                if existing:
                    all_papers = existing
                    recognition = [p for p in all_papers if p.get("category") == "人脸识别"]
                    generation = [p for p in all_papers if p.get("category") == "人脸生成"]

    # 保存论文数据
    repo_root = os.path.dirname(scripts_dir)
    data_path = os.path.join(repo_root, "papers.json")

    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(all_papers, f, ensure_ascii=False, indent=2)
    print(f"\n[2/2] 论文数据已保存: {data_path}")

    print("\n" + "=" * 60)
    print("  ✅ 完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
