import streamlit as st
import subprocess
from utils import *

# Parameters and their default, min, and max values
parameter_limits = {
    "duration_adsorption": {"default": 2.0, "min": 0.5, "max": 3.0},
    "duration_desorption": {"default": 2.0, "min": 0.5, "max": 3.0},
    "T_ambient_des": {"default": 363.0, "min": 353.0, "max": 403.0},
    "T_feed_des": {"default": 363.0, "min": 353.0, "max": 403.0},
    "u_des": {"default": 0.01, "min": 0.001, "max": 0.03}
}

parameters = ["duration_adsorption", "duration_desorption", "T_ambient_des", "T_feed_des", "u_des"]
objectives = ["productivity", "CO2_purity", "CO2_recovery", "total_electric_power_cons", "total_heat_cons", 
                "total_cons", "spec_electric_power_cons", "spec_heat_cons", "spec_cons"]
objectives_TeX = ["Productivity", r"$CO_2$ Purity", r"$CO_2$ Recovery", "Total Electric Power Cons", "Total Heat Cons",
                  "Total Cons", "Specific Electric Power Cons", "Specific Heat Cons", "Specific Cons"]

st.set_page_config(page_title="Parameter and Objective Selector", layout="wide")

# Apply custom CSS
st.markdown("""
    <style>
    .block-container {
        padding: 1rem 2rem;  /* Add wider margins */
        max-width: 1000px;  /* Limit content width */
        margin: auto;       /* Center content */
    }
    .stCheckbox > div {
        display: flex;
        align-items: center;  /* Center align the checkbox */
        margin-bottom: 0 !important; /* Remove unnecessary spacing */
    }
    .stNumberInput input {
        width: 100px !important; /* Compact input width */
    }
    .stSlider {
        margin-top: -0.5rem; /* Tighten slider spacing */
    }
    </style>
""", unsafe_allow_html=True)

st.title("Adsorption Desorption Optimisation")

params = {}
param_constants = {}
objectives_selected = {}

# Add subheaders for alignment
col_headers = st.columns([2, 1, 2, 2])  # Column widths
with col_headers[0]:
    st.subheader("Parameters")
with col_headers[1]:
    st.subheader("Constant")
with col_headers[2]:
    st.subheader("Values")
with col_headers[3]:
    st.subheader("Objectives")

# Align parameter text field and tick boxes
level_1_cols = st.columns([5, 2], gap='medium')
with level_1_cols[0]:
    for i, (param, limits) in enumerate(parameter_limits.items()):
        row = st.columns([2, 1, 2])  # Adjusted widths for parameter, constant, value
        with row[0]:
            st.text(param)  # Parameter name
        with row[1]:
            param_constants[param] = st.checkbox(param, key=f"{param}_const", label_visibility="collapsed")
        with row[2]:
            # Value input is always visible but greyed out (disabled) when checkbox is not ticked

            param_value = st.text_input(
                label=param,
                value=str(limits["default"]),  # Initialize with default value as a string
                key=f"{param}_value",
                label_visibility='collapsed',
                disabled=not param_constants[param]  # Disable input if the checkbox is not ticked
            )
            
            try:
                params[param] = float(param_value) if param_value else limits["default"]
                if float(param_value) > limits["max"] or float(param_value) < limits["min"]:
                    raise ValueError('Chosen value not in valid range')
            except ValueError:
                params[param] = limits["default"]


st.markdown("""
    <style>
        /* Target the checkbox elements specifically */
        .stCheckbox {
            margin-bottom: -10px;  /* Adjust this value to control the space */
        }
    </style>
""", unsafe_allow_html=True)

with level_1_cols[1]:
    for i in range(len(objectives)): 
        obj = objectives[i]
        objectives_selected[obj] = st.checkbox(objectives_TeX[i], value=True)

# Settings Section
st.subheader("Settings")
settings_col1, settings_col2 = st.columns(2)

with settings_col1:

    population_size = st.slider("Population Size", min_value=1, max_value=80, value=40)
    local_optimisation = st.button("Start Optimisation Locally", key='local', type="secondary")

with settings_col2:
    num_generations = st.slider("Number of Generations", min_value=1, max_value=100, value=50)

    subcol1, subcol2 = st.columns([1, 1]) 

    with subcol1:
        server_optimisation = st.button("Start Optimisation On Server", key='server', type="primary")
        
    with subcol2:
        password = st.text_input("Password", type="password", key="password", label_visibility='collapsed', placeholder="Password")

if local_optimisation or server_optimisation:
    
    consts = {param: (value if param_constants[param] else None) for param, value in params.items()}
    objs = {obj: objectives_selected[obj] for obj in objectives}

    run_params = {
        "consts": consts,
        "objs": objs
    }
    
    if local_optimisation:

        #run_path = threading.Thread(target=open_dir_dialog, daemon=True).start()
        run_path = open_dir_dialog()
        
        if run_path:
            command = f"""cd {run_path} && python ./run.py --pop_size {population_size} --n_gen {num_generations}"""
            save_run_params(run_path, run_params)

            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)

                # Check if there was any error in stderr
                if result.returncode != 0:
                    st.code(f"Error: {result.stderr}", language='text')
                else:
                    st.code(result.stdout, language='text')

            except FileNotFoundError as e:
                st.code(f"Command not found: {e}", language='text')
            except Exception as e:
                st.code(f"Error occurred: {e}", language='text')

    if server_optimisation:
        
        try:
            st.write("Running commands on the remote server...")
            sshclient = connect_remote(password)
            for message in run_remote_commands(sshclient, population_size, num_generations, run_params):
                if message == "All commands executed and connection closed.":
                    st.success(message)
                    break

                st.code(message, language='text')

        except Exception as e:
            st.code(f"Error occurred: {e}", language='text')
