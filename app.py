import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- Constants & Constants ---
LHV = 43_000_000  
CO2_FACTOR = 3.15 
R = 287

st.set_page_config(page_title="AeroPropulse NPSS-Lite", layout="wide")
st.title("🚀 AeroPropulse: High-Fidelity Coupled Simulator")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("1. Operational Conditions")
    alt = st.slider("Altitude (ft)", 0, 50000, 35000)
    mach = st.slider("Flight Mach", 0.0, 2.0, 0.8)
    
    st.header("2. Mechanical Driver")
    # RPM now drives the Mass Flow and Pressure Ratio
    rpm = st.slider("Engine RPM", 5000, 16000, 12000)
    material = st.selectbox("Turbine Material", ["Stainless Steel", "Inconel 718", "CMSX-4 Superalloy"])
    
    st.header("3. Thermodynamic Design")
    target_tit = st.slider("Target TIT (K)", 1000, 2200, 1600)
    ref_pr = st.number_input("Design Pressure Ratio (at 12k RPM)", value=25.0)

# --- THE COUPLED ENGINE CALCULATIONS ---

# 1. Atmospheric Model
t_amb = 288.15 - (0.00198 * alt)
p_amb = 101325 * (t_amb / 288.15)**5.256
v_flight = mach * np.sqrt(1.4 * R * t_amb)

# 2. Coupling: RPM to Pressure Ratio & Mass Flow
rpm_ratio = rpm / 12000
# Physics: PR scales with RPM squared
current_pr = 1 + (ref_pr - 1) * (rpm_ratio**2)
# Physics: Mass flow scales with RPM and Air Density
m_dot = 100 * rpm_ratio * (p_amb / 101325)

# 3. Coupling: Material Safety Throttle (The FADEC logic)
limits = {"Stainless Steel": 950, "Inconel 718": 1350, "CMSX-4 Superalloy": 1900}
actual_tit = min(target_tit, limits[material])

# 4. Cycle Analysis
t2 = t_amb * (1 + 0.2 * mach**2)
p2 = p_amb * (t2 / t_amb)**3.5
t3 = t2 + (t2 * (current_pr**0.285) - t2) / 0.88 # 0.88 = Compressor Eff
f = (1150 * actual_tit - 1005 * t3) / (0.98 * LHV - 1150 * actual_tit)
t5 = actual_tit - (1005 * (t3 - t2)) / ((1 + f) * 1150)
p5 = (p2 * current_pr) * (t5 / actual_tit)**(1.33 / (0.33 * 0.92)) # 0.92 = Turbine Eff
v_e = np.sqrt(max(0, 2 * 1150 * t5 * (1 - (p_amb/p5)**0.248)))

# 5. Output Metrics
thrust = m_dot * ((1 + f) * v_e - v_flight)
sfc = (f / ((1 + f) * v_e - v_flight)) * 1_000_000 
co2_hr = (f * m_dot * 3600) * CO2_FACTOR

# --- Dashboard Display ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Net Thrust", f"{round(thrust/1000, 2)} kN")
c2.metric("SFC", f"{round(sfc, 2)} mg/Ns")
c3.metric("Operating PR", f"{round(current_pr, 1)}")
c4.metric("CO2 Emission", f"{round(co2_hr/1000, 2)} T/hr")

if actual_tit < target_tit:
    st.error(f"⚠️ SAFETY LIMIT ACTIVE: {material} cannot handle {target_tit}K. Throttled to {actual_tit}K.")

st.divider()

# Visualization
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Velocity Vectors")
    fig, ax = plt.subplots()
    ax.barh(['Inlet Velocity', 'Exhaust Velocity'], [v_flight, v_e], color=['#2ecc71', '#e67e22'])
    st.pyplot(fig)
    

with col_b:
    st.subheader("Thermal Envelope")
    fig2, ax2 = plt.subplots()
    ax2.plot(['Amb', 'Inlet', 'Comp', 'TIT', 'Turbine'], [t_amb, t2, t3, actual_tit, t5], marker='D', ls='--', color='blue')
    st.pyplot(fig2)