import pandas as pd
import os
import time
import datetime
#######################################################################se
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
#######################################################################se
def salva_html(arquivo, dado):
    modo = "w" #escrita
    f = open(arquivo, modo, encoding="utf-8")
    f.write(dado)
    f.close()
    
def criar_driver():
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless")
    
    path = os.getcwd() 
    path_driver = rf'{path}\driver\chromedriver.exe'

    options.add_experimental_option("prefs", {
        "download.default_directory": path,
        "download.Prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    
    chrome_service = webdriver.chrome.service.Service(path_driver)
    driver = webdriver.Chrome(service=chrome_service, options=options)
    driver.set_page_load_timeout(600)
    driver.set_script_timeout(600)

    return driver

def encontrar_valores_casas_bahia(pagina):
    pagina = pagina.split('<div class="product-card__highlight-price" aria-hidden="true"')

    valores = []
    for x in pagina:
        if '>R$ ' in x:
            a = x.split('>R$ ')[1].split('<')[0]
            a = a.replace(',', '.')
            valores.append(a)
            
    df = pd.DataFrame({'valores': valores})
    df['valores'] = pd.to_numeric(df['valores'], errors='coerce')

    return df

def encontrar_valores_amazon(pagina):
    parte1 = '<span class="a-price" data-a-size="xl" data-a-color="base"><span class="a-offscreen">'
    pagina = pagina.split(parte1)
    valores = []
    for x in pagina:
        if 'R$' in x:
            x = x.replace("&nbsp;", " ")
            a = x.split('</span><span aria-hidden="true">')[0]
            a = a.replace('R$ ', '')
            a = a.replace(',', '.')
            valores.append(a)
            
    
    df = pd.DataFrame({'valores': valores})
    df['valores'] = pd.to_numeric(df['valores'], errors='coerce')

    return df
    

def encontrar_valores_mercado_livre(pagina):    
    pagina = pagina.split('andes-money-amount ui-search-price__part shops__price-part ui-search-price__part--medium andes-money-amount--cents-superscript')
    valores = []
    for x in pagina:
        if 'style="font-size:12px' in x:
            '''
            limpar a string e ficar somente com o valor
            '''
            a = x.split('class="andes-money-amount__currency-symbol" aria-hidden="true">')[1]
            a = a.split('</span></span><span class="ui-search-price__second-line__label shops__price-second-line__label">')[0]
            a = a.replace('</span><span class="andes-money-amount__fraction" aria-hidden="true">', ' ')
            a = a.replace('</span><span class="andes-visually-hidden" aria-hidden="true">,</span><span class="andes-money-amount__cents andes-money-amount__cents--superscript-24" style="font-size:12px;margin-top:4px" aria-hidden="true">', ',')
            a = a.replace('R$ ', '')
            a = a.replace(',', '.')
            
            #acumular valores
            valores.append(a)
    
    df = pd.DataFrame({'valores': valores})
    df['valores'] = pd.to_numeric(df['valores'], errors='coerce')
    return df

def consulta_mercado_livre(driver, produto):
    produto_corrigido = produto.replace(" ", "-")
    link = f'https://lista.mercadolivre.com.br/{produto_corrigido}'
    driver.get(link)
    pagina = driver.page_source
    salva_html(f"html/mercado_livre_{produto}.html", pagina)
    df = encontrar_valores_mercado_livre(pagina)
    df['item'] = produto
    df['loja'] = 'mercado livre'
    df['link'] = link
    return df

def consulta_amazon(driver, produto):
    produto_corrigido = produto.replace(" ", "+")
    link = f'https://www.amazon.com.br/s?k={produto_corrigido}'
    driver.get(link)
    pagina = driver.page_source
    salva_html(f"html/amazon_{produto}.html", pagina)
    df = encontrar_valores_amazon(pagina)
    df['item'] = produto
    df['loja'] = 'amazon'
    df['link'] = link
    return df

def consulta_casas_bahia(driver, produto):
    produto_corrigido = produto.replace(" ", "-")
    link = f'https://www.casasbahia.com.br/{produto_corrigido}/b'
    driver.get(link)
    pagina = driver.page_source
    salva_html(f"html/casas_bahia_{produto}.html", pagina)
    df = encontrar_valores_casas_bahia(pagina)
    df['item'] = produto
    df['loja'] = 'casas bahia'
    df['link'] = link
    return df  
    
def procurar_dados(produtos):
    driver = criar_driver()
    df = pd.DataFrame()
    for produto in produtos:
        data1 = consulta_mercado_livre(driver, produto)
        data2 = consulta_amazon(driver, produto)
        data3 = consulta_casas_bahia(driver, produto)
        df = pd.concat([df, data1, data2, data3], ignore_index=True, sort=False)
    
    driver.quit()
    df.to_excel('valores.xlsx')

def entender_dados():
    df = pd.read_excel('valores.xlsx')
    #df = df.groupby('item')['valores'].agg(['mean', 'min', 'max', 'median', 'std', 'var', 'sum', 'count']).reset_index()
    #df.columns = ['item', 'valor_medio', 'menor_valor', 'maior_valor', 'mediana', 'desvio_padrao', 'variancia', 'soma', 'contagem']
    
    df = df.groupby('item')['valores'].agg(['mean', 'min', 'max', 'median', 'std']).reset_index()
    df.columns = ['item', 'valor_medio', 'menor_valor', 'maior_valor', 'mediana', 'desvio_padrao']
    
    for coluna in df.columns:
        if coluna != "item":
            df[coluna] = df[coluna].round(2)

    df.to_excel('resumo.xlsx')



if __name__ == '__main__':
    produtos = ['Air Frier Mundial', 'Oculos de Sol']
    procurar_dados(produtos)
    entender_dados()
    
