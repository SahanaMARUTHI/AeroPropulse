import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- Physical Constants ---
GAMMA = 1.4
CP = 1005 
R = 287    

def get_ambient_conditions(alt_ft):
    t_amb = 288.15 - (0.00198 * alt_ft)
    p_amb = 101325 * (t_amb / 288.15)**5.256
    return t_amb, p_amb

# --- UI Setup ---
st.set_page_config(page_title="AeroPropulse Tech Report", layout="wide")
st.title("🚀 AeroPropulse: Propulsion & Structural Analysis")

# Sidebar with UNIQUE KEYS added
st.sidebar.header("1. Flight Conditions")
alt = st.sidebar.slider("Altitude (ft)", 0, 50000, 30000, key="alt_slider")
mach = st.sidebar.slider("Mach Number", 0.0, 2.0, 0.8, key="mach_slider")

st.sidebar.header("2. Engine Design")
pr = st.sidebar.slider("Compressor Pressure Ratio", 5, 40, 25, key="pr_slider")
tit = st.sidebar.slider("Turbine Inlet Temp (K)", 1000, 2200, 1600, key="tit_slider")
m_dot = st.sidebar.number_input("Air Mass Flow (kg/s)", value=50.0, key="mdot_input")

st.sidebar.header("3. Material Science")
material = st.sidebar.selectbox("Blade Material", ["Stainless Steel", "Inconel 718", "CMSX-4 Superalloy"], key="mat_select")
rpm = st.sidebar.number_input("Engine RPM", value=12000, key="rpm_input")

# --- Math Logic ---
t_amb, p_amb = get_ambient_conditions(alt)
v_flight = mach * np.sqrt(GAMMA * R * t_amb)
t2 = t_amb * (1 + 0.5 * (GAMMA - 1) * mach**2)
p2 = p_amb * (t2 / t_amb)**(GAMMA / (GAMMA - 1))
p3 = p2 * pr
t3 = t2 * (pr**((GAMMA-1)/GAMMA))
t4 = tit
t5 = t4 - (t3 - t2)
p5 = p3 * (t5 / t4)**(GAMMA / (GAMMA - 1))
v_e = np.sqrt(max(0, 2 * CP * t5 * (1 - (p_amb/p5)**((GAMMA-1)/GAMMA))))
thrust = m_dot * (v_e - v_flight)

# --- Material Check ---
stress_mpa = (rpm / 1000)**2 * 2.5 
def get_strength(mat, temp):
    if mat == "Stainless Steel": return max(0, 500 - (temp-300)*0.8)
    if mat == "Inconel 718": return max(0, 1000 - (temp-400)*0.5)
    return max(0, 1200 - (temp-600)*0.3)
yield_str = get_strength(material, t4)

# --- Layout ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Performance Metrics")
    st.metric("Net Thrust", f"{round(thrust/1000, 2)} kN")
    st.metric("Exhaust Velocity", f"{round(v_e, 1)} m/s")
    
    fig, ax = plt.subplots()
    ax.plot(['Amb', '2', '3', '4', '5'], [t_amb, t2, t3, t4, t5], marker='o', color='red')
    ax.set_ylabel("Temperature (K)")
    st.pyplot(fig)

with col2:
    st.subheader("Structural Integrity")
    if stress_mpa > yield_str:
        st.error(f"❌ FAILURE: {material} yields at {round(t4)}K")
    else:
        st.success(f"✅ SAFE: Factor of Safety {round(yield_str/stress_mpa, 2)}")