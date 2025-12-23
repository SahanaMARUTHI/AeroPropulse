import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- Advanced Constants ---
LHV = 43_000_000  # Lower Heating Value of Jet-A (J/kg)
GAMMA_AIR = 1.4
GAMMA_GAS = 1.33  # Gas properties change after combustion
CP_AIR = 1005
CP_GAS = 1150     # Higher Cp for combustion products

st.set_page_config(page_title="AeroPropulse Level 2", layout="wide")
st.title("🚀 AeroPropulse Pro: Level 2 Performance Suite")

# --- Sidebar: Advanced Inputs ---
st.sidebar.header("Design Parameters")
alt = st.sidebar.slider("Altitude (ft)", 0, 50000, 35000)
mach = st.sidebar.slider("Mach Number", 0.0, 2.5, 0.85)
pr = st.sidebar.slider("Overall Pressure Ratio", 10, 50, 30)
tit = st.sidebar.slider("TIT (K)", 1000, 2200, 1650)

st.sidebar.header("Component Efficiencies")
eta_c = st.sidebar.slider("Isentropic Compressor Eff", 0.8, 0.95, 0.88)
eta_t = st.sidebar.slider("Isentropic Turbine Eff", 0.8, 0.98, 0.92)
eta_b = st.sidebar.slider("Burner Efficiency", 0.9, 1.0, 0.98)

# --- Math Logic ---
t_amb = 288.15 - (0.00198 * alt)
p_amb = 101325 * (t_amb / 288.15)**5.256
v_flight = mach * np.sqrt(GAMMA_AIR * 287 * t_amb)

# Inlet
t2 = t_amb * (1 + 0.5 * (GAMMA_AIR - 1) * mach**2)
p2 = p_amb * (t2 / t_amb)**(GAMMA_AIR / (GAMMA_AIR - 1))

# Compressor (Real-world losses included)
p3 = p2 * pr
t3_ideal = t2 * (pr**((GAMMA_AIR-1)/GAMMA_AIR))
t3 = t2 + (t3_ideal - t2) / eta_c

# Combustor (Fuel-Air Ratio Calculation)
# Calculation of fuel needed to reach TIT
f = (CP_GAS * tit - CP_AIR * t3) / (eta_b * LHV - CP_GAS * tit)

# Turbine (Work Balance with f)
# Power_c = Power_t -> CP_AIR * (T3 - T2) = (1 + f) * CP_GAS * (T4 - T5)
t4 = tit
t5 = t4 - (CP_AIR * (t3 - t2)) / ((1 + f) * CP_GAS)
p5 = p3 * (t5 / t4)**(GAMMA_GAS / ((GAMMA_GAS - 1) * eta_t))

# Nozzle & Thrust
v_e = np.sqrt(max(0, 2 * CP_GAS * t5 * (1 - (p_amb/p5)**((GAMMA_GAS-1)/GAMMA_GAS))))
thrust_specific = (1 + f) * v_e - v_flight
sfc = (f / thrust_specific) * 1_000_000 # mg/Ns (Industry Standard)

# --- Results Display ---
col1, col2, col3 = st.columns(3)
col1.metric("Specific Thrust", f"{round(thrust_specific, 1)} N/(kg/s)")
col2.metric("Fuel-Air Ratio (f)", f"{round(f, 4)}")
col3.metric("SFC", f"{round(sfc, 2)} mg/Ns")

# Visualization: T-s Diagram
fig, ax = plt.subplots()
ax.plot(['Amb', '2', '3', '4', '5'], [t_amb, t2, t3, t4, t5], marker='s', color='#1f77b4', label="Actual Cycle")
ax.set_ylabel("Temperature (K)")
ax.grid(True, linestyle='--')
st.pyplot(fig)