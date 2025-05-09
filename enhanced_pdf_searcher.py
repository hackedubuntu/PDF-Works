# Gerekli kütüphaneler: PySide6, requests, beautifulsoup4, lxml, pdfminer.six
# Kurulum: pip install PySide6 requests beautifulsoup4 lxml pdfminer.six

import sys
import os
import re
import io
import random
import time
from urllib.parse import urlparse, parse_qs, unquote, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem,
    QLabel, QProgressBar, QFileDialog, QMessageBox,
    QComboBox, QCheckBox, QSpinBox, QTabWidget, QTextEdit
)
from PySide6.QtCore import Qt, QThread, Signal, QObject, QSettings, QUrl
from PySide6.QtGui import QDesktopServices, QIcon, QFont

import requests
from bs4 import BeautifulSoup
import io

# PDF önizleme için pdfminer.six kullanımı (opsiyonel)
try:
    from pdfminer.high_level import extract_text
    PDF_PREVIEW_AVAILABLE = True
except ImportError:
    PDF_PREVIEW_AVAILABLE = False

# Sabitler ve yapılandırma
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36 Edg/96.0.1054.29',
]

SEARCH_ENGINES = {
    "Google": {
        "base_url": "https://www.google.com/search",
        "params": lambda query, num: {"q": f"{query} filetype:pdf", "num": num, "hl": "tr"}
    },
    "Bing": {
        "base_url": "https://www.bing.com/search",
        "params": lambda query, num: {"q": f"{query} filetype:pdf", "count": num}
    },
    "DuckDuckGo": {
        "base_url": "https://html.duckduckgo.com/html/",
        "params": lambda query, num: {"q": f"{query} filetype:pdf"}
    },
    "Yandex": {
        "base_url": "https://yandex.com/search/",
        "params": lambda query, num: {"text": f"{query} mime:pdf", "numdoc": num}
    }
}

# --- PDF URL Doğrulayıcı ve Önizleyici ---
class PDFValidator(QObject):
    """
    PDF URL'lerini doğrulayan ve önizleme metni çıkartan yardımcı sınıf
    """
    validation_result = Signal(bool, str, str)  # başarılı mı, url, mesaj veya önizleme
    
    def __init__(self):
        super().__init__()
        
    def validate_and_preview(self, url):
        try:
            headers = self._get_random_headers()
            # HEAD isteğiyle dosya tipini kontrol et (ancak bazı sunucular HEAD'i desteklemez)
            try:
                head_response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
                content_type = head_response.headers.get('Content-Type', '').lower()
                
                if 'application/pdf' in content_type:
                    # Content-Type doğru, şimdi önizleme için PDF'ten metin çıkarmayı dene
                    if PDF_PREVIEW_AVAILABLE:
                        preview_text = self._get_pdf_preview(url, headers)
                        self.validation_result.emit(True, url, preview_text)
                    else:
                        self.validation_result.emit(True, url, "PDF Önizleme kullanılamıyor (pdfminer.six kurulu değil)")
                    return
            except requests.exceptions.RequestException:
                # HEAD isteği başarısız oldu, GET ile deneyelim
                pass
                
            # GET ile PDF içeriğini kontrol et (ilk birkaç byte)
            response = requests.get(url, headers=headers, timeout=10, stream=True)
            content_sample = next(response.iter_content(chunk_size=1024))
            response.close()
            
            # PDF sihirli numarası ile kontrol
            if content_sample.startswith(b'%PDF-'):
                if PDF_PREVIEW_AVAILABLE:
                    preview_text = self._get_pdf_preview(url, headers)
                    self.validation_result.emit(True, url, preview_text)
                else:
                    self.validation_result.emit(True, url, "PDF doğrulandı, önizleme kullanılamıyor")
            else:
                self.validation_result.emit(False, url, "Geçersiz PDF. İçerik PDF formatında değil.")
                
        except Exception as e:
            self.validation_result.emit(False, url, f"Doğrulama hatası: {str(e)}")
    
    def _get_pdf_preview(self, url, headers):
        try:
            response = requests.get(url, headers=headers, timeout=20, stream=True)
            pdf_bytes = io.BytesIO()
            
            # PDF'in ilk 100KB'ını indir (tam dosyayı indirmek yerine)
            MAX_PREVIEW_SIZE = 100 * 1024  # 100KB
            bytes_read = 0
            
            for chunk in response.iter_content(chunk_size=8192):
                pdf_bytes.write(chunk)
                bytes_read += len(chunk)
                if bytes_read >= MAX_PREVIEW_SIZE:
                    break
            
            pdf_bytes.seek(0)
            
            # PDF'ten metin çıkar
            preview_text = extract_text(pdf_bytes, page_numbers=[0])  # Sadece ilk sayfadan
            
            # Metni temizle ve kısalt
            preview_text = ' '.join(preview_text.split())
            if len(preview_text) > 500:
                preview_text = preview_text[:500] + "..."
                
            return preview_text if preview_text.strip() else "PDF'te çıkarılabilir metin bulunamadı."
                
        except Exception as e:
            return f"Önizleme alınamadı: {str(e)}"
    
    def _get_random_headers(self):
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        }

