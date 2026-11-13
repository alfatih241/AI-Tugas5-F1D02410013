"""
Sistem Pakar Gangguan Koneksi WiFi pada Laptop
Metode : Forward Chaining 
Basis pengetahuan dibaca dari file knowledge_base.json
"""

import json
import sys
from pathlib import Path

# File JSON dicari di folder yang sama dengan main.py,
# jadi program bisa dijalankan dari folder mana pun.
FILE_KB = Path(__file__).parent / "knowledge_base.json"


# ---------------------------------------------------------------
# 1. Membaca basis pengetahuan
# ---------------------------------------------------------------
def muat_kb(path):
    """Membaca file JSON dan mengembalikannya sebagai dictionary Python."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------
# 2. Menentukan fakta apa saja yang harus ditanyakan ke pengguna
# ---------------------------------------------------------------
def cari_fakta_dasar(daftar_aturan):
    """
    Fakta dasar = fakta yang muncul di bagian 'jika' tetapi TIDAK pernah
    menjadi hasil ('maka') dari aturan mana pun. Fakta seperti ini hanya
    bisa diketahui dari pengguna, jadi harus ditanyakan.
    """
    semua_hasil = {aturan["maka"] for aturan in daftar_aturan}
    fakta_dasar = []
    for aturan in daftar_aturan:
        for fakta in aturan["jika"]:
            if fakta not in semua_hasil and fakta not in fakta_dasar:
                fakta_dasar.append(fakta)
    return fakta_dasar


def tanya_pengguna(fakta_dasar):
    """Mengajukan pertanyaan y/t. Fakta yang dijawab 'y' menjadi fakta awal."""
    fakta_awal = []
    print("Jawab dengan y (ya) atau t (tidak).")
    for nomor, fakta in enumerate(fakta_dasar, start=1):
        while True:
            jawaban = input(f"{nomor}. Apakah {fakta}? (y/t) > ").strip().lower()
            if not sys.stdin.isatty():
                print(jawaban)
            if jawaban in ("y", "t"):
                break
            print("   Jawaban tidak dikenal, ketik y atau t.")
        if jawaban == "y":
            fakta_awal.append(fakta)
    return fakta_awal


def cari_konflik(kb, fakta_awal):
    """Mencari pasangan jawaban yang saling bertentangan (daftar 'bertentangan' di JSON)."""
    for fakta_a, fakta_b in kb["bertentangan"]:
        if fakta_a in fakta_awal and fakta_b in fakta_awal:
            return fakta_a, fakta_b
    return None


# ---------------------------------------------------------------
# 3. Mesin inferensi: Forward Chaining
# ---------------------------------------------------------------
def syarat_terpenuhi(aturan, memori):
    """
    Mode 'dan'  : semua syarat harus ada di memori.
    Mode 'atau' : cukup salah satu syarat ada di memori.
    """
    if aturan["mode"] == "dan":
        return all(syarat in memori for syarat in aturan["jika"])
    return any(syarat in memori for syarat in aturan["jika"])


def forward_chaining(daftar_aturan, fakta_awal):
    """
    Mulai dari fakta awal, jalankan aturan yang cocok, tambahkan hasilnya
    ke memori, ulangi sampai tidak ada aturan baru.
    Mengembalikan: (memori akhir, urutan aturan yang dijalankan).
    """
    memori = set(fakta_awal)   # working memory: semua fakta yang sudah diketahui
    urutan = []                # aturan yang dijalankan, sesuai urutan siklus

    while True:
        # Aturan yang cocok = syaratnya terpenuhi DAN hasilnya belum ada di memori.
        # Syarat kedua mencegah aturan dijalankan berulang-ulang (loop tanpa akhir).
        cocok = [
            aturan for aturan in daftar_aturan
            if syarat_terpenuhi(aturan, memori) and aturan["maka"] not in memori
        ]
        if not cocok:
            break                       # kriteria berhenti
        aturan = cocok[0]               # ambil aturan pertama yang cocok
        memori.add(aturan["maka"])      # hasil aturan menjadi fakta baru
        urutan.append(aturan)
        print(f"Siklus {len(urutan)}: {aturan['id']} -> {aturan['maka']}")

    print(f"Siklus {len(urutan) + 1}: tidak ada aturan baru, berhenti")
    return memori, urutan


# ---------------------------------------------------------------
# 4. Menampilkan alasan
# ---------------------------------------------------------------
def cetak_alasan(fakta, asal, memori, tingkat=1):
    """
    Menelusuri mundur: fakta ini dihasilkan aturan mana, dari syarat apa,
    dan jika syarat itu juga hasil aturan lain, telusuri lagi (rantai inferensi).
    """
    aturan = asal[fakta]
    terpenuhi = [syarat for syarat in aturan["jika"] if syarat in memori]
    spasi = "  " * tingkat
    print(f"{spasi}{fakta}  <- {aturan['id']} ({', '.join(terpenuhi)}) "
          f"[sumber: {aturan['sumber']}]")
    for syarat in terpenuhi:
        if syarat in asal:
            cetak_alasan(syarat, asal, memori, tingkat + 1)


# ---------------------------------------------------------------
# 5. Program utama
# ---------------------------------------------------------------
def main():
    kb = muat_kb(FILE_KB)
    daftar_aturan = kb["aturan"]

    print(kb["judul"])
    print("=" * len(kb["judul"]))

    # a. Tanya pengguna -> fakta awal
    fakta_dasar = cari_fakta_dasar(daftar_aturan)
    fakta_awal = tanya_pengguna(fakta_dasar)

    konflik = cari_konflik(kb, fakta_awal)
    if konflik:
        print("\nJawaban saling bertentangan:")
        print(f"  - {konflik[0]}")
        print(f"  - {konflik[1]}")
        print("Silakan jalankan ulang program dan jawab dengan konsisten.")
        return

    print("\nFakta awal:", ", ".join(fakta_awal) if fakta_awal else "(tidak ada)")
    print()

    # b. Jalankan forward chaining
    memori, urutan = forward_chaining(daftar_aturan, fakta_awal)
    asal = {aturan["maka"]: aturan for aturan in urutan}   # hasil -> aturan penghasilnya

    # c. Pisahkan kesimpulan akhir dari fakta antara
    kesimpulan = [aturan["maka"] for aturan in urutan if aturan["maka"] in kb["kesimpulan"]]

    print()
    if kesimpulan:
        for k in kesimpulan:
            print(f"Kesimpulan: {k}")
            print("Alasan:")
            cetak_alasan(k, asal, memori)
            print(f"Saran awal: {kb['kesimpulan'][k]}")
            print()
        # "sumber" tiap aturan berupa teks
        id_sumber = sorted({s.strip() for aturan in urutan for s in aturan["sumber"].split(",")})
        print("Sumber yang dipakai:")
        for s in id_sumber:
            print(f"  {s}: {kb['sumber'][s]}")
    else:
        print("Tidak ditemukan kesimpulan berdasarkan fakta yang diberikan.")
        fakta_antara = [aturan["maka"] for aturan in urutan]
        if fakta_antara:
            print("Fakta turunan yang diperoleh: " + ", ".join(fakta_antara))

    # d. Batas keberlakuan selalu ditampilkan
    print()
    print("Catatan (batas keberlakuan): " + kb["batas"])


if __name__ == "__main__":
    main()
