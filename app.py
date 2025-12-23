import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- Constants ---
LHV = 43_000_000  
GAMMA_AIR = 1.4
GAMMA_GAS = 1.33  
CP_AIR = 1005
CP_GAS = 1150     
CO2_FACTOR = 3.15 # kg of CO2 per kg of fuel

st.set_page_config(page_title="AeroPropulse Enterprise", layout="wide")
st.title("🚀 AeroPropulse Enterprise: Performance, Safety & Sustainability")

# --- Sidebar ---
with st.sidebar:
    st.header("1. Flight & Design")
    alt = st.slider("Altitude (ft)", 0, 50000, 35000)
    mach = st.slider("Mach Number", 0.0, 2.5, 0.85)
    pr = st.slider("Overall Pressure Ratio", 10, 50, 30)
    tit = st.slider("TIT (K)", 1000, 2200, 1650)
    m_dot = st.number_input("Air Mass Flow (kg/s)", value=100.0)
    
    st.header("2. Component Efficiency")
    eta_c = st.slider("Compressor Eff", 0.8, 0.95, 0.88)
    eta_t = st.slider("Turbine Eff", 0.8, 0.98, 0.92)
    
    st.header("3. Structural & Materials")
    material = st.selectbox("Blade Material", ["Stainless Steel", "Inconel 718", "CMSX-4 Superalloy"])
    rpm = st.number_input("Engine RPM", value=12000)

# --- Engine Physics ---
t_amb = 288.15 - (0.00198 * alt)
p_amb = 101325 * (t_amb / 288.15)**5.256
v_flight = mach * np.sqrt(GAMMA_AIR * 287 * t_amb)

t2 = t_amb * (1 + 0.5 * (GAMMA_AIR - 1) * mach**2)
p2 = p_amb * (t2 / t_amb)**(GAMMA_AIR / (GAMMA_AIR - 1))
p3 = p2 * pr
t3 = t2 + (t2 * (pr**((GAMMA_AIR-1)/GAMMA_AIR)) - t2) / eta_c

f = (CP_GAS * tit - CP_AIR * t3) / (0.98 * LHV - CP_GAS * tit)
t5 = tit - (CP_AIR * (t3 - t2)) / ((1 + f) * CP_GAS)
p5 = p3 * (t5 / tit)**(GAMMA_GAS / ((GAMMA_GAS - 1) * eta_t))
v_e = np.sqrt(max(0, 2 * CP_GAS * t5 * (1 - (p_amb/p5)**((GAMMA_GAS-1)/GAMMA_GAS))))
thrust_total = m_dot * ((1 + f) * v_e - v_flight)
sfc = (f / ((1 + f) * v_e - v_flight)) * 1_000_000 

# --- Sustainability Metrics ---
fuel_flow_hr = f * m_dot * 3600 # kg/hr
co2_hr = fuel_flow_hr * CO2_FACTOR

# --- Structural Physics ---
stress_mpa = (rpm / 1000)**2 * 2.5 
def get_strength(mat, temp):
    if mat == "Stainless Steel": return max(0, 500 - (temp-300)*0.8)
    if mat == "Inconel 718": return max(0, 1000 - (temp-400)*0.5)
    return max(0, 1200 - (temp-600)*0.3)
yield_str = get_strength(material, tit)

# --- Display Dashboard ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Net Thrust", f"{round(thrust_total/1000, 2)} kN")
m2.metric("SFC", f"{round(sfc, 2)} mg/Ns")
m3.metric("CO2 Emission", f"{round(co2_hr)} kg/hr")
m4.metric("Fuel Burn", f"{round(fuel_flow_hr)} kg/hr")

st.divider()

col_left, col_right = st.columns(2)
with col_left:
    st.subheader("📊 Performance Visualization")
    fig, ax = plt.subplots()
    ax.plot(['Amb', 'Inlet', 'Comp', 'TIT', 'Turb'], [t_amb, t2, t3, tit, t5], marker='o', color='#00FFAA')
    ax.set_title("Temperature Profile (K)")
    st.pyplot(fig)

with col_right:
    st.subheader("🛡️ Structural & Environmental Report")
    if stress_mpa > yield_str:
        st.error(f"🚨 ALERT: STRUCTURAL FAILURE. {material} cannot sustain {tit}K.")
    else:
        st.success(f"✅ DESIGN PASS. Safety Factor: {round(yield_str/stress_mpa, 2)}")
    
    st.info(f"🌍 Environmental Impact: At current settings, this engine emits {round(co2_hr/1000, 2)} tonnes of CO2 per hour.")