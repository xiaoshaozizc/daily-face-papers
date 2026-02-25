#!/usr/bin/env python3
"""
多来源论文获取脚本
支持 arXiv, CVPR, ICCV, ECCV, NeurIPS, ICML 等网站
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict
from abc import ABC, abstractmethod


# ========== 基础类 ==========

class PaperFetcher(ABC):
    """论文获取器基类"""

    def __init__(self):
        self.face_keywords = [
            "face", "facial", "face recognition", "face detection",
            "face verification", "face generation", "face synthesis",
            "face editing", "face reconstruction", "face restoration",
            "portrait", "face GAN", "face diffusion", "face anti-spoofing",
            "face alignment", "face parsing", "face swapping", "face cloning"
        ]

    @abstractmethod
    def fetch_papers(self, days: int = 7, max_per_keyword: int = 5) -> List[Dict]:
        """获取论文"""
        pass

    def _is_face_related(self, text: str) -> bool:
        """检查是否与人脸相关"""
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in self.face_keywords)

    def _clean_summary(self, summary: str) -> str:
        """清理摘要文本"""
        summary = re.sub(r"\s+", " ", summary)
        if len(summary) > 500:
            summary = summary[:500] + "..."
        return summary

    def _classify_category(self, title: str, summary: str) -> str:
        """分类"""
        text = (title + " " + summary).lower()
        recognition_kw = ["recognition", "detection", "verification", "identification",
                          "alignment", "anti-spoofing", "liveness", "tracking"]
        generation_kw = ["generation", "synthesis", "editing", "reconstruction",
                         "restoration", "portrait", "GAN", "diffusion", "swap"]

        for kw in recognition_kw:
            if kw in text:
                return "人脸识别"
        for kw in generation_kw:
            if kw in text:
                return "人脸生成"
        return "人脸识别"  # 默认


# ========== ArXiv 获取器 ==========

class ArxivFetcher(PaperFetcher):
    """arXiv 论文获取器"""

    def __init__(self):
        super().__init__()
        self.base_url = "http://export.arxiv.org/api/query"

    def fetch_papers(self, days: int = 7, max_per_keyword: int = 5) -> List[Dict]:
        papers = []
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d%H%M")
        date_to = datetime.now().strftime("%Y%m%d%H%M")

        # 搜索关键词
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

                with urllib.request.urlopen(url, timeout=30) as response:
                    data = response.read().decode("utf-8")

                root = ET.fromstring(data)
                ns = {"atom": "http://www.w3.org/2005/Atom"}

                for entry in root.findall("atom:entry", ns):
                    try:
                        title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
                        summary = entry.find("atom:summary", ns).text.strip()

                        # 检查是否与人脸相关
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

                        paper = {
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
                        }
                        papers.append(paper)

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


# ========== CVPR/OpenCV 获取器 ==========

class CVPRFetcher(PaperFetcher):
    """CVPR/ICCV/ECCV 论文获取器 (openaccess.thecvf.com)"""

    def __init__(self):
        super().__init__()
        self.base_url = "http://openaccess.thecvf.com"

    def fetch_papers(self, days: int = 30, max_per_keyword: int = 5) -> List[Dict]:
        papers = []

        # 会议列表
        conferences = ["CVPR", "ICCV", "ECCV", "WACV"]

        for conf in conferences:
            try:
                url = f"{self.base_url}/{conf}_html.py"
                with urllib.request.urlopen(url, timeout=30) as response:
                    html = response.read().decode("utf-8")

                # 解析论文列表
                papers.extend(self._parse_conf_papers(html, conf))

            except Exception as e:
                print(f"  {conf} 获取出错: {e}")
                continue

        return papers[:50]

    def _parse_conf_papers(self, html: str, conference: str) -> List[Dict]:
        papers = []

        # 简单的HTML解析
        import re
        # 匹配论文标题和链接
        pattern = r'<a href="(content_[^"]+\.html)">([^<]+)</a>'
        matches = re.findall(pattern, html)

        for match in matches[:20]:
            link, title = match
            if self._is_face_related(title):
                try:
                    # 获取详情页
                    detail_url = f"{self.base_url}/{link}"
                    with urllib.request.urlopen(detail_url, timeout=30) as response:
                        detail_html = response.read().decode("utf-8")

                    # 提取信息
                    paper = self._parse_detail(detail_html, conference, detail_url)
                    if paper:
                        papers.append(paper)

                except Exception:
                    continue

        return papers

    def _parse_detail(self, html: str, conference: str, url: str) -> Dict:
        try:
            # 提取标题
            title_match = re.search(r'<div class="paper-title">([^<]+)</div>', html)
            if not title_match:
                return None
            title = title_match.group(1).strip()

            # 提取作者
            authors_match = re.search(r'<div class="authors">(.*?)</div>', html, re.DOTALL)
            authors = []
            if authors_match:
                authors = [a.strip() for a in authors_match.group(1).split(",")]

            # 提取摘要
            summary_match = re.search(r'<div class="abstract">(.*?)</div>', html, re.DOTALL)
            summary = ""
            if summary_match:
                summary = self._clean_summary(summary_match.group(1).strip())

            # 提取PDF链接
            pdf_match = re.search(r'<a href="([^"]+\.pdf)">PDF</a>', html)
            pdf_link = ""
            if pdf_match:
                pdf_link = f"{self.base_url}/{pdf_match.group(1)}"

            # 提取日期 (从URL或内容)
            date_match = re.search(r'CVPR (\d{4})|ICCV (\d{4})|ECCV (\d{4})', html)
            published = date_match.group(1) or date_match.group(2) or date_match.group(3)
            if published:
                published = f"{published}-01-01"

            return {
                "id": f"{conference}_{title[:20].replace(' ', '_')}",
                "title": title,
                "authors": authors[:5],
                "summary": summary,
                "pdf_link": pdf_link,
                "arxiv_link": url,
                "published": published or "2024-01-01",
                "category": self._classify_category(title, summary),
                "source": conference,
                "keywords": ["computer vision", "face"]
            }

        except Exception:
            return None


# ========== NeurIPS 获取器 ==========

class NeurIPSFetcher(PaperFetcher):
    """NeurIPS 论文获取器"""

    def __init__(self):
        super().__init__()
        self.base_url = "https://papers.nips.cc"

    def fetch_papers(self, days: int = 30, max_per_keyword: int = 5) -> List[Dict]:
        papers = []

        try:
            url = f"{self.base_url}/book/intro/-1"
            with urllib.request.urlopen(url, timeout=30) as response:
                html = response.read().decode("utf-8")

            # 解析论文
            papers = self._parse_nips_papers(html)

        except Exception as e:
            print(f"  NeurIPS 获取出错: {e}")

        return papers

    def _parse_nips_papers(self, html: str) -> List[Dict]:
        papers = []

        # 匹配论文链接
        pattern = r'<a href="/paper/(\d+)-([^"]+)"'
        matches = re.findall(pattern, html)

        for pid, title_slug in matches[:30]:
            try:
                paper_url = f"{self.base_url}/paper/{pid}-{title_slug}"
                with urllib.request.urlopen(paper_url, timeout=30) as response:
                    paper_html = response.read().decode("utf-8")

                if not self._is_face_related(paper_html):
                    continue

                # 提取标题
                title_match = re.search(r'<h1>([^<]+)</h1>', paper_html)
                title = title_match.group(1) if title_match else title_slug.replace("-", " ")

                # 提取作者
                authors_match = re.search(r'<div class="meta">(.*?)</div>', paper_html, re.DOTALL)
                authors = []
                if authors_match:
                    authors = [a.strip() for a in authors_match.group(1).split(",")]

                # 提取PDF链接
                pdf_match = re.search(r'href="(paper/{}-\w+\.pdf)"'.format(pid), paper_html)
                pdf_link = f"{self.base_url}/{pdf_match.group(1)}" if pdf_match else ""

                paper = {
                    "id": f"NeurIPS_{pid}",
                    "title": title,
                    "authors": authors[:5],
                    "summary": "请查看PDF获取摘要",
                    "pdf_link": pdf_link,
                    "arxiv_link": paper_url,
                    "published": "2024-01-01",
                    "category": self._classify_category(title, ""),
                    "source": "NeurIPS",
                    "keywords": ["neural networks", "face"]
                }
                papers.append(paper)

            except Exception:
                continue

        return papers


# ========== Papers with Code 获取器 ==========

class PapersWithCodeFetcher(PaperFetcher):
    """Papers with Code 获取器"""

    def __init__(self):
        super().__init__()
        self.base_url = "https://paperswithcode.com"

    def fetch_papers(self, days: int = 30, max_per_keyword: int = 5) -> List[Dict]:
        papers = []

        # 搜索人脸相关论文
        keywords = ["face-recognition", "face-generation", "face-detection"]

        for kw in keywords:
            try:
                url = f"{self.base_url}/search?q={kw}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=30) as response:
                    html = response.read().decode("utf-8")

                papers.extend(self._parse_pwc(html, kw))

            except Exception as e:
                print(f"  PapersWithCode 搜索 '{kw}' 出错: {e}")
                continue

        return papers

    def _parse_pwc(self, html: str, keyword: str) -> List[Dict]:
        papers = []

        # 简化的解析
        pattern = r'<a href="/paper/([^"]+)"'
        matches = re.findall(pattern, html)

        for slug in matches[:10]:
            try:
                paper_url = f"{self.base_url}/paper/{slug}"
                papers.append({
                    "id": f"PWC_{slug[:20]}",
                    "title": slug.replace("-", " ").title(),
                    "authors": [],
                    "summary": "请访问 Papers with Code 查看详情",
                    "pdf_link": "",
                    "arxiv_link": paper_url,
                    "published": datetime.now().strftime("%Y-%m-%d"),
                    "category": "人脸识别" if "recognition" in keyword or "detection" in keyword else "人脸生成",
                    "source": "PapersWithCode",
                    "keywords": [keyword]
                })
            except Exception:
                continue

        return papers


# ========== 统一获取器 ==========

class PaperAggregator:
    """论文聚合器"""

    def __init__(self):
        self.fetchers = {
            "arXiv": ArxivFetcher(),
            "CVPR": CVPRFetcher(),
            "NeurIPS": NeurIPSFetcher(),
            # "PapersWithCode": PapersWithCodeFetcher(),  # 可选启用
        }

    def fetch_all(self, days: int = 7) -> Dict[str, List[Dict]]:
        """获取所有来源的论文"""
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

        # 去重
        all_papers = self._deduplicate(all_papers)
        # 排序
        all_papers.sort(key=lambda x: x["published"], reverse=True)

        # 分类
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


def main():
    """测试脚本"""
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


if __name__ == "__main__":
    main()
