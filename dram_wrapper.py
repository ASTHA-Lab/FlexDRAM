'''
First:
Clone this git repo. 
git clone https://github.com/ASTHA-Lab/FlexDRAM.git

Step 0:
Edit parameter's value in param.scs

Step 1: 
Edit the config.ini file for technology parameteres and other configuration.

Step 2:
Make sure to turn ON the generate_access_dev_model = True for generating/update the access device model

Step 3:
Load/Source Cadence Module (to run spectre) 

Step 4:
Run this scirpt to build the model for specific configuration and simulation run in spectre.

Step 5:
Open Virtuoso --> Tools --> VIVA XL --> Waveform

Step 6:
File --> Open Results --> Nevigate to your psf result file --> Probe to any signal you want

Step 7:
Right click --> Send to --> Export --> CSV



'''





import os
import subprocess
import configparser
import re
import math
from access_tran import *


# Load the scaling factors from the scaling.ini file
def load_scaling_factors(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    factors = {
        'tech_node': int(config['scaling']['tech_node']),
        'access_tran_L_factor': 0.95 ** int(config['scaling']['tech_node']),
        'access_tran_W_factor': 0.85 ** int(config['scaling']['tech_node']),
        'other_tran_L_factor': 0.93 ** int(config['scaling']['tech_node']),
        'other_tran_W_factor': 0.93 ** int(config['scaling']['tech_node']),
    }
    return factors

# Calculate the actual gate length based on the technology node
def get_actual_gate_length(tech_node):
    tech_mapping = {1: 45, 4: 32, 7: 22, 9: 16}
    return tech_mapping.get(tech_node, 45)  # Default to 45nm if tech_node is not found

# Convert value and unit to nanometers if necessary
def to_nanometers(value, unit):
    if unit == 'u':  # Micrometer to nanometer conversion
        return value * 1000
    return value

# Process the parameters, applying the scaling, and write to a new file
def process_parameters(param_file, factors, output_file):
    actual_gate_length = get_actual_gate_length(factors['tech_node'])

    with open(param_file, 'r') as f:
        params = f.read()

    # Extract all parameter names, values, and units
    param_pattern = re.compile(r'(\w+)=(\d+)([nu])')
    matches = param_pattern.findall(params)

    with open(output_file, 'w') as out_f:
        out_f.write("parameters ")
        for i, (name, value, unit) in enumerate(matches):
            value = float(value)
            value = to_nanometers(value, unit)  # Convert all values to nanometers for consistent scaling

            if 'accessfetw' in name:
                scaled_value = value * factors['access_tran_W_factor']
            elif 'w' in name[-1]:  # Width parameters
                scaled_value = value * factors['other_tran_W_factor']
            elif 'l' in name[-1]:  # Length parameters
                scaled_value = actual_gate_length
            else:
                continue  # Skip any parameters that don't match the expected naming

            # Convert back to original unit if necessary and apply ceiling to width values
            scaled_value_str = f"{math.ceil(scaled_value) / 1000 if unit == 'u' else math.ceil(scaled_value)}{unit}"
            
            # Add backslash except for the last parameter
            if i < len(matches) - 1:
                out_f.write(f"{name}={scaled_value_str} \\ \n    ")
            else:
                out_f.write(f"{name}={scaled_value_str}\n")


import configparser

def update_and_save_netlist(config_ini_path, netlist_file_path):
    # Read and parse the config.ini file
    config = configparser.ConfigParser()
    config.read(config_ini_path)
    
    # Extract required parameters from config.ini
    config_params = {section: dict(config.items(section)) for section in config.sections()}

    # Load the netlist file content
    with open(netlist_file_path, 'r') as file:
        netlist_content = file.read()

    # Perform the replacements
    netlist_content = netlist_content.replace("<parameter_path>", "scaled_parameters.scs")
    netlist_content = netlist_content.replace("<model_path>", config_params['simulation_model']['model_path'])
    netlist_content = netlist_content.replace("<nmos>", config_params['simulation_model']['nmos_model_name'])
    netlist_content = netlist_content.replace("<pmos>", config_params['simulation_model']['pmos_model_name'])
    netlist_content = netlist_content.replace("<nom_voltage>", config_params['simulation_control']['nominal_voltage'])
    netlist_content = netlist_content.replace("<half_vdd>", str(float(config_params['simulation_control']['nominal_voltage']) / 2))
    netlist_content = netlist_content.replace("<act_voltage>", config_params['simulation_control']['activation_voltage'])
    netlist_content = netlist_content.replace("<temp>", config_params['simulation_control']['temperature'])

    # Check the save_modified_netlist flag and decide the file to write to
    if config_params['script_control']['save_modified_netlist'].lower() == 'true':
        # If true, save to a new file with _modified suffix
        modified_file_path = 'DRAM_BASELINE_TOP_modified.scs'
    else:
        # If false, overwrite the original file
        modified_file_path = 'DRAM_BASELINE_TOP.scs'

    # Write the modified content to the chosen file
    with open(modified_file_path, 'w') as file:
        file.write(netlist_content)
    print(f"Netlist modifications saved to: {modified_file_path}")

# Usage:
# Provide the path to your config.ini file and the netlist file

# config_ini_path = "path/to/config.ini"
# netlist_file_path = "path/to/netlist_file.scs"
# update_and_save_netlist(config_ini_path, netlist_file_path)





def update_and_create_access_tran_model(config_path, atv_path):
    # Read and parse the configuration
    config = configparser.ConfigParser()
    config.read(config_path)

    # Check if we need to generate the access transistor model
    if not config.getboolean('script_control', 'generate_access_dev_model'):
        print("generate_access_dev_model flag is False. Skipping access transistor model generation.")
        return

    # Extract access device parameters
    adm = config['access_device_model']
    I_ON  = float(adm.get('I_ON'))     # Desired ON current (A)
    I_OFF = float(adm.get('I_OFF'))    # Desired OFF current (A)
    vgs   = float(adm.get('vgs'))      # Gate-to-source voltage (V)
    vds   = float(adm.get('vds'))      # Drain-to-source voltage (V)
    width_m  = float(adm.get('width'))  # Width (m)
    length_m = float(adm.get('length')) # Length (m)
    xj     = float(adm.get('xj'))      # Junction depth (m)
    u0     = float(adm.get('u0'))      # Mobility (cm^2/Vs)

    # Compute oxide thickness to meet I_ON target
    tox = adjust_tox(I_ON, vgs, vds, width_m, length_m, xj, u0)

    # Convert width and length from meters to micrometers for Verilog-A
    width_um  = width_m  * 1e6
    length_um = length_m * 1e6

    # Prepare replacement strings
    width_str  = f"{width_um}u"
    length_str = f"{length_um}u"
    tox_str    = f"{tox}"
    u0_str     = f"{u0}"
    xj_str     = f"{xj}"
    is_str     = f"{I_OFF}"

    # Read the base Verilog-A file
    with open(atv_path, 'r') as f:
        verilog = f.read()

    # Define regex patterns and replacements
    replacements = {
        r'parameter\s+real\s+width\s*=\s*[^;]+;':  f'parameter real width  = {width_str}  from (0:inf);',
        r'parameter\s+real\s+length\s*=\s*[^;]+;': f'parameter real length = {length_str} from (0:inf);',
        r'parameter\s+real\s+tox\s*=\s*[^;]+;':    f'parameter real tox    = {tox_str}    from (0:inf);',
        r'parameter\s+real\s+u0\s*=\s*[^;]+;':     f'parameter real u0     = {u0_str}     from (0:inf);',
        r'parameter\s+real\s+xj\s*=\s*[^;]+;':     f'parameter real xj     = {xj_str}     from [0:inf);',
        r'parameter\s+real\s+is\s*=\s*[^;]+;':     f'parameter real is     = {is_str}     from (0:inf);'
    }

    # Apply all replacements
    for pattern, repl in replacements.items():
        verilog = re.sub(pattern, repl, verilog)

    # Write out the new Verilog-A model
    output_path = 'access_tran_model.va'
    with open(output_path, 'w') as f:
        f.write(verilog)

    print(f"Generated access transistor Verilog-A model saved to: {output_path}")

def run_spectre_simulation():
    command = [
        "spectre", "-64", "DRAM_BASELINE_TOP_modified.scs",
        "+escchars",
        "+log", "./DRAM_BASELINE_TOP/psf/spectre.out",
        "-format", "psfascii",
        "-raw", "./butterworth/psf",
        "+lqtimeout", "900",
        "-maxw", "5",
        "-maxn", "5",
        "+logstatus"
    ]

    try:
        print("Running Spectre simulation...")
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("Spectre simulation completed successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error during Spectre simulation:")
        print(e.stderr)


# Main function to run the script
def main():
    config_ini_path = "config.ini"
    netlist_file_path = "/scratch/s550a945/proj/DRAM/git/sources/DRAM_BASELINE_TOP.scs"
    access_tran_base_verilog_path = "/scratch/s550a945/proj/DRAM/git/sources/access_tran.v"
    param_file = "/scratch/s550a945/proj/DRAM/git/sources/param.scs"
    scaling_factors = load_scaling_factors('config.ini')
    process_parameters(param_file, scaling_factors, 'scaled_parameters.scs')
    update_and_save_netlist(config_ini_path, netlist_file_path)
    update_and_create_access_tran_model (config_ini_path,  access_tran_base_verilog_path)
    
    run_spectre_simulation()

if __name__ == '__main__':
    main()

