import requests
import re
import datetime
from bs4 import BeautifulSoup

# --- AYARLAR ---
OUTPUT_FILE = "Canli_Spor_Hepsi.m3u"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
WORKING_BS1_URL = "https://andro.adece12.sbs/checklist/receptestt.m3u8"

# --- 1. VAVOO SİSTEMİ (STABİL KAYNAK) ---
def fetch_vavoo():
    print("[*] Vavoo kanalları ekleniyor...")
    results = []
    proxy_base = "https://yildiziptv-turktv.hf.space/proxy/hls/manifest.m3u8?d=https://vavoo.to/vavoo-iptv/play/"
    vavoo_channels = [
        {"n": "beIN SPORTS Haber", "id": "398999553310ffc0558467", "img": "https://www.digiturkburada.com.tr/kanal3/bein-sports-haber-hd.png"},
        {"n": "beIN SPORTS 1 HD", "id": "257621689779b8fed9899e", "img": "https://www.digiturkburada.com.tr/kanal3/bein-sports-hd-1-1.png"},
        {"n": "beIN SPORTS 2 FHD", "id": "3694662475b76c08f52108", "img": "https://www.digiturkburada.com.tr/kanal3/bein-sports-hd-2-1.png"},
        {"n": "beIN SPORTS 3 FHD", "id": "34101675603c7aea8fa6b1", "img": "https://www.digiturkburada.com.tr/kanal3/bein-sports-hd-3-1.png"},
        {"n": "beIN SPORTS 4 FHD", "id": "293826835381972adead05", "img": "https://www.digiturkburada.com.tr/kanal3/bein-sports-hd-4.png"},
        {"n": "beIN SPORTS 5 FHD", "id": "400031560107e5581e3624", "img": "https://www.digiturkburada.com.tr/kanal3/bein-sports-hd-5.png"},
        {"n": "beIN SPORTS MAX 1", "id": "2832430535849b88f81e2d", "img": "https://www.digiturkburada.com.tr/kanal3/bein-sports-max-1-hd.png"},
        {"n": "beIN SPORTS MAX 2", "id": "34079362426e8ca1ffedf7", "img": "https://www.digiturkburada.com.tr/kanal3/bein-sports-max-2-hd.png"}
    ]
    for ch in vavoo_channels:
        results.append({"name": f"VAVOO - {ch['n']}", "url": f"{proxy_base}{ch['id']}", "group": "VAVOO SPOR (STABIL)", "logo": ch['img'], "ref": ""})
    return results

