# -*- coding: utf-8 -*-
"""data/cameras.json -> 우아카메라(WooaCamera) 무인교통단속카메라 정적 HTML 생성"""
import hashlib
import html
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import quote

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"
BASE_URL = "https://wooacamera.wooahouse.com"
SITE_NAME = "우아카메라"
TODAY = date.today().isoformat()
YEAR = TODAY[:4]
AD_CLIENT = "ca-pub-6464921081676309"

COUPANG_HTML = '''
<div class="coupang-partners" style="margin:28px auto 0;max-width:720px;padding:0 16px;text-align:center;overflow-x:auto;">
  <script src="https://ads-partners.coupang.com/g.js"></script>
  <script>
    new PartnersCoupang.G({"id":980427,"trackingCode":"AF5600192","subId":"camera","template":"carousel","width":"680","height":"140"});
  </script>
</div>
'''
COUPANG_DISCLOSURE = '<p style="margin:6px 0 0;font-size:.68rem;opacity:.5;">이 페이지는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</p>'


def head_common(root):
    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-9ZGENFSXWC"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-9ZGENFSXWC');</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={AD_CLIENT}" crossorigin="anonymous"></script>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%93%B7%3C/text%3E%3C/svg%3E">
<link rel="stylesheet" href="{root}css/style.css">
"""

HEADER_TMPL = """<header class="site-header">
  <div class="header-inner">
    <a href="{root}index.html" class="logo">📷 우아카메라</a>
    <nav>
      <a href="{root}index.html">지역 검색</a>
      <a href="{root}about.html">소개</a>
    </nav>
  </div>
</header>
"""

MOBILE_AD = f"""<div class="mobile-top-ad">
  <ins class="adsbygoogle" style="display:block;width:100%;min-height:60px" data-ad-client="{AD_CLIENT}" data-ad-slot="7080296704" data-ad-format="auto" data-full-width-responsive="true"></ins>
  <script>(adsbygoogle=window.adsbygoogle||[]).push({{}});</script>
</div>"""


def ad_banner(slot="1419180025"):
    return (f'<div class="ad-banner"><ins class="adsbygoogle" style="display:block" data-ad-client="{AD_CLIENT}" '
            f'data-ad-slot="{slot}" data-ad-format="auto" data-full-width-responsive="true"></ins>'
            f'<script>(adsbygoogle=window.adsbygoogle||[]).push({{}});</script></div>')


def page_head(title, desc, canonical, root, extra_ld=""):
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
{head_common(root)}
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{canonical}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{canonical}">
  <meta property="og:site_name" content="{SITE_NAME}">
{extra_ld}
</head>
"""


def footer_html(root):
    return f"""{COUPANG_HTML}
<footer class="site-footer">
  <div class="footer-inner">
    <p class="footer-disclaimer">본 정보는 경찰청·지방자치단체가 제공하는 전국무인교통단속카메라표준데이터(공공데이터포털)를 기반으로 합니다.<br>이동식 단속카메라는 포함되지 않으며, 실제 단속 여부·기준은 관할 기관에 문의해 확인하세요.</p>
    {COUPANG_DISCLOSURE}
    <p class="copyright">&copy; {YEAR} 우아카메라 · <a href="https://wooahouse.com" target="_blank">WooaHouse</a> · <a href="{root}privacy.html">개인정보처리방침</a></p>
  </div>
</footer>
</body>
</html>
"""


def slugify(sido, sigungu):
    base = sigungu.replace(" ", "")
    h = hashlib.md5(f"{sido}_{sigungu}".encode("utf-8")).hexdigest()[:6]
    return f"{base}-{h}"


CRACKDOWN_LABEL = {
    "1": "속도", "01": "속도",
    "2": "신호위반", "02": "신호위반",
    "3": "통행위반", "03": "통행위반",
    "4": "불법주정차·기타", "04": "불법주정차·기타",
    "99": "기타",
}


def esc(s):
    return html.escape((s or "").strip())


