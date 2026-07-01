# Prompt untuk Claude — Project baru "Overview Kilang"

> Salin seluruh teks di bawah ini sebagai prompt awal ke Claude, dan lampirkan
> semua file di folder ini (atau zip-nya). Ganti bagian **[isi]** sesuai kondisi Anda.

---

Saya ingin kamu men-setup dan mengembangkan sebuah project web **standalone khusus
"Overview Kilang"** — dashboard strategis reliability kilang Pertamina untuk VP
Reliability / Operation Director. Kode awal yang sudah berfungsi saya lampirkan;
tugasmu menjadikannya project mandiri yang jalan penuh dengan **data live dari
database**, lalu memperbaiki/melengkapi bagian yang masih perlu.

## Stack (WAJIB dipertahankan — jangan ganti ke React/Next/Tailwind)
- **Backend:** Python 3.11, **FastAPI**, **Jinja2** templates
- **DB:** **PostgreSQL** (via `psycopg`), koneksi dari `DATABASE_URL` di `.env`
- **Frontend:** HTML Jinja + **CSS biasa** (vanilla), sedikit JS vanilla. Tidak
  ada npm/bundler. Peta Indonesia = SVG statis (bukan library peta).

## File yang saya lampirkan (sudah jalan)
- `main.py` (FastAPI + routes), `db.py` (get_conn), `executive_data.py` (layer
  data live), `executive_mock.py` (skeleton/fallback)
- `templates/`: `base.html`, `executive.html`, `_exec_components.html`
  (macro), `_exec_map.html` (peta SVG), `drilldown.html`
- `static/css/`: `style.css`, `executive.css` · `static/js/`: `app.js`, `executive.js`
- `requirements.txt`, `Procfile`, `.env.example`, `README.md`

Jalankan: `pip install -r requirements.txt` → set `DATABASE_URL` → `uvicorn main:app --reload`
→ buka `/dashboard/executive`.

## Konsep data (penting)
Semua angka dihitung di `executive_data.get_executive_snapshot(period)` dari tabel
reliability berikut. Layer ini **defensif**: tanggal & angka diparse di Python
(tahan `dd/mm/yyyy`, desimal koma `94,5`, ribuan titik `1.000.000.000`), string RU
dinormalisasi (`RU II`/`RU-2`/`vi`/`Balikpapan` → kode internal), dan tiap bagian
yang gagal/kosong otomatis **fallback ke mock**. Tab **Metodologi** &
`/dashboard/executive/debug` menampilkan sumber + kolom asli yang terdeteksi.

### 7 unit kilang
RU II Dumai, RU III Plaju, RU IV Cilacap, RU V Balikpapan, RU VI Balongan,
RU VII Kasim, TPPI Tuban.

### Tabel sumber (PostgreSQL) & pemakaian
| KPI / Bagian | Tabel | Kolom yang dipakai (konfirmasi kalau beda) |
|---|---|---|
| PLO / Sertifikasi | `atg_monitoring`, `metering_monitoring`, `readiness_jetty`, `readiness_spm` | `date_expired_atg`, `date_expired_metering`, `expired_tuks`, `expired_laik_operasi`, `refinery_unit` |
| RKAP & Program % | `irkap_program` | `status_prognosa`, `finish_plan`, `refinery_unit`, `program_kerja` |
| Alerts / Reliability Hotspots | `bad_actor_monitoring`(`ru`,`status`), `icu_monitoring`(`ru`,`icu_status`), `zero_clamp`(`ru`,`status`), `power_stream`(`refinery_unit`,`status_operation`) | — |
| Program Execution | `workplan_jetty`,`workplan_tank`,`spm_workplan`(`status_rtl`,`target`), `inspection_plan`(`due_date`,`actual_date`) | — |
| Readiness cards | `bad_actor_monitoring`, `icu_monitoring`, `zero_clamp`, `boc`, `inspection_plan` | — |
| **PAF** (asumsi) | `paf` | target=??, realisasi=?? — **KONFIRMASI** |
| **OA** (asumsi) | `monitoring_operasi` | kolom availability=?? — **KONFIRMASI** |
| **Kapasitas/util** (asumsi) | `monitoring_operasi` | design=??, actual=?? — **KONFIRMASI** |
| **Maintenance Spend** (asumsi) | `anggaran_maintenance` | plan=??, aktual=?? — **KONFIRMASI** |
| Data Freshness | semua tabel | COUNT(*) + kolom tanggal |

Tabel yang belum di-wire (opsional lanjut): `issue_paf`, `rcps`, `rcps_rekomendasi`,
`program_kerja_atg`, `rotor_monitoring`, `jumlah_eqp_utl`, `critical_eqp_utl`,
`critical_eqp_prim_sec`, `pipeline_inspection`, `tkdn`, `monitoring_pr`.

### Rumus ringkas (detail lengkap ada di tab Metodologi / `executive_data.py`)
- **OA/PAF**: rata-rata per RU → nasional rata-rata antar RU. Status PAF: ≥94 Healthy · 88–93 Watch · <88 Critical.
- **RKAP**: %=selesai/total; overdue=`finish_plan`<tanggal-acuan & belum selesai.
- **Spend**: Σaktual/Σplan; <80% Under-spend, 100–105% Execution Risk, >105% Over-spend, selain itu On Plan.
- **PLO**: bucket expiry vs tanggal-acuan (Expired / ≤30 hari / ≤90 hari).
- **Periode**: bulan → akhir bulan sebagai tanggal-acuan; `YTD` → hari ini/akhir tahun. Mengubah periode mengubah PLO/overdue/severity.

## Tugasmu
1. **Setup** project ini agar jalan (venv, requirements, `.env`), pastikan
   `/dashboard/executive` tampil.
2. **Verifikasi ke DB asli**: buka `/dashboard/executive/debug` dan tab Metodologi;
   pastikan tiap KPI benar-benar **Live** (bukan mock). Untuk kolom yang tertulis
   `❓ tidak terdeteksi` atau angkanya janggal, **konfirmasi nama kolom aslinya**
   dan pin di `executive_data.py` (fungsi `_apply_paf`/`_capacity`/`_oa`/`_spend`
   dan heuristik `_pick`).
   > Struktur DB saya: **[tempel di sini output `\d paf`, `\d monitoring_operasi`,
   > `\d anggaran_maintenance`, atau JSON dari `/dashboard/executive/debug`]**
3. **Lengkapi** panel yang masih pakai contoh: wire `issue_paf`, `rcps_rekomendasi`,
   `program_kerja_atg`, `rotor_monitoring`, `critical_eqp_utl` ke panel
   Reliability/Program/Readiness bila datanya ada.
4. **Jaga prinsip**: tetap defensif (fallback ke mock, jangan bikin error),
   period-aware, **jangan mengarang angka** — kalau kolom tak jelas, tandai
   `❓` di Metodologi dan tanya saya.

## Preferensi
- Tema **terang** (light), gaya enterprise, rapi & kompak. Warna status:
  hijau=Healthy, kuning=Watch, merah=Critical, abu=No data.
- Semua komponen reusable (macro Jinja). Data live terpusat di `executive_data.py`.
- Bahasa UI campur ID/EN mengikuti yang sudah ada. Konfirmasi ke saya dalam Bahasa Indonesia.

Mulai dengan: ringkas apa yang sudah ada, jalankan, lalu tunjukkan hasil
`/dashboard/executive/debug` dan minta saya konfirmasi 4 kolom asumsi di atas.
