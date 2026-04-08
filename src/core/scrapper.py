"""
Scraper concurrente en 2 fases para la pagina: bancolombia.com/personas; 
aunque puede ser adaptado a otros sitios con estructura similar.
   > Htmls dinámicos, requiere renderizado completo para este caso particular usamos Playwright;
   > Sin embargo, en caso de requerir usar otras herramientas como Scrapy o BeautifulSoup, 
   > se podrían adaptar las funciones de extracción de contenido y links. 
   > Dandole la flexibilidad de usar otras herramienta más adecuada para cada caso.
   > Esto anterior para mostrar un diseño modular y adaptable a diferentes necesidades de scraping.

Fase 1: Descubrimiento BFS de URLs.
Fase 2: Scraping paralelo de contenido con semáforo.

Retorna un DataFrame con columnas: id, metadata, texto.
Lista para limpieza, chunking y carga a base de conocimiento.
"""

import asyncio, json, logging
from datetime import datetime
from pathlib import Path
import pandas as pd
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DROP_TAGS = ["script", "style", "footer", "nav", "header"]
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
ERRORS_FILE = Path("data/scraping_errors.json")

# Funciones auxiliares 
def load_robots(base_url: str) -> RobotFileParser:
    """
    Descarga y parsea robots.txt del sitio base.
    """
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception as exc:
        logger.warning("No se pudo leer robots.txt desde %s: %s", robots_url, exc)
    return rp

def same_section(base_url: str, url: str) -> bool:
    """Retorna True si url pertenece al mismo host + path prefix que base_url."""
    base = urlparse(base_url)
    candidate = urlparse(url)
    return (
        candidate.scheme in ("http", "https")
        and candidate.netloc == base.netloc
        and candidate.path.startswith(base.path)
    )

