import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- Engineering Constants ---
LHV = 43_000_000  # Lower Heating Value of Jet-A (J/kg)
CO2_FACTOR = 3.15  # kg of CO2 per kg of fuel
R = 287
GAMMA_AIR = 1.4
GAMMA_GAS = 1.33
CP_AIR = 1005
CP_GAS = 1150

st.set_page_config(page_title="AeroPropulse NPSS-Lite", layout="wide")
st.title("🚀 AeroPropulse: High-Fidelity Coupled Simulator")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("1. Operational Conditions")
    alt = st.slider("Altitude (ft)", 0, 50000, 35000)
    mach = st.slider("Flight Mach", 0.0, 2.0, 0.8)
    
    st.header("2. Mechanical Driver")
    rpm = st.slider("Engine RPM", 5000, 16000, 12000)
    material = st.selectbox("Turbine Material", ["Stainless Steel", "Inconel 718", "CMSX-4 Superalloy"])
    
    st.header("3. Thermodynamic Design")
    target_tit = st.slider("Target TIT (K)", 1000, 2200, 1600)
    ref_pr = st.number_input("Design Pressure Ratio (at 12k RPM)", value=25.0)

# --- THE COUPLED ENGINE CALCULATIONS ---

# 1. Atmospheric Model (ISA)
t_amb = 288.15 - (0.00198 * alt)
p_amb = 101325 * (t_amb / 288.15)**5.256
v_flight = mach * np.sqrt(GAMMA_AIR * R * t_amb)

# 2. Coupling Logic: RPM drives PR and Mass Flow
# Industry scaling laws: PR scales with RPM^2
rpm_ratio = rpm / 12000
current_pr = 1 + (ref_pr - 1) * (rpm_ratio**2)
# Mass flow scales with RPM and Ambient Density
m_dot = 100 * rpm_ratio * (p_amb / 101325)

# 3. Material Safety Throttle (FADEC Simulation)
limits = {"Stainless Steel": 950, "Inconel 718": 1350, "CMSX-4 Superalloy": 1900}
actual_tit = min(target_tit, limits[material])

# 4. Thermodynamic Cycle Analysis
t2 = t_amb * (1 + 0.5 * (GAMMA_AIR - 1) * mach**2)
p2 = p_amb * (t2 / t_amb)**(GAMMA_AIR / (GAMMA_AIR - 1))
t3 = t2 + (t2 * (current_pr**((GAMMA_AIR-1)/GAMMA_AIR)) - t2) / 0.88 
f = (CP_GAS * actual_tit - CP_AIR * t3) / (0.98 * LHV - CP_GAS * actual_tit)
t5 = actual_tit - (CP_AIR * (t3 - t2)) / ((1 + f) * CP_GAS)
p5 = (p2 * current_pr) * (t5 / actual_tit)**(GAMMA_GAS / ((GAMMA_GAS - 1) * 0.92))
v_e = np.sqrt(max(0, 2 * CP_GAS * t5 * (1 - (p_amb/p5)**((GAMMA_GAS-1)/GAMMA_GAS))))

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

# Charts
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Velocity Vectors")
    fig, ax = plt.subplots()
    ax.barh(['Inlet Velocity', 'Exhaust Velocity'], [v_flight, v_e], color=['#2ecc71', '#e67e22'])
    ax.set_xlabel("m/s")
    st.pyplot(fig)
    

with col_b:
    st.subheader("Thermal Cycle Profile")
    fig2, ax2 = plt.subplots()
    ax2.plot(['Amb', 'Inlet', 'Comp', 'TIT', 'Turbine'], [t_amb, t2, t3, actual_tit, t5], marker='D', ls='--', color='blue')
    ax2.set_ylabel("Temperature (K)")
    st.pyplot(fig2)