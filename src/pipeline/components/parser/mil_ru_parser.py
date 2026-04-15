"""
Military News Parser - mil.ru source.
Real implementation using Playwright for dynamic content and requests as fallback.
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
from typing import Optional
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from src.pipeline.interfaces import NewsItem, Parser


class MilRuParser(Parser):
    """
    Parser for mil.ru news source.
    
    Fetches news from the Russian Ministry of Defense website.
    Uses dynamic parsing with Playwright by default, falls back to static if needed.
    """

    def __init__(
        self,
        use_dynamic: bool = True,
        timeout: int = 20,
        source_url: str = "https://mil.ru/",
    ):
        self.use_dynamic = use_dynamic
        self.timeout = timeout
        self.source_url = source_url.rstrip('/')
        self.base_url = self.source_url
        self.news_url = urljoin(self.base_url, "/news")
    
    def fetch_latest(self) -> list[NewsItem]:
        """Fetch latest news from mil.ru."""
        logger.info(f"Fetching news from {self.news_url} (dynamic={self.use_dynamic})")
        if self.use_dynamic:
            return self._fetch_dynamic()
        else:
            return self._fetch_static()
    
    # ------------------------------------------------------------
    # Динамический метод через Playwright
    # ------------------------------------------------------------
    def _fetch_dynamic(self) -> list[NewsItem]:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            try:
                page.goto(self.news_url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
                page.wait_for_selector("div[class*='CardListItems'] div[class*='CardT3']", timeout=self.timeout * 1000)

                html = page.content()
                soup = BeautifulSoup(html, 'html.parser')

                # Поиск контейнера с классом, содержащим CardListItems
                container = soup.select_one('div[class*="CardListItems"]')
                if container:
                    cards = container.select('a[class*="Card"]')
                else:
                    cards = soup.select('a[class*="Card"]')

                if not cards:
                    logger.error("No news cards found")
                    return []

                logger.info(f"Found {len(cards)} news cards")
                news_items = []

                for card in cards[:15]:
                    # Извлечение href с приведением к str
                    href_attr = card.get('href')
                    if not href_attr:
                        continue
                    if isinstance(href_attr, list):
                        relative_url = str(href_attr[0]) if href_attr else None
                    else:
                        relative_url = str(href_attr)
                    if not relative_url:
                        continue
                    full_url = urljoin(self.base_url, relative_url)

                    # Заголовок
                    title_elem = card.select_one('div[class*="CardT3Title"]')
                    title = title_elem.get_text(strip=True) if title_elem else "Без заголовка"

                    # Краткое содержание (опционально)
                    brief_elem = card.select_one('div[class*="CardT3Text"]')
                    brief = brief_elem.get_text(strip=True) if brief_elem else ""

                    # Дата
                    date_elem = card.select_one('div[class*="CardT3Date"]')
                    date_str = date_elem.get_text(strip=True) if date_elem else ""

                    logger.debug(f"Processing: {title} ({date_str})")

                    # Полный текст новости
                    full_text = self._fetch_article_text_dynamic(context, full_url)
                    if not full_text:
                        full_text = brief or "Не удалось загрузить полный текст."

                    # Parse date if possible (optional)
                    date_obj = None
                    if date_str:
                        try:
                            # Example: "15 апреля 2026 18:33"
                            from dateutil import parser
                            date_obj = parser.parse(date_str, fuzzy=True)
                        except Exception:
                            pass

                    news_items.append(NewsItem(
                        title=title,
                        url=full_url,
                        content_text=full_text,
                        date=date_obj,
                    ))

                return news_items

            except PlaywrightTimeoutError:
                logger.error("Timeout waiting for news cards")
                return []
            except Exception as e:
                logger.exception(f"Dynamic parsing failed: {e}")
                return []
            finally:
                browser.close()

    def _fetch_article_text_dynamic(self, context, url: str) -> Optional[str]:
        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
            # Ждём появления контента
            try:
                page.wait_for_selector("div[class*='-Content'] div[class='jodit-wysiwyg']", timeout=self.timeout * 1000)
            except PlaywrightTimeoutError:
                logger.debug(f"No jodit-wysiwyg found on {url} within timeout, trying fallback")
            
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')

            # Ищем все div с точным классом "jodit-wysiwyg"
            divs = soup.find_all('div', class_='jodit-wysiwyg')
            if len(divs) >= 2:
                # Берём второй по счёту (индекс 1)
                content_div = divs[1]
                text = content_div.get_text(strip=True)
                if text:
                    return text
                else:
                    logger.warning(f"Second jodit-wysiwyg div is empty for {url}")
            else:
                logger.warning(f"Less than two jodit-wysiwyg divs found on {url} (found {len(divs)})")

            # Fallback: старые селекторы
            for selector in ['div.news-text', 'div.b-news__text', 'div.news-detail__text', 'article', '.content-text']:
                content_div = soup.select_one(selector)
                if content_div:
                    paragraphs = content_div.find_all('p')
                    if paragraphs:
                        return ' '.join(p.get_text(strip=True) for p in paragraphs)
                    return content_div.get_text(strip=True)

            # Последний fallback: все параграфы
            paragraphs = soup.find_all('p')
            if paragraphs:
                return ' '.join(p.get_text(strip=True) for p in paragraphs[:20])
            return None

        except Exception as e:
            logger.warning(f"Failed to fetch article text from {url}: {e}")
            return None
        finally:
            page.close()

    # ------------------------------------------------------------
    # Статический метод (резервный)
    # ------------------------------------------------------------
    def _fetch_static(self) -> list[NewsItem]:
        logger.warning("Using static parser (may not work on dynamic site)")
        html = self._fetch_html_static(self.news_url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        news_items = []
        for link in soup.find_all('a', href=True):
            href_attr = link.get('href')
            if not href_attr:
                continue
            if isinstance(href_attr, list):
                href = str(href_attr[0]) if href_attr else ''
            else:
                href = str(href_attr)

            if '/news/more.htm?id=' in href:
                title = link.get_text(strip=True)
                if not title:
                    continue
                full_url = urljoin(self.base_url, href)
                full_text = self._fetch_article_text_static(full_url)
                news_items.append(NewsItem(
                    title=title,
                    url=full_url,
                    content_text=full_text or "",
                    date=None,
                ))
        return news_items[:10]

    def _fetch_html_static(self, url: str) -> Optional[str]:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        try:
            resp = requests.get(url, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            return resp.text
        except Exception as e:
            logger.error(f"Static fetch failed: {e}")
            return None

    def _fetch_article_text_static(self, url: str) -> Optional[str]:
        html = self._fetch_html_static(url)
        if not html:
            return None
        soup = BeautifulSoup(html, 'html.parser')
        for selector in ['div.news-text', 'div.b-news__text', 'article']:
            div = soup.select_one(selector)
            if div:
                return div.get_text(strip=True)
        return None