# --- 2. NETSPOR SİSTEMİ (BS1 FIXLİ) ---
def fetch_netspor():
    print("[*] Netspor taranıyor...")
    results = []
    source_url = "https://netspor-amp.xyz/"
    stream_base = "https://andro.adece12.sbs/checklist/" 
    try:
        res = requests.get(source_url, headers=HEADERS, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        for div in soup.find_all('div', class_='mac', option=True):
            sid = div.get('option')
            t_div = div.find('div', class_='match-takimlar')
            if not sid or not t_div: continue
            title = t_div.get_text(strip=True)
            group = "CANLI TV KANALLARI" if div.find_parent('div', id='kontrolPanelKanallar') else "Günün Maçları"
            if group == "Günün Maçları":
                alt = div.find('div', class_='match-alt')
                if alt: title = f"{title} ({alt.get_text(' | ', strip=True)})"
            # bs1 Link Onarımı
            final_url = WORKING_BS1_URL if sid == "androstreamlivebs1" else f"{stream_base}{sid}.m3u8"
            results.append({"name": f"NET - {title}", "url": final_url, "group": f"NETSPOR {group.upper()}", "ref": source_url, "logo": ""})
    except: pass
    return results

# --- 3. TRGOALS SİSTEMİ (TAM LİSTE) ---
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
        # SENİN VERDİĞİN TÜM TRGOALS KANAL LİSTESİ
        trg_channels = {
            "yayin1":"BEIN SPORTS 1 HD", "yayinb2":"BEIN SPORTS 2 HD", "yayinb3":"BEIN SPORTS 3 HD",
            "yayinb4":"BEIN SPORTS 4 HD", "yayinb5":"BEIN SPORTS 5 HD", "yayinbm1":"BEIN SPORTS MAX 1",
            "yayinbm2":"BEIN SPORTS MAX 2", "yayinss":"S SPORT 1", "yayinss2":"S SPORT 2",
            "yayint1":"TIVIBU SPOR 1", "yayint2":"TIVIBU SPOR 2", "yayint3":"TIVIBU SPOR 3", "yayint4":"TIVIBU SPOR 4",
            "yayinsmarts":"SMART SPOR 1", "yayinsms2":"SMART SPOR 2", "yayintrtspor":"TRT SPOR",
            "yayinas":"A SPOR", "yayintv85":"TV8.5 HD", "yayinex1":"TABII 1", "yayinex2":"TABII 2", "yayinex3":"TABII 3"
        }
        for cid, name in trg_channels.items():
            try:
                r = requests.get(f"{domain}/channel.html?id={cid}", headers=HEADERS, timeout=5)
                m = re.search(r'const baseurl = "(.*?)"', r.text)
                if m: results.append({"name": f"TRG - {name}", "url": f"{m.group(1)}{cid}.m3u8", "group": "TRGOALS TV", "ref": f"{domain}/", "logo": "https://i.ibb.co/gFyFDdDN/trgoals.jpg"})
            except: continue
    return results

# --- 4. SELÇUKSPOR SİSTEMİ (TAM LİSTE) ---
def fetch_selcuk_sporcafe():
    print("[*] Selçukspor taranıyor...")
    results = []
    # SENİN VERDİĞİN TÜM SELÇUKSPOR KANAL LİSTESİ
    selcuk_channels = [
        {"id": "selcukbeinsports1", "n": "BEIN SPORTS 1"}, {"id": "selcukbeinsports2", "n": "BEIN SPORTS 2"},
        {"id": "selcukbeinsports3", "n": "BEIN SPORTS 3"}, {"id": "selcukbeinsports4", "n": "BEIN SPORTS 4"},
        {"id": "selcukbeinsports5", "n": "BEIN SPORTS 5"}, {"id": "selcukbeinsportsmax1", "n": "BEIN MAX 1"},
        {"id": "selcukbeinsportsmax2", "n": "BEIN MAX 2"}, {"id": "selcukssport", "n": "S SPORT 1"},
        {"id": "selcukssport2", "n": "S SPORT 2"}, {"id": "selcuktivibuspor1", "n": "TIVIBU 1"},
        {"id": "selcuktivibuspor2", "n": "TIVIBU 2"}, {"id": "selcuksmartspor", "n": "SMART SPOR 1"},
        {"id": "selcukaspor", "n": "A SPOR"}, {"id": "selcukeurosport1", "n": "EUROSPORT 1"}
    ]
    referer, html = None, None
    for i in range(6, 150):
        url = f"https://www.sporcafe{i}.xyz/"
        try:
            res = requests.get(url, headers=HEADERS, timeout=1)
            if "uxsyplayer" in res.text: referer, html = url, res.text; break
        except: continue
    if html:
        m_dom = re.search(r'https?://(main\.uxsyplayer[0-9a-zA-Z\-]+\.click)', html)
        if m_dom:
            s_dom = f"https://{m_dom.group(1)}"
            for ch in selcuk_channels:
                try:
                    r = requests.get(f"{s_dom}/index.php?id={ch['id']}", headers={**HEADERS, "Referer": referer}, timeout=5)
                    base = re.search(r'this\.adsBaseUrl\s*=\s*[\'"]([^\'"]+)', r.text)
                    if base: results.append({"name": f"SL - {ch['n']}", "url": f"{base.group(1)}{ch['id']}/playlist.m3u8", "group": "SELÇUKSPOR HD", "ref": referer, "logo": ""})
                except: continue
    return results

# --- ANA ÇALIŞTIRICI ---
def main():
    all_streams = []
    all_streams.extend(fetch_vavoo())
    all_streams.extend(fetch_netspor())
    all_streams.extend(fetch_trgoals())
    all_streams.extend(fetch_selcuk_sporcafe())
    
    if not all_streams: return

    content = "#EXTM3U\n"
    content += f"# Son Guncelleme: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
    for s in all_streams:
        logo = f' tvg-logo="{s["logo"]}"' if s.get("logo") else ""
        content += f'#EXTINF:-1 group-title="{s["group"]}"{logo},{s["name"]}\n'
        if s.get("ref"): content += f'#EXTVLCOPT:http-referrer={s["ref"]}\n'
        content += f'{s["url"]}\n'

    with open(OUTPUT_FILE, "w", encoding="utf-8-sig") as f:
        f.write(content)
    print(f"\n[OK] Tum siteler ve kanallar eksiksiz olarak birlestirildi.")

if __name__ == "__main__":
    main()
