# MEGA27-19: Medical Microbots and Xenobots - Computational Design and Control

Physics-first computational study of medical microswimmers and living xenobots.

## Studies
1. **Helical magnetic microbot**: resistive-force-theory (RFT) hydrodynamics at low
   Reynolds number - thrust, torque, step-out frequency; geometry optimization for
   drug-delivery payload transport.
2. **Microbot swarm control**: closed-loop path tracking of magnetic microbots with
   PID + model-predictive control under Brownian noise; real stability analysis.
3. **Xenobot morphology search**: voxel-based soft-body design optimization
   (CPPN-free, direct encoding + evolutionary search) for locomotion and
   object-transport tasks, in the spirit of Kriegman et al. 2020 - reimplemented
   with a real 2D physics integrator (spring-mass soft body), not a claim on their code.
4. **Biobot chemotaxis simulation**: run-and-tumble agent model navigating a drug
   concentration gradient; delivery-efficiency statistics.

Real math throughout: Stokes-flow RFT, rotating magnetic field actuation,
Langevin dynamics, MPC with quadratic costs, evolutionary optimization.
Hermetic pytest suite; no network needed.
