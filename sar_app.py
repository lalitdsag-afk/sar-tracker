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

# --- RAW HTML SAR RENDERER ENGINE ---
def render_sar_html_table(all_records):
    """Compiles an alphabetized clean HTML table for SAR tracking metrics without whitespace leaks"""
    if not all_records:
        st.info("No records found inside tracking partitions.")
        return
        
    sorted_sar = sorted(all_records, key=lambda x: x.get("cab", "").lower())
    
    html_rows = []
    for idx, item in enumerate(sorted_sar, start=1):
        receipt_dt_str = item.get("date_of_receipt")
        status_val = item.get("status", "Accounts Not Received")
        
        # Target Date calculations based on the Date of Receipt parameter
        if receipt_dt_str and status_val != "Accounts Not Received":
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
            t_field = t_hq = t_issue = ""
            status_val = "Accounts Not Received"
            
        # Determine cell output text content dynamically using your status gating laws
        act_field = item.get("actual_date_field") if item.get("actual_date_field") and status_val in ["Field Audit in Progress", "Draft SAR sent to HQ", "SAR issued"] else ""
        act_hq = item.get("actual_date_hq") if item.get("actual_date_hq") and status_val in ["Draft SAR sent to HQ", "SAR issued"] else ""
        act_issue = item.get("actual_date_issue") if item.get("actual_date_issue") and status_val == "SAR issued" else ""
        
        # Workflow status colors configuration layout mapping
        badge_color = "#e74c3c" if status_val == "Accounts Not Received" else ("#3498db" if status_val == "Field Audit in Progress" else ("#f39c12" if status_val == "Draft SAR sent to HQ" else "#2cc357"))
        
        row_string = f"""<tr style="border-bottom: 1px solid #e6e6e6;">
            <td style="padding: 8px; text-align: left;">{idx}</td>
            <td style="padding: 8px; text-align: left; font-weight: bold; color: #1f77b4;">{item['cab']}</td>
            <td style="padding: 8px; text-align: left;">{receipt_display}</td>
            <td style="padding: 8px; text-align: left; color: #d35400;">{t_field}</td>
            <td style="padding: 8px; text-align: left; font-weight: 500;">{act_field}</td>
            <td style="padding: 8px; text-align: left; color: #d35400;">{t_hq}</td>
            <td style="padding: 8px; text-align: left; font-weight: 500;">{act_hq}</td>
            <td style="padding: 8px; text-align: left; color: #d35400;">{t_issue}</td>
            <td style="padding: 8px; text-align: left; font-weight: 500;">{act_issue}</td>
            <td style="padding: 8px; text-align: left;"><span style="background-color: {badge_color}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; white-space: nowrap;">{status_val}</span></td>
        </tr>"""
        html_rows.append(row_string)
        
    combined_rows = "".join(html_rows)
    
    full_html_table = f"""<div style="overflow-x: auto; width: 100%; margin-top: 10px;">
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
                    <th style="padding: 10px; text-align: left; font-weight: bold;">Workflow Status</th>
                </tr>
            </thead>
            <tbody>
                {combined_rows}
            </tbody>
        </table>
    </div>"""
    
    st.components.v1.html(full_html_table, height=500, scrolling=True)

# --- MAIN RENDER LOGIC SWITCHBOARD ---
raw_sars = fetch_all_sars()

if st.session_state["go_authenticated"]:
    go_tab_view, go_tab_create, go_tab_update = st.tabs([
        "📊 Master Tracking Dashboard",
        "📋 Add Fresh Autonomous Body (CAB)",
        "✏️ Edit & Overwrite Pipeline Data"
    ])
    
    with go_tab_view:
        st.markdown("### 📋 Status of SARs O/o DGA, CE (ESD)")
        render_sar_html_table(raw_sars)
else:
    st.info("ℹ️ Viewing public read-only Master Dashboard stream. Administrative credentials required to update records.")
    st.markdown("### 📋 Status of SARs O/o DGA, CE (ESD)")
    render_sar_html_table(raw_sars)

