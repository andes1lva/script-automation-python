# organizador.py
import json, glob, os, pandas as pd

BRUTOS = "dados_brutos"
ORGANIZADOS = "dados_organizados"
os.makedirs(ORGANIZADOS, exist_ok=True)

def safe_get(d, key, default="N/A"):
    return d.get(key, default)

arquivos = sorted(glob.glob(f"{BRUTOS}/log_*.json"))
if not arquivos:
    print("[ERRO] Nenhum JSON encontrado!")
    exit()

dados = []
for arq in arquivos:
    try:
        with open(arq, 'r', encoding='utf-8') as f:
            d = json.load(f)
        linha = {
            'Tipo do Produto': safe_get(d, 'tipo_produto'),
            'Nome do Produto': safe_get(d, 'nome_produto'),
            'Preço': safe_get(d, 'preco'),
            'Vendas Semanal': safe_get(d, 'vendas_semanal'),
            'Vendas Mensal': safe_get(d, 'vendas_mensal'),
            'Vendas Anual': safe_get(d, 'vendas_anual'),
            'Fabricante': safe_get(d, 'fabricante'),
            'Modelo': safe_get(d, 'modelo'),
            'Marca': safe_get(d, 'marca'),
            'Link Direto': safe_get(d, 'link_direto'),
            'Imagem Principal': safe_get(d, 'imagens', [])[:1] or "N/A",
            'Meta Descrição': safe_get(d, 'meta_descricao')
        }
        dados.append(linha)
    except Exception as e:
        print(f"[ERRO AO LER] {arq} → {e}")

df = pd.DataFrame(dados).fillna('N/A')
excel_path = f"{ORGANIZADOS}/produtos_organizados.xlsx"

with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name='Produtos')
    ws = writer.sheets['Produtos']
    for col in ws.columns:
        max_l = max(len(str(cell.value)) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_l + 2, 50)

print(f"[OK] Excel gerado: {excel_path} ({len(df)} produtos)")