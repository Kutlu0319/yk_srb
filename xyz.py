from httpx import Client
import re
import sys


class XYZsportsManager:
    def __init__(self, cikti_dosyasi):
        self.cikti_dosyasi = cikti_dosyasi
        self.httpx = Client(timeout=10, verify=False)

        self.domain_list_url = (
            "https://raw.githubusercontent.com/karams81/domain_slc/"
            "refs/heads/main/selcuk_sports_guncel_domain.txt"
        )

        self.channel_ids = [
            "bein-sports-1", "bein-sports-2", "bein-sports-3",
            "bein-sports-4", "bein-sports-5", "bein-sports-max-1",
            "bein-sports-max-2", "smart-spor", "smart-spor-2",
            "trt-spor", "trt-spor-2", "aspor", "s-sport",
            "s-sport-2", "s-sport-plus-1", "s-sport-plus-2",
            "tivibu-spor-1", "tivibu-spor-2", "tivibu-spor-3",
            "tivibu-spor-4", "trt-spor", "selcukatv"
        ]


    # ----------------------------
    # GitHub'dan sadece xyzsports domainini al
    # ----------------------------
    def get_domain_list(self):
        headers = {"User-Agent": "Mozilla/5.0"}
        r = self.httpx.get(self.domain_list_url, headers=headers)
        r.raise_for_status()

        domains = []

        for line in r.text.splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue

            _, value = line.split("=", 1)
            value = value.strip()

            if "xyzsports" not in value.lower():
                continue

            if not value.startswith("http"):
                value = "https://" + value

            if not value.endswith("/"):
                value += "/"

            domains.append(value)

        return domains

    # ----------------------------
    # Çalışan domaini bul
    # ----------------------------
    def find_working_domain(self):
        headers = {"User-Agent": "Mozilla/5.0"}
        domains = self.get_domain_list()

        if not domains:
            return None, None

        for url in domains:
            try:
                r = self.httpx.get(url, headers=headers)
                if r.status_code == 200 and "uxsyplayer" in r.text:
                    print(f"Çalışan domain bulundu: {url}")
                    return r.text, url
                else:
                    print(f"Denenen domain: {url} | Durum: {r.status_code}")
            except Exception as e:
                print(f"Hata ({url}): {e}")

        return None, None

    # ----------------------------
    # Player domainini çıkar
    # ----------------------------
    def find_dynamic_player_domain(self, html):
        m = re.search(
            r'https?://([a-z0-9\-]+\.[0-9a-z]+\.click)',
            html,
            re.IGNORECASE
        )
        return f"https://{m.group(1)}" if m else None

    # ----------------------------
    # Base stream URL çıkar
    # ----------------------------
    def extract_base_stream_url(self, html):
        m = re.search(
            r'this\.baseStreamUrl\s*=\s*[\'"]([^\'"]+)',
            html
        )
        return m.group(1) if m else None

    # ----------------------------
    # M3U oluştur
    # ----------------------------
    def build_m3u8_content(self, base_stream_url, referer_url):
        m3u = ["#EXTM3U"]

        for cid in self.channel_ids:
            channel_name = cid.replace("-", " ").title()
            m3u.append(f'#EXTINF:-1 group-title="Umitmod",{channel_name}')
            m3u.append('#EXTVLCOPT:http-user-agent=Mozilla/5.0')
            m3u.append(f'#EXTVLCOPT:http-referrer={referer_url}')
            m3u.append(f'{base_stream_url}{cid}/playlist.m3u8')

        return "\n".join(m3u)

    # ----------------------------
    # Ana çalışma fonksiyonu
    # ----------------------------
    def calistir(self):
        html, referer_url = self.find_working_domain()
        if not html:
            raise RuntimeError("Çalışan xyzsports domaini bulunamadı!")

        player_domain = self.find_dynamic_player_domain(html)
        if not player_domain:
            raise RuntimeError("Player domain bulunamadı!")

        r = self.httpx.get(
            f"{player_domain}/index.php?id={self.channel_ids[0]}",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": referer_url
            }
        )

        base_url = self.extract_base_stream_url(r.text)
        if not base_url:
            raise RuntimeError("Base stream URL bulunamadı!")

        m3u_icerik = self.build_m3u8_content(base_url, referer_url)

        with open(self.cikti_dosyasi, "w", encoding="utf-8") as f:
            f.write(m3u_icerik)

        print(f"M3U dosyası oluşturuldu: {self.cikti_dosyasi}")
        print(f"Toplam kanal sayısı: {len(self.channel_ids)}")


# ----------------------------
# Çalıştır
# ----------------------------
if __name__ == "__main__":
    try:
        XYZsportsManager("zvt.m3u").calistir()
    except Exception as e:
        print(f"HATA: {e}")
        sys.exit(1)