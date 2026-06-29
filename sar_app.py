import streamlit as st
import requests
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SAR Tracking Management System", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- TOP RIGHT LINK ---
st.markdown(
    """
    <style>
    .top-right-link {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        font-family: sans-serif;
    }
    </style>
    <div class="top-right-link">
        <a href="https://atn-tracking-dga-esd.streamlit.app/" target="_blank">🔗 ATN Portal</a>
    </div>
    """, 
    unsafe_allow_html=True
)

# --- SECURE CLOUD CONFIGURATION ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except (KeyError, FileNotFoundError):
    st.error("🔑 **Missing Database Configuration!**")
    st.stop()

HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Prefer": "return=representation"}

# --- DATABASE ENGINE FUNCTIONS ---
def fetch_all_sars():
    try:
        url = f"{SUPABASE_URL}/rest/v1/sar_trackers"
        response = requests.get(url, headers={**HEADERS, "Content-Type": "application/json"}, timeout=10)
        return response.json() if response.status_code == 200 else []
    except Exception: return []

def insert_sar_record(payload):
    url = f"{SUPABASE_URL}/rest/v1/sar_trackers"
    return requests.post(url, headers={**HEADERS, "Content-Type": "application/json"}, json=payload)

def update_sar_record(record_id, payload):
    url = f"{SUPABASE_URL}/rest/v1/sar_trackers?id=eq.{record_id}"
    return requests.patch(url, headers={**HEADERS, "Content-Type": "application/json"}, json=payload)

def delete_sar_record(record_id):
    url = f"{SUPABASE_URL}/rest/v1/sar_trackers?id=eq.{record_id}"
    return requests.delete(url, headers=HEADERS)

def authenticate_go(uid, pwd):
    url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{uid}&password=eq.{pwd}&role=eq.Group Officer (GO)"
    res = requests.get(url, headers={**HEADERS, "Content-Type": "application/json"}).json()
    return res[0] if res else None

# --- CONFIGURATION ARRAYS ---
CAB_OPTIONS = ["CSIR", "TDB", "RCB", "ANRF", "WII", "NTCA", "CAMPA", "CAQM", "CZA", "NBA", "SCTIMST"]
STATUS_OPTIONS = ["Accounts Not Received", "Field Audit in Progress", "Draft SAR sent to HQ", "SAR issued"]

# --- APP LAYOUT ---
st.title("🛡️ Separate Audit Report (SAR) Tracking Portal")
st.markdown("##### **DGA, CE (ESD) — Standalone Monitoring Engine**")
st.markdown("---")

if "go_authenticated" not in st.session_state:
    st.session_state["go_authenticated"] = False
    st.session_state["go_user"] = None

# --- SIDEBAR AUTHENTICATION ---
st.sidebar.header("🔐 Group Officer (GO) Gateway")
if not st.session_state["go_authenticated"]:
    go_uid = st.sidebar.text_input("GO Username ID")
    go_pwd = st.sidebar.text_input("GO Security Password", type="password")
    if st.sidebar.button("🔑 Access Updates Control"):
        go_account = authenticate_go(go_uid, go_pwd)
        if go_account:
            st.session_state["go_authenticated"] = True
            st.session_state["go_user"] = go_account["username"]
            st.rerun()
        else: st.sidebar.error("❌ Invalid Credentials.")
else:
    st.sidebar.success(f"Logged In: **{st.session_state['go_user']}**")
    if st.sidebar.button("🚪 Lock Control Console"):
        st.session_state["go_authenticated"] = False
        st.rerun()

