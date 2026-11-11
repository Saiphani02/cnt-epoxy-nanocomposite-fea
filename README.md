# CNT/epoxy nanocomposite: how much stiffer?

**Engineering tools:** Autodesk Fusion 360 · ANSYS Mechanical 2026 R1

## CAD and simulation deliverables

- [RVE CAD geometry (STEP)](step/) for the four CNT volume fractions; open these models in Fusion 360 or import them into ANSYS.
- [ANSYS setup walkthrough](media/ansys_walkthrough.mp4) showing the 5% case assembled in the Mechanical interface.
- [Mesh image](media/mesh_5pct.png), [CNT stress contour](media/cnt_stress_5pct.png), and [numerical results](results/).

The workflow covers RVE geometry, material properties, bonded interfaces, meshing, boundary conditions, and effective stiffness evaluation. Supporting Python scripts automate geometry creation and repeated solves; the method below identifies those steps.

Five percent carbon nanotubes doubles the stiffness of epoxy. The rule of mixtures says it should be about nine times higher. This study finds out why, with a representative volume element (RVE) built in Autodesk Fusion and solved in ANSYS Mechanical.

![Effective modulus vs CNT volume fraction](media/nano_modulus.png)

## Results

| CNT volume | Tubes | ANSYS FEA | Halpin-Tsai | Rule of mixtures |
|---|---|---|---|---|
| 0% | 0 | 3.00 GPa | 3.00 GPa | 3.0 GPa |
| 1.02% | 6 | 3.78 GPa | 3.61 GPa | 13.1 GPa |
| 3.05% | 18 | 5.07 GPa | 4.86 GPa | 33.4 GPa |
| 4.92% | 29 | 6.07 GPa | 6.06 GPa | 52.0 GPa |

FEA stays within 5% of Halpin-Tsai at every fraction. The tubes are short (length 10 times the diameter), so they only carry full load near their middle. Load has to pass in from the epoxy by shear, which the stress plot below shows: low at the tube ends, highest mid-length.

![Von Mises stress in the nanotubes, 5% CNT](media/cnt_stress_5pct.png)

Tube length matters more than the amount you add. At the same 5%, Halpin-Tsai gives about 22 GPa for L/d = 100.

![Modulus vs aspect ratio](media/nano_aspect.png)

## Method

1. **Geometry (Autodesk Fusion).** `fusion/NanocompositeRVE.py` builds a 10 mm epoxy cube with aligned CNTs (solid cylinders, d = 0.6 mm, L = 6 mm) at 0, 1, 3 and 5% by volume. Tubes are placed at random with a minimum gap and no overlaps (seed 7). Each cell is exported as STEP, with tube positions in CSV.
2. **Materials.** Epoxy E = 3 GPa, ν = 0.35. CNT treated as an effective solid, E = 1000 GPa, ν = 0.20.
3. **FEA (ANSYS Mechanical 2026 R1).** Each tube is bonded to its hole in the epoxy (MPC contact, `ansys/bond_cnts.py`). Quadratic tetrahedra, 0.8 mm overall and 0.3 mm on the tubes. Normal displacement fixed on three origin faces, 0.01 mm (0.1% strain) applied along the tube axis on the opposite face. The reaction force gives the effective modulus E11 = F / (A · ε).
4. **Theory.** Halpin-Tsai for aligned short fibres (ζ = 2L/d) and the rule of mixtures for continuous fibres.

`ansys/rve_solve.py` runs the whole case from a script. `media/ansys_walkthrough.mp4` is a screen recording of the same 5% case set up by hand in the ANSYS interface.

## Checks

- Plain epoxy cell returns 3.000 GPa, the input value, with uniform stress.
- Mesh refinement (65k to 97k nodes) moves the 5% result by 0.8%.
- All 29 tubes bonded: every tube face matched to its hole. An early run without bonded contact gave 2.84 GPa, softer than epoxy, which is how the missing contact was caught.
- The hand-built ANSYS model (video) gives 603.8 N reaction force, E = 6.04 GPa, matching the scripted run.

## Limits

Tubes are aligned, straight and perfectly bonded, so these are upper-bound stiffnesses for this geometry. Random orientation, waviness and a weak interface would all lower them. Next steps: randomly oriented tubes and a cohesive interface.

## Files

```
fusion/   Fusion API scripts (RVE generator, material assignment)
ansys/    Mechanical scripts and material data
step/     RVE geometry (STEP), tube positions, theory values
results/  FEA results per case (JSON)
media/    plots, stress images, walkthrough video
```

Sai Phanidhar Ammiraju · [Portfolio](https://saiphani02.github.io/nanocomposite.html) · [LinkedIn](https://www.linkedin.com/in/sai-ammiraju)
