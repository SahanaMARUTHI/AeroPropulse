import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- Setup ---
LHV = 43_000_000  
CO2_FACTOR = 3.15 

st.set_page_config(page_title="AeroPropulse Professional", layout="wide")
st.title("🚀 AeroPropulse Professional: Multi-Disciplinary Design Suite")

# --- Sidebar: User Controlled Design ---
with st.sidebar:
    st.header("1. Environmental & Mechanical")
    alt = st.slider("Altitude (ft)", 0, 50000, 35000)
    mach = st.slider("Mach Number", 0.0, 2.5, 0.85)
    material = st.selectbox("Blade Material", ["Stainless Steel", "Inconel 718", "CMSX-4 Superalloy"])
    rpm = st.slider("Operational RPM", 5000, 18000, 12000)
    
    st.header("2. Thermodynamic Cycle")
    pr = st.slider("Overall Pressure Ratio (OPR)", 5, 50, 30)
    tit_target = st.slider("Target TIT (K)", 1000, 2500, 1700)
    
    st.header("3. Efficiency Metrics")
    eta_c = st.slider("Compressor Isentropic Eff", 0.7, 0.98, 0.88)
    eta_t = st.slider("Turbine Isentropic Eff", 0.7, 0.98, 0.92)

# --- Physics Engine ---
# Material Safety Throttling (The 'Real-World' constraint)
def get_limit(mat):
    limits = {"Stainless Steel": 950, "Inconel 718": 1380, "CMSX-4 Superalloy": 1950}
    return limits[mat]

safe_limit = get_limit(material)
actual_tit = min(tit_target, safe_limit)

# Core Math
t_amb = 288.15 - (0.00198 * alt)
p_amb = 101325 * (t_amb / 288.15)**5.256
v_flight = mach * np.sqrt(1.4 * 287 * t_amb)

t2 = t_amb * (1 + 0.2 * mach**2)
p2 = p_amb * (t2 / t_amb)**3.5
t3 = t2 + (t2 * (pr**(0.285)) - t2) / eta_c
f = (1150 * actual_tit - 1005 * t3) / (0.98 * LHV - 1150 * actual_tit)
t5 = actual_tit - (1005 * (t3 - t2)) / ((1 + f) * 1150)
p5 = (p2 * pr) * (t5 / actual_tit)**(1.33 / (0.33 * eta_t))
v_e = np.sqrt(max(0, 2 * 1150 * t5 * (1 - (p_amb/p5)**(0.248))))

# Metrics
thrust_spec = (1 + f) * v_e - v_flight
sfc = (f / thrust_spec) * 1_000_000
co2_hr = (f * 100 * 3600) * CO2_FACTOR # Assumes 100kg/s flow for scale

# --- UI Layout ---
m1, m2, m3 = st.columns(3)
m1.metric("Specific Thrust", f"{round(thrust_spec, 1)} Ns/kg")
m2.metric("SFC", f"{round(sfc, 2)} mg/Ns")
m3.metric("CO2 Impact", f"{round(co2_hr/1000, 1)} Tonnes/hr")

if actual_tit < tit_target:
    st.warning(f"⚠️ SAFETY THROTTLE: Engine temperature capped at {safe_limit}K to protect {material} blades.")

st.divider()

# Charts
c1, c2 = st.columns(2)
with c1:
    st.subheader("Temperature-Station Diagram")
    fig, ax = plt.subplots()
    ax.plot(['Amb', 'Inlet', 'Comp', 'TIT', 'Turb'], [t_amb, t2, t3, actual_tit, t5], marker='o', color='red')
    st.pyplot(fig)
    

with c2:
    st.subheader("Performance Comparison")
    st.write(f"SFC is a key differentiator in industry. Your current SFC: **{round(sfc, 2)}**")
    st.progress(max(0.0, min(1.0, (60-sfc)/40))) # Scale 0-1 for visual