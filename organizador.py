import pandas as pd
import json
import os
import re

# CARREGA DADOS
json_path = "dados_brutos/produtos_brutos.json"
if not os.path.exists(json_path):
    print("Nenhum arquivo JSON encontrado! Rode o scraper primeiro.")
    exit()

with open(json_path, "r", encoding="utf-8") as f:
    dados = json.load(f)

# CRIA DATAFRAME
df = pd.DataFrame(dados)

# LIMPEZA
df["preco"] = df["preco"].str.replace(r"[^\d,]", "", regex=True).str.replace(",", ".").str.strip()
df["preco"] = pd.to_numeric(df["preco"], errors='coerce').fillna("N/A")

# ORDENA POR PREÇO
df = df.sort_values(by="preco")

# SALVA EXCEL
os.makedirs("dados_organizados", exist_ok=True)
output_path = "dados_organizados/produtos_organizados.xlsx"
df.to_excel(output_path, index=False, sheet_name="Produtos")

print(f"Excel gerado com {len(df)} produtos em {output_path}")
print("Colunas: Nome, Preço, URL, Imagem, Site, Tipo, Marca")