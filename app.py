import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- Constants ---
LHV = 43_000_000  
GAMMA_AIR = 1.4
GAMMA_GAS = 1.33  
CP_AIR = 1005
CP_GAS = 1150     
CO2_FACTOR = 3.15 

st.set_page_config(page_title="AeroPropulse Level 3", layout="wide")
st.title("🚀 AeroPropulse Level 3: Fully Coupled Engineering Suite")

# --- Sidebar ---
with st.sidebar:
    st.header("1. Operational Inputs")
    alt = st.slider("Altitude (ft)", 0, 50000, 35000)
    mach = st.slider("Mach Number", 0.0, 2.5, 0.85)
    
    st.header("2. Mechanical Design")
    material = st.selectbox("Blade Material", ["Stainless Steel", "Inconel 718", "CMSX-4 Superalloy"])
    # RPM now drives the Pressure Ratio (Coupled Physics)
    rpm = st.slider("Engine RPM", 8000, 16000, 12000)
    
    st.header("3. Thermodynamics")
    # Base TIT - will be adjusted by material limits
    base_tit = st.slider("Target TIT (K)", 1000, 2200, 1650)
    m_dot_ref = st.number_input("Reference Air Mass Flow (kg/s)", value=100.0)

# --- COUPLED PHYSICS LOGIC ---

# A. RPM to Pressure Ratio Coupling (Simplified scaling)
# PR scales with the square of RPM ratio
pr = 10 + (rpm / 16000)**2 * 40 

# B. Material-Temperature Integrity Coupling
def get_max_safe_temp(mat):
    if mat == "Stainless Steel": return 900
    if mat == "Inconel 718": return 1350
    return 1900 # CMSX-4

max_temp = get_max_safe_temp(material)
actual_tit = min(base_tit, max_temp) # The engine "throttles" if material is weak

# C. Engine Physics
t_amb = 288.15 - (0.00198 * alt)
p_amb = 101325 * (t_amb / 288.15)**5.256
v_flight = mach * np.sqrt(GAMMA_AIR * 287 * t_amb)

t2 = t_amb * (1 + 0.5 * (GAMMA_AIR - 1) * mach**2)
p2 = p_amb * (t2 / t_amb)**(GAMMA_AIR / (GAMMA_AIR - 1))
p3 = p2 * pr
t3 = t2 + (t2 * (pr**((GAMMA_AIR-1)/GAMMA_AIR)) - t2) / 0.88 # 0.88 eta_c

f = (CP_GAS * actual_tit - CP_AIR * t3) / (0.98 * LHV - CP_GAS * actual_tit)
t5 = actual_tit - (CP_AIR * (t3 - t2)) / ((1 + f) * CP_GAS)
p5 = p3 * (t5 / actual_tit)**(GAMMA_GAS / ((GAMMA_GAS - 1) * 0.92))
v_e = np.sqrt(max(0, 2 * CP_GAS * t5 * (1 - (p_amb/p5)**((GAMMA_GAS-1)/GAMMA_GAS))))

# Mass flow scales with RPM
m_dot_actual = m_dot_ref * (rpm / 12000) * (p_amb / 101325) 
thrust_total = m_dot_actual * ((1 + f) * v_e - v_flight)
sfc = (f / ((1 + f) * v_e - v_flight)) * 1_000_000 

# D. Sustainability & Structural
fuel_flow_hr = f * m_dot_actual * 3600
co2_hr = fuel_flow_hr * CO2_FACTOR
stress_mpa = (rpm / 1000)**2 * 2.5 

# --- Display Dashboard ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Coupled Net Thrust", f"{round(thrust_total/1000, 2)} kN")
m2.metric("SFC", f"{round(sfc, 2)} mg/Ns")
m3.metric("Hourly CO2", f"{round(co2_hr)} kg/hr")
m4.metric("Operating PR", f"{round(pr, 1)}")

st.divider()

col_left, col_right = st.columns(2)
with col_left:
    st.subheader("📈 Performance Mapping")
    st.write(f"**Current Material Mode:** {material}")
    if actual_tit < base_tit:
        st.warning(f"⚠️ Performance Throttled! Material cannot handle {base_tit}K. Operating at {actual_tit}K safety limit.")
    
    fig, ax = plt.subplots()
    ax.bar(['Flight Speed', 'Exhaust Velocity'], [v_flight, v_e], color=['#3498db', '#e74c3c'])
    ax.set_ylabel("Velocity (m/s)")
    st.pyplot(fig)
    

with col_right:
    st.subheader("🛡️ Structural Safety Analysis")
    st.write(f"Applied Centrifugal Stress: **{round(stress_mpa)} MPa**")
    if actual_tit >= max_temp and base_tit > max_temp:
        st.error("🚨 CRITICAL: Operation at absolute material limit. High risk of Creep failure.")
    else:
        st.success("✅ Operating within Material Thermal Envelope.")

    # Show Operating Efficiency vs Altitude
    alt_range = np.linspace(0, 50000, 10)
    temp_drop = 288.15 - (0.00198 * alt_range)
    # Simple efficiency visual
    fig2, ax2 = plt.subplots()
    ax2.plot(alt_range, (1 - (temp_drop/actual_tit)), color='green')
    ax2.set_title("Theoretical Thermal Efficiency vs Altitude")
    ax2.set_xlabel("Altitude (ft)")
    st.pyplot(fig2)