import streamlit as st
import requests
from datetime import datetime, timedelta
import os
import json

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
        st.error("📡 **Database Connection Timeout!** The app couldn't reach your Supabase server. Please verify your `SUPABASE_URL` in secrets or check if your Supabase project is paused.")
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
    url = f"{SUPABASE_URL}/rest/v1/sar_trackers?id=eq.{record_id}"
    return requests.delete(url, headers=HEADERS)

def authenticate_go(uid, pwd):
    """Authenticates the Group Officer against your centralized user directory matrix"""
    url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{uid}&password=eq.{pwd}&role=eq.Group Officer (GO)"
    res = requests.get(url, headers={**HEADERS, "Content-Type": "application/json"}).json()
    return res[0] if res else None

# --- CONFIGURATION ARRAYS ---
CAB_OPTIONS = ["CSIR", "TDB", "RCB", "ANRF", "WII", "NTCA", "CAMPA", "CAQM", "CZA", "NBA", "SCTIMST"]

# --- APP LAYOUT ---
st.set_page_config(page_title="SAR Tracking Management System", layout="wide")

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

# --- MAIN RENDER LOGIC ---
if st.session_state["go_authenticated"]:
    go_tab_view, go_tab_create, go_tab_update = st.tabs([
        "📊 Master Tracking Dashboard",
        "📋 Add Fresh Autonomous Body (CAB)",
        "✏️ Edit & Overwrite Pipeline Data"
    ])
else:
    # Public layout mapping logic
    go_tab_view = st.container()
    st.info("ℹ️ Viewing public read-only Master Dashboard stream. Administrative credentials required to update records.")

# --- RAW HTML SAR RENDERER ENGINE ---
def render_sar_html_table(all_records):
    """Compiles a case-insensitive alphabetized table for SAR tracking metrics without hover copy tags"""
    if not all_records:
        return
        
    sorted_sar = sorted(all_records, key=lambda x: x.get("cab", "").lower())
    
    html_rows = ""
    for idx, item in enumerate(sorted_sar, start=1):
        receipt_dt_str = item.get("date_of_receipt")
        
        if receipt_dt_str:
            try:
                base_dt = datetime.strptime(receipt_dt_str, "%Y-%m-%d")
                t_field = (base_dt + timedelta(days=60)).strftime("%Y-%m-%d")
                t_hq = (base_dt + timedelta(days=90)).strftime("%Y-%m-%d")
                t_issue = (base_dt + timedelta(days=120)).strftime("%Y-%m-%d")
                receipt_display = receipt_dt_str
            except:
                t_field = t_hq = t_issue = "Date Error"
                receipt_display = receipt_dt_str
        else:
            receipt_display = "Account Not received"
            t_field = t_hq = t_issue = "Pending Initialization"
            
        act_field = item.get("actual_date_field") if item.get("actual_date_field") else "Pending"
        act_hq = item.get("actual_date_hq") if item.get("actual_date_hq") else "Pending"
        act_issue = item.get("actual_date_issue") if item.get("actual_date_issue") else "Pending"
        
        html_rows += f"""
        <tr style="border-bottom: 1px solid #e6e6e6;">
            <td style="padding: 8px; text-align: left;">{idx}</td>
            <td style="padding: 8px; text-align: left; font-weight: bold; color: #1f77b4;">{item['cab']}</td>
            <td style="padding: 8px; text-align: left; background-color: #fdfefe;">{receipt_display}</td>
            <td style="padding: 8px; text-align: left; color: #d35400;">{t_field}</td>
            <td style="padding: 8px; text-align: left; font-weight: 500;">{act_field}</td>
            <td style="padding: 8px; text-align: left; color: #d35400;">{t_hq}</td>
            <td style="padding: 8px; text-align: left; font-weight: 500;">{act_hq}</td>
            <td style="padding: 8px; text-align: left; color: #d35400;">{t_issue}</td>
            <td style="padding: 8px; text-align: left; font-weight: 500;">{act_issue}</td>
        </tr>
        """
        
    html_table = f"""
    <div style="overflow-x: auto; width: 100%; margin-top: 10px;">
        <table style="width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 13px; color: #333;">
            <thead>
                <tr style="background-color: #2c3e50; color: white; border-bottom: 2px solid #34495e;">
                    <th style="padding: 10px; text-align: left; font-weight: bold;">S.No.</th>
                    <th style="padding: 10px; text-align: left; font-weight: bold;">CAB</th>
                    <th style="padding: 10px; text-align: left; font-weight: bold;">Date of Receipt of Account</th>
                    <th style="padding: 10px; text-align: left; font-weight: bold;">Target Date: Field Audit</th>
                    <th style="padding: 10px; text-align: left; font-weight: bold;">Actual Date: Field Audit</th>
                    <th style="padding: 10px; text-align: left; font-weight: bold;">Target Date: Draft to HQ</th>
                    <th style="padding: 10px; text-align: left; font-weight: bold;">Actual Date: Draft to HQ</th>
                    <th style="padding: 10px; text-align: left; font-weight: bold;">Target Date: Issue of SAR</th>
                    <th style="padding: 10px; text-align: left; font-weight: bold;">Actual Date: Issue of SAR</th>
                </tr>
            </thead>
            <tbody>
                {html_rows}
            </tbody>
        </table>
    </div>
    """
    st.markdown(html_table, unsafe_allow_html=True)

