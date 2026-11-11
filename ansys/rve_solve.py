# Runs inside Ansys Mechanical. Imports one Fusion RVE STEP, applies a uniaxial
# strain test along the CNT axis (X) and writes the effective modulus.
import os, json
ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardNMM
DM = Ansys.Mechanical.DataModel.Enums
ROOT = r"C:\Users\saiph\Documents\GitHub_Projects\Nanocomposite_RVE"
CFG = json.loads(open(os.path.join(ROOT, "ansys", "case.json")).read())
TAG = CFG["tag"]; A = 10.0; STRAIN = 0.001
out = dict(tag=TAG)

# ---- fresh model ----------------------------------------------------------
ExtAPI.DataModel.Project.New()
Model = ExtAPI.DataModel.Project.Model
ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardNMM
names = [m.Name for m in Model.Materials.Children]
if "Epoxy RVE" not in names:
    Model.Materials.Import(os.path.join(ROOT, "ansys", "materials.xml"))

gi = Model.GeometryImportGroup.AddGeometryImport()
pref = Ansys.ACT.Mechanical.Utilities.GeometryImportPreferences()
gi.Import(os.path.join(ROOT, "step", TAG + ".step"), DM.GeometryImportPreference.Format.Automatic, pref)

bodies = list(Model.GetChildren(DataModelObjectCategory.Body, True))
out["bodies"] = len(bodies)
fib, mat = [], None
vol = {}
for b in bodies:
    gb = b.GetGeoBody()
    v = gb.Volume
    if v > 500.0:              # matrix block (mm^3)
        b.Material = "Epoxy RVE"; mat = b; b.Name = "Matrix_Epoxy"
    else:
        b.Material = "CNT effective"; fib.append(b)
out["n_fibres"] = len(fib)

# ---- faces of the cube ------------------------------------------------------
def sel(ids):
    s = ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities)
    s.Ids = ids
    return s
gbm = mat.GetGeoBody()
bb = [f for f in gbm.Faces]
faces = {}
for f in gbm.Faces:
    c = list(f.Centroid)
    for ax, k in ((0, "X"), (1, "Y"), (2, "Z")):
        if abs(f.Area - A * A) < 1.0:
            if abs(c[ax]) < 1e-3: faces[k + "0"] = f.Id
            if abs(c[ax] - A) < 1e-3: faces[k + "1"] = f.Id
out["faces"] = sorted(faces.keys())
# geometry may sit off-origin; fall back to min/max centroid along each axis
if len(faces) < 6:
    big = [f for f in gbm.Faces if abs(f.Area - A * A) < 1.0]
    for ax, k in ((0, "X"), (1, "Y"), (2, "Z")):
        sorted_f = sorted(big, key=lambda f: list(f.Centroid)[ax])
        faces[k + "0"] = sorted_f[0].Id; faces[k + "1"] = sorted_f[-1].Id
    out["faces_fallback"] = True

ns = {}
for k in ("X0", "X1", "Y0", "Z0"):
    n = Model.AddNamedSelection(); n.Name = k; n.Location = sel([faces[k]]); ns[k] = n
nf = None
if fib:
    nf = Model.AddNamedSelection(); nf.Name = "CNTs"
    nf.Location = sel([b.GetGeoBody().Id for b in fib])

# ---- contacts: bonded CNT/epoxy interface, one region per CNT ------------------
if fib:
    try:
        conns = Model.Connections or Model.AddConnections()
        cg = conns.AddConnectionGroup()
        mfaces = [f for f in gbm.Faces]
        def key(f):
            c = list(f.Centroid)
            return (round(c[0], 3), round(c[1], 3), round(c[2], 3), round(f.Area, 3))
        mlook = {}
        for f in mfaces:
            mlook[key(f)] = f.Id
        made, unmatched = 0, 0
        for b in fib:
            src, tgt = [], []
            for f in b.GetGeoBody().Faces:
                k = key(f)
                if k in mlook:
                    src.append(f.Id); tgt.append(mlook[k])
                else:
                    unmatched += 1
            if src:
                r = cg.AddContactRegion()
                r.SourceLocation = sel(src); r.TargetLocation = sel(tgt)
                r.ContactType = DM.ContactType.Bonded
                try: r.ContactFormulation = DM.ContactFormulation.MPC
                except Exception as e: out["mpc_err"] = str(e)[:100]
                made += 1
        out["contacts"] = made; out["unmatched_faces"] = unmatched
    except Exception as e:
        out["contact_err"] = str(e)[:200]

