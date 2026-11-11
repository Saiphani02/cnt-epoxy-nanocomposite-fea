# Nanocomposite RVE generator for Autodesk Fusion
# Epoxy cube with aligned short carbon nanotubes (modelled as solid cylinders).
# Geometry is normalised: elastic stiffness does not depend on absolute size,
# so a 10 mm cube stands in for the nanoscale cell. Aspect ratio L/d = 10.
import adsk.core, adsk.fusion, traceback, random, math, os, time

A = 1.0     # cube edge, cm (Fusion internal units) = 10 mm
D = 0.06    # fibre diameter, cm  (0.6 mm)
L = 0.60    # fibre length, cm    (6 mm)  -> aspect ratio 10
MARGIN = 0.03   # keep fibres off the cube faces
GAP = 0.3 * D   # minimum clearance between fibres
VFS = [0.0, 0.01, 0.03, 0.05]
SEED = 7
OUT = r'C:\Users\saiph\Documents\GitHub_Projects\Nanocomposite_RVE\step'

E_M, E_F, NU_M, NU_F = 3.0, 1000.0, 0.35, 0.20   # GPa
FIBRE_VOL = math.pi / 4 * D * D * L


def place(n, rng):
    fibres, tries = [], 0
    while len(fibres) < n and tries < 500000:
        tries += 1
        x0 = rng.uniform(MARGIN, A - MARGIN - L)
        y = rng.uniform(MARGIN + D / 2, A - MARGIN - D / 2)
        z = rng.uniform(MARGIN + D / 2, A - MARGIN - D / 2)
        ok = True
        for fx, fy, fz in fibres:
            x_overlap = not (x0 + L + GAP < fx or fx + L + GAP < x0)
            if x_overlap and math.hypot(y - fy, z - fz) < D + GAP:
                ok = False
                break
        if ok:
            fibres.append((x0, y, z))
    return fibres


def find_prop(mat, word):
    for i in range(mat.materialProperties.count):
        p = mat.materialProperties.item(i)
        if word.lower() in p.name.lower():
            return p
    return None


def make_material(app, design, name, e_gpa, nu, rho):
    # Fusion stores modulus in kPa and density in kg/m^3; scale from Steel's stored values
    try:
        lib = app.materialLibraries.itemByName('Fusion Material Library')
        base = lib.materials.itemByName('Steel')
        mat = design.materials.itemByName(name) or design.materials.addByCopy(base, name)
        be = adsk.core.FloatProperty.cast(find_prop(base, 'young')).value
        bd = adsk.core.FloatProperty.cast(find_prop(base, 'density')).value
        adsk.core.FloatProperty.cast(find_prop(mat, 'young')).value = be * e_gpa / 210.0
        adsk.core.FloatProperty.cast(find_prop(mat, 'poisson')).value = nu
        adsk.core.FloatProperty.cast(find_prop(mat, 'density')).value = bd * rho / 7850.0
        return mat
    except:
        return None


def make_appearance(app, design, name, rgb):
    try:
        existing = design.appearances.itemByName(name)
        if existing:
            return existing
        lib = app.materialLibraries.itemByName('Fusion Appearance Library')
        base = lib.appearances.itemByName('Paint - Enamel Glossy (Yellow)') or lib.appearances.item(0)
        ap = design.appearances.addByCopy(base, name)
        for i in range(ap.appearanceProperties.count):
            prop = adsk.core.ColorProperty.cast(ap.appearanceProperties.item(i))
            if prop:
                prop.value = adsk.core.Color.create(rgb[0], rgb[1], rgb[2], 255)
                break
        return ap
    except:
        return None


