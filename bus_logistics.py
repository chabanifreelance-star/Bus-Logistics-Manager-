import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# ─── Config ───────────────────────────────────────────────────────────────────
DATA_FILE = "bus_data.json"
DEFAULT_CAPACITY = 50

st.set_page_config(
    page_title="Bus Logistics Manager",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }
    h1, h2, h3 { font-family: 'Syne', sans-serif; font-weight: 800; }

    .stApp { background: #0f1117; color: #f0f0f0; }

    .bus-card {
        background: linear-gradient(135deg, #1a1d27 0%, #21253a 100%);
        border: 1px solid #2e3250;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        transition: border-color 0.2s;
    }
    .bus-card:hover { border-color: #4f6ef7; }

    .bus-title {
        font-family: 'Syne', sans-serif;
        font-size: 1.3rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0 0 4px 0;
    }
    .bus-count {
        font-size: 2.5rem;
        font-weight: 800;
        font-family: 'Syne', sans-serif;
        color: #4f6ef7;
        line-height: 1;
    }
    .bus-label { font-size: 0.8rem; color: #8a8fa8; text-transform: uppercase; letter-spacing: 1px; }

    .stat-card {
        background: #1a1d27;
        border: 1px solid #2e3250;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
    }
    .stat-num {
        font-family: 'Syne', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        color: #4f6ef7;
    }
    .stat-label { font-size: 0.8rem; color: #8a8fa8; text-transform: uppercase; letter-spacing: 1px; }

    .warning-badge {
        background: #ff6b35;
        color: white;
        font-size: 0.7rem;
        padding: 2px 8px;
        border-radius: 20px;
        font-weight: 600;
        margin-left: 8px;
    }
    .ok-badge {
        background: #2ecc71;
        color: white;
        font-size: 0.7rem;
        padding: 2px 8px;
        border-radius: 20px;
        font-weight: 600;
        margin-left: 8px;
    }

    .member-row {
        background: #13151f;
        border-radius: 8px;
        padding: 8px 14px;
        margin: 4px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.95rem;
    }
    .role-tag {
        background: #2e3250;
        color: #a0a8d0;
        font-size: 0.72rem;
        padding: 2px 8px;
        border-radius: 20px;
    }

    div[data-testid="stProgress"] > div > div {
        background: linear-gradient(90deg, #4f6ef7, #8a60f7);
    }

    .stButton > button {
        background: #4f6ef7;
        color: white;
        border: none;
        border-radius: 8px;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton > button:hover { background: #3a58d6; transform: translateY(-1px); }

    .stTextInput > div > input, .stSelectbox > div, .stNumberInput > div > input {
        background: #1a1d27 !important;
        border: 1px solid #2e3250 !important;
        color: #f0f0f0 !important;
        border-radius: 8px !important;
    }

    .sidebar-section {
        background: #1a1d27;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        border: 1px solid #2e3250;
    }

    .duplicate-warning {
        background: #3a2010;
        border: 1px solid #ff6b35;
        border-radius: 8px;
        padding: 8px 14px;
        color: #ff9f72;
        font-size: 0.88rem;
        margin: 4px 0;
    }
</style>
""", unsafe_allow_html=True)

# ─── Data Persistence ─────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"buses": {}, "capacity": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_all_members(buses):
    all_members = []
    for bus_name, members in buses.items():
        for m in members:
            all_members.append({"Bus": bus_name, "Name": m["name"], "Role": m.get("role", ""), "Added": m.get("added", "")})
    return all_members

# ─── Init Session ─────────────────────────────────────────────────────────────
if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data
buses = data.setdefault("buses", {})
capacity = data.setdefault("capacity", {})

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚌 Bus Manager")
    st.markdown("---")

    # Add Bus
    st.markdown("### ➕ New Bus")
    new_bus_name = st.text_input("Bus name", placeholder="e.g. Bus A", key="new_bus_input")
    new_bus_cap = st.number_input("Capacity", min_value=1, max_value=200, value=DEFAULT_CAPACITY, key="new_cap")
    if st.button("Create Bus", use_container_width=True):
        if new_bus_name.strip():
            bname = new_bus_name.strip()
            if bname not in buses:
                buses[bname] = []
                capacity[bname] = int(new_bus_cap)
                save_data(data)
                st.success(f"Bus '{bname}' created!")
                st.rerun()
            else:
                st.error("Bus already exists.")
        else:
            st.warning("Enter a bus name.")

    st.markdown("---")

    # Delete Bus
    if buses:
        st.markdown("### 🗑️ Delete Bus")
        del_bus = st.selectbox("Select bus to delete", list(buses.keys()), key="del_bus")
        if st.button("Delete Bus", use_container_width=True):
            confirm = st.session_state.get("confirm_delete", False)
            st.session_state["confirm_delete"] = True
            st.rerun()
        if st.session_state.get("confirm_delete"):
            st.warning(f"Delete **{del_bus}** and all its members?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, delete", use_container_width=True):
                    del buses[del_bus]
                    capacity.pop(del_bus, None)
                    save_data(data)
                    st.session_state["confirm_delete"] = False
                    st.rerun()
            with col2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state["confirm_delete"] = False
                    st.rerun()

    st.markdown("---")

    # Move Member
    if len(buses) >= 2:
        st.markdown("### 🔄 Move Member")
        from_bus = st.selectbox("From bus", list(buses.keys()), key="move_from")
        if buses.get(from_bus):
            member_names = [m["name"] for m in buses[from_bus]]
            move_member = st.selectbox("Member", member_names, key="move_member")
            to_bus_options = [b for b in buses if b != from_bus]
            to_bus = st.selectbox("To bus", to_bus_options, key="move_to")
            if st.button("Move Member", use_container_width=True):
                member_obj = next((m for m in buses[from_bus] if m["name"] == move_member), None)
                if member_obj:
                    buses[from_bus] = [m for m in buses[from_bus] if m["name"] != move_member]
                    buses[to_bus].append(member_obj)
                    save_data(data)
                    st.success(f"Moved {move_member} to {to_bus}!")
                    st.rerun()
        else:
            st.info("No members in this bus.")

    st.markdown("---")

    # Export
    st.markdown("### 📤 Export")
    if buses:
        all_m = get_all_members(buses)
        if all_m:
            df_export = pd.DataFrame(all_m)
            csv = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV",
                data=csv,
                file_name=f"bus_roster_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

# ─── Main Area ────────────────────────────────────────────────────────────────
st.markdown("# 🚌 Bus Logistics Manager")

# Stats row
total_members = sum(len(m) for m in buses.values())
total_buses = len(buses)
total_capacity = sum(capacity.get(b, DEFAULT_CAPACITY) for b in buses)
full_buses = sum(1 for b in buses if len(buses[b]) >= capacity.get(b, DEFAULT_CAPACITY))

col1, col2, col3, col4 = st.columns(4)
stats = [
    (total_buses, "Total Buses"),
    (total_members, "Total Members"),
    (total_capacity - total_members if total_capacity > 0 else 0, "Seats Available"),
    (full_buses, "Full Buses"),
]
for col, (num, label) in zip([col1, col2, col3, col4], stats):
    with col:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-num">{num}</div>
            <div class="stat-label">{label}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Search bar
search_query = st.text_input("🔍 Search member by name", placeholder="Type a name to search across all buses...", key="search")
if search_query:
    results = []
    for bname, members in buses.items():
        for m in members:
            if search_query.lower() in m["name"].lower():
                results.append({"Bus": bname, "Name": m["name"], "Role": m.get("role", "—"), "Added": m.get("added", "—")})
    if results:
        st.success(f"Found {len(results)} result(s):")
        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
    else:
        st.warning("No members found.")
    st.markdown("---")

# Duplicate check across all buses
all_names = [m["name"].lower() for members in buses.values() for m in members]
duplicates = set(n for n in all_names if all_names.count(n) > 1)

if duplicates:
    st.markdown("### ⚠️ Duplicate Names Detected")
    for dup in duplicates:
        dup_buses = [b for b, members in buses.items() if any(m["name"].lower() == dup for m in members)]
        st.markdown(f'<div class="duplicate-warning">⚠️ <b>{dup.title()}</b> appears in: {", ".join(dup_buses)}</div>', unsafe_allow_html=True)
    st.markdown("")

# ─── Bus Cards ────────────────────────────────────────────────────────────────
if not buses:
    st.info("No buses yet. Create one in the sidebar ➡️")
else:
    tabs = st.tabs(list(buses.keys()) + ["📋 All Members"])

    for i, bname in enumerate(buses.keys()):
        with tabs[i]:
            members = buses[bname]
            cap = capacity.get(bname, DEFAULT_CAPACITY)
            count = len(members)
            pct = count / cap if cap > 0 else 0
            badge = '<span class="warning-badge">FULL</span>' if count >= cap else '<span class="ok-badge">OK</span>'

            col_info, col_add = st.columns([1, 1])

            with col_info:
                st.markdown(f"""
                <div class="bus-card">
                    <div class="bus-title">{bname} {badge}</div>
                    <div class="bus-count">{count}</div>
                    <div class="bus-label">of {cap} seats</div>
                </div>""", unsafe_allow_html=True)
                st.progress(min(pct, 1.0))

            with col_add:
                st.markdown("#### Add Member")
                new_name = st.text_input("Name", key=f"name_{bname}", placeholder="Full name")
                new_role = st.selectbox("Role", ["Member", "Leader", "Driver", "Assistant", "Other"], key=f"role_{bname}")
                if st.button("Add ➕", key=f"add_{bname}", use_container_width=True):
                    if new_name.strip():
                        if count >= cap:
                            st.error(f"Bus is full! ({cap} seats)")
                        else:
                            buses[bname].append({
                                "name": new_name.strip(),
                                "role": new_role,
                                "added": datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
                            save_data(data)
                            st.success(f"Added {new_name.strip()}!")
                            st.rerun()
                    else:
                        st.warning("Enter a name.")

            # Capacity edit
            with st.expander("⚙️ Edit capacity"):
                new_cap = st.number_input("Max seats", min_value=1, max_value=500, value=cap, key=f"cap_{bname}")
                if st.button("Update capacity", key=f"savecap_{bname}"):
                    capacity[bname] = int(new_cap)
                    save_data(data)
                    st.success("Capacity updated!")
                    st.rerun()

            st.markdown(f"#### 👥 Members ({count})")

            if not members:
                st.info("No members yet.")
            else:
                # Filter within bus
                bus_search = st.text_input("Filter this bus", placeholder="Search...", key=f"busfilter_{bname}")
                filtered = [m for m in members if bus_search.lower() in m["name"].lower()] if bus_search else members

                for j, m in enumerate(filtered):
                    c1, c2, c3 = st.columns([3, 2, 1])
                    with c1:
                        st.markdown(f"**{m['name']}**")
                    with c2:
                        st.markdown(f'<span class="role-tag">{m.get("role","Member")}</span>', unsafe_allow_html=True)
                    with c3:
                        # Find actual index in original list
                        orig_idx = next((idx for idx, om in enumerate(buses[bname]) if om["name"] == m["name"]), None)
                        if st.button("✕", key=f"del_{bname}_{j}_{m['name']}"):
                            if orig_idx is not None:
                                buses[bname].pop(orig_idx)
                                save_data(data)
                                st.rerun()

    # All Members tab
    with tabs[-1]:
        st.markdown("#### 📋 All Members Across All Buses")
        all_m = get_all_members(buses)
        if all_m:
            df_all = pd.DataFrame(all_m)
            st.dataframe(df_all, use_container_width=True, hide_index=True)
            st.markdown(f"**Total: {len(all_m)} members across {len(buses)} buses**")
        else:
            st.info("No members added yet.")
