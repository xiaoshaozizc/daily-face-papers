#!/usr/bin/env python3
"""
多来源论文获取脚本
支持 arXiv, CVPR, NeurIPS 等网站
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timedelta
from typing import List, Dict


class PaperFetcher:
    """论文获取基类"""

    def __init__(self):
        self.face_keywords = [
            "face", "facial", "face recognition", "face detection",
            "face verification", "face generation", "face synthesis",
            "face editing", "face reconstruction", "portrait",
            "face GAN", "face anti-spoofing", "face alignment"
        ]

    def _is_face_related(self, text: str) -> bool:
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in self.face_keywords)

    def _clean_summary(self, summary: str) -> str:
        summary = re.sub(r"\s+", " ", summary)
        if len(summary) > 500:
            summary = summary[:500] + "..."
        return summary

    def _classify_category(self, title: str, summary: str) -> str:
        text = (title + " " + summary).lower()
        recognition_kw = ["recognition", "detection", "verification", "alignment", "anti-spoofing"]
        generation_kw = ["generation", "synthesis", "editing", "reconstruction", "GAN"]

        for kw in recognition_kw:
            if kw in text:
                return "人脸识别"
        for kw in generation_kw:
            if kw in text:
                return "人脸生成"
        return "人脸识别"


class ArxivFetcher(PaperFetcher):
    """arXiv 论文获取器"""

    def __init__(self):
        super().__init__()
        self.base_url = "http://export.arxiv.org/api/query"

    def fetch_papers(self, days: int = 7, max_per_keyword: int = 10) -> List[Dict]:
        papers = []
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d%H%M")
        date_to = datetime.now().strftime("%Y%m%d%H%M")

        keywords = [
            "face recognition", "face detection", "face verification",
            "face generation", "face synthesis", "face editing",
            "face reconstruction", "face anti-spoofing"
        ]

        for keyword in keywords:
            try:
                query = f"all:{keyword}+AND+submittedDate:[{date_from}+TO+{date_to}]"
                params = f"search_query={urllib.parse.quote(query)}&start=0&max_results={max_per_keyword}&sortBy=submittedDate&sortOrder=descending"
                url = f"{self.base_url}?{params}"

                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=30) as response:
                    data = response.read().decode("utf-8")

                root = ET.fromstring(data)
                ns = {"atom": "http://www.w3.org/2005/Atom"}

                for entry in root.findall("atom:entry", ns):
                    try:
                        title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
                        summary = entry.find("atom:summary", ns).text.strip()

                        if not self._is_face_related(title + " " + summary):
                            continue

                        authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
                        arxiv_id = entry.find("atom:id", ns).text.split("/")[-1]

                        pdf_link = ""
                        for link in entry.findall("atom:link", ns):
                            if link.get("title") == "pdf":
                                pdf_link = link.get("href")
                                break

                        published = entry.find("atom:published", ns).text[:10]

                        papers.append({
                            "id": arxiv_id,
                            "title": title,
                            "authors": authors[:5],
                            "summary": self._clean_summary(summary),
                            "pdf_link": pdf_link,
                            "arxiv_link": f"https://arxiv.org/abs/{arxiv_id}",
                            "published": published,
                            "category": self._classify_category(title, summary),
                            "source": "arXiv",
                            "keywords": [keyword]
                        })
                    except Exception:
                        continue

            except Exception as e:
                print(f"  arXiv 搜索 '{keyword}' 出错: {e}")
                continue

        return self._deduplicate(papers)

    def _deduplicate(self, papers: List[Dict]) -> List[Dict]:
        seen = set()
        result = []
        for p in papers:
            if p["id"] not in seen:
                seen.add(p["id"])
                result.append(p)
        return result


class PaperAggregator:
    """论文聚合器"""

    def __init__(self):
        self.fetchers = {
            "arXiv": ArxivFetcher(),
        }

    def fetch_all(self, days: int = 7) -> Dict[str, List[Dict]]:
        all_papers = []
        sources_info = {}

        for name, fetcher in self.fetchers.items():
            print(f"正在从 {name} 获取论文...")
            try:
                papers = fetcher.fetch_papers(days=days)
                sources_info[name] = len(papers)
                all_papers.extend(papers)
                print(f"  {name}: 获取到 {len(papers)} 篇")
            except Exception as e:
                print(f"  {name}: 获取失败 - {e}")
                sources_info[name] = 0

        # 去重和排序
        all_papers = self._deduplicate(all_papers)
        all_papers.sort(key=lambda x: x["published"], reverse=True)

        recognition = [p for p in all_papers if p.get("category") == "人脸识别"]
        generation = [p for p in all_papers if p.get("category") == "人脸生成"]

        return {
            "all": all_papers,
            "face_recognition": recognition,
            "face_generation": generation,
            "sources": sources_info
        }

    def _deduplicate(self, papers: List[Dict]) -> List[Dict]:
        seen = set()
        result = []
        for p in papers:
            pid = p.get("id", "")
            if pid and pid not in seen:
                seen.add(pid)
                result.append(p)
        return result


if __name__ == "__main__":
    print("=" * 60)
    print("  多来源论文获取系统")
    print("=" * 60)

    aggregator = PaperAggregator()
    papers = aggregator.fetch_all(days=30)

    print("\n" + "=" * 60)
    print(f"共获取 {len(papers['all'])} 篇论文")
    print(f"人脸识别: {len(papers['face_recognition'])} 篇")
    print(f"人脸生成: {len(papers['face_generation'])} 篇")
    print(f"来源统计: {papers['sources']}")
    print("=" * 60)
