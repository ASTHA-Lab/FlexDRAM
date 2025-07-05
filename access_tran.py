import numpy as np

# Constants
EPS_OX = 3.9 * 8.854187817e-12 / 100  # Oxide permittivity (F/m)
vth = 1  # Threshold voltage (V), this should ideally be input or calculated based on other parameters
lambda_ = 0.05  # Channel length modulation, might be an input

def calculate_id(vgs, vds, width, leff, tox, u0):
    kp = u0 * EPS_OX / tox
    #print(kp)
    beta = kp * width / leff
    return beta * 0.5 * (vgs - vth)**2 * (1 + lambda_ * vds)


def adjust_tox(target_id, vgs, vds, width, length, xj, u0):
    leff = length - 2 * xj
    initial_tox = 1e-7  # Initial guess for tox
    min_tox = 5.8e-9  # Updated based on your observation

    def f(tox):
        return calculate_id(vgs, vds, width, leff, tox, u0) - target_id

    tox = initial_tox
    prev_tox = tox
    for _ in range(100):  # Increased number of iterations for finer control
        id_current = calculate_id(vgs, vds, width, leff, tox, u0)
        if np.isclose(id_current, target_id, atol=1e-12):
            break
        derivative = (calculate_id(vgs, vds, width, leff, tox + 1e-9, u0) - id_current) / 1e-9
        if abs(derivative) < 1e-20:  # Small derivative protection
            print("Derivative too small, adjusting step.")
            derivative = 1e-20  # Avoid division by zero by using a small placeholder

        tox_change = (id_current - target_id) / derivative
        new_tox = tox - tox_change
        if abs(new_tox - prev_tox) < 1e-12:  # Convergence check
            break
        prev_tox = tox
        tox = new_tox
        if tox < min_tox:
            tox = min_tox
            print("Minimum tox reached.")
            break

    return tox


# Example usage
desired_id = 70e-6  # Desired drain current (A)
vgs = 2.6  # V
vds = 1.5  # V
width = 80e-9  # m
length = 40e-9  # m
xj = 0  # m
u0 = 600  # cm^2/Vs

tox = adjust_tox(desired_id, vgs, vds, width, length, xj, u0)
#tox = str(round(tox,2))
print(f'Adjusted oxide thickness (tox) to achieve target Id: {tox} meters')