def gen_sigungu_page(sido, sigungu, cams, slug):
    cams = sorted(cams, key=lambda c: (c.get("도로노선명", ""), c.get("설치장소", "")))
    n = len(cams)

    title = f"{sigungu} 무인단속카메라 위치 {n}곳 | {SITE_NAME}"
    desc = f"{sido} {sigungu}에 설치된 고정식 무인교통단속카메라 {n}곳의 위치·설치장소·제한속도·설치연도를 확인하세요."
    canonical = f"{BASE_URL}/{quote(slug)}/index.html"

    intro = (f"{sido} {sigungu}에 설치된 고정식 무인교통단속카메라는 총 {n}곳입니다. "
             f"이동식 카메라는 포함되지 않으며, 도로명·설치장소별로 확인할 수 있습니다.")

    rows = []
    for i, c in enumerate(cams):
        addr = c.get("소재지도로명주소") or c.get("소재지지번주소") or ""
        place = c.get("설치장소") or c.get("도로노선명") or "위치 정보"
        speed = (c.get("제한속도") or "").strip()
        year = (c.get("설치연도") or "").strip()
        lat = (c.get("위도") or "").strip()
        lng = (c.get("경도") or "").strip()
        crack = CRACKDOWN_LABEL.get((c.get("단속구분") or "").strip(), "")

        badges = []
        if speed and speed != "0":
            badges.append(f"제한 {esc(speed)}km/h")
        if crack:
            badges.append(esc(crack))
        if year:
            badges.append(f"{esc(year)}년 설치")
        badge_html = " · ".join(badges)

        map_link = ""
        if lat and lng:
            map_link = f'<a href="https://map.kakao.com/link/map/{quote(place)},{lat},{lng}" class="cam-map-link">지도 보기 →</a>'

        rows.append(
            f'<div class="cam-row" data-search="{esc(place)} {esc(addr)}">'
            f'<div class="cam-place">{esc(place)}</div>'
            f'<div class="cam-addr">{esc(addr)}</div>'
            f'<div class="cam-badges">{badge_html}</div>'
            f'{map_link}'
            f'</div>'
        )
    rows_html = "\n".join(rows)

    body = f"""<div class="container" style="padding:20px 16px 40px;max-width:720px;margin:0 auto;">
  <nav style="font-size:.82rem;color:#6B7280;margin-bottom:14px;">
    <a href="../index.html" style="color:#6B7280;">홈</a> › {esc(sido)} › {esc(sigungu)}
  </nav>
  <h1 style="font-size:1.4rem;font-weight:800;margin-bottom:6px;">📷 {esc(sigungu)} 무인단속카메라</h1>
  <p style="color:#374151;line-height:1.75;margin:12px 0 20px;">{intro}</p>

  {MOBILE_AD}

  <input type="text" id="camSearch" placeholder="도로명·설치장소로 검색" style="width:100%;padding:11px 14px;border:1px solid #E5E7EB;border-radius:8px;font-size:.92rem;margin-bottom:14px;">
  <p style="font-size:.8rem;color:#9CA3AF;margin-bottom:10px;">총 {n}곳</p>

  <div id="camList">
  {rows_html}
  </div>
  <p id="camEmpty" style="display:none;text-align:center;color:#9CA3AF;padding:30px 0;">검색 결과가 없습니다.</p>

  <div style="margin-top:20px;padding:14px;background:#F9FAFB;border-radius:10px;font-size:.85rem;color:#6B7280;line-height:1.7;">
    ※ 이동식 단속카메라, 최근 신설·철거된 카메라는 반영되지 않을 수 있습니다. 참고용으로 확인하세요.
  </div>
</div>
<style>
.cam-row{{border:1px solid #E5E7EB;border-radius:10px;padding:12px 14px;margin-bottom:8px;}}
.cam-place{{font-weight:700;font-size:.98rem;}}
.cam-addr{{color:#6B7280;font-size:.85rem;margin-top:2px;}}
.cam-badges{{color:#0D9488;font-size:.82rem;margin-top:6px;font-weight:600;}}
.cam-map-link{{display:inline-block;margin-top:6px;font-size:.82rem;color:#0891B2;text-decoration:none;font-weight:600;}}
</style>
<script>
document.getElementById('camSearch').addEventListener('input', function(e){{
  var q = e.target.value.trim().toLowerCase();
  var rows = document.querySelectorAll('.cam-row');
  var shown = 0;
  rows.forEach(function(r){{
    var match = r.dataset.search.toLowerCase().indexOf(q) !== -1;
    r.style.display = match ? '' : 'none';
    if(match) shown++;
  }});
  document.getElementById('camEmpty').style.display = shown === 0 ? 'block' : 'none';
}});
</script>
"""
    head = page_head(title, desc, canonical, "../")
    return head + "<body>\n\n" + HEADER_TMPL.format(root="../") + "\n" + body + footer_html("../")


