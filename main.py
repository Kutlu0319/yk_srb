import requests
import re
import datetime
from bs4 import BeautifulSoup

# --- AYARLAR ---
OUTPUT_FILE = "Canli_Spor_Hepsi.m3u"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

def fetch_netspor():
    print("\n--- [SİTE 1: NETSPOR TARAMASI BAŞLADI] ---")
    channels_list, matches_list = [], []
    source_url = "https://netspor-amp.xyz/"
    stream_base = "https://andro.6441255.xyz/checklist/"
    
    try:
        res = requests.get(source_url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Kanalları Çek
        ch_container = soup.find('div', id='kontrolPanelKanallar')
        if ch_container:
            for div in ch_container.find_all('div', class_='mac', option=True):
                sid = div.get('option')
                title = div.find('div', class_='match-takimlar').get_text(strip=True)
                channels_list.append({"name": title, "url": f"{stream_base}{sid}.m3u8", "group": "CANLI TV KANALLARI", "ref": source_url, "logo": ""})
            print(f"[OK] Netspor: {len(channels_list)} kanal çekildi.")
        
        # Maçları Çek
        m_container = soup.find('div', id='kontrolPanel')
        if m_container:
            for div in m_container.find_all('div', class_='mac', option=True):
                sid = div.get('option')
                title = div.find('div', class_='match-takimlar').get_text(strip=True)
                matches_list.append({"name": title, "url": f"{stream_base}{sid}.m3u8", "group": "Günün Maçları", "ref": source_url, "logo": ""})
            print(f"[OK] Netspor: {len(matches_list)} maç çekildi.")
            
        return channels_list + list(reversed(matches_list)), "BAŞARILI"
    except Exception as e:
        return [], f"HATA: {str(e)}"

def fetch_trgoals():
    print("\n--- [SİTE 2: TRGOALS TARAMASI BAŞLADI] ---")
    results, domain = [], None
    try:
        for i in range(1485, 2150):
            test = f"https://trgoals{i}.xyz"
            try:
                if requests.head(test, timeout=1).status_code == 200:
                    domain = test; break
            except: continue
        
        if not domain: return [], "HATA: Aktif domain bulunamadı"
        
        cids = {"yayin1":"BEIN 1","yayinb2":"BEIN 2","yayinb3":"BEIN 3","yayinss":"S SPORT"}
        for cid, name in cids.items():
            r = requests.get(f"{domain}/channel.html?id={cid}", headers=HEADERS, timeout=5)
            m = re.search(r'const baseurl = "(.*?)"', r.text)
            if m:
                results.append({"name": f"TRG - {name}", "url": f"{m.group(1)}{cid}.m3u8", "group": "TRGOALS TV", "ref": f"{domain}/", "logo": "https://i.ibb.co/gFyFDdDN/trgoals.jpg"})
        
        print(f"[OK] Trgoals: {len(results)} kanal çekildi.")
        return results, "BAŞARILI"
    except Exception as e:
        return [], f"HATA: {str(e)}"

def fetch_selcuk_sporcafe():
    print("\n--- [SİTE 3: SELÇUKSPOR / SPORCAFE TARAMASI BAŞLADI] ---")
    results, referer, html_content = [], None, None
    try:
        for i in range(6, 130):
            url = f"https://www.sporcafe{i}.xyz/"
            try:
                res = requests.get(url, headers=HEADERS, timeout=1)
                if "uxsyplayer" in res.text:
                    referer, html_content = url, res.text; break
            except: continue
            
        if not html_content: return [], "HATA: Aktif site bulunamadı"
        
        m = re.search(r'https?://(main\.uxsyplayer[0-9a-zA-Z\-]+\.click)', html_content)
        if m:
            s_domain = f"https://{m.group(1)}"
            c_ids = [("selcukbeinsports1","BeIN 1"), ("selcukbeinsports2","BeIN 2"), ("selcukssport","S SPORT")]
            for cid, cname in c_ids:
                r = requests.get(f"{s_domain}/index.php?id={cid}", headers={**HEADERS, "Referer": referer}, timeout=5)
                base = re.search(r'this\.adsBaseUrl\s*=\s*[\'"]([^\'"]+)', r.text)
                if base:
                    results.append({"name": f"SL - {cname}", "url": f"{base.group(1)}{cid}/playlist.m3u8", "group": "SELÇUKSPOR HD", "ref": referer, "logo": ""})
        
        print(f"[OK] Selçukspor: {len(results)} kanal çekildi.")
        return results, "BAŞARILI"
    except Exception as e:
        return [], f"HATA: {str(e)}"

def main():
    all_streams = []
    rapor = {}

    # 1. Netspor
    res, msg = fetch_netspor()
    all_streams.extend(res); rapor["Netspor"] = msg
    
    # 2. Trgoals
    res, msg = fetch_trgoals()
    all_streams.extend(res); rapor["Trgoals"] = msg
    
    # 3. Selçukspor
    res, msg = fetch_selcuk_sporcafe()
    all_streams.extend(res); rapor["Selcukspor"] = msg

    print("\n" + "="*40)
    print("      --- DURUM RAPOR PANELİ ---")
    for site, durum in rapor.items():
        print(f"{site.ljust(15)}: {durum}")
    print("="*40)

    if not all_streams:
        print("\n[!] KRİTİK HATA: Hiçbir siteden veri alınamadı. Bot durduruluyor.")
        exit(1) # GitHub Action'ın hata vermesini sağlar

    content = "#EXTM3U\n"
    content += f"# Son Guncelleme: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
    for s in all_streams:
        logo = f' tvg-logo="{s["logo"]}"' if s["logo"] else ""
        content += f'#EXTINF:-1 group-title="{s["group"]}"{logo},{s["name"]}\n'
        content += f'#EXTVLCOPT:http-referrer={s["ref"]}\n'
        content += f'{s["url"]}\n'

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n[OK] Dosya '{OUTPUT_FILE}' başarıyla güncellendi.")

if __name__ == "__main__":
    main()
