import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

# Configurações
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PRECO_ALVO = 700.0  # Mude para o preço que você considera promoção (ex: 650, 680, etc.)

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def limpar_preco(texto):
    if not texto:
        return None
    # Remove R$, pontos de milhar e troca vírgula por ponto
    texto = re.sub(r"[^\d,]", "", texto)
    texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except:
        return None

def buscar_magazine_luiza():
    resultados = []
    urls = [
        "https://www.magazineluiza.com.br/busca/climatizador+clin+60+pro/",
        "https://www.magazineluiza.com.br/busca/climatizador+ventisol+clin+60+pro/"
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=20)
            soup = BeautifulSoup(r.text, "lxml")

            # Seletores comuns do Magalu (podem mudar — ajuste se necessário)
            produtos = soup.select("[data-testid='product-card']") or soup.select(".product")
            for p in produtos[:8]:  # pega os 8 primeiros
                titulo = p.select_one("h2, h3, [data-testid='product-title']")
                preco = p.select_one("[data-testid='price-value'], .price-template__text, .price")
                link = p.select_one("a")

                if titulo and preco:
                    nome = titulo.get_text(strip=True)
                    valor = limpar_preco(preco.get_text())
                    href = link["href"] if link and link.get("href") else url
                    if not href.startswith("http"):
                        href = "https://www.magazineluiza.com.br" + href

                    if valor and "clin" in nome.lower() and "60" in nome.lower():
                        resultados.append({
                            "loja": "Magazine Luiza",
                            "nome": nome[:80],
                            "preco": valor,
                            "link": href
                        })
        except Exception as e:
            print(f"Erro Magalu: {e}")
    return resultados

def buscar_mercadolivre():
    resultados = []
    url = "https://lista.mercadolivre.com.br/climatizador-clin-60-pro"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, "lxml")
        itens = soup.select(".ui-search-layout__item") or soup.select(".ui-search-result")
        for item in itens[:8]:
            titulo = item.select_one("h2, .ui-search-item__title")
            preco = item.select_one(".andes-money-amount__fraction, .price-tag-fraction")
            link = item.select_one("a")
            if titulo and preco:
                nome = titulo.get_text(strip=True)
                valor = limpar_preco(preco.get_text())
                href = link["href"] if link else url
                if valor and "clin" in nome.lower() and "60" in nome.lower():
                    resultados.append({
                        "loja": "Mercado Livre",
                        "nome": nome[:80],
                        "preco": valor,
                        "link": href
                    })
    except Exception as e:
        print(f"Erro Mercado Livre: {e}")
    return resultados

def main():
    print(f"Iniciando busca em {datetime.now()}")
    todos = buscar_magazine_luiza() + buscar_mercadolivre()

    # Remove duplicados aproximados e ordena por preço
    unicos = {}
    for r in todos:
        chave = f"{r['loja']}-{r['preco']}"
        if chave not in unicos or r["preco"] < unicos[chave]["preco"]:
            unicos[chave] = r

    ordenados = sorted(unicos.values(), key=lambda x: x["preco"])

    boas_ofertas = [o for o in ordenados if o["preco"] <= PRECO_ALVO]

    if boas_ofertas:
        mensagem = f"🔥 <b>Promoções Clin 60 Pro encontradas!</b>\n\n"
        for o in boas_ofertas[:5]:  # máximo 5
            mensagem += (
                f"🏪 <b>{o['loja']}</b>\n"
                f"📦 {o['nome']}\n"
                f"💰 <b>R$ {o['preco']:.2f}</b>\n"
                f"🔗 <a href='{o['link']}'>Ver oferta</a>\n\n"
            )
        mensagem += f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        enviar_telegram(mensagem)
        print("Mensagem enviada!")
    else:
        print("Nenhuma promoção abaixo do preço alvo encontrada.")
        # Opcional: descomente a linha abaixo se quiser receber status mesmo sem promoção
        # enviar_telegram(f"✅ Monitor rodou. Nenhum preço ≤ R$ {PRECO_ALVO:.0f} encontrado.")

if __name__ == "__main__":
    main()
