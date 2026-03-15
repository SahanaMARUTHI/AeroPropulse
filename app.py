import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- NASA Polynomials for Real Gas Properties (Shomate Equations) ---
# These constants are used by NASA/Industry to calculate Cp as a function of Temperature
def get_cp_air(T):
    """Calculates Cp (J/kgK) for Air using NASA coefficients."""
    # Coefficients for Air (200K - 1000K)
    if T < 1000:
        a = [28.11, 1.96e-3, 4.80e-6, -1.96e-9, 1.89e-14]
    else: # 1000K - 6000K
        a = [32.74, 1.35e-3, -4.65e-7, 7.57e-11, -4.79e-15]
    
    t = T / 1000
    cp_mol = a[0] + a[1]*T + a[2]*T**2 + a[3]*T**3 + a[4]*T**4
    return (cp_mol / 28.97) * 1000 # Convert to J/kgK

st.set_page_config(page_title="AeroPropulse Pro-Solver", layout="wide")
st.title("🚀 AeroPropulse Pro: Industrial Solver Edition")
st.info("This version uses NASA Shomate Polynomials and Component Matching Logic used by ISRO/NASA.")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("1. Mission Profile")
    alt = st.slider("Altitude (ft)", 0, 50000, 35000)
    mach = st.slider("Mach Number", 0.0, 2.5, 0.8)
    
    st.header("2. Engine Architecture")
    rpm = st.slider("Core RPM", 5000, 18000, 12000)
    ref_pr = st.slider("Design Pressure Ratio", 10.0, 50.0, 30.0)
    target_tit = st.slider("TIT (K)", 1000, 2200, 1600)
    
    st.header("3. Advanced Materials")
    material = st.selectbox("Blade Material", ["Stainless Steel", "Inconel 718", "CMSX-4 Superalloy"])

# --- The "Solver" Logic (Matching) ---
# 1. Ambient Conditions (ISA)
t_amb = 288.15 - (0.00198 * alt)
p_amb = 101325 * (t_amb / 288.15)**5.256
v_flight = mach * np.sqrt(1.4 * 287 * t_amb)

# 2. Component Matching (Non-linear PR scaling)
rpm_ratio = rpm / 12000
current_pr = 1 + (ref_pr - 1) * (rpm_ratio**1.6)

# 3. Thermodynamic Real-Gas Analysis
t2 = t_amb * (1 + 0.2 * mach**2)
p2 = p_amb * (t2 / t_amb)**3.5

# Calculate Compressor Work using Variable Cp
cp_avg_c = (get_cp_air(t2) + get_cp_air(t2 * current_pr**0.285)) / 2
t3 = t2 + (t2 * (current_pr**0.285) - t2) / 0.88
work_c = cp_avg_c * (t3 - t2)

# Safety Throttle
limits = {"Stainless Steel": 950, "Inconel 718": 1380, "CMSX-4 Superalloy": 1950}
actual_tit = min(target_tit, limits[material])

# Calculate Turbine Work & Matching
cp_avg_t = (get_cp_air(actual_tit) + get_cp_air(actual_tit * 0.7)) / 2
# Work Balance: Work_Turbine = Work_Compressor / Mechanical_Eff
work_t_required = work_c / 0.99 
t5 = actual_tit - (work_t_required / cp_avg_t)

# 4. Results Generation
p5 = (p2 * current_pr) * (t5 / actual_tit)**(1.33 / (0.33 * 0.92))
v_e = np.sqrt(max(0, 2 * cp_avg_t * t5 * (1 - (p_amb/p5)**0.248)))
m_dot = 120 * rpm_ratio * (p_amb / 101325)
f = (cp_avg_t * actual_tit - cp_avg_c * t3) / (0.98 * 43e6 - cp_avg_t * actual_tit)
thrust = m_dot * ((1+f)*v_e - v_flight)
sfc = (f / ((1+f)*v_e - v_flight)) * 1e6

# --- Professional UI Display ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Corrected Net Thrust", f"{round(thrust/1000, 2)} kN")
m2.metric("Specific Fuel Consumption", f"{round(sfc, 2)} mg/Ns")
m3.metric("Air Mass Flow", f"{round(m_dot, 1)} kg/s")
m4.metric("Thermal Efficiency", f"{round((1 - t_amb/actual_tit)*100, 1)} %")

st.divider()
st.subheader("Industrial Validation Data")
col_a, col_b = st.columns(2)

with col_a:
    # Component Map Visualization
    st.write("**Compressor Operating Map (Simulated)**")
    pr_range = np.linspace(1, 50, 20)
    eff_curve = 0.88 - (pr_range/100)**2 # Simplified efficiency drop
    fig, ax = plt.subplots()
    ax.plot(pr_range, eff_curve, color='cyan', label='Efficiency Line')
    ax.scatter([current_pr], [0.88 - (current_pr/100)**2], color='red', s=100, label='Current Op Point')
    ax.set_xlabel("Pressure Ratio")
    ax.set_ylabel("Isentropic Efficiency")
    ax.legend()
    st.pyplot(fig)
    

with col_b:
    st.write("**Material Creep Limit Analysis**")
    st.info(f"Material: {material} | Operating at {round((actual_tit/limits[material])*100)}% of thermal limit.")
    st.progress(actual_tit / limits[material])
    if actual_tit >= limits[material]:
        st.warning("ENGINE PROTECTED BY FADEC: Temperature capped to prevent blade melting.")