def gen_index(groups, total):
    title = f"전국 무인단속카메라 위치 조회 {YEAR} | {SITE_NAME}"
    desc = f"전국 {len(groups)}개 시군구, {total:,}곳의 무인교통단속카메라 위치를 무료로 조회하세요. 속도·신호위반·불법주정차 단속카메라 포함."
    canonical = f"{BASE_URL}/"

    by_sido = defaultdict(list)
    for (sido, sigungu), (slug, n) in groups.items():
        by_sido[sido].append((sigungu, slug, n))

    sections = []
    for sido in sorted(by_sido.keys()):
        items = sorted(by_sido[sido], key=lambda x: x[0])
        cards = "".join(
            f'<a href="{quote(slug)}/index.html" class="sgg-card"><span>{esc(sigungu)}</span><em>{n}곳</em></a>'
            for sigungu, slug, n in items
        )
        sections.append(
            f'<div class="sido-group"><h2>{esc(sido)}</h2><div class="sgg-grid">{cards}</div></div>'
        )
    sections_html = "\n".join(sections)

    body = f"""<div class="hero" style="background:linear-gradient(135deg,#0D9488,#0891B2);color:#fff;padding:44px 16px;text-align:center;">
  <h1 style="font-size:1.7rem;font-weight:800;margin-bottom:8px;">📷 전국 무인단속카메라 위치 조회</h1>
  <p style="opacity:.92;">지역을 선택하면 무인교통단속카메라 설치 위치를 바로 확인할 수 있어요</p>
</div>

<div class="container" style="padding:20px 16px 40px;max-width:960px;margin:0 auto;">
  {MOBILE_AD}
  <p style="font-size:.85rem;color:#6B7280;margin:16px 0;">전국 {len(groups)}개 시군구, {total:,}곳의 무인단속카메라 정보를 제공합니다(고정식만 포함, 이동식 제외).</p>

  {sections_html}

  {ad_banner()}
</div>
<style>
.sido-group{{margin-bottom:26px;}}
.sido-group h2{{font-size:1.05rem;font-weight:800;margin-bottom:10px;color:#111827;}}
.sgg-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px;}}
.sgg-card{{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;border:1px solid #E5E7EB;border-radius:8px;text-decoration:none;color:#111827;font-size:.88rem;}}
.sgg-card em{{color:#0D9488;font-style:normal;font-weight:700;font-size:.8rem;}}
</style>
"""
    head = page_head(title, desc, canonical, "")
    return head + "<body>\n\n" + HEADER_TMPL.format(root="") + "\n" + body + footer_html("")


