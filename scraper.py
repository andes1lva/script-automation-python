# scraper.py
import json, time, re, os, random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

BRUTOS = "dados_brutos"
os.makedirs(BRUTOS, exist_ok=True)

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def extrair_preco(driver):
    seletores = [
        "span.andes-money-amount__fraction", ".price-tag-fraction", ".andes-money-amount__fraction",
        ".price", ".product-price", ".price-final", "[data-price]", ".valor", ".preco"
    ]
    for sel in seletores:
        try:
            el = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
            preco = el.text.strip()
            if re.search(r'\d+', preco): return f"R$ {preco}"
        except: continue
    return "Não encontrado"

def extrair_vendas(driver):
    try:
        texto = driver.find_element(By.TAG_NAME, "body").text
        match = re.search(r'(\d+[\d\.]*)[\s\+]*vendas?', texto, re.I)
        if match:
            total = int(re.sub(r'\D', '', match.group(1)))
            return {'total': total, 'semanal': round(total/52, 1), 'mensal': round(total/12, 1), 'anual': total}
    except: pass
    return {'total': 0, 'semanal': 0, 'mensal': 0, 'anual': 0}

def extrair_marca_modelo(texto, url):
    texto_lower = texto.lower()
    marcas = ['crucial','kingston','corsair','samsung','seagate','wd','intel','amd','nvidia']
    marca = next((m.title() for m in marcas if m in texto_lower), "N/A")
    modelo = re.search(r'/([a-z0-9]{4,})', url) or re.search(r'model[oô][:\s]+([a-z0-9]+)', texto_lower)
    return marca, (modelo.group(1).upper() if modelo else "N/A")

def detectar_tipo(texto):
    t = texto.lower()
    if any(k in t for k in ['ram','ddr','mhz']): return "Memória RAM"
    if any(k in t for k in ['ssd','nvme','tb','gb']): return "SSD"
    if 'placa' in t: return "Placa de Vídeo"
    return "Outro"

def coletar(url):
    driver = setup_driver()
    try:
        print(f"[COLETANDO] {url}")
        driver.get(url); time.sleep(random.uniform(4, 7))
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Rolagem
        for i in range(3): driver.execute_script(f"window.scrollTo(0, {i*1000});"); time.sleep(1)

        texto = re.sub(r'\s+', ' ', driver.find_element(By.TAG_NAME, "body").text).strip()
        preco = extrair_preco(driver)
        vendas = extrair_vendas(driver)
        marca, modelo = extrair_marca_modelo(texto, url)
        tipo = detectar_tipo(texto)

        # Dados básicos
        titulo = driver.title
        meta = "N/A"
        try:
            meta_el = driver.find_element(By.XPATH, "//meta[@name='description']")
            meta = meta_el.get_attribute('content')[:200]
        except: pass

        # Imagens
        imagens = [img.get_attribute('src') for img in driver.find_elements(By.TAG_NAME, "img") if img.get_attribute('src') and 'http' in img.get_attribute('src')][:2]

        dados = {
            'url': url,
            'nome_produto': titulo,
            'preco': preco,
            'tipo_produto': tipo,
            'vendas_semanal': vendas['semanal'],
            'vendas_mensal': vendas['mensal'],
            'vendas_anual': vendas['anual'],
            'fabricante': marca,
            'modelo': modelo,
            'marca': marca,
            'link_direto': url,
            'imagens': imagens,
            'meta_descricao': meta,
            'texto_completo': texto
        }

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_path = f"{BRUTOS}/log_{ts}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

        print(f"[OK] {os.path.basename(json_path)} | Preço: {preco} | Tipo: {tipo}")
        return dados
    except Exception as e:
        print(f"[ERRO] {url} → {e}")
        return None
    finally:
        driver.quit()

if __name__ == "__main__":
    urls_file = "urls.txt"
    if not os.path.exists(urls_file):
        print(f"[ERRO] {urls_file} não encontrado! Use adicionar_urls.html")
        exit()
    with open(urls_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip().startswith('http')]
    if not urls: print("[ERRO] URLs vazias!"); exit()
    print(f"[INFO] {len(urls)} URLs\n")
    for url in urls:
        coletar(url); time.sleep(random.uniform(3, 5))
    print("\n[CONCLUÍDO]")