# FlexDRAM

# A Reconfigurable and Accurate Circuit-Level Substrate for DRAM Design and Analysis

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**FlexDRAM** is an open-source, reconfigurable DRAM circuit-level simulation tool that enables precise design, modeling, and timing analysis of DRAM datapath from bitcell to I/O. It includes a Verilog-A access transistor generator, automated model wrappers, JEDEC-compliant timing, and a Spectre-compatible simulation flow.

## 🔬 Motivation

Existing DRAM models lack accuracy in sense amplifier design and access transistor characterization, leading to large errors in power and performance estimates. FlexDRAM addresses these gaps by:
- Supporting accurate access transistor modeling using I<sub>ON</sub> and I<sub>OFF</sub>
- Providing a DRAM datapath model validated against JEDEC DDR4 specs
- Enabling fast design-space exploration with scaling, sizing, and transistor modeling tools

## 🧩 Repository Structure

```

FlexDRAM/
├── dram_wrapper.py # Wrapper to update netlist and generate access transistor model
├── access_tran.py # Access transistor modeling tool (Verilog-A generator)
├── config.ini # Configuration file for simulation and tech parameters
├── README.md # Documentation and usage guide
│
├── source/
│ ├── access_tran.v # Base Verilog-A access transistor model
│ ├── DRAM_BASELINE_TOP.scs # DRAM datapath SPICE netlist (editable)
│ └── param.scs # Parameter file for transistor dimensions
│
├── model/
│ └── transistor_model.pm # Transistor model (e.g., PTM or PDK model)

````


## 🚀 Getting Started

### 🔧 Prerequisites

- Python 3.x
- Cadence Spectre installed and accessible in your environment (`spectre` command)
- Cadence Virtuoso for waveform inspection (optional but recommended)

### 📥 Installation

```bash
git clone https://github.com/ASTHA-Lab/FlexDRAM.git
cd FlexDRAM
````

---

## 🛠️ Workflow

Follow this step-by-step guide to simulate a DRAM datapath with FlexDRAM:

```text
Step 0:
Edit parameters in `param.scs` — e.g., transistor widths and lengths

Step 1:
Configure simulation and device parameters in `config.ini`

Step 2:
Ensure `generate_access_dev_model = True` in `[script_control]` to generate access transistor model

Step 3:
Load Cadence Spectre:
module load cadence/spectre  # or source your environment setup script

Step 4:
Run the wrapper script to generate all models and initiate simulation
$ python3 dram_wrapper.py

Step 5:
Open waveform viewer in Virtuoso:
Tools → VIVA XL → Waveform

Step 6:
Load results from:
File → Open Results → Navigate to `./butterworth/psf`

Step 7:
Probe signals → Right-click → Send to → Export → CSV
```

### 🧪 Changing the DRAM Datapath Model

To modify the datapath model or integrate new sub-circuits:

* Edit `./sources/DRAM_BASELINE_TOP.scs`
* Use Verilog-A or SPICE blocks as needed

---

## 📜 Citation

If you use this tool or any part of the model in your research, please cite our GLSVLSI 2025 paper:

```bibtex
@inproceedings{10.1145/3716368.3735231,
author = {Ahsan, S M Mojahidul and Nouri, Mohammad and Ganapam, Ramesh Reddy and Alian, Mohammad and Hoque, Tamzidul},
title = {A Reconfigurable and Accurate Circuit-Level Substrate for DRAM Design and Analysis},
year = {2025},
isbn = {9798400714962},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
doi = {10.1145/3716368.3735231},
booktitle = {Proceedings of the Great Lakes Symposium on VLSI 2025},
pages = {169–176},
series = {GLSVLSI '25}
}
```

📄 Full Paper: [DOI Link](https://doi.org/10.1145/3716368.3735231)

---

## 🤝 Contributing

We welcome contributions! Please open issues for bugs or enhancements and fork the repository to make your own contributions. All pull requests will be reviewed.

---

## 🛡️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

This work is developed in collaboration with ASTHA LAB at The University of Kansas and Cornell University.

---

## 📬 Contact

For questions or collaborations, please contact:

**S M Mojahidul Ahsan**
Email: ahsan@ku.edu 