def gen_about():
    title = f"소개 | {SITE_NAME}"
    desc = "우아카메라는 전국 고정식 무인교통단속카메라 위치를 무료로 조회할 수 있는 서비스입니다."
    canonical = f"{BASE_URL}/about.html"
    body = f"""<div class="container" style="padding:20px 16px 40px;max-width:680px;margin:0 auto;">
  <nav style="font-size:.82rem;color:#6B7280;margin-bottom:14px;"><a href="index.html" style="color:#6B7280;">홈</a> › 소개</nav>
  <h1 style="font-size:1.4rem;font-weight:800;margin-bottom:16px;">📷 우아카메라란?</h1>
  <p style="color:#374151;line-height:1.8;margin-bottom:14px;">우아카메라는 경찰청·지방자치단체가 공공데이터포털을 통해 공개하는 <b>전국무인교통단속카메라표준데이터</b>를 바탕으로, 전국 고정식 무인교통단속카메라의 설치 위치를 누구나 무료로 조회할 수 있도록 만든 서비스입니다.</p>
  <p style="color:#374151;line-height:1.8;margin-bottom:14px;">설치장소, 도로명, 제한속도, 설치연도 등의 정보를 지역별로 확인할 수 있으며, 회원가입 없이 바로 이용할 수 있습니다.</p>
  <p style="color:#374151;line-height:1.8;margin-bottom:14px;">※ 이동식 단속카메라는 포함되지 않으며, 데이터 갱신 주기(반기)에 따라 최신 설치·철거 현황이 일부 반영되지 않을 수 있습니다. 참고용으로 확인해 주세요.</p>
  <p style="color:#374151;line-height:1.8;">데이터 출처: <a href="https://www.data.go.kr/data/15028200/standard.do" target="_blank" style="color:#0891B2;">공공데이터포털 - 전국무인교통단속카메라표준데이터</a></p>
</div>
"""
    head = page_head(title, desc, canonical, "")
    return head + "<body>\n\n" + HEADER_TMPL.format(root="") + "\n" + body + footer_html("")


def gen_privacy():
    title = f"개인정보처리방침 | {SITE_NAME}"
    canonical = f"{BASE_URL}/privacy.html"
    body = f"""<div class="container" style="padding:20px 16px 40px;max-width:680px;margin:0 auto;">
  <nav style="font-size:.82rem;color:#6B7280;margin-bottom:14px;"><a href="index.html" style="color:#6B7280;">홈</a> › 개인정보처리방침</nav>
  <h1 style="font-size:1.4rem;font-weight:800;margin-bottom:16px;">개인정보처리방침</h1>
  <p style="color:#374151;line-height:1.8;">우아카메라는 별도의 회원가입 및 개인정보 수집 없이 운영됩니다. 광고 게재를 위해 Google AdSense, 쿠팡 파트너스가 쿠키를 사용할 수 있으며, 이용자는 브라우저 설정을 통해 쿠키 저장을 거부할 수 있습니다.</p>
</div>
"""
    head = page_head(title, "개인정보처리방침", canonical, "")
    return head + "<body>\n\n" + HEADER_TMPL.format(root="") + "\n" + body + footer_html("")


def gen_sitemap(paths):
    urls = "\n".join(
        f"  <url><loc>{BASE_URL}/{quote(p)}</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>"
        for p in paths
    )
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "\n</urlset>\n"
    (DOCS_DIR / "sitemap.xml").write_text(xml, encoding="utf-8")
    print(f"  sitemap: {len(paths):,}개 URL")


def main():
    cams = json.loads((DATA_DIR / "cameras.json").read_text(encoding="utf-8"))
    print(f"{len(cams):,}건 로드")

    by_sgg = defaultdict(list)
    for c in cams:
        sido = (c.get("시도명") or "").strip()
        sigungu = (c.get("시군구명") or "").strip()
        if not sido or not sigungu:
            continue
        by_sgg[(sido, sigungu)].append(c)

    groups = {}
    url_paths = ["index.html", "about.html", "privacy.html"]
    for (sido, sigungu), items in by_sgg.items():
        slug = slugify(sido, sigungu)
        groups[(sido, sigungu)] = (slug, len(items))
        gate_dir = DOCS_DIR / slug
        gate_dir.mkdir(parents=True, exist_ok=True)
        (gate_dir / "index.html").write_text(gen_sigungu_page(sido, sigungu, items, slug), encoding="utf-8")
        url_paths.append(f"{slug}/index.html")

    (DOCS_DIR / "index.html").write_text(gen_index(groups, len(cams)), encoding="utf-8")
    (DOCS_DIR / "about.html").write_text(gen_about(), encoding="utf-8")
    (DOCS_DIR / "privacy.html").write_text(gen_privacy(), encoding="utf-8")
    gen_sitemap(url_paths)

    robots = f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n"
    (DOCS_DIR / "robots.txt").write_text(robots, encoding="utf-8")

    print(f"\n총 {len(by_sgg)}개 시군구 허브페이지 + 홈/소개/방침 생성 완료 ({len(cams):,}건)")


if __name__ == "__main__":
    main()