# --- GO ONLY RESTRICTED EDITING SECTIONS ---
if st.session_state["go_authenticated"]:
    # --- TAB 2: INSERT NEW AUTONOMOUS BODY RECORDS (WITH ONE-ENTRY DUP GUARDRAIL) ---
    with go_tab_create:
        st.subheader("📋 Initialize New Central Autonomous Body Tracker")
        
        # Build index mapping list of existing CAB entries in the database
        existing_cabs = [item["cab"].strip().upper() for item in raw_sars if "cab" in item]
        
        with st.form("sar_create_form", clear_on_submit=True):
            new_cab = st.selectbox("Select Target CAB", CAB_OPTIONS)
            status_flow = st.selectbox("Select Workflow Status Trigger", STATUS_OPTIONS, index=0)
            
            new_receipt_dt = None
            if status_flow != "Accounts Not Received":
                new_receipt_dt = st.date_input("Date of Receipt of Account", value=datetime.today().date())
                
            if st.form_submit_button("🚀 Add CAB to Master Log"):
                # Enforce unique constraint lookup step
                if new_cab.strip().upper() in existing_cabs:
                    st.error(f"❌ **Duplicate Entry Blocked!** A tracker for **{new_cab}** already exists. Please navigate to the 'Edit & Overwrite Data' tab to modify this record.")
                else:
                    final_status = "Accounts Not Received" if not new_receipt_dt else status_flow
                    create_payload = {
                        "cab": new_cab,
                        "date_of_receipt": str(new_receipt_dt) if new_receipt_dt else None,
                        "actual_date_field": None,
                        "actual_date_hq": None,
                        "actual_date_issue": None,
                        "status": final_status
                    }
                    res = insert_sar_record(create_payload)
                    if res.status_code in [200, 201]:
                        st.success(f"Successfully initialized standalone SAR matrix for {new_cab}!")
                        st.rerun()
                    else:
                        st.error("Database connection fault encountered writing payload.")

    # --- TAB 3: UPDATE OR OVERWRITE EXISTING ENTRIES (WITH DELETION INTEGRATED) ---
    with go_tab_update:
        st.subheader("✏️ Administrative Overwrite & Modification Deck")
        
        if not raw_sars:
            st.info("No records currently initialized to update.")
        else:
            # Format and select entries
            edit_mapper = {f"CAB: {x['cab']} | Status: {x.get('status', 'Accounts Not Received')}": x for x in raw_sars}
            selected_edit_label = st.selectbox("Select Target Record to Manage:", list(edit_mapper.keys()))
            target_record = edit_mapper[selected_edit_label]
            
            current_status = target_record.get("status", "Accounts Not Received")
            saved_receipt_str = target_record.get("date_of_receipt")
            
            # Form wrapper block for data edits
            with st.form("sar_edit_form"):
                st.markdown(f"Modifying Entry Parameters for: **{target_record['cab']}**")
                
                updated_cab = st.selectbox("CAB Assignment", CAB_OPTIONS, index=CAB_OPTIONS.index(target_record['cab']) if target_record['cab'] in CAB_OPTIONS else 0)
                updated_status = st.selectbox("Update Workflow Operational Status", STATUS_OPTIONS, index=STATUS_OPTIONS.index(current_status) if current_status in STATUS_OPTIONS else 0)
                
                def parse_saved_date_or_none(key_name):
                    if target_record.get(key_name):
                        try: return datetime.strptime(target_record[key_name], "%Y-%m-%d").date()
                        except: return None
                    return None
                
                updated_receipt_dt = None
                updated_field_dt = None
                updated_hq_dt = None
                updated_issue_dt = None
                
                if updated_status != "Accounts Not Received":
                    st.markdown("---")
                    st.markdown("##### 📅 Active Stage Timeline Milestones")
                    ec1, ec2 = st.columns(2)
                    
                    with ec1:
                        try: r_init = datetime.strptime(saved_receipt_str, "%Y-%m-%d").date() if saved_receipt_str else datetime.today().date()
                        except: r_init = datetime.today().date()
                        updated_receipt_dt = st.date_input("Date of Receipt of Account", value=r_init)
                        
                        if updated_status in ["Field Audit in Progress", "Draft SAR sent to HQ", "SAR issued"]:
                            updated_field_dt = st.date_input("Actual Date of Completion of Field Audit", value=parse_saved_date_or_none("actual_date_field"))
                            
                    with ec2:
                        if updated_status in ["Draft SAR sent to HQ", "SAR issued"]:
                            updated_hq_dt = st.date_input("Actual Date of Sending Draft SAR to HQ", value=parse_saved_date_or_none("actual_date_hq"))
                        if updated_status == "SAR issued":
                            updated_issue_dt = st.date_input("Actual Date of Issue of SAR", value=parse_saved_date_or_none("actual_date_issue"))
                            
                if st.form_submit_button("💾 Save Changes & Update Records"):
                    if updated_status == "Accounts Not Received":
                        update_payload = {
                            "cab": updated_cab,
                            "date_of_receipt": None,
                            "actual_date_field": None,
                            "actual_date_hq": None,
                            "actual_date_issue": None,
                            "status": "Accounts Not Received"
                        }
                    else:
                        update_payload = {
                            "cab": updated_cab,
                            "date_of_receipt": str(updated_receipt_dt) if updated_receipt_dt else None,
                            "actual_date_field": str(updated_field_dt) if updated_field_dt else None,
                            "actual_date_hq": str(updated_hq_dt) if updated_hq_dt else None,
                            "actual_date_issue": str(updated_issue_dt) if updated_issue_dt else None,
                            "status": updated_status
                        }
                        
                    update_sar_record(target_record["id"], update_payload)
                    st.success("Record parameters securely updated in cloud partition!")
                    st.rerun()

            # --- DEDICATED DELETE CONTROL OUTSIDE MANAGE EDIT FORM BLOCK ---
            st.markdown("---")
            st.markdown("##### ⚠️ Administrative Danger Zone")
            if st.button(f"🗑️ Delete Tracking Data for {target_record['cab']} Permanent", help="This operation cannot be undone. It removes the line entry entirely from the Master Board."):
                del_res = delete_sar_record(target_record["id"])
                if del_res.status_code in [200, 204]:
                    st.warning(f"Successfully dropped record parameters for {target_record['cab']}.")
                    st.rerun()
                else:
                    st.error("Database connection fault encountered trying to execute drop sequence.")