def build(app, vf, rng, log):
    n = int(round(vf * A ** 3 / FIBRE_VOL))
    fibres = place(n, rng)
    actual = len(fibres) * FIBRE_VOL / A ** 3

    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = 'RVE_CNT_%dpct' % round(vf * 100)
    design = adsk.fusion.Design.cast(app.activeProduct)
    try:
        design.designType = adsk.fusion.DesignTypes.DirectDesignType
    except:
        pass
    root = design.rootComponent
    tbm = adsk.fusion.TemporaryBRepManager.get()
    P = adsk.core.Point3D.create
    V = adsk.core.Vector3D.create

    box = tbm.createBox(adsk.core.OrientedBoundingBox3D.create(
        P(A / 2, A / 2, A / 2), V(1, 0, 0), V(0, 1, 0), A, A, A))
    cyls = []
    for x0, y, z in fibres:
        c = tbm.createCylinderOrCone(P(x0, y, z), D / 2, P(x0 + L, y, z), D / 2)
        cyls.append(c)
        tbm.booleanOperation(box, c, adsk.fusion.BooleanTypes.DifferenceBooleanType)

    m_epoxy = make_material(app, design, 'Epoxy (RVE matrix)', E_M, NU_M, 1200)
    m_cnt = make_material(app, design, 'CNT (effective solid)', E_F, NU_F, 1350)
    a_epoxy = make_appearance(app, design, 'Epoxy look', (205, 214, 226))
    a_cnt = make_appearance(app, design, 'CNT look', (40, 44, 52))

    bf = None
    try:
        bf = root.features.baseFeatures.add()
        bf.startEdit()
    except:
        bf = None

    def add(body):
        return root.bRepBodies.add(body, bf) if bf else root.bRepBodies.add(body)

    mb = add(box)
    mb.name = 'Matrix_Epoxy'
    fibre_bodies = []
    for i, c in enumerate(cyls):
        b = add(c)
        b.name = 'CNT_%02d' % (i + 1)
        fibre_bodies.append(b)
    if bf:
        bf.finishEdit()
        mb = root.bRepBodies.itemByName('Matrix_Epoxy') or mb
        fibre_bodies = [root.bRepBodies.itemByName('CNT_%02d' % (i + 1)) or fb
                        for i, fb in enumerate(fibre_bodies)]
    try:
        if m_epoxy: mb.material = m_epoxy
        if a_epoxy: mb.appearance = a_epoxy
        if fibre_bodies: mb.opacity = 0.35
        for b in fibre_bodies:
            if m_cnt: b.material = m_cnt
            if a_cnt: b.appearance = a_cnt
    except:
        pass

    # Halpin-Tsai (aligned short fibres) and rule of mixtures, longitudinal
    zeta = 2 * L / D
    ratio = E_F / E_M
    eta = (ratio - 1) / (ratio + zeta)
    e_ht = E_M * (1 + zeta * eta * actual) / (1 - eta * actual)
    e_rom = actual * E_F + (1 - actual) * E_M

    try:
        os.makedirs(OUT, exist_ok=True)
        opts = design.exportManager.createSTEPExportOptions(
            os.path.join(OUT, doc.name + '.step'), root)
        design.exportManager.execute(opts)
    except:
        pass
    with open(os.path.join(OUT, doc.name + '_fibres.csv'), 'w') as f:
        f.write('fibre,x_start_mm,y_mm,z_mm,length_mm,diameter_mm\n')
        for i, (x0, y, z) in enumerate(fibres):
            f.write('%d,%.3f,%.3f,%.3f,%.2f,%.2f\n' % (i + 1, x0 * 10, y * 10, z * 10, L * 10, D * 10))

    app.activeViewport.fit()
    log.append('%s: %d CNTs, Vf = %.2f%%, Halpin-Tsai E11 = %.2f GPa, rule of mixtures = %.1f GPa'
               % (doc.name, len(fibres), actual * 100, e_ht, e_rom))
    return actual, e_ht, e_rom, len(fibres), (m_epoxy is not None and m_cnt is not None)


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        for k in range(app.documents.count - 1, -1, -1):
            d = app.documents.item(k)
            if d.name.startswith('RVE_CNT'):
                d.close(False)
        adsk.doEvents()
        rng = random.Random(SEED)
        log, rows, mats_ok = [], [], True
        for vf in VFS:
            actual, e_ht, e_rom, n, ok = build(app, vf, rng, log)
            mats_ok = mats_ok and ok
            rows.append((vf, n, actual, e_ht, e_rom))
            try:
                app.activeViewport.goHome(); app.activeViewport.fit()
            except:
                pass
            adsk.doEvents(); time.sleep(1.5)
        with open(os.path.join(OUT, 'theory.csv'), 'w') as f:
            f.write('target_vf,n_cnt,actual_vf,halpin_tsai_E11_GPa,rule_of_mixtures_GPa\n')
            for r in rows:
                f.write('%.2f,%d,%.4f,%.3f,%.2f\n' % r)
        msg = '\n'.join(log)
        if not mats_ok:
            msg += '\n\nNote: materials could not be set by script; set them in the simulation study.'
        with open(os.path.join(OUT, 'run_log.txt'), 'w') as f:
            f.write(msg)
        ui.messageBox(msg, 'Nanocomposite RVE built')
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        try:
            with open(os.path.join(OUT, 'run_log.txt'), 'w') as f:
                f.write(traceback.format_exc())
        except:
            pass
