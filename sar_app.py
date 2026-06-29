import streamlit as st
import requests
from datetime import datetime, timedelta
import os
import json

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="SAR Tracking Management System", layout="wide", initial_sidebar_state="collapsed")

# --- TOP RIGHT LINK ---
st.markdown(
    """
    <style>
    .top-right-link { position: fixed; top: 20px; right: 20px; z-index: 1000; font-family: sans-serif; }
    </style>
    <div class="top-right-link"><a href="https://atn-tracking-dga-esd.streamlit.app/" target="_blank">🔗 ATN Portal</a></div>
    """, unsafe_allow_html=True
)

# --- SECURE CLOUD CONFIGURATION ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except (KeyError, FileNotFoundError):
    st.error("🔑 **Missing Database Configuration!** Please add `SUPABASE_URL` and `SUPABASE_KEY` to your Streamlit Cloud Secrets dashboard.")
    st.stop()

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Prefer": "return=representation"
}

# --- DATABASE ENGINE FUNCTIONS ---
def fetch_all_sars():
    """Queries the dedicated SAR database partition table securely with connection safeguards"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/sar_trackers"
        response = requests.get(url, headers={**HEADERS, "Content-Type": "application/json"}, timeout=10)
        return response.json() if response.status_code == 200 else []
    except requests.exceptions.ConnectionError:
        st.error("📡 **Database Connection Timeout!** Please check if your Supabase project is paused or your secrets configurations are invalid.")
        return []
    except Exception as e:
        print(f"General fetch fault log: {e}")
        return []

def insert_sar_record(payload):
    url = f"{SUPABASE_URL}/rest/v1/sar_trackers"
    return requests.post(url, headers={**HEADERS, "Content-Type": "application/json"}, json=payload)

def update_sar_record(record_id, payload):
    url = f"{SUPABASE_URL}/rest/v1/sar_trackers?id=eq.{record_id}"
    return requests.patch(url, headers={**HEADERS, "Content-Type": "application/json"}, json=payload)

def delete_sar_record(record_id):
    """Deletes an active tracking record cleanly via unique primary identifiers"""
    url = f"{SUPABASE_URL}/rest/v1/sar_trackers?id=eq.{record_id}"
    return requests.delete(url, headers=HEADERS)

def authenticate_go(uid, pwd):
    """Authenticates the Group Officer against your centralized user directory matrix"""
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

# Initialize authentication states cleanly
if "go_authenticated" not in st.session_state:
    st.session_state["go_authenticated"] = False
    st.session_state["go_user"] = None

# --- SIDEBAR AUTHENTICATION INTERFACE ---
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
        else:
            st.sidebar.error("❌ Invalid Credentials or Account lacks GO administrative rights.")
else:
    st.sidebar.success(f"Logged In: **{st.session_state['go_user']}** (Group Officer)")
    if st.sidebar.button("🚪 Lock Control Console"):
        st.session_state["go_authenticated"] = False
        st.session_state["go_user"] = None
        st.rerun()

# --- RAW HTML SAR RENDERER ENGINE ---
def render_sar_html_table(all_records):
    """Compiles an alphabetized clean HTML table for SAR tracking metrics"""
    if not all_records:
        st.info("No records found inside tracking partitions.")
        return
        
    sorted_sar = sorted(all_records, key=lambda x: x.get("cab", "").lower())
    
    html_rows = []
    for idx, item in enumerate(sorted_sar, start=1):
        receipt_dt_str = item.get("date_of_receipt")
        status_val = item.get("status", "Accounts Not Received")
        
        # Target Date calculations
        if receipt_dt_str and status_val != "Accounts Not Received":
            try:
                base_dt = datetime.strptime(receipt_dt_str, "%Y-%m-%d")
                t_field = (base_dt + timedelta(days=60)).strftime("%d-%m-%y")
                t_hq = (base_dt + timedelta(days=90)).strftime("%d-%m-%y")
                t_issue = (base_dt + timedelta(days=120)).strftime("%d-%m-%y")
                receipt_display = base_dt.strftime("%d-%m-%y")
            except:
                t_field = t_hq = t_issue = "Date Error"
                receipt_display = receipt_dt_str
        else:
            receipt_display = "-"
            t_field = t_hq = t_issue = "-"
            status_val = "Accounts Not Received"
            
        def get_fmt_date(val):
            if val:
                try: return datetime.strptime(val, "%Y-%m-%d").strftime("%d-%m-%y")
                except: return val
            return ""

        act_field = get_fmt_date(item.get("actual_date_field")) if status_val in ["Field Audit in Progress", "Draft SAR sent to HQ", "SAR issued"] else ""
        act_hq = get_fmt_date(item.get("actual_date_hq")) if status_val in ["Draft SAR sent to HQ", "SAR issued"] else ""
        act_issue = get_fmt_date(item.get("actual_date_issue")) if status_val == "SAR issued" else ""
        
        badge_color = "#e74c3c" if status_val == "Accounts Not Received" else ("#3498db" if status_val == "Field Audit in Progress" else ("#f39c12" if status_val == "Draft SAR sent to HQ" else "#2cc357"))
        
        row_string = f"""<tr style="border-bottom: 1px solid #e6e6e6;">
            <td style="padding: 8px; text-align: center;">{idx}</td>
            <td style="padding: 8px; text-align: left; font-weight: bold; color: #1f77b4;">{item['cab']}</td>
            <td style="padding: 8px; text-align: center;">{receipt_display}</td>
            <td style="padding: 8px; text-align: center; color: #d35400;">{t_field}</td>
            <td style="padding: 8px; text-align: center; font-weight: 500;">{act_field}</td>
            <td style="padding: 8px; text-align: center; color: #d35400;">{t_hq}</td>
            <td style="padding: 8px; text-align: center; font-weight: 500;">{act_hq}</td>
            <td style="padding: 8px; text-align: center; color: #d35400;">{t_issue}</td>
            <td style="padding: 8px; text-align: center; font-weight: 500;">{act_issue}</td>
            <td style="padding: 8px; text-align: center;"><span style="background-color: {badge_color}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; white-space: nowrap;">{status_val}</span></td>
        </tr>"""
        html_rows.append(row_string)
        
    full_html_table = f"""<div style="overflow-x: auto; width: 100%; margin-top: 10px;">
        <table style="width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 13px; color: #333;">
            <thead>
                <tr style="background-color: #2c3e50; color: white; border-bottom: 2px solid #34495e;">
                    <th style="padding: 10px; text-align: center;">S.No.</th>
                    <th style="padding: 10px; text-align: left;">CAB</th>
                    <th style="padding: 10px; text-align: center;">Receipt</th>
                    <th style="padding: 10px; text-align: center;">Target: Field</th>
                    <th style="padding: 10px; text-align: center;">Actual: Field</th>
                    <th style="padding: 10px; text-align: center;">Target: HQ</th>
                    <th style="padding: 10px; text-align: center;">Actual: HQ</th>
                    <th style="padding: 10px; text-align: center;">Target: Issue</th>
                    <th style="padding: 10px; text-align: center;">Actual: Issue</th>
                    <th style="padding: 10px; text-align: center;">Status</th>
                </tr>
            </thead>
            <tbody>{"".join(html_rows)}</tbody>
        </table>
    </div>"""
    
    st.components.v1.html(full_html_table, height=500, scrolling=True)

# --- MAIN RENDER LOGIC ---
raw_sars = fetch_all_sars()

if st.session_state["go_authenticated"]:
    go_tab_view, go_tab_create, go_tab_update = st.tabs(["📊 Master Tracking Dashboard", "📋 Add Fresh Autonomous Body (CAB)", "✏️ Edit & Overwrite Pipeline Data"])
    with go_tab_view:
        st.markdown("### 📋 Status of SARs O/o DGA, CE (ESD)")
        render_sar_html_table(raw_sars)
    with go_tab_create:
        with st.form("sar_create_form", clear_on_submit=True):
            new_cab = st.selectbox("Select Target CAB", CAB_OPTIONS)
            status_flow = st.selectbox("Select Workflow Status Trigger", STATUS_OPTIONS)
            new_receipt_dt = st.date_input("Date of Receipt of Account", value=datetime.today().date()) if status_flow != "Accounts Not Received" else None
            if st.form_submit_button("🚀 Add CAB to Master Log"):
                create_payload = {"cab": new_cab, "date_of_receipt": str(new_receipt_dt) if new_receipt_dt else None, "status": status_flow}
                res = insert_sar_record(create_payload)
                if res.status_code in [200, 201]: st.rerun()
    with go_tab_update:
        edit_mapper = {f"CAB: {x['cab']} | Status: {x.get('status', 'Accounts Not Received')}": x for x in raw_sars}
        selected = st.selectbox("Select Target Record to Manage:", list(edit_mapper.keys()))
        target_record = edit_mapper[selected]
        if st.button(f"🗑️ Delete Tracking Data for {target_record['cab']} Permanent"):
            delete_sar_record(target_record["id"]); st.rerun()
else:
    render_sar_html_table(raw_sars)