# --- RENDERER ENGINE ---
def render_sar_html_table(all_records):
    if not all_records:
        st.info("No records found.")
        return
        
    sorted_sar = sorted(all_records, key=lambda x: x.get("cab", "").lower())
    
    html_rows = []
    for idx, item in enumerate(sorted_sar, start=1):
        receipt_dt_str = item.get("date_of_receipt")
        status_val = item.get("status", "Accounts Not Received")
        
        # Calculate Dates (DD-MM-YY)
        if receipt_dt_str and status_val != "Accounts Not Received":
            try:
                base_dt = datetime.strptime(receipt_dt_str, "%Y-%m-%d")
                t_field = (base_dt + timedelta(days=60)).strftime("%d-%m-%y")
                t_hq = (base_dt + timedelta(days=90)).strftime("%d-%m-%y")
                t_issue = (base_dt + timedelta(days=120)).strftime("%d-%m-%y")
                receipt_display = base_dt.strftime("%d-%m-%y")
            except: t_field = t_hq = t_issue = "Error"; receipt_display = receipt_dt_str
        else: receipt_display = "-"; t_field = t_hq = t_issue = "-"; status_val = "Accounts Not Received"
            
        def fmt_act(k):
            val = item.get(k)
            return datetime.strptime(val, "%Y-%m-%d").strftime("%d-%m-%y") if val else "-"

        badge_color = "#e74c3c" if status_val == "Accounts Not Received" else ("#3498db" if status_val == "Field Audit in Progress" else ("#f39c12" if status_val == "Draft SAR sent to HQ" else "#2cc357"))
        
        html_rows.append(f"""<tr style="border-bottom: 1px solid #e6e6e6;">
            <td style="padding: 8px; text-align: center;">{idx}</td>
            <td style="padding: 8px; text-align: left; font-weight: bold; color: #1f77b4;">{item['cab']}</td>
            <td style="padding: 8px; text-align: center;">{receipt_display}</td>
            <td style="padding: 8px; text-align: center; color: #d35400;">{t_field}</td>
            <td style="padding: 8px; text-align: center;">{fmt_act('actual_date_field')}</td>
            <td style="padding: 8px; text-align: center; color: #d35400;">{t_hq}</td>
            <td style="padding: 8px; text-align: center;">{fmt_act('actual_date_hq')}</td>
            <td style="padding: 8px; text-align: center; color: #d35400;">{t_issue}</td>
            <td style="padding: 8px; text-align: center;">{fmt_act('actual_date_issue')}</td>
            <td style="padding: 8px; text-align: center;"><span style="background-color: {badge_color}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px;">{status_val}</span></td>
        </tr>""")
        
    st.components.v1.html(f"""<div style="overflow-x: auto;"><table style="width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 13px;">
        <thead><tr style="background-color: #2c3e50; color: white;">
            <th style="padding: 10px; text-align: center;">S.No.</th><th style="padding: 10px; text-align: left;">CAB</th>
            <th style="padding: 10px; text-align: center;">Receipt</th><th style="padding: 10px; text-align: center;">Target: Field</th>
            <th style="padding: 10px; text-align: center;">Actual: Field</th><th style="padding: 10px; text-align: center;">Target: HQ</th>
            <th style="padding: 10px; text-align: center;">Actual: HQ</th><th style="padding: 10px; text-align: center;">Target: Issue</th>
            <th style="padding: 10px; text-align: center;">Actual: Issue</th><th style="padding: 10px; text-align: center;">Status</th>
        </tr></thead><tbody>{''.join(html_rows)}</tbody></table></div>""", height=500, scrolling=True)

# --- MAIN LOGIC ---
raw_sars = fetch_all_sars()

if st.session_state["go_authenticated"]:
    tabs = st.tabs(["📊 Dashboard", "📋 Add CAB", "✏️ Edit/Delete"])
    with tabs[0]: render_sar_html_table(raw_sars)
    with tabs[1]:
        with st.form("create_form", clear_on_submit=True):
            new_cab = st.selectbox("CAB", CAB_OPTIONS)
            status = st.selectbox("Status", STATUS_OPTIONS)
            if st.form_submit_button("Add"):
                res = insert_sar_record({"cab": new_cab, "status": status})
                if res.status_code in [200, 201]: st.rerun()
    with tabs[2]:
        edit_mapper = {f"{x['cab']}": x for x in raw_sars}
        target = st.selectbox("Select", list(edit_mapper.keys()))
        t_data = edit_mapper[target]
        if st.button("🗑️ Delete"):
            delete_sar_record(t_data["id"]); st.rerun()
else:
    render_sar_html_table(raw_sars)
