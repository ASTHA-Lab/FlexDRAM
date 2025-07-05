`include "discipline.h"
`include "constants.h"

// Temperature-dependent MOSFET model

`define n_type 1
`define p_type 0

module mos_level1(vdrain, vgate, vsource, vbody);
inout vdrain, vgate, vsource, vbody;
electrical vdrain, vgate, vsource, vbody;

parameter real width = 1u from (0:inf);
parameter real length = 1u from (0:inf);
parameter real vto = 1 from (0:inf);
parameter real gamma = 0 from [0:inf);
parameter real phi = 0.6 from (0:inf);
parameter real lambda = 0.05 from [0:inf);
parameter real tox = 1e-7 from (0:inf);
parameter real u0 = 600 from (0:inf);
parameter real xj = 0 from [0:inf);
parameter real is = 1e-14 from (0:inf);
parameter real cj = 0 from [0:inf);
parameter real vj = 0.75 exclude 0;
parameter real mj = 0.5 from [0:1);
parameter real fc = 0.5 from [0:1);
parameter real tau = 0 from [0:inf);
parameter real cgbo = 0 from [0:inf);
parameter real cgso = 0 from [0:inf);
parameter real cgdo = 0 from [0:inf);
parameter integer dev_type = `n_type;
parameter real temp_nom = 300.15; // Nominal temperature (in Kelvin)
parameter real delta_vto = 2e-3;  // Temperature coefficient of threshold voltage
parameter real A = 1e-14;
parameter real B = 0.5;
parameter real C = 7;


// Define physical constants
real k = 1.380649e-23; // Boltzmann constant in J/K
real q = 1.602176634e-19; // Elementary charge in C

`define EPS0 8.8541879239442001396789635e-12
`define EPS_OX 3.9*`EPS0/100.0

`define F1(m, f, v) ((v/(1 - m))*(1 - pow((1 - f), m)))
`define F2(m, f) (pow((1 - f), (1 + m)))
`define F3(m, f) (1 - f*(1 + m))

real vds, vgs, vbs, vbd, vgb, vgd, vth, id, ibs, ibd, qgb, qgs, qgd, qbd, qbs;
real kp, fc1, fc2, fc3, fpb, leff;
real beta, vt, temp;
real gamma_temp, phi_temp;
integer dev_type_sign;
real leakage_temp_coeff;

analog begin
    temp = $temperature; // Current temperature

    vt = k * temp / q;
    leff = length - 2 * xj;
    kp = u0 * `EPS_OX / tox * pow((temp / temp_nom), -1.5);
    fc1 = `F1(mj, fc, vj);
    fc2 = `F2(mj, fc);
    fc3 = `F3(mj, fc);
    fpb = fc * mj;

    if (dev_type == `n_type) dev_type_sign = 1;
    else dev_type_sign = -1;

    vds = dev_type_sign * V(vdrain, vsource);
    vgs = dev_type_sign * V(vgate, vsource);
    vgb = dev_type_sign * V(vgate, vbody);
    vgd = dev_type_sign * V(vgate, vdrain);
    vbs = dev_type_sign * V(vbody, vsource);
    vbd = dev_type_sign * V(vbody, vdrain);

    // Temperature-dependent threshold voltage and bulk threshold
    if (vbs > 2 * phi) begin
        vth = vto + gamma * sqrt(2 * phi);
    end else begin
        vth = vto - gamma * (sqrt(2 * phi - vbs) - sqrt(2 * phi));
    end
    vth = vth - delta_vto * (temp - temp_nom) / temp_nom;

    gamma_temp = gamma * sqrt(temp / temp_nom);
    phi_temp = phi * (temp / temp_nom) + (k * temp / q) * log(temp_nom / 300.15);

    // Improved leakage current model
    //leakage_temp_coeff = is * pow(temp / temp_nom, 2)*(exp(vds*B));
	leakage_temp_coeff = is * pow(temp / temp_nom, 2)+A*(exp(vds*B))*exp(C * (temp-temp_nom)/temp_nom);

    ibd = leakage_temp_coeff * (exp(vbd / vt) - 1);
    ibs = leakage_temp_coeff * (exp(vbs / vt) - 1);

    if (vbd <= fpb) begin
        qbd = tau * ibd + cj * vj * (1 - pow((1 - vbd / vj), (1 - mj))) / (1 - mj);
    end else begin
        qbd = tau * ibd + cj * (fc1 + (1 / fc2) * (fc3 * (vbd - fpb) + (0.5 * mj / vj) * (vbd * vbd - fpb * fpb)));
    end

    if (vbs <= fpb) begin
        qbs = tau * ibs + cj * vj * (1 - pow((1 - vbs / vj), (1 - mj))) / (1 - mj);
    end else begin
        qbs = tau * ibs + cj * (fc1 + (1 / fc2) * (fc3 * (vbs - fpb) + (0.5 * mj / vj) * (vbs * vbs - fpb * fpb)));
    end

    beta = kp * width / leff;
    if (vgs <= vth) begin
        id = 0;
    end else if (vgs > vth && vds < vgs - vth) begin
        // linear region.
        id = beta * (vgs - vth - 0.5 * vds) * vds * (1 + lambda * vds);
    end else begin
        // saturation region.
        id = beta * 0.5 * (vgs - vth) * (vgs - vth) * (1 + lambda * vds);
    end

    qgb = cgbo * vgb;
    qgs = cgso * vgs;
    qgd = cgdo * vgd;

    I(vdrain, vsource) <+ dev_type_sign * id;
    I(vbody, vdrain) <+ dev_type_sign * (ibd + ddt(qbd));
    I(vbody, vsource) <+ dev_type_sign * (ibs + ddt(qbs));
    I(vgate, vbody) <+ dev_type_sign * ddt(qgb);
    I(vgate, vsource) <+ dev_type_sign * ddt(qgs);
    I(vgate, vdrain) <+ dev_type_sign * ddt(qgd);
end
endmodule