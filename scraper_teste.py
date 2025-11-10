import csv
import json
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import nltk
from nltk.tokenize import sent_tokenize

# Baixe NLTK data (uma vez)
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt')
    nltk.download('punkt_tab')

def setup_driver(headless=True):
    """
    Configura o driver Selenium com opcoes anti-deteccao.
    """
    options = Options()
    if headless:
        options.add_argument('--headless')  # Sem janela visivel
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def coletar_tudo_selenium(url, delay=3, max_rolagens=5):
    """
    Coleta TODAS as informacoes visiveis de uma pagina usando Selenium.
    Simula mouse e rolagem para carregar conteudo dinamico.
    Retorna dict com log completo; salva em CSV e screenshot.
    
    Parametros:
    - url: Qualquer URL para scrapear.
    - delay: Segundos de espera inicial.
    - max_rolagens: Quantas vezes rolar a pagina.
    """
    time.sleep(delay)
    driver = setup_driver(headless=True)  # Mude para False para ver o navegador
    wait = WebDriverWait(driver, 10)
    
    try:
        # Navega e espera carregar
        driver.get(url)
        time.sleep(2)
        
        # Simula movimentos de mouse (humaniza)
        actions = ActionChains(driver)
        actions.move_by_offset(100, 100).perform()  # Move mouse
        time.sleep(1)
        
        # Rola a pagina para carregar lazy content
        for i in range(max_rolagens):
            driver.execute_script(f"window.scrollTo(0, {i * 500});")
            time.sleep(1)
        driver.execute_script("window.scrollTo(0, 0);")  # Volta ao topo
        
        # Espera elementos principais
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Coleta dados basicos
        texto_completo = re.sub(r'\s+', ' ', driver.find_element(By.TAG_NAME, "body").text).strip()
        frases_tokenizadas = sent_tokenize(texto_completo, language='portuguese')[:20]  # Primeiras 20 frases (AI-like)
        
        # Coleta headings (H1 a H6)
        headings = {}
        for i in range(1, 7):
            elements = driver.find_elements(By.XPATH, f'//h{i}')
            headings[f'H{i}'] = [h.text.strip() for h in elements]
        
        # Coleta links
        links = []
        for a in driver.find_elements(By.TAG_NAME, "a"):
            if a.text.strip():
                links.append({
                    'texto': a.text.strip(),
                    'href': a.get_attribute('href')
                })
        
        # Coleta imagens
        imagens = []
        for img in driver.find_elements(By.TAG_NAME, "img"):
            src = img.get_attribute('src') or img.get_attribute('data-src')
            if src:
                imagens.append({
                    'alt': img.get_attribute('alt') or '',
                    'src': src
                })
        
        # Coleta botoes
        botoes = []
        for btn in driver.find_elements(By.TAG_NAME, "button"):
            botoes.append({
                'texto': btn.text.strip(),
                'tipo': btn.get_attribute('type') or ''
            })
        
        # Coleta inputs
        inputs_list = []
        for inp in driver.find_elements(By.TAG_NAME, "input"):
            inputs_list.append({
                'tipo': inp.get_attribute('type') or '',
                'valor': inp.get_attribute('value') or '',
                'placeholder': inp.get_attribute('placeholder') or ''
            })
        
        # Coleta tabelas
        tabelas = []
        for table in driver.find_elements(By.TAG_NAME, "table"):
            try:
                rows = []
                for row in table.find_elements(By.TAG_NAME, "tr"):
                    cols = [col.text.strip() for col in row.find_elements(By.TAG_NAME, "td")]
                    if cols:
                        rows.append(cols)
                if rows:
                    tabelas.append({
                        'cabecalho': rows[0] if rows else [],
                        'linhas': rows[1:]
                    })
            except Exception:
                pass
        
        # Coleta console logs
        console_logs = driver.get_log('browser')
        
        # Monta dict final
        dados = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'titulo_pagina': driver.title,
            'meta_descricao': '',
            'texto_completo': texto_completo,
            'frases_tokenizadas': frases_tokenizadas,
            'headings': headings,
            'links': links,
            'imagens': imagens,
            'botoes': botoes,
            'inputs': inputs_list,
            'tabelas': tabelas,
            'console_logs': console_logs
        }
        
        # Tenta pegar meta descricao
        try:
            meta_desc = driver.find_element(By.XPATH, "//meta[@name='description']").get_attribute('content')
            dados['meta_descricao'] = meta_desc
        except NoSuchElementException:
            dados['meta_descricao'] = "Nao encontrado"
        
        # Screenshot como log visual
        screenshot_nome = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        driver.save_screenshot(screenshot_nome)
        dados['screenshot'] = screenshot_nome
        
        # Placeholder para AI resumida (ex: integre com API)
        # dados['resumo_ai'] = chamar_llm_api(dados['texto_completo'])  # Implemente se quiser
        
        print(f"Coletado de {url}: {len(links)} links, {len(imagens)} imagens, {len(texto_completo)} chars de texto.")
        
        # Salva em CSV (achata tudo em linhas: Tipo | Conteudo | Detalhes)
        with open('log_completo.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(['URL', 'Timestamp', 'Tipo_Dado', 'Conteudo', 'Detalhes_JSON'])
            
            # Linha para dados simples
            for tipo, conteudo in [
                ('titulo', dados['titulo_pagina']),
                ('meta_desc', dados['meta_descricao'][:100])  # Limita tamanho
            ]:
                writer.writerow([url, dados['timestamp'], tipo, conteudo, ''])
            
            # Para listas (limita a 10 para nao explodir o CSV)
            for item in dados['links'][:10]:
                writer.writerow([url, dados['timestamp'], 'link', item['texto'], json.dumps(item['href'])])
            for item in dados['imagens'][:10]:
                writer.writerow([url, dados['timestamp'], 'imagem', item['alt'], json.dumps(item['src'])])
            for item in dados['botoes'][:10]:
                writer.writerow([url, dados['timestamp'], 'botao', item['texto'], json.dumps(item['tipo'])])
            for item in dados['inputs'][:10]:
                writer.writerow([url, dados['timestamp'], 'input', item['placeholder'], json.dumps({'tipo': item['tipo'], 'valor': item['valor']})])
            for tabela in dados['tabelas']:
                writer.writerow([url, dados['timestamp'], 'tabela', 'Tabela encontrada', json.dumps(tabela)])
        
        # Salva JSON bruto
        json_nome = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_nome, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        return dados
    
    except TimeoutException:
        print("Timeout: Pagina demorou a carregar.")
        return None
    except Exception as e:
        print(f"Erro: {e}")
        return None
    finally:
        driver.quit()

# Exemplo de uso
if __name__ == "__main__":
    # Insira sua URL aqui (generico!)
    url_exemplo = "https://www.mercadolivre.com.br/memoria-ram-para-notebook-16gb-ddr5-4800mhz-cl40-sodimm-crucial-ct16g48c40s5-preto/p/MLB21754935"
    dados = coletar_tudo_selenium(url_exemplo)
    
    # Para multiplas URLs
    # urls = [url1, url2]
    # for u in urls:
    #     coletar_tudo_selenium(u, delay=5)
    #     time.sleep(10)  # Pausa maior entre paginas