# --- TAB 1: MASTER DASHBOARD STREAM ---
with go_tab_view:
    # --- UPDATED HEADER INTERFACE ---
    st.subheader("📋 Status of SARs O/o DGA, CE (ESD)")
    raw_sars = fetch_all_sars()
    render_sar_html_table(raw_sars)

# --- GO ONLY RESTRICTED EDITING SECTIONS ---
if st.session_state["go_authenticated"]:
    # --- TAB 2: INSERT NEW AUTONOMOUS BODY RECORDS ---
    with go_tab_create:
        st.subheader("📋 Initialize New Central Autonomous Body Tracker")
        with st.form("sar_create_form", clear_on_submit=True):
            new_cab = st.selectbox("Select Target CAB", CAB_OPTIONS)
            
            receipt_mode = st.radio("Initial Account Status:", ["Account Not received", "Received"], index=0, key="new_receipt_mode")
            if receipt_mode == "Received":
                new_receipt_dt = st.date_input("Select Ingestion Date of Receipt", value=datetime.today().date())
            else:
                new_receipt_dt = None
                
            if st.form_submit_button("🚀 Add CAB to Master Log"):
                create_payload = {
                    "cab": new_cab,
                    "date_of_receipt": str(new_receipt_dt) if new_receipt_dt else None,
                    "actual_date_field": None,
                    "actual_date_hq": None,
                    "actual_date_issue": None
                }
                res = insert_sar_record(create_payload)
                if res.status_code in [200, 201]:
                    st.success(f"Successfully initialized standalone SAR matrix for {new_cab}!")
                    st.rerun()
                else:
                    st.error("Database connection fault encountered writing payload.")

    # --- TAB 3: UPDATE OR OVERWRITE EXISTING ENTRIES ---
    with go_tab_update:
        st.subheader("✏️ Administrative Overwrite & Modification Deck")
        active_records = fetch_all_sars()
        
        if not active_records:
            st.info("No records currently initialized to update.")
        else:
           edit_mapper = {f"CAB: {x['cab']} | Received: {x.get('date_of_receipt', 'Account Not received')}": x for x in active_records}
            selected_edit_label = st.selectbox("Select Target Record to Modify:", list(edit_mapper.keys()))
            target_record = edit_mapper[selected_edit_label]
            
            with st.form("sar_edit_form"):
                st.markdown(f"Modifying Entry Parameters for: **{target_record['cab']}**")
                
                ec1, ec2 = st.columns(2)
                with ec1:
                    updated_cab = st.selectbox("CAB Assignment", CAB_OPTIONS, index=CAB_OPTIONS.index(target_record['cab']) if target_record['cab'] in CAB_OPTIONS else 0)
                    edit_receipt_mode = st.radio("Current Account Status", ["Account Not received", "Received"], index=1 if target_record.get("date_of_receipt") else 0, key="edit_receipt_mode")
                    
                    if edit_receipt_mode == "Received":
                        saved_dt_str = target_record.get("date_of_receipt", datetime.today().strftime("%Y-%m-%d"))
                        try: default_receipt_dt = datetime.strptime(saved_dt_str, "%Y-%m-%d").date()
                        except: default_receipt_dt = datetime.today().date()
                        updated_receipt_dt = st.date_input("Date of Receipt of Account", value=default_receipt_dt)
                    else:
                        updated_receipt_dt = None
                        
                with ec2:
                    def parse_saved_date_or_none(key_name):
                        if target_record.get(key_name):
                            try: return datetime.strptime(target_record[key_name], "%Y-%m-%d").date()
                            except: return None
                        return None
                        
                    v_field = parse_saved_date_or_none("actual_date_field")
                    v_hq = parse_saved_date_or_none("actual_date_hq")
                    v_issue = parse_saved_date_or_none("actual_date_issue")
                    
                    updated_field_dt = st.date_input("Actual Date of Completion of Field Audit", value=v_field if v_field else None)
                    updated_hq_dt = st.date_input("Actual Date of Sending Draft SAR to HQ", value=v_hq if v_hq else None)
                    updated_issue_dt = st.date_input("Actual Date of Issue of SAR", value=v_issue if v_issue else None)
                    
                col_btn1, col_btn2 = st.columns([4, 1])
                with col_btn1:
                    if st.form_submit_button("💾 Save Changes & Update Records"):
                        update_payload = {
                            "cab": updated_cab,
                            "date_of_receipt": str(updated_receipt_dt) if updated_receipt_dt else None,
                            "actual_date_field": str(updated_field_dt) if updated_field_dt else None,
                            "actual_date_hq": str(updated_hq_dt) if updated_hq_dt else None,
                            "actual_date_issue": str(updated_issue_dt) if updated_issue_dt else None
                        }
                        update_sar_record(target_record["id"], update_payload)
                        st.success("Record parameters securely updated in cloud partition!")
                        st.rerun()
                        
                with col_btn2:
                    st.write("")