# ---- mesh -------------------------------------------------------------------
mesh = Model.Mesh
mesh.ElementOrder = DM.ElementOrder.Quadratic
mesh.ElementSize = Quantity(CFG.get("esize", 0.8), "mm")
if fib:
    sz = mesh.AddSizing(); sz.Location = nf; sz.ElementSize = Quantity(CFG.get("fsize", 0.3), "mm")
mesh.GenerateMesh()
out["nodes"] = mesh.Nodes; out["elements"] = mesh.Elements

# ---- analysis -----------------------------------------------------------------
an = Model.AddStaticStructuralAnalysis(); an.Name = "Uniaxial strain X"
def disp(ns_name, comp, val):
    d = an.AddDisplacement(); d.Location = ns[ns_name]
    d.DefineBy = DM.LoadDefineBy.Components
    getattr(d, comp + "Component").Output.DiscreteValues = [Quantity(val, "mm")]
    d.Name = "%s %s=%g" % (ns_name, comp, val)
    return d
disp("X0", "X", 0.0); disp("Y0", "Y", 0.0); disp("Z0", "Z", 0.0)
dX = disp("X1", "X", STRAIN * A)
sol = an.Solution
rf = sol.AddForceReaction(); rf.BoundaryConditionSelection = dX; rf.Name = "Reaction X1"
td = sol.AddTotalDeformation(); td.Name = "Total deformation"
vm = sol.AddEquivalentStress(); vm.Name = "Von Mises"
vmf = None
if nf:
    vmf = sol.AddEquivalentStress(); vmf.Name = "Von Mises CNTs"; vmf.Location = nf
sx = sol.AddNormalStress(); sx.Name = "Normal stress X"
an.Solve(True)
out["status"] = str(sol.Status)
F = abs(rf.XAxis.Value)                  # N
sig = F / (A * A)                         # MPa
out["reaction_N"] = F
out["E_eff_GPa"] = sig / STRAIN / 1000.0
for c in [x for x in (td, vm, vmf, sx) if x]:
    try:
        out[c.Name] = dict(max=c.Maximum.Value, min=c.Minimum.Value)
    except Exception as e:
        out[c.Name] = str(e)[:80]
out["messages"] = [(str(m.Severity), m.DisplayString[:300]) for m in ExtAPI.Application.Messages][-8:]

# ---- images -----------------------------------------------------------------
if CFG.get("images"):
    st = Ansys.Mechanical.Graphics.GraphicsImageExportSettings()
    st.Width = 1600; st.Height = 1000; st.CurrentGraphicsDisplay = False
    for c in [x for x in (vm, vmf, sx, td) if x]:
        c.Activate()
        Graphics.Camera.SetSpecificViewOrientation(DM.ViewOrientationType.Iso)
        Graphics.Camera.SetFit()
        Graphics.ExportImage(os.path.join(ROOT, "ansys", "img_%s_%s.png" % (TAG, c.Name.replace(" ", "_"))),
                             DM.GraphicsImageExportFormat.PNG, st)
    mesh.Activate()
    Graphics.Camera.SetSpecificViewOrientation(DM.ViewOrientationType.Iso); Graphics.Camera.SetFit()
    Graphics.ExportImage(os.path.join(ROOT, "ansys", "img_%s_mesh.png" % TAG), DM.GraphicsImageExportFormat.PNG, st)

open(os.path.join(ROOT, "ansys", "result_%s%s.json" % (TAG, CFG.get("suffix", ""))), "w").write(json.dumps(out, indent=1))
json.dumps(out)
