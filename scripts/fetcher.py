#!/usr/bin/env python3
"""
arXiv 论文获取脚本
从 arXiv API 获取人脸识别和人脸生成相关的最新论文
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict
import re


class ArxivFetcher:
    """arXiv 论文获取器"""

    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
        # 人脸识别相关搜索关键词
        self.face_recognition_keywords = [
            "face recognition",
            "face detection",
            "face verification",
            "face identification",
            "face detection",
        ]
        # 人脸生成相关搜索关键词
        self.face_generation_keywords = [
            "face generation",
            "face synthesis",
            "face editing",
            "face restoration",
            "face reconstruction",
            "portrait generation",
            "face GAN",
            "face diffusion",
        ]

    def search_papers(self, keywords: List[str], max_results: int = 10) -> List[Dict]:
        """
        搜索 arXiv 论文

        Args:
            keywords: 搜索关键词列表
            max_results: 最大返回数量

        Returns:
            论文信息列表
        """
        papers = []

        # 获取最近7天的论文
        date_from = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d%H%M")
        date_to = datetime.now().strftime("%Y%m%d%H%M")

        for keyword in keywords:
            # 构建搜索查询
            query = f"all:{keyword}+AND+submittedDate:[{date_from}+TO+{date_to}]"
            search_query = f"search_query={urllib.parse.quote(query)}"
            params = f"{search_query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"

            url = f"{self.base_url}?{params}"

            try:
                # 获取数据
                with urllib.request.urlopen(url, timeout=30) as response:
                    data = response.read().decode("utf-8")

                # 解析 XML
                root = ET.fromstring(data)
                ns = {"atom": "http://www.w3.org/2005/Atom"}

                for entry in root.findall("atom:entry", ns):
                    paper = self._parse_entry(entry, keyword)
                    if paper and not self._is_duplicate(papers, paper):
                        papers.append(paper)

            except Exception as e:
                print(f"搜索 '{keyword}' 时出错: {e}")
                continue

        # 按日期排序
        papers.sort(key=lambda x: x["published"], reverse=True)

        # 去重并限制数量
        papers = self._deduplicate(papers)[:20]

        return papers

    def _parse_entry(self, entry, keyword: str) -> Dict:
        """解析单个论文条目"""
        try:
            # 提取基本信息
            title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
            summary = entry.find("atom:summary", ns).text.strip()

            # 提取作者
            authors = []
            for author in entry.findall("atom:author", ns):
                name = author.find("atom:name", ns)
                if name is not None:
                    authors.append(name.text)

            # 提取 ID 和链接
            arxiv_id = entry.find("atom:id", ns).text.split("/")[-1]
            pdf_link = ""
            for link in entry.findall("atom:link", ns):
                if link.get("title") == "pdf":
                    pdf_link = link.get("href")
                    break

            # 提取发布日期
            published = entry.find("atom:published", ns).text[:10]

            # 判断分类
            category = self._classify_keyword(keyword)

            # 清理摘要
            summary = self._clean_summary(summary)

            return {
                "id": arxiv_id,
                "title": title,
                "authors": authors[:5],  # 最多5个作者
                "summary": summary,
                "pdf_link": pdf_link,
                "arxiv_link": f"https://arxiv.org/abs/{arxiv_id}",
                "published": published,
                "category": category,
                "keywords": keyword,
            }
        except Exception as e:
            print(f"解析论文条目时出错: {e}")
            return None

    def _classify_keyword(self, keyword: str) -> str:
        """根据关键词分类"""
        face_recognition = [
            "face recognition",
            "face detection",
            "face verification",
            "face identification",
        ]
        if keyword.lower() in [k.lower() for k in face_recognition]:
            return "人脸识别"
        return "人脸生成"

    def _clean_summary(self, summary: str) -> str:
        """清理摘要文本"""
        # 移除多余空白
        summary = re.sub(r"\s+", " ", summary)
        # 截断到合适长度
        if len(summary) > 500:
            summary = summary[:500] + "..."
        return summary

    def _is_duplicate(self, papers: List[Dict], paper: Dict) -> bool:
        """检查是否重复"""
        for p in papers:
            if p["id"] == paper["id"]:
                return True
        return False

    def _deduplicate(self, papers: List[Dict]) -> List[Dict]:
        """去重"""
        seen = set()
        result = []
        for paper in papers:
            if paper["id"] not in seen:
                seen.add(paper["id"])
                result.append(paper)
        return result

    def fetch_all_papers(self) -> Dict[str, List[Dict]]:
        """获取所有相关论文"""
        print("正在获取人脸识别相关论文...")
        recognition_papers = self.search_papers(self.face_recognition_keywords)

        print("正在获取人脸生成相关论文...")
        generation_papers = self.search_papers(self.face_generation_keywords)

        # 合并并去重
        all_papers = recognition_papers + generation_papers
        all_papers = self._deduplicate(all_papers)
        all_papers.sort(key=lambda x: x["published"], reverse=True)

        return {
            "face_recognition": recognition_papers,
            "face_generation": generation_papers,
            "all": all_papers,
        }


def main():
    """测试脚本"""
    fetcher = ArxivFetcher()
    papers = fetcher.fetch_all_papers()

    print(f"\n获取到 {len(papers['all'])} 篇论文")
    print(f"人脸识别: {len(papers['face_recognition'])} 篇")
    print(f"人脸生成: {len(papers['face_generation'])} 篇")

    for paper in papers["all"][:5]:
        print(f"\n--- {paper['category']} ---")
        print(f"标题: {paper['title']}")
        print(f"ID: {paper['id']}")
        print(f"作者: {', '.join(paper['authors'])}")
        print(f"日期: {paper['published']}")


if __name__ == "__main__":
    main()
