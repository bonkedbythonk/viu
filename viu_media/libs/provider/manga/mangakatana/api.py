import logging
import re
from typing import Optional
from urllib.parse import quote_plus

from ..base import MangaProvider
from .constants import BASE_URL, HEADERS, SEARCH_URL

logger = logging.getLogger(__name__)


class MangaKatanaApi(MangaProvider):
    """MangaKatana scraper implementing the manga provider interface."""

    HEADERS = HEADERS

    def search_for_manga(self, title: str, *args):
        """Search for manga on MangaKatana.

        Args:
            title: The manga title to search for.

        Returns:
            A list of dicts with keys: title, url, cover_image.
            None on failure.
        """
        try:
            encoded_query = quote_plus(title)
            url = f"{SEARCH_URL}?search={encoded_query}&search_by=book_name"
            response = self.session.get(url, follow_redirects=True)
            if not response.is_success:
                logger.error(
                    f"[MANGAKATANA] Search request failed: {response.status_code}"
                )
                return None

            html = response.text

            # If the search redirects directly to a manga page (single result),
            # handle that case
            if "/manga/" in str(response.url) and "search" not in str(response.url):
                return self._parse_single_result(html, str(response.url))

            return self._parse_search_results(html)

        except Exception as e:
            logger.error(f"[MANGAKATANA] Search error: {e}")
            return None

    def _parse_search_results(self, html: str):
        """Parse the search results page HTML.

        Structure:
            #book_list > .item > (.media .wrap_img a img for cover,
                                   .text h3.title a for title+url)
        """
        try:
            from lxml import html as lxml_html
        except ImportError:
            return self._parse_search_results_fallback(html)

        try:
            tree = lxml_html.fromstring(html)
            items = tree.xpath('//*[@id="book_list"]//*[contains(@class, "item")]')

            results = []
            for item in items:
                title_el = item.xpath('.//h3[contains(@class, "title")]//a')
                if not title_el:
                    continue

                title = title_el[0].text_content().strip()
                manga_url = title_el[0].get("href", "")

                cover_els = item.xpath(".//img")
                cover_image = ""
                if cover_els:
                    cover_image = cover_els[0].get("src", "")

                results.append(
                    {
                        "title": title,
                        "url": manga_url,
                        "cover_image": cover_image,
                    }
                )

            return results if results else None

        except Exception as e:
            logger.error(f"[MANGAKATANA] Parse search results error: {e}")
            return None

    def _parse_search_results_fallback(self, html: str):
        """Fallback parser using regex when lxml is unavailable."""
        results = []
        # Match title links within book_list items
        pattern = re.compile(
            r'<h3[^>]*class="[^"]*title[^"]*"[^>]*>\s*<a\s+href="([^"]+)"[^>]*>([^<]+)</a>',
            re.IGNORECASE,
        )
        for match in pattern.finditer(html):
            manga_url = match.group(1)
            title = match.group(2).strip()
            results.append(
                {
                    "title": title,
                    "url": manga_url,
                    "cover_image": "",
                }
            )

        return results if results else None

    def _parse_single_result(self, html: str, url: str):
        """Handle case where search redirects to a single manga page."""
        try:
            from lxml import html as lxml_html

            tree = lxml_html.fromstring(html)
            title_el = tree.xpath("//h1")
            title = title_el[0].text_content().strip() if title_el else "Unknown"

            cover_els = tree.xpath('//*[contains(@class, "cover")]//img')
            cover_image = cover_els[0].get("src", "") if cover_els else ""

            return [
                {
                    "title": title,
                    "url": url,
                    "cover_image": cover_image,
                }
            ]
        except Exception as e:
            logger.error(f"[MANGAKATANA] Parse single result error: {e}")
            return [{"title": "Unknown", "url": url, "cover_image": ""}]

    def get_manga(self, manga_url: str):
        """Fetch manga details and chapter list.

        Args:
            manga_url: The full MangaKatana URL for the manga.

        Returns:
            Dict with keys: id (url), title, poster, availableChapters.
            None on failure.
        """
        try:
            response = self.session.get(manga_url, follow_redirects=True)
            if not response.is_success:
                logger.error(
                    f"[MANGAKATANA] Manga fetch failed: {response.status_code}"
                )
                return None

            html = response.text
            return self._parse_manga_detail(html, manga_url)

        except Exception as e:
            logger.error(f"[MANGAKATANA] Get manga error: {e}")
            return None

    def _parse_manga_detail(self, html: str, manga_url: str):
        """Parse manga detail page to extract title and chapters.

        Structure:
            .chapters > .chapter > a (href=chapter_url, text=chapter_title)
        """
        try:
            from lxml import html as lxml_html
        except ImportError:
            return self._parse_manga_detail_fallback(html, manga_url)

        try:
            tree = lxml_html.fromstring(html)

            # Extract title
            title_el = tree.xpath(
                '//h1[contains(@class, "heading")]'
            ) or tree.xpath("//h1")
            title = title_el[0].text_content().strip() if title_el else "Unknown"

            # Extract cover image
            cover_els = tree.xpath(
                '//*[contains(@class, "cover")]//img'
            ) or tree.xpath('//*[contains(@class, "media")]//img')
            poster = cover_els[0].get("src", "") if cover_els else ""

            # Extract chapters
            chapter_els = tree.xpath(
                '//*[contains(@class, "chapters")]//*[contains(@class, "chapter")]//a'
            )

            chapters = []
            for ch_el in chapter_els:
                ch_url = ch_el.get("href", "")
                ch_title = ch_el.text_content().strip()
                if ch_url and ch_title:
                    chapters.append(
                        {
                            "title": ch_title,
                            "url": ch_url,
                        }
                    )

            return {
                "id": manga_url,
                "title": title,
                "poster": poster,
                "availableChapters": chapters,
            }

        except Exception as e:
            logger.error(f"[MANGAKATANA] Parse manga detail error: {e}")
            return None

    def _parse_manga_detail_fallback(self, html: str, manga_url: str):
        """Fallback parser for manga detail page."""
        # Extract title
        title_match = re.search(r"<h1[^>]*>([^<]+)</h1>", html)
        title = title_match.group(1).strip() if title_match else "Unknown"

        # Extract chapters
        chapter_pattern = re.compile(
            r'<div[^>]*class="[^"]*chapter[^"]*"[^>]*>\s*<a\s+href="([^"]+)"[^>]*>([^<]+)</a>',
            re.IGNORECASE,
        )
        chapters = []
        
        # Restrict search to the chapters container to avoid sidebar links
        chapters_block_match = re.search(
            r'<div[^>]*class="[^"]*chapters[^"]*"[^>]*>(.*?)</div>\s*</div>', 
            html, 
            re.DOTALL | re.IGNORECASE
        )
        search_html = chapters_block_match.group(1) if chapters_block_match else html

        for match in chapter_pattern.finditer(search_html):
            chapters.append(
                {
                    "title": match.group(2).strip(),
                    "url": match.group(1),
                }
            )

        return {
            "id": manga_url,
            "title": title,
            "poster": "",
            "availableChapters": chapters,
        }

    def get_chapter_thumbnails(self, manga_url: str, chapter_url: str):
        """Fetch page images for a specific chapter.

        MangaKatana loads images via a JavaScript array variable (e.g., var thzq = [...]).
        We extract this array from the page source.

        Args:
            manga_url: The manga URL (unused but kept for interface compatibility).
            chapter_url: The full URL to the chapter reader page.

        Returns:
            Dict with keys: thumbnails (list of image URLs), title.
            None on failure.
        """
        try:
            response = self.session.get(chapter_url, follow_redirects=True)
            if not response.is_success:
                logger.error(
                    f"[MANGAKATANA] Chapter fetch failed: {response.status_code}"
                )
                return None

            html = response.text
            return self._parse_chapter_pages(html, chapter_url)

        except Exception as e:
            logger.error(f"[MANGAKATANA] Get chapter thumbnails error: {e}")
            return None

    def _parse_chapter_pages(self, html: str, chapter_url: str):
        """Extract page image URLs from the chapter reader page.

        Images are in a JS array like: var thzq = ['url1', 'url2', ...];
        The variable name can vary (thzq, ytaw, th_ytaf, y_data, etc.)
        """
        # Try to extract the JS image array
        # Pattern matches: var VARNAME = ['url1','url2',...];
        js_array_pattern = re.compile(
            r"var\s+\w+\s*=\s*\[([^\]]+)\]\s*;", re.DOTALL
        )

        image_urls: list[str] = []
        for match in js_array_pattern.finditer(html):
            array_content = match.group(1)
            # Extract quoted URLs from the array
            url_pattern = re.compile(r"['\"]([^'\"]+(?:\.jpg|\.png|\.webp|\.jpeg)[^'\"]*)['\"]", re.IGNORECASE)
            urls = url_pattern.findall(array_content)
            if urls and len(urls) > 1:
                image_urls = urls
                break

        # Fallback: try to find img tags in #imgs container
        if not image_urls:
            img_pattern = re.compile(
                r'<img[^>]+src=["\']([^"\']+(?:\.jpg|\.png|\.webp|\.jpeg)[^"\']*)["\'][^>]*>',
                re.IGNORECASE,
            )
            # Look for images within the reading area
            imgs_section = re.search(
                r'id=["\']imgs["\'][^>]*>(.*?)</div>', html, re.DOTALL
            )
            if imgs_section:
                image_urls = img_pattern.findall(imgs_section.group(1))
            else:
                # Last resort: find all manga page images
                all_imgs = img_pattern.findall(html)
                image_urls = [
                    url
                    for url in all_imgs
                    if "mangakatana" in url and "/manga/" in url
                ]

        if not image_urls:
            logger.warning(
                f"[MANGAKATANA] No images found for chapter: {chapter_url}"
            )
            return None

        # Extract chapter title from URL
        chapter_title = chapter_url.rstrip("/").split("/")[-1]

        return {
            "thumbnails": image_urls,
            "title": chapter_title,
        }
