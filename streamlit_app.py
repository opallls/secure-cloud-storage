"""
streamlit_app.py
Web UI Secure Cloud File Storage dengan autentikasi login.
"""
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os, json
from datetime import datetime

from utils import ensure_rsa_keys, compute_sha256
from encrypt import hybrid_encrypt_bytes
from decrypt import hybrid_decrypt_file
from google_drive import get_drive_service, get_or_create_folder, upload_file, download_file, DEFAULT_FOLDER_NAME

PRIVATE_KEY_PATH = "credentials/rsa_private.pem"
PUBLIC_KEY_PATH = "credentials/rsa_public.pem"
MANIFEST_PATH = "results/manifest.json"
CONFIG_PATH = "credentials/auth_config.yaml"

st.set_page_config(
    page_title="Secure Cloud File Storage",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# ---------- CUSTOM CSS (modern glassmorphism theme) ----------
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    :root {
        --bg-0: #0a0c12;
        --bg-1: #0f1320;
        --panel: rgba(255,255,255,0.035);
        --panel-border: rgba(255,255,255,0.08);
        --accent-a: #22d3ee;
        --accent-b: #a78bfa;
        --accent-c: #34d399;
        --text-main: #e8eaf2;
        --text-dim: #8b90a3;
        --danger: #f87171;
    }

    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }

    .stApp {
        background:
            radial-gradient(1200px 600px at 10% -10%, rgba(34,211,238,0.10), transparent 60%),
            radial-gradient(1000px 500px at 100% 0%, rgba(167,139,250,0.10), transparent 55%),
            var(--bg-0);
        color: var(--text-main);
    }

    /* ---------- Hero header ---------- */
    .app-header {
        position: relative;
        padding: 2rem 2.2rem;
        background: linear-gradient(135deg, rgba(34,211,238,0.14) 0%, rgba(167,139,250,0.14) 55%, rgba(52,211,153,0.10) 100%);
        border: 1px solid var(--panel-border);
        border-radius: 20px;
        margin-bottom: 1.6rem;
        overflow: hidden;
        backdrop-filter: blur(6px);
    }
    .app-header::after {
        content: "";
        position: absolute; inset: 0;
        background: linear-gradient(90deg, var(--accent-a), var(--accent-b), var(--accent-c));
        opacity: 0.06;
        pointer-events: none;
    }
    .app-header h1 {
        margin: 0; font-size: 1.9rem; font-weight: 800; letter-spacing: -0.02em;
        background: linear-gradient(90deg, #ffffff, #cdeefc 60%, #d9d0ff);
        -webkit-background-clip: text; background-clip: text; color: transparent;
    }
    .app-header p { color: var(--text-dim); margin: 0.4rem 0 0 0; font-size: 0.95rem; }
    .header-badges { margin-top: 1rem; display: flex; gap: 0.6rem; flex-wrap: wrap; }
    .pill {
        display: inline-flex; align-items: center; gap: 0.4rem;
        padding: 0.32rem 0.8rem; border-radius: 999px;
        background: rgba(255,255,255,0.06); border: 1px solid var(--panel-border);
        font-size: 0.78rem; color: var(--text-dim); font-weight: 600;
    }

    /* ---------- Panels / forms / tabs ---------- */
    div[data-testid="stForm"], .stTabs [data-baseweb="tab-panel"] {
        background: var(--panel);
        border-radius: 18px;
        padding: 1.5rem;
        border: 1px solid var(--panel-border);
        backdrop-filter: blur(8px);
    }

    .stTabs [data-baseweb="tab-list"] { gap: 4px; background: transparent; }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600; padding: 0.65rem 1.3rem; border-radius: 12px 12px 0 0;
        color: var(--text-dim); background: rgba(255,255,255,0.02);
    }
    .stTabs [aria-selected="true"] {
        color: var(--text-main) !important;
        background: rgba(255,255,255,0.06) !important;
        border-bottom: 2px solid var(--accent-a) !important;
    }

    /* ---------- Status / result cards ---------- */
    .status-card {
        padding: 1rem 1.3rem; border-radius: 14px; margin: 0.7rem 0;
        font-weight: 500; display: flex; align-items: center; gap: 0.6rem;
        border: 1px solid transparent;
    }
    .status-ok   { background: rgba(52,211,153,0.10); color: #86efc9; border-color: rgba(52,211,153,0.3); }
    .status-fail { background: rgba(248,113,113,0.10); color: #ffb3b3; border-color: rgba(248,113,113,0.3); }

    /* ---------- File row card (dashboard) ---------- */
    .file-row {
        display: flex; align-items: center; justify-content: space-between;
        padding: 0.85rem 1.1rem; margin-bottom: 0.55rem;
        background: rgba(255,255,255,0.03); border: 1px solid var(--panel-border);
        border-radius: 14px; transition: all 0.15s ease;
    }
    .file-row:hover { background: rgba(255,255,255,0.06); border-color: rgba(34,211,238,0.35); }
    .file-name { font-weight: 600; color: var(--text-main); }
    .file-meta { color: var(--text-dim); font-size: 0.78rem; font-family: 'JetBrains Mono', monospace; }

    /* ---------- Buttons ---------- */
    div.stButton > button, div.stDownloadButton > button {
        border-radius: 10px; font-weight: 600; padding: 0.55rem 1.5rem;
        border: 1px solid var(--panel-border); transition: all 0.15s ease;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(90deg, var(--accent-a), var(--accent-b));
        border: none; color: #061018;
    }
    div.stButton > button[kind="primary"]:hover { filter: brightness(1.08); transform: translateY(-1px); }

    /* ---------- Uploader box ---------- */
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(255,255,255,0.02) !important;
        border: 1.5px dashed rgba(34,211,238,0.35) !important;
        border-radius: 14px !important;
    }

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b0e17 0%, #0a0c12 100%);
        border-right: 1px solid var(--panel-border);
    }
    .profile-card {
        display: flex; align-items: center; gap: 0.7rem;
        padding: 0.9rem; border-radius: 14px;
        background: rgba(255,255,255,0.04); border: 1px solid var(--panel-border);
        margin-bottom: 0.8rem;
    }
    .avatar-circle {
        width: 40px; height: 40px; border-radius: 50%;
        background: linear-gradient(135deg, var(--accent-a), var(--accent-b));
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; color: #061018; font-size: 1rem; flex-shrink: 0;
    }

    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.03); border: 1px solid var(--panel-border);
        border-radius: 14px; padding: 0.8rem 1rem;
    }

    hr, div[data-testid="stDivider"] { border-color: var(--panel-border) !important; }

    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

