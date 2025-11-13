import json
import os
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse

# CONFIGURAÇÃO DO NAVEGADOR
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def safe_get(element, attr=None):
    try:
        return element.get_attribute(attr) if attr else element.text.strip()
    except:
        return "N/A"

def coletar_produtos_generic(url):
    driver.get(url)
    time.sleep(5)
    produtos = []
    # Seletores genéricos para produtos em e-commerce
    seletores = [
        "div.product-item, li.product, article.product, div.item, .product-card, .product-item, .grid-item",
        ".product-grid, .item-list, .product-list, .search-result, .ui-search-result",
        "div[data-testid='product']", ".product", "[data-product-id]"
    ]
    for sel in seletores:
        items = driver.find_elements(By.CSS_SELECTOR, sel)
        if items:
            for item in items[:50]:  # Limita a 50 produtos por página
                try:
                    # Nome
                    nome = safe_get(item.find_element(By.CSS_SELECTOR, "h2, h3, .title, .name, .product-title, .product-name"))
                    # Preço
                    preco = safe_get(item.find_element(By.CSS_SELECTOR, ".price, .preco, .amount, .product-price, span.andes-money-amount__fraction, .a-price-whole"))
                    # Link
                    link = safe_get(item.find_element(By.CSS_SELECTOR, "a"), "href")
                    if link and not link.startswith('http'):
                        link = urlparse(url).scheme + '://' + urlparse(url).netloc + link
                    # Imagem
                    imagem = safe_get(item.find_element(By.CSS_SELECTOR, "img"), "src")
                    # Tipo/Marca (extração simples do nome)
                    tipo = re.search(r'(ram|ssd|placa|monitor|notebook|mouse|teclado)', nome.lower())
                    marca = re.search(r'(crucial|kingston|samsung|lg|dell|hp|logitech|razer)', nome.lower())
                    produtos.append({
                        "nome": nome,
                        "preco": preco,
                        "url": link,
                        "imagem": imagem,
                        "site": urlparse(url).netloc,
                        "tipo": tipo.group(1).title() if tipo else "Outro",
                        "marca": marca.group(1).title() if marca else "N/A"
                    })
                except:
                    continue
            break  # Para o primeiro seletor que encontrar itens
    return produtos

# LEITURA DAS URLs
with open("urls.txt", "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

todos_produtos = []

for url in urls:
    print(f"Coletando de {url}")
    produtos = coletar_produtos_generic(url)
    todos_produtos.extend(produtos)
    print(f"{len(produtos)} produtos coletados de {urlparse(url).netloc}")

# SALVA EM JSON
os.makedirs("dados_brutos", exist_ok=True)
json_path = "dados_brutos/produtos_brutos.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(todos_produtos, f, ensure_ascii=False, indent=2)

driver.quit()
print(f"Total: {len(todos_produtos)} produtos coletados e salvos em {json_path}")