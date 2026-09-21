# -*- coding: utf-8 -*-
"""
전국무인교통단속카메라표준데이터(publicDataPk=15028200) - 진짜 하위 126개 제출 파일 전부 다운로드.
1) selectStdDataDetailView.do 페이지네이션(pageIndex 1..N)으로 uddi 전체 수집
2) 각 uddi -> selectDpkDetailInfo.do 로 atchFileId 추출 (fn_fileDataDown(...) 파싱)
3) /cmm/cmm/fileDownload.do 로 실제 CSV 다운로드, EUC-KR 디코딩 후 병합
"""
import csv
import io
import json
import re
import time
from pathlib import Path

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
SCRATCH = Path(r"C:\Users\ingma\AppData\Local\Temp\claude\C-----wooahouse\b3d6ef2f-7a5f-49cc-8bb6-2d014e48960a\scratchpad")
RAW_DIR = SCRATCH / "camera_raw2"
OUT_FILE = SCRATCH / "cameras_final.json"
UDDI_LIST_FILE = SCRATCH / "camera_uddis.json"

PUBLIC_DATA_PK = "15028200"
BASE = "https://www.data.go.kr"

UDDI_PAT = re.compile(r'data-public-pk="(uddi:[a-f0-9-]+)"')
NAME_PAT = re.compile(
    r'data-public-pk="uddi:[a-f0-9-]+"[^>]*>\s*<span[^>]*>[^<]*</span>\s*([^<\n]+)'
)
FN_DOWN_PAT = re.compile(
    r"fn_fileDataDown\('(\d+)',\s*'(uddi:[a-f0-9-]+)',\s*'([^']+)',\s*'(\d+)'"
)

sess = requests.Session()
sess.headers.update(HEADERS)


def collect_uddis(total_pages=27):
    uddis = {}
    for page in range(1, total_pages + 1):
        r = sess.post(
            f"{BASE}/tcs/dss/selectStdDataDetailView.do",
            data={"pageIndex": str(page), "publicDataPk": PUBLIC_DATA_PK, "searchKeyword2": ""},
            timeout=30,
        )
        found = UDDI_PAT.findall(r.text)
        names = NAME_PAT.findall(r.text)
        for i, u in enumerate(found):
            nm = names[i].strip() if i < len(names) else ""
            uddis[u] = nm
        print(f"  page {page}: +{len(found)} (누적 {len(uddis)})")
        time.sleep(0.15)
    return uddis


def get_atchfile(uddi):
    r = sess.post(
        f"{BASE}/tcs/dss/selectDpkDetailInfo.do",
        data={"publicDataDetailPk": uddi},
        timeout=30,
    )
    m = FN_DOWN_PAT.search(r.text)
    if not m:
        return None
    _pk, _uddi, atch_file_id, file_detail_sn = m.groups()
    return atch_file_id, file_detail_sn


def download_csv(atch_file_id, file_detail_sn):
    r = sess.get(
        f"{BASE}/cmm/cmm/fileDownload.do",
        params={"atchFileId": atch_file_id, "fileDetailSn": file_detail_sn},
        timeout=60,
    )
    r.raise_for_status()
    return r.content


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if UDDI_LIST_FILE.exists():
        uddis = json.loads(UDDI_LIST_FILE.read_text(encoding="utf-8"))
    else:
        print("[1/3] uddi 목록 수집...")
        uddis = collect_uddis()
        UDDI_LIST_FILE.write_text(json.dumps(uddis, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"총 {len(uddis)}개 제출 파일")

    print("[2/3] 각 파일 다운로드...")
    all_rows = []
    kept = skipped_schema = skipped_error = 0
    for i, (uddi, nm) in enumerate(uddis.items(), 1):
        safe_id = uddi.replace("uddi:", "")
        raw_path = RAW_DIR / f"{safe_id}.csv"
        try:
            if raw_path.exists():
                content = raw_path.read_bytes()
            else:
                af = get_atchfile(uddi)
                if not af:
                    print(f"  [{i}/{len(uddis)}] {nm}: atchFileId 못찾음")
                    skipped_error += 1
                    continue
                content = download_csv(*af)
                raw_path.write_bytes(content)
                time.sleep(0.15)

            if content.startswith(b"\xef\xbb\xbf"):
                text = content.decode("utf-8-sig")
            else:
                try:
                    text = content.decode("utf-8")
                    if "�" in text:
                        raise UnicodeDecodeError("utf-8", b"", 0, 1, "fallback")
                except UnicodeDecodeError:
                    text = content.decode("euc-kr", errors="replace")
            reader = csv.reader(io.StringIO(text))
            rows = list(reader)
            if not rows:
                skipped_error += 1
                continue
            header = [h.strip() for h in rows[0]]
            if not header[0].startswith("무인교통단속카메라관리번호") and not header[0].startswith("관리번호"):
                skipped_schema += 1
                continue
            for row in rows[1:]:
                if not row or not any(c.strip() for c in row):
                    continue
                if len(row) < len(header):
                    row = row + [""] * (len(header) - len(row))
                all_rows.append(dict(zip(header, row[: len(header)])))
            kept += 1
        except Exception as e:
            skipped_error += 1
        if i % 20 == 0:
            print(f"  진행 {i}/{len(uddis)} (채택 {kept}, 누적행 {len(all_rows)})")

    print(f"\n[3/3] 완료: 채택 {kept} / 스키마스킵 {skipped_schema} / 에러 {skipped_error}")
    print(f"총 {len(all_rows)}건")
    OUT_FILE.write_text(json.dumps(all_rows, ensure_ascii=False), encoding="utf-8")
    print(f"저장: {OUT_FILE}")


if __name__ == "__main__":
    main()
