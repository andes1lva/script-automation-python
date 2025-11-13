@echo off
cd /d "%~dp0"
python -m pip install --quiet pandas openpyxl selenium webdriver-manager --upgrade >nul
python scraper.py > log_scraper.txt 2>&1
python organizador.py > log_excel.txt 2>&1
start "" "dados_organizados\produtos_organizados.xlsx"
exit