def save_errors(errors: list[dict]) -> None:
    """Guarda errores acumulados en data/scraping_errors.json."""
    if not errors:
        return
    ERRORS_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if ERRORS_FILE.exists():
        try:
            existing = json.loads(ERRORS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    ERRORS_FILE.write_text(
        json.dumps(existing + errors, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("💾 %d errores guardados en %s", len(errors), ERRORS_FILE)


# ── Scraping concurrente ─────────────────────────────────────────────────────



async def fetch_page_content_only(context, url: str, semaphore: asyncio.Semaphore, max_retries: int = 3) -> dict | None:
    """Versión optimizada: solo extrae contenido, NO links.
    Usa semáforo para controlar concurrencia.
    """
    async with semaphore:
        for attempt in range(1, max_retries + 1):
            page = None
            try:
                page = await context.new_page()
                response = await page.goto(url, wait_until="load", timeout=45_000)
                await page.wait_for_timeout(1_500)

                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")

                # Limpiar tags de navegación
                for tag in soup(DROP_TAGS):
                    tag.decompose()

                title_tag = soup.find("title")
                title = title_tag.get_text(strip=True) if title_tag else ""
                content = soup.get_text(separator=" ", strip=True)

                # Derivar categoría del path
                path_parts = [p for p in urlparse(url).path.strip("/").split("/") if p]
                category = path_parts[-1] if len(path_parts) > 1 else "personas"

                status = response.status if response else None
                logger.info("✅ %s  status=%s  chars=%d", url, status, len(content))

                return {
                    "url": url,
                    "title": title,
                    "content": content,
                    "category": category,
                    "scraped_at": datetime.utcnow().isoformat(),
                }

            except Exception as exc:
                logger.warning("Intento %d/%d falló para %s: %s", attempt, max_retries, url, exc)
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return None
            finally:
                if page and not page.is_closed():
                    await page.close()

        return None

async def discover_urls_bfs(base_url: str, max_depth: int, max_pages: int, respect_robots: bool) -> list[str]:
    """Fase 1: Descubrimiento rápido de URLs usando BFS.
    Solo extrae links, NO scrapea contenido completo.
    """
    robots = load_robots(base_url) if respect_robots else None
    visited = set()
    queue = [(base_url, 0)]
    discovered = []

    logger.info("🔍 Fase 1: Descubriendo URLs (BFS hasta depth=%d)...", max_depth)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            user_agent=USER_AGENT,
            locale="es-CO",
            viewport={"width": 1280, "height": 800},
        )
        try:
            while queue and len(discovered) < max_pages:
                url, depth = queue.pop(0)
                if url in visited:
                    continue
                visited.add(url)

                if robots and not robots.can_fetch("*", url):
                    logger.debug("robots.txt disallows %s", url)
                    continue

                discovered.append(url)
                logger.info("[%3d] Descubierto: %s (depth=%d)", len(discovered), url, depth)

                # Si no hemos alcanzado max_depth, extraer links
                if depth < max_depth:
                    page = None
                    try:
                        page = await context.new_page()
                        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                        await page.wait_for_timeout(1_000)

                        html = await page.content()
                        soup = BeautifulSoup(html, "html.parser")

                        links = [
                            urljoin(url, a["href"])
                            for a in soup.find_all("a", href=True)
                            if not a["href"].startswith(("#", "mailto:", "tel:"))
                        ]

                        for link in links:
                            if link not in visited and same_section(base_url, link):
                                queue.append((link, depth + 1))

                    except Exception as exc:
                        logger.warning("Error extrayendo links de %s: %s", url, exc)
                    finally:
                        if page and not page.is_closed():
                            await page.close()

        finally:
            await context.close()
            await browser.close()

    logger.info("✅ Fase 1 completada: %d URLs descubiertas", len(discovered))
    return discovered[:max_pages]

async def crawl_to_dataframe(url: str, depth: int, max_pages: int, concurrency: int) -> list[dict]:
    """Crawler concurrente en 2 fases:
    1. Descubrimiento BFS de URLs
    2. Scraping paralelo de contenido
    """
    logger.info("🚀 Crawler concurrente iniciado")
    logger.info("   Base: %s", url)
    logger.info("   Depth: %d | Max pages: %d | Concurrency: %d", depth, max_pages, concurrency)

    # Fase 1: Descubrir URLs con BFS
    urls = await discover_urls_bfs(
        base_url=url,
        max_depth=depth,
        max_pages=max_pages,
        respect_robots=True,
    )

    if not urls:
        logger.warning("⚠️ No se descubrieron URLs")
        return []

    # Fase 2: Scraping concurrente de contenido
    logger.info("\n📥 Fase 2: Scraping concurrente de %d URLs...", len(urls))
    semaphore = asyncio.Semaphore(concurrency)
    errors = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent=USER_AGENT,
            locale="es-CO",
            timezone_id="America/Bogota",
            viewport={"width": 1280, "height": 800},
        )

        try:
            # Crear tareas concurrentes para todas las URLs
            tasks = [
                fetch_page_content_only(context, url, semaphore)
                for url in urls
            ]

            # Ejecutar todas en paralelo (limitadas por el semáforo)
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filtrar resultados exitosos
            pages = []
            for url, result in zip(urls, results):
                if isinstance(result, Exception):
                    logger.error("❌ Error en %s: %s", url, result)
                    errors.append({"url": url, "reason": str(result)})
                elif result is None:
                    errors.append({"url": url, "reason": "failed after retries"})
                else:
                    pages.append(result)

        finally:
            await context.close()
            await browser.close()
            if errors:
                save_errors(errors)

    logger.info("✅ Scraping completado: %d páginas extraídas, %d errores", len(pages), len(errors))
    return pages

def list_json_to_df(pages: list[dict]) -> pd.DataFrame:
    """Convierte lista de dicts a DataFrame con 3 columnas id, metadata y texto.
    Id: hash de la url para asegurar unicidad.
    Metadata: dict con url, title, category.
    Texto: Metadata.content 
    Ejemplo de estructura final:
    | id          | metadata                                                      |          texto                       |
    |-------------|---------------------------------------------------------------|--------------------------------------|
    |             | {"url": "https://www.bancolombia.com/personas/creditos",      |                                      |
    | 1234567890  |   "title": "Créditos - Bancolombia",                          | "Contenido completo de la página..." | 
    |             |   "category": "creditos"}                                     |                                      |
    |-------------|---------------------------------------------------------------|--------------------------------------|
    | 09876543210 | {"url": "https://www.bancolombia.com/personas/inversiones",   |                                      |
    |             |   "title": "Inversiones - Bancolombia",                       | "Contenido completo de la página..." |
    |             |   "category": "inversiones"}                                  |                                      |   
    """
    records = []
    for page in pages:
        url = page["url"]
        record = {
            "id": hash(url),
            "metadata": json.dumps({
                "url": url,
                "title": page.get("title", ""),
                "category": page.get("category", ""),
            }, ensure_ascii=False),
            "texto": page.get("content", ""),
        }
        records.append(record)
    return pd.DataFrame(records)


def run_scrapping(url: str = "https://www.bancolombia.com/personas", depth: int = 2, max_pages: int = 5, concurrency: int = 5) -> pd.DataFrame | None:
    """Función principal: ejecuta el crawler y retorna DataFrame.
    
    Returns:
        DataFrame con columnas: id, metadata, texto
        None si no se pudieron extraer páginas
    """
    try:
        pages = asyncio.run(crawl_to_dataframe(url, depth, max_pages, concurrency))

    except KeyboardInterrupt:
        logger.warning("⚠️ Scraping interrumpido por el usuario.")
        raise

    except Exception as exc:
        logger.error("❌ Error fatal durante el scraping: %s", exc, exc_info=True)
        raise
    
    # Convertir páginas a DataFrame
    if not pages:
        logger.warning("⚠️ No se extrajeron páginas. DataFrame vacío.")
        return None
    
    logger.info("📊 Convirtiendo %d páginas a DataFrame...", len(pages))
    df = list_json_to_df(pages)
    
    # Configurar pandas para mejor visualización
    pd.set_option('display.max_colwidth', 100)
    pd.set_option('display.width', None)
    
    logger.info("✅ DataFrame creado exitosamente con %d registros", len(df))
    
    return df
