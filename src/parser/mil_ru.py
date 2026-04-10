import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from urllib.parse import urljoin
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from src.interfaces import Parser
from src.models import NewsItem


class MilRuParser(Parser):
    BASE_URL = "https://mil.ru"
    NEWS_URL = urljoin(BASE_URL, "/news")

    def __init__(self, use_dynamic: bool = True, timeout: int = 10):
        self.use_dynamic = use_dynamic
        self.timeout = timeout

    def fetch_latest(self) -> List[NewsItem]:
        logger.info(f"Fetching news from {self.NEWS_URL} (dynamic={self.use_dynamic})")
        if self.use_dynamic:
            return self._fetch_dynamic()
        else:
            return self._fetch_static()

    # ------------------------------------------------------------
    # Динамический метод через Playwright
    # ------------------------------------------------------------
    def _fetch_dynamic(self) -> List[NewsItem]:
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
                page.goto(self.NEWS_URL, wait_until="domcontentloaded", timeout=self.timeout * 1000)
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
                    full_url = urljoin(self.BASE_URL, relative_url)

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

                    news_items.append(NewsItem(
                        title=title,
                        url=full_url,
                        content_text=full_text,
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
            page.wait_for_selector("div[class*='-Content'] div[class='jodit-wysiwyg']", timeout=self.timeout * 1000)
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')

            # Ищем все div с точным классом "jodit-wysiwyg"
            divs = soup.find_all('div', class_='jodit-wysiwyg')
            if len(divs) >= 2:
                # Берём второй по счёту (индекс 1)
                content_div = divs[1]
                # Извлекаем текст, удаляем лишние пробелы
                text = content_div.get_text(strip=True)
                if text:
                    return text
                else:
                    logger.warning(f"Second jodit-wysiwyg div is empty for {url}")
            else:
                logger.warning(f"Less than two jodit-wysiwyg divs found on {url} (found {len(divs)})")

            # Fallback: старые селекторы (на случай, если структура изменится)
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
    def _fetch_static(self) -> List[NewsItem]:
        logger.warning("Using static parser (may not work on dynamic site)")
        html = self._fetch_html_static(self.NEWS_URL)
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
                full_url = urljoin(self.BASE_URL, href)
                full_text = self._fetch_article_text_static(full_url)
                news_items.append(NewsItem(title=title, url=full_url, content_text=full_text or ""))
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