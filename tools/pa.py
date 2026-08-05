"""Jalankan perintah di PythonAnywhere dari laptop, tanpa copas ke konsol browser.

Token dibaca dari ~/.pythonanywhere_token (mode 600) dan TIDAK PERNAH dicetak.
Berkas ini aman masuk repo: tidak ada rahasia di dalamnya.

    python3 tools/pa.py "cd ~/giftcard && git pull"
    python3 tools/pa.py --reload
    python3 tools/pa.py --deploy          # pull + collectstatic + reload

Kenapa ada: menempel perintah ke konsol browser PythonAnywhere berkali-kali
gagal karena teks prompt ikut tersalin (`(kartuku) 14:43 ~/giftcard (main)$ …`
→ `bash: syntax error`), dan sekali membuat bash tersangkut di mode lanjutan `>`
sehingga perintahnya tidak pernah jalan.
"""

import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

USER = "kartuku"
DOMAIN = f"{USER}.pythonanywhere.com"
BASE = f"https://www.pythonanywhere.com/api/v0/user/{USER}"
BERKAS_TOKEN = pathlib.Path.home() / ".pythonanywhere_token"

ANSI = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")


def token():
    if not BERKAS_TOKEN.exists():
        raise SystemExit(
            f"Token tidak ada di {BERKAS_TOKEN}.\n"
            "Ambil di PythonAnywhere → Account → API token, lalu simpan tanpa\n"
            "menampilkannya:\n"
            f"  read -s t && printf %s \"$t\" > {BERKAS_TOKEN} && chmod 600 {BERKAS_TOKEN}"
        )
    return BERKAS_TOKEN.read_text().strip()


def api(path, method="GET", data=None):
    req = urllib.request.Request(
        f"{BASE}{path}",
        method=method,
        data=json.dumps(data).encode() if data else None,
        headers={"Authorization": f"Token {token()}",
                 "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            mentah = r.read()
            return r.status, (json.loads(mentah) if mentah else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


def konsol_bash():
    status, daftar = api("/consoles/")
    if status != 200:
        raise SystemExit(f"Gagal membaca daftar konsol: {status} {daftar}")
    for c in daftar:
        if c["executable"].endswith("bash"):
            return c["id"]
    raise SystemExit(
        "Tidak ada konsol Bash. Buka satu lewat tab Consoles di PythonAnywhere "
        "— konsol harus pernah dijalankan di browser sebelum API bisa memakainya."
    )


def jalankan(perintah, batas_detik=300):
    """Kirim perintah, tunggu sampai selesai, kembalikan keluarannya.

    Konsol PythonAnywhere mengembalikan seluruh isi layar, bukan hasil perintah
    terakhir saja. Penanda unik dipakai supaya keluaran lama tidak ikut terbaca
    dan supaya selesainya diketahui pasti, bukan ditebak lewat jeda waktu.
    """
    cid = konsol_bash()
    tanda = f"__SELESAI_{int(time.time())}__"

    status, _ = api(f"/consoles/{cid}/send_input/", "POST",
                    {"input": f"{perintah}; echo {tanda}\n"})
    if status not in (200, 201):
        raise SystemExit(f"Gagal mengirim perintah: {status}")

    mulai = time.time()
    while time.time() - mulai < batas_detik:
        time.sleep(3)
        status, keluaran = api(f"/consoles/{cid}/get_latest_output/")
        if status != 200:
            continue
        layar = keluaran.get("output", "")
        # Kemunculan pertama = gema perintahnya, kedua = hasil echo.
        if layar.count(tanda) >= 2:
            badan = layar.rsplit(tanda, 1)[0].split(tanda, 1)[-1]
            return ANSI.sub("", badan).strip()
    raise SystemExit(f"Lewat {batas_detik} detik, perintahnya belum selesai.")


def reload_web():
    status, _ = api(f"/webapps/{DOMAIN}/reload/", "POST")
    if status not in (200, 201):
        raise SystemExit(f"Reload gagal: HTTP {status}")
    return status


# Jalur mutlak ke Python virtualenv. JANGAN andalkan `python` di PATH: konsol
# PythonAnywhere yang baru dibuka tidak selalu mengaktifkan virtualenv, dan
# Python sistem tidak punya whitenoise maupun paket proyek lainnya — perintahnya
# gagal dengan ModuleNotFoundError yang membingungkan.
PY = f"/home/{USER}/.virtualenvs/{USER}/bin/python"


def deploy():
    print(jalankan(
        f"cd ~/giftcard && git pull --ff-only"
        f" && {PY} manage.py migrate --noinput"
        f" && {PY} manage.py collectstatic --noinput"
    ))
    print(f"\nReload {DOMAIN} -> HTTP {reload_web()}")


if __name__ == "__main__":
    arg = sys.argv[1:]
    if arg == ["--reload"]:
        print(f"Reload {DOMAIN} -> HTTP {reload_web()}")
    elif arg == ["--deploy"]:
        deploy()
    elif arg:
        print(jalankan(" ".join(arg)))
    else:
        raise SystemExit(__doc__)