# --- Arama İş Parçacığı için Worker ---
class SearchWorker(QObject):
    """
    Çeşitli arama motorlarında PDF aramasını ayrı bir iş parçacığında yürüten worker sınıfı.
    """
    results_ready = Signal(list)  # Sonuçlar: [(başlık, url, açıklama), ...]
    progress_update = Signal(str, int)  # Durum mesajı, ilerleme yüzdesi
    error = Signal(str)           # Hata mesajı veya durum bilgisi
    finished = Signal()           # İş parçacığının bittiğini bildirir

    def __init__(self, query, engine="Google", num_results=20, verify_urls=True, max_depth=1):
        super().__init__()
        self.query = query
        self.engine = engine
        self.num_results = num_results
        self.verify_urls = verify_urls
        self.max_depth = max_depth
        self._is_running = True
        self.session = requests.Session()
        # Proxy kullanım desteği (ileride eklenebilir)
        # self.session.proxies = {"http": "http://proxy.example.com:8080", "https": "https://proxy.example.com:8080"}

    def run(self):
        """Arama işlemini gerçekleştirir."""
        if not self._is_running:
            self.finished.emit()
            return

        try:
            self.progress_update.emit(f"{self.engine} arama motoru kullanılarak PDF'ler aranıyor...", 10)
            
            if self.engine in SEARCH_ENGINES:
                engine_config = SEARCH_ENGINES[self.engine]
                initial_results = self._search_with_engine(
                    engine_config["base_url"],
                    engine_config["params"](self.query, self.num_results)
                )
            else:
                # Varsayılan olarak Google'da ara
                engine_config = SEARCH_ENGINES["Google"]
                initial_results = self._search_with_engine(
                    engine_config["base_url"],
                    engine_config["params"](self.query, self.num_results)
                )
            
            if not self._is_running:
                self.finished.emit()
                return

            # PDF URL'lerini doğrula ve detaylandır
            if self.verify_urls and initial_results:
                self.progress_update.emit("PDF URL'leri doğrulanıyor ve ek bilgiler toplanıyor...", 50)
                verified_results = self._verify_pdf_urls(initial_results)
                
                if not self._is_running:
                    self.finished.emit()
                    return
                    
                if verified_results:
                    self.results_ready.emit(verified_results)
                else:
                    self.error.emit("Doğrulanmış PDF bulunamadı. Lütfen farklı anahtar kelimelerle tekrar deneyin.")
            else:
                if initial_results:
                    self.results_ready.emit(initial_results)
                else:
                    self.error.emit("PDF bulunamadı. Lütfen farklı anahtar kelimelerle tekrar deneyin veya başka bir arama motoru seçin.")
                
        except requests.exceptions.Timeout:
            if self._is_running:
                self.error.emit("Arama zaman aşımına uğradı. İnternet bağlantınızı kontrol edin.")
        except requests.exceptions.RequestException as e:
            if self._is_running:
                self.error.emit(f"Ağ hatası: {e}")
        except Exception as e:
            if self._is_running:
                self.error.emit(f"Arama sırasında beklenmedik bir hata oluştu: {str(e)}")
        finally:
            if self._is_running:
                self.finished.emit()

    def _search_with_engine(self, base_url, params):
        """Belirtilen arama motoruyla arama yapar ve PDF sonuçlarını döndürür."""
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        try:
            # Arama motoruna istek gönder
            response = self.session.get(
                base_url, 
                params=params, 
                headers=headers, 
                timeout=20
            )
            response.raise_for_status()
            
            # HTML'i ayrıştır
            soup = BeautifulSoup(response.text, 'lxml')  # lxml daha hızlı
            
            results = []
            processed_urls = set()
            
            # Arama motoruna göre seçicileri ayarla
            if self.engine == "Google":
                results = self._parse_google_results(soup, processed_urls)
            elif self.engine == "Bing":
                results = self._parse_bing_results(soup, processed_urls)
            elif self.engine == "DuckDuckGo":
                results = self._parse_duckduckgo_results(soup, processed_urls)
            elif self.engine == "Yandex":
                results = self._parse_yandex_results(soup, processed_urls)
            else:
                # Varsayılan olarak Google parser'ı kullan
                results = self._parse_google_results(soup, processed_urls)
                
            # Yeterli sonuç bulunamadıysa ve max_depth > 1 ise, daha fazla derinlemesine ara
            if len(results) < self.num_results and self.max_depth > 1:
                self.progress_update.emit("Daha fazla PDF sonucu aranıyor...", 30)
                
                # Sayfadaki diğer bağlantıları tara (örn. akademik siteler, repositories vb.)
                depth_results = self._search_deeper(soup, processed_urls)
                results.extend(depth_results)
                
            return results[:min(len(results), self.num_results)]
            
        except Exception as e:
            self.error.emit(f"Arama motoru sorgulanırken hata: {str(e)}")
            return []

    def _parse_google_results(self, soup, processed_urls):
        """Google arama sonuçlarından PDF URL'lerini ayrıştırır."""
        results = []
        
        # Google'ın tipik sonuç kapsayıcıları değişebilir, birkaç olası varyasyonu dene
        possible_containers = [
            soup.select('div.g'), 
            soup.select('div.MjjYud'),
            soup.select('div.Gx5Zad'),
            soup.select('div.tF2Cxc'),
            soup.select('div[data-hveid]'),  # Genel bir seçici
            soup.select('a[href*=".pdf"]')   # Doğrudan PDF bağlantıları
        ]
        
        # Boş olmayan ilk kapsayıcıyı seç
        containers = next((c for c in possible_containers if c), [])
        
        if not containers:
            # Hiçbir kapsayıcı bulunamadıysa, HTML içindeki tüm bağlantıları kontrol et
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                if not self._is_running:
                    break
                    
                href = link.get('href', '')
                if self._is_pdf_url(href):
                    actual_url = self._extract_actual_url_from_google(href)
                    if actual_url and actual_url not in processed_urls:
                        title = self._extract_title_from_link(link) or "Başlıksız PDF"
                        description = self._extract_description_near_link(link) or "Açıklama yok"
                        results.append((title, actual_url, description))
                        processed_urls.add(actual_url)
        
        # Normal sonuç kapsayıcılarını işle
        for container in containers:
            if not self._is_running:
                break
                
            # Kapsayıcı bir div ise bağlantıları ara
            if container.name == 'div':
                links = container.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if self._is_pdf_url(href):
                        actual_url = self._extract_actual_url_from_google(href)
                        if actual_url and actual_url not in processed_urls:
                            title = self._extract_title_from_container(container) or "Başlıksız PDF"
                            description = self._extract_description_from_container(container) or "Açıklama yok"
                            results.append((title, actual_url, description))
                            processed_urls.add(actual_url)
            
            # Kapsayıcı doğrudan bir bağlantı ise
            elif container.name == 'a':
                href = container.get('href', '')
                if self._is_pdf_url(href):
                    actual_url = self._extract_actual_url_from_google(href)
                    if actual_url and actual_url not in processed_urls:
                        title = self._extract_title_from_link(container) or "Başlıksız PDF"
                        description = self._extract_description_near_link(container) or "Açıklama yok"
                        results.append((title, actual_url, description))
                        processed_urls.add(actual_url)
        
        return results

    def _parse_bing_results(self, soup, processed_urls):
        """Bing arama sonuçlarından PDF URL'lerini ayrıştırır."""
        results = []
        
        # Bing'in yaygın sonuç kapsayıcıları
        containers = soup.select('li.b_algo') or soup.select('div.b_title') or soup.select('.b_algo')
        
        for container in containers:
            if not self._is_running:
                break
                
            links = container.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if self._is_pdf_url(href) and href not in processed_urls:
                    title = self._extract_title_from_link(link) or "Başlıksız PDF"
                    # Bing genellikle bir açıklama paragrafı içerir
                    description = container.select_one('.b_caption p') 
                    description = description.get_text(strip=True) if description else "Açıklama yok"
                    
                    results.append((title, href, description))
                    processed_urls.add(href)
        
        # Hiç sonuç bulunamadıysa, sayfa üzerindeki tüm PDF bağlantılarını ara
        if not results:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                if not self._is_running:
                    break
                    
                href = link.get('href', '')
                if self._is_pdf_url(href) and href not in processed_urls:
                    title = self._extract_title_from_link(link) or "Başlıksız PDF"
                    description = "Açıklama yok"
                    results.append((title, href, description))
                    processed_urls.add(href)
        
        return results

    def _parse_duckduckgo_results(self, soup, processed_urls):
        """DuckDuckGo arama sonuçlarından PDF URL'lerini ayrıştırır."""
        results = []
        
        # DuckDuckGo'nun HTML yapısı
        containers = soup.select('.result') or soup.select('.links_main') or soup.select('.result__body')
        
        for container in containers:
            if not self._is_running:
                break
                
            links = container.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                
                # DDG genellikle yönlendirme URL'leri kullanır
                if '/l/?kh=' in href or '/l/?uddg=' in href:
                    # URL'yi çözümle
                    parsed_url = parse_qs(urlparse(href).query)
                    actual_url = parsed_url.get('uddg', [None])[0] or parsed_url.get('kh', [None])[0]
                    
                    if actual_url and self._is_pdf_url(actual_url) and actual_url not in processed_urls:
                        title = self._extract_title_from_link(link) or "Başlıksız PDF"
                        # DDG genellikle snippet/özet içerir
                        description_elem = container.select_one('.result__snippet')
                        description = description_elem.get_text(strip=True) if description_elem else "Açıklama yok"
                        
                        results.append((title, actual_url, description))
                        processed_urls.add(actual_url)
                
                # Doğrudan PDF bağlantıları
                elif self._is_pdf_url(href) and href not in processed_urls:
                    title = self._extract_title_from_link(link) or "Başlıksız PDF"
                    description = "Açıklama yok"
                    results.append((title, href, description))
                    processed_urls.add(href)
        
        # Hiç sonuç bulunamadıysa, sayfa üzerindeki tüm PDF bağlantılarını ara
        if not results:
            all_links = soup.find_all('a', href=True) 
            for link in all_links:
                if not self._is_running:
                    break
                    
                href = link.get('href', '')
                if '/l/?kh=' in href or '/l/?uddg=' in href:
                    parsed_url = parse_qs(urlparse(href).query)
                    actual_url = parsed_url.get('uddg', [None])[0] or parsed_url.get('kh', [None])[0]
                    
                    if actual_url and self._is_pdf_url(actual_url) and actual_url not in processed_urls:
                        title = self._extract_title_from_link(link) or "Başlıksız PDF"
                        results.append((title, actual_url, "Açıklama yok"))
                        processed_urls.add(actual_url)
                elif self._is_pdf_url(href) and href not in processed_urls:
                    title = self._extract_title_from_link(link) or "Başlıksız PDF"
                    results.append((title, href, "Açıklama yok"))
                    processed_urls.add(href)
        
        return results

    def _parse_yandex_results(self, soup, processed_urls):
        """Yandex arama sonuçlarından PDF URL'lerini ayrıştırır."""
        results = []
        
        # Yandex'in yaygın sonuç kapsayıcıları
        containers = soup.select('.serp-item') or soup.select('.organic') or soup.select('.search-result')
        
        for container in containers:
            if not self._is_running:
                break
                
            links = container.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                
                # Yandex genellikle yönlendirme URL'leri kullanır
                if '/r.xml?' in href:
                    # URL'yi çözümle
                    parsed_url = parse_qs(urlparse(href).query)
                    actual_url = parsed_url.get('u', [None])[0]
                    
                    if actual_url and self._is_pdf_url(actual_url) and actual_url not in processed_urls:
                        title = self._extract_title_from_link(link) or "Başlıksız PDF"
                        # Yandex genellikle snippet/özet içerir
                        description_elem = container.select_one('.organic__snippet')
                        description = description_elem.get_text(strip=True) if description_elem else "Açıklama yok"
                        
                        results.append((title, actual_url, description))
                        processed_urls.add(actual_url)
                
                # Doğrudan PDF bağlantıları
                elif self._is_pdf_url(href) and href not in processed_urls:
                    title = self._extract_title_from_link(link) or "Başlıksız PDF"
                    description = "Açıklama yok"
                    results.append((title, href, description))
                    processed_urls.add(href)
        
        # Hiç sonuç bulunamadıysa, sayfa üzerindeki tüm PDF bağlantılarını ara
        if not results:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                if not self._is_running:
                    break
                    
                href = link.get('href', '')
                if '/r.xml?' in href:
                    parsed_url = parse_qs(urlparse(href).query)
                    actual_url = parsed_url.get('u', [None])[0]
                    
                    if actual_url and self._is_pdf_url(actual_url) and actual_url not in processed_urls:
                        title = self._extract_title_from_link(link) or "Başlıksız PDF"
                        results.append((title, actual_url, "Açıklama yok"))
                        processed_urls.add(actual_url)
                elif self._is_pdf_url(href) and href not in processed_urls:
                    title = self._extract_title_from_link(link) or "Başlıksız PDF"
                    results.append((title, href, "Açıklama yok"))
                    processed_urls.add(href)
        
        return results

    def _search_deeper(self, soup, processed_urls):
        """Sayfadaki diğer potansiyel PDF kaynağı olabilecek linkleri tarar."""
        additional_results = []
        
        # Bir depo veya akademik site olabilecek bağlantıları topla
        potential_sites = set()
        domain_blacklist = {'google.com', 'bing.com', 'duckduckgo.com', 'yandex.com'}
        
        # Tüm bağlantıları kontrol et
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            if not self._is_running or len(potential_sites) >= 5:  # En fazla 5 siteyi daha derin ara
                break
                
            href = link.get('href', '')
            
            # URL'nin domain'ini al
            try:
                parsed = urlparse(href)
                if not parsed.netloc:  # Göreceli URL ise, tam URL oluştur
                    continue
                
                domain = parsed.netloc
                if domain in domain_blacklist or not domain:
                    continue
                    
                # Akademik veya depo olabilecek sitelere öncelik ver
                priority_keywords = [
                    'academia', 'researchgate', 'sci-hub', 'repository', 'arxiv', 
                    'library', 'kutuphane', 'edu', '.ac.', '.gov', 'research', 
                    'journal', 'conference', 'dergi', 'makale', 'tez'
                ]
                
                # Eğer domain öncelikli anahtar kelimelerden birini içeriyorsa veya şansa bağlı olarak ekle
                if any(keyword in domain.lower() for keyword in priority_keywords) or random.random() < 0.2:
                    potential_sites.add(href)
            except:
                continue
        
        # Seçilen siteleri ara
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_url = {
                executor.submit(self._extract_pdfs_from_site, site): site 
                for site in potential_sites
            }
            
            for future in as_completed(future_to_url):
                if not self._is_running:
                    break
                    
                site = future_to_url[future]
                try:
                    site_results = future.result()
                    for result in site_results:
                        if result[1] not in processed_urls:
                            additional_results.append(result)
                            processed_urls.add(result[1])
                except Exception as e:
                    self.progress_update.emit(f"Ek site taranırken hata: {str(e)}", 40)
        
        return additional_results[:10]  # En fazla 10 ek sonuç döndür

    def _extract_pdfs_from_site(self, url):
        """Bir site içindeki PDF bağlantılarını tarar ve bulduklarını döndürür."""
        results = []
        try:
            # Siteye istek gönder
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return results
                
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Sayfadaki tüm bağlantıları kontrol et
            links = soup.find_all('a', href=True)
            for link in links:
                if not self._is_running or len(results) >= 10:  # En fazla 10 PDF al
                    break
                    
                href = link.get('href', '')
                
                # Göreceli URL'leri mutlak URL'lere dönüştür
                full_url = urljoin(url, href)
                
                if self._is_pdf_url(full_url):
                    title = self._extract_title_from_link(link)
                    if not title:
                        # Dosya adını URL'den çıkarmayı dene
                        parsed = urlparse(full_url)
                        file_name = os.path.basename(unquote(parsed.path))
                        title = file_name if file_name else "Başlıksız PDF"
                    
                    results.append((title, full_url, "Site taramasından bulundu"))
            
            return results
                
        except Exception:
            return results
        