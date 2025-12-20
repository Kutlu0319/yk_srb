import requests
import re
import datetime
from bs4 import BeautifulSoup

# --- AYARLAR ---
OUTPUT_FILE = "Canli_Spor_Hepsi.m3u"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def fetch_netspor():
    print("\n--- [SİTE 1: NETSPOR TARAMASI] ---")
    final_list = []
    source_url = "https://netspor-amp.xyz/"
    stream_base = "https://andro.6441255.xyz/checklist/"
    
    try:
        res = requests.get(source_url, headers=HEADERS, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. CANLI TV KANALLARI (Sırasıyla: BeIN 1, 2, 3...)
        ch_section = soup.find('div', id='kontrolPanelKanallar')
        if ch_section:
            for div in ch_section.find_all('div', class_='mac', option=True):
                sid = div.get('option')
                t_div = div.find('div', class_='match-takimlar')
                if sid and t_div:
                    name = t_div.get_text(strip=True)
                    final_list.append({
                        "name": name,
                        "url": f"{stream_base}{sid}.m3u8",
                        "group": "CANLI TV KANALLARI",
                        "ref": source_url, "logo": ""
                    })
            print(f"[OK] Netspor: {len(final_list)} kanal çekildi.")

        # 2. GÜNÜN MAÇLARI (Sitedeki orijinal sırayla)
        match_section = soup.find('div', id='kontrolPanel')
        if match_section:
            added_urls = set() # Tekrar eden maçları engellemek için
            all_match_divs = match_section.find_all('div', class_='mac', option=True)
            for div in all_match_divs:
                sid = div.get('option')
                t_div = div.find('div', class_='match-takimlar')
                if sid and t_div:
                    m_url = f"{stream_base}{sid}.m3u8"
                    if m_url not in added_urls:
                        teams = t_div.get_text(strip=True).replace("CANLI", "").strip()
                        alt = div.find('div', class_='match-alt')
                        info = alt.get_text(" | ", strip=True) if alt else ""
                        
                        final_list.append({
                            "name": f"{teams} ({info})",
                            "url": m_url,
                            "group": "Günün Maçları",
                            "ref": source_url, "logo": ""
                        })
                        added_urls.add(m_url)
            print(f"[OK] Netspor: Maçlar eklendi.")
            
        return final_list, "BAŞARILI"
    except Exception as e:
        return [], f"HATA: {str(e)}"

def fetch_trgoals():
    print("\n--- [SİTE 2: TRGOALS TARAMASI] ---")
    results = []
    domain = None
    # Aktif domain bulma
    for i in range(1485, 2150):
        test = f"https://trgoals{i}.xyz"
        try:
            if requests.head(test, timeout=1).status_code == 200:
                domain = test
                break
        except: continue
    
    if domain:
        cids = {"yayin1":"BEIN 1","yayinb2":"BEIN 2","yayinb3":"BEIN 3","yayinss":"S SPORT"}
        for cid, name in cids.items():
            try:
                r = requests.get(f"{domain}/channel.html?id={cid}", headers=HEADERS, timeout=5)
                m = re.search(r'const baseurl = "(.*?)"', r.text)
                if m:
                    results.append({
                        "name": f"TRG - {name}", "url": f"{m.group(1)}{cid}.m3u8",
                        "group": "TRGOALS TV", "ref": f"{domain}/",
                        "logo": "https://i.ibb.co/gFyFDdDN/trgoals.jpg"
                    })
            except: continue
    return results, "BAŞARILI" if domain else "DOMAIN BULUNAMADI"

def fetch_selcuk_sporcafe():
    print("\n--- [SİTE 3: SELÇUKSPOR TARAMASI] ---")
    results = []
    referer = None
    html_content = None
    for i in range(6, 130):
        url = f"https://www.sporcafe{i}.xyz/"
        try:
            res = requests.get(url, headers=HEADERS, timeout=1)
            if "uxsyplayer" in res.text:
                referer, html_content = url, res.text
                break
        except: continue
    
    if html_content and referer:
        m = re.search(r'https?://(main\.uxsyplayer[0-9a-zA-Z\-]+\.click)', html_content)
        if m:
            s_domain = f"https://{m.group(1)}"
            c_ids = [("selcukbeinsports1","BeIN 1"), ("selcukbeinsports2","BeIN 2"), ("selcukssport","S SPORT")]
            for cid, cname in c_ids:
                try:
                    r = requests.get(f"{s_domain}/index.php?id={cid}", headers={**HEADERS, "Referer": referer}, timeout=5)
                    base = re.search(r'this\.adsBaseUrl\s*=\s*[\'"]([^\'"]+)', r.text)
                    if base:
                        results.append({
                            "name": f"SL - {cname}", "url": f"{base.group(1)}{cid}/playlist.m3u8",
                            "group": "SELÇUKSPOR HD", "ref": referer, "logo": ""
                        })
                except: continue
    return results, "BAŞARILI" if referer else "SİTE BULUNAMADI"

def main():
    all_streams = []
    
    # 1. Netspor (Sıralama: Kanallar -> Maçlar)
    res_n, _ = fetch_netspor()
    all_streams.extend(res_n)
    
    # 2. Trgoals
    res_t, _ = fetch_trgoals()
    all_streams.extend(res_t)
    
    # 3. Selçukspor
    res_s, _ = fetch_selcuk_sporcafe()
    all_streams.extend(res_s)

    if not all_streams:
        print("[!] Veri bulunamadı.")
        return

    # Dosya oluşturma (UTF-8-SIG karakter sorununu kökten çözer)
    content = "#EXTM3U\n"
    content += f"# Son Guncelleme: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
    
    for s in all_streams:
        logo = f' tvg-logo="{s["logo"]}"' if s["logo"] else ""
        content += f'#EXTINF:-1 group-title="{s["group"]}"{logo},{s["name"]}\n'
        content += f'#EXTVLCOPT:http-referrer={s["ref"]}\n'
        content += f'{s["url"]}\n'

    with open(OUTPUT_FILE, "w", encoding="utf-8-sig") as f:
        f.write(content)
    print(f"\n[OK] Sıralama ve karakterler düzeltildi. '{OUTPUT_FILE}' hazır.")

if __name__ == "__main__":
    main()
