import requests
import re
import datetime
from bs4 import BeautifulSoup

# --- AYARLAR ---
OUTPUT_FILE = "Canli_Spor_Hepsi.m3u"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# --- 1. NETSPOR FONKSİYONU (Kanallar ve Günün Maçları) ---
def fetch_netspor():
    print("[*] Netspor taranıyor...")
    results = []
    source_url = "https://netspor-amp.xyz/"
    stream_base = "https://andro.6441255.xyz/checklist/"
    try:
        res = requests.get(source_url, headers=HEADERS, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # A) Kanallar (Sıralı: BeIN 1, 2, 3...)
        ch_sec = soup.find('div', id='kontrolPanelKanallar')
        if ch_sec:
            for div in ch_sec.find_all('div', class_='mac', option=True):
                sid = div.get('option')
                title = div.find('div', class_='match-takimlar').get_text(strip=True)
                results.append({"name": title, "url": f"{stream_base}{sid}.m3u8", "group": "CANLI TV KANALLARI", "ref": source_url, "logo": ""})
        
        # B) Maçlar (Günün Maçları)
        m_sec = soup.find('div', id='kontrolPanel')
        if m_sec:
            for div in m_sec.find_all('div', class_='mac', option=True):
                sid = div.get('option')
                teams = div.find('div', class_='match-takimlar').get_text(strip=True).replace("CANLI", "").strip()
                alt = div.find('div', class_='match-alt').get_text(" | ", strip=True) if div.find('div', class_='match-alt') else ""
                results.append({"name": f"{teams} ({alt})", "url": f"{stream_base}{sid}.m3u8", "group": "Günün Maçları", "ref": source_url, "logo": ""})
    except Exception as e:
        print(f"Netspor Hatası: {e}")
    return results

# --- 2. TRGOALS FONKSİYONU ---
def fetch_trgoals():
    print("[*] Trgoals taranıyor...")
    results = []
    domain = None
    for i in range(1485, 2150):
        test = f"https://trgoals{i}.xyz"
        try:
            if requests.head(test, timeout=1).status_code == 200:
                domain = test; break
        except: continue
    
    if domain:
        cids = [("yayin1","BEIN 1"), ("yayinb2","BEIN 2"), ("yayinb3","BEIN 3"), ("yayinb4","BEIN 4"), ("yayinb5","BEIN 5"), ("yayinss","S SPORT")]
        for cid, name in cids:
            try:
                r = requests.get(f"{domain}/channel.html?id={cid}", headers=HEADERS, timeout=5)
                m = re.search(r'const baseurl = "(.*?)"', r.text)
                if m:
                    results.append({"name": f"TRG - {name}", "url": f"{m.group(1)}{cid}.m3u8", "group": "TRGOALS TV", "ref": f"{domain}/", "logo": "https://i.ibb.co/gFyFDdDN/trgoals.jpg"})
            except: continue
    return results

# --- 3. SELÇUKSPOR / SPORCAFE FONKSİYONU ---
def fetch_selcuk_sporcafe():
    print("[*] Selçukspor / Sporcafe taranıyor...")
    results = []
    selcuk_channels = [
        {"id": "selcukbeinsports1", "name": "BeIN Sports 1", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/5rhmw31628798883.png"},
        {"id": "selcukbeinsports2", "name": "BeIN Sports 2", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/7uv6x71628799003.png"},
        {"id": "selcukssport", "name": "S Sport 1", "logo": "https://itv224226.tmp.tivibu.com.tr:6430/images/poster/20230302923239.png"}
    ]
    referer, html_content = None, None
    for i in range(6, 130):
        url = f"https://www.sporcafe{i}.xyz/"
        try:
            res = requests.get(url, headers=HEADERS, timeout=1)
            if "uxsyplayer" in res.text:
                referer, html_content = url, res.text; break
        except: continue
    
    if html_content and referer:
        m = re.search(r'https?://(main\.uxsyplayer[0-9a-zA-Z\-]+\.click)', html_content)
        if m:
            s_domain = f"https://{m.group(1)}"
            for ch in selcuk_channels:
                try:
                    r = requests.get(f"{s_domain}/index.php?id={ch['id']}", headers={**HEADERS, "Referer": referer}, timeout=5)
                    base_m = re.search(r'this\.adsBaseUrl\s*=\s*[\'"]([^\'"]+)', r.text)
                    if base_m:
                        results.append({"name": f"SL - {ch['name']}", "url": f"{base_m.group(1)}{ch['id']}/playlist.m3u8", "group": "SELÇUKSPOR HD", "ref": referer, "logo": ch['logo']})
                except: continue
    return results

# --- ANA ÇALIŞTIRICI ---
def main():
    all_streams = []
    
    # Tüm sitelerden verileri çek ve listeye ekle
    all_streams.extend(fetch_netspor())
    all_streams.extend(fetch_trgoals())
    all_streams.extend(fetch_selcuk_sporcafe())
    
    if not all_streams:
        print("[!] Hiçbir siteden veri çekilemedi.")
        return

    # Dosyayı Oluştur (UTF-8-SIG Türkçe karakterler için)
    content = "#EXTM3U\n"
    content += f"# Birlesik Spor Paketi - Guncelleme: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
    
    for s in all_streams:
        logo = f' tvg-logo="{s["logo"]}"' if s["logo"] else ""
        content += f'#EXTINF:-1 group-title="{s["group"]}"{logo},{s["name"]}\n'
        content += f'#EXTVLCOPT:http-referrer={s["ref"]}\n'
        content += f'{s["url"]}\n'

    with open(OUTPUT_FILE, "w", encoding="utf-8-sig") as f:
        f.write(content)
    print(f"\n[BASARILI] Toplam {len(all_streams)} kanal '{OUTPUT_FILE}' dosyasına kaydedildi.")

if __name__ == "__main__":
    main()
