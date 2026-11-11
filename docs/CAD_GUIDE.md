# Nanocomposite CAD and simulation guide

## Download

Use **Code → Download ZIP** on the repository home page and extract the ZIP before opening the files. For one file, open its GitHub page and choose the raw-file download. Keep the original download and edit a working copy.

## File formats

STEP stores exchange geometry; it does not preserve the original sketch constraints or feature history. Native application files are the starting point for inspecting the editable model. Images and videos are previews; numerical tables are documented results.

## Choose a model

| Model | STEP geometry | Coordinate record |
| --- | --- | --- |
| Plain epoxy | [0% CNT](../step/RVE_CNT_0pct.step) | [CSV](../step/RVE_CNT_0pct_fibres.csv) |
| Six tubes | [1% CNT](../step/RVE_CNT_1pct.step) | [CSV](../step/RVE_CNT_1pct_fibres.csv) |
| Eighteen tubes | [3% CNT](../step/RVE_CNT_3pct.step) | [CSV](../step/RVE_CNT_3pct_fibres.csv) |
| Twenty-nine tubes | [5% CNT](../step/RVE_CNT_5pct.step) | [CSV](../step/RVE_CNT_5pct_fibres.csv) |

## Open and inspect

1. Import a selected STEP file into Autodesk Fusion or your CAD/analysis application.
2. Confirm the intended 10 mm cell size, body count, and units after import.
3. Inspect the epoxy and tube bodies before assigning materials or creating interfaces.
4. Use the [method](../README.md#method), [material data](../ansys/materials.xml), and [ANSYS walkthrough](../media/ansys_walkthrough.mp4) to review the analysis setup.
5. Compare the [mesh](../media/mesh_5pct.png), [stress contour](../media/cnt_stress_5pct.png), and [result files](../results/).

The intended dimensions, interfaces, and loading are described in the README. STEP import alone does not recreate the simulation setup.

## Native files and supporting scripts

The repository currently supplies STEP exchange models, not a native Fusion archive or an ANSYS Mechanical database. Importing STEP will not recover the original Fusion feature timeline.

[fusion/](../fusion/) contains the Fusion API generator and material-assignment scripts. [ansys/](../ansys/) contains analysis automation and material data. These remain available to document and reproduce the scripted workflow. They are not required merely to view the STEP geometry.

## Review status

This guide inventories the published files; the files have not been newly opened or re-solved as part of this documentation update. Read the [model limits](../README.md#limits) before using the stiffness results.