with open(CONFIG_PATH) as f:
    config = yaml.load(f, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)


def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH) as mf:
            return json.load(mf)
    return {}


def save_manifest(manifest):
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w") as mf:
        json.dump(manifest, mf, indent=2)


manifest_all = load_manifest()

# ---------- HEADER (selalu tampil) ----------
st.markdown(f"""
<div class="app-header">
    <h1>🔒 Secure Cloud File Storage</h1>
    <p>Enkripsi ujung-ke-ujung dengan AES-256 + RSA-2048, disimpan aman di Google Drive.</p>
    <div class="header-badges">
        <span class="pill">🧬 AES-256</span>
        <span class="pill">🔑 RSA-2048</span>
        <span class="pill">☁️ Google Drive API</span>
        <span class="pill">🧾 SHA-256 Integrity Check</span>
        <span class="pill">📁 {len(manifest_all)} file tersimpan</span>
    </div>
</div>
""", unsafe_allow_html=True)

authenticator.login(location="main")

if st.session_state["authentication_status"] is False:
    st.markdown('<div class="status-card status-fail">❌ Username atau password salah</div>', unsafe_allow_html=True)

elif st.session_state["authentication_status"] is None:
    st.info("👋 Silakan login untuk mengakses Secure Cloud File Storage")

else:
    # ---------- SIDEBAR ----------
    user_name = st.session_state["name"]
    initials = "".join([p[0] for p in user_name.split()[:2]]).upper()

    with st.sidebar:
        st.markdown(f"""
        <div class="profile-card">
            <div class="avatar-circle">{initials}</div>
            <div>
                <div style="font-weight:700; color:var(--text-main);">{user_name}</div>
                <div style="font-size:0.75rem; color:var(--text-dim);">🟢 Login pukul {datetime.now().strftime('%H:%M')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.metric("📁 Total file tersimpan", len(manifest_all))
        st.divider()
        st.caption("SISTEM")
        st.markdown(
            "<span class='pill'>🔐 AES-256-CBC</span>&nbsp;<span class='pill'>🔑 RSA-2048</span>",
            unsafe_allow_html=True,
        )
        st.divider()
        authenticator.logout("🚪 Logout", "sidebar")

    tab_upload, tab_download, tab_dashboard = st.tabs(
        ["⬆️  Upload & Encrypt", "⬇️  Download & Decrypt", "📊  Dashboard"]
    )

    # ================= TAB UPLOAD =================
    with tab_upload:
        st.subheader("Unggah & Enkripsi File Baru")
        col1, col2 = st.columns([2, 1])

        with col1:
            uploaded = st.file_uploader("Pilih file untuk dienkripsi", label_visibility="collapsed")
            if uploaded is not None:
                st.markdown(
                    f"<div class='file-meta'>📄 <b style='color:var(--text-main)'>{uploaded.name}</b> "
                    f"&nbsp;•&nbsp; {len(uploaded.getvalue())/1024:.1f} KB</div>",
                    unsafe_allow_html=True,
                )

        with col2:
            st.markdown("&nbsp;")
            encrypt_clicked = st.button("🔐 Encrypt & Upload", use_container_width=True, type="primary")

        if uploaded is not None and encrypt_clicked:
            progress = st.progress(0, text="Menyiapkan kunci RSA...")
            priv, pub = ensure_rsa_keys(PRIVATE_KEY_PATH, PUBLIC_KEY_PATH)
            file_data = uploaded.getvalue()
            original_hash = compute_sha256(file_data)

            progress.progress(35, text="Mengenkripsi dengan AES-256 + RSA-2048...")
            enc_key, enc_file, _ = hybrid_encrypt_bytes(file_data, pub)

            progress.progress(65, text="Mengunggah ke Google Drive...")
            service = get_drive_service()
            folder_id = get_or_create_folder(service, DEFAULT_FOLDER_NAME)
            file_id = upload_file(service, enc_file, uploaded.name + ".enc", folder_id=folder_id)
            key_id = upload_file(service, enc_key, uploaded.name + ".key.enc", folder_id=folder_id)

            progress.progress(90, text="Menyimpan manifest...")
            manifest = load_manifest()
            manifest[uploaded.name] = {
                "file_id": file_id,
                "key_id": key_id,
                "original_hash": original_hash,
                "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "size_kb": round(len(file_data) / 1024, 1),
            }
            save_manifest(manifest)
            progress.progress(100, text="Selesai!")

            st.markdown(f"""
            <div class="status-card status-ok">
                ✅ <b>{uploaded.name}</b> berhasil dienkripsi &amp; diunggah ke Google Drive
            </div>
            """, unsafe_allow_html=True)

            with st.expander("Lihat detail teknis"):
                st.code(f"file_id : {file_id}\nkey_id  : {key_id}\nhash    : {original_hash}", language="text")

    # ================= TAB DOWNLOAD =================
    with tab_download:
        st.subheader("Unduh & Dekripsi File")
        manifest = load_manifest()

        if not manifest:
            st.info("📭 Belum ada file yang diunggah.")
        else:
            col1, col2 = st.columns([2, 1])
            with col1:
                filename = st.selectbox("Pilih file", list(manifest.keys()), label_visibility="collapsed")
            with col2:
                decrypt_clicked = st.button("🔓 Download & Decrypt", use_container_width=True, type="primary")

            if decrypt_clicked:
                progress = st.progress(0, text="Mengunduh dari Google Drive...")
                entry = manifest[filename]
                priv, _ = ensure_rsa_keys(PRIVATE_KEY_PATH, PUBLIC_KEY_PATH)
                service = get_drive_service()
                enc_file = download_file(service, entry["file_id"])
                enc_key = download_file(service, entry["key_id"])

                progress.progress(55, text="Mendekripsi RSA + AES...")
                decrypted_data = hybrid_decrypt_file(enc_key, enc_file, priv)

                progress.progress(85, text="Memverifikasi integritas...")
                is_valid = compute_sha256(decrypted_data) == entry["original_hash"]
                progress.progress(100, text="Selesai!")

                if is_valid:
                    st.markdown(
                        '<div class="status-card status-ok">✅ Integritas file <b>TERJAGA</b> — '
                        'data identik dengan file asli</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div class="status-card status-fail">❌ Integritas file <b>GAGAL</b> — '
                        'data mungkin rusak/berubah</div>',
                        unsafe_allow_html=True,
                    )

                st.download_button(
                    f"💾 Simpan {filename}",
                    data=decrypted_data,
                    file_name=filename,
                    use_container_width=False,
                )

    # ================= TAB DASHBOARD =================
    with tab_dashboard:
        st.subheader("Ringkasan Penyimpanan")
        manifest = load_manifest()

        m1, m2, m3 = st.columns(3)
        total_size = sum(v.get("size_kb", 0) for v in manifest.values())
        m1.metric("📁 Total file", len(manifest))
        m2.metric("💾 Total ukuran", f"{total_size:.1f} KB")
        m3.metric("🔐 Status enkripsi", "Aktif" if manifest else "—")

        st.markdown("&nbsp;")

        if not manifest:
            st.info("📭 Belum ada file yang tersimpan. Unggah file pertamamu di tab **Upload & Encrypt**.")
        else:
            st.caption("DAFTAR FILE TERENKRIPSI")
            for fname, entry in manifest.items():
                uploaded_at = entry.get("uploaded_at", "—")
                size_kb = entry.get("size_kb", "—")
                st.markdown(f"""
                <div class="file-row">
                    <div>
                        <div class="file-name">📄 {fname}</div>
                        <div class="file-meta">🕒 {uploaded_at} &nbsp;•&nbsp; 📦 {size_kb} KB</div>
                    </div>
                    <div class="file-meta">SHA-256: {entry['original_hash'][:16]}...</div>
                </div>
                """, unsafe_allow_html=True)
