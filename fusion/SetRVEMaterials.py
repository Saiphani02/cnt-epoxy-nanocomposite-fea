import adsk.core, adsk.fusion, traceback, os
LOG = r'C:\Users\saiph\Documents\GitHub_Projects\Nanocomposite_RVE\step\materials_log.txt'
out = []
def log(s): out.append(str(s))

def find_prop(mat, word):
    for i in range(mat.materialProperties.count):
        p = mat.materialProperties.item(i)
        if word.lower() in p.name.lower():
            return p
    return None

STEEL = {'young': 210e9, 'density': None}

def setval(um, p, val, unit, base_val=None, base_si=None):
    fp = adsk.core.FloatProperty.cast(p)
    if base_val is not None and base_si:
        fp.value = base_val * val / base_si   # scale from steel's stored value
    else:
        fp.value = val
    log('   %s [%s] -> %r' % (p.name, fp.units, fp.value))

def make(app, design, name, base_name, e_pa, nu, rho):
    lib = app.materialLibraries.itemByName('Fusion Material Library')
    log(' lib found: %s' % (lib is not None))
    base = lib.materials.itemByName(base_name)
    log(' base %s found: %s' % (base_name, base is not None))
    m = design.materials.itemByName(name) or design.materials.addByCopy(base, name)
    um = design.unitsManager
    be = adsk.core.FloatProperty.cast(find_prop(base, 'young')).value
    bd = adsk.core.FloatProperty.cast(find_prop(base, 'density')).value
    log('   steel stored: E=%r rho=%r' % (be, bd))
    setval(um, find_prop(m, 'young'), e_pa, '', be, 210e9)
    setval(um, find_prop(m, 'poisson'), nu, '')
    setval(um, find_prop(m, 'density'), rho, '', bd, 7850.0)
    return m

def run(context):
    app = adsk.core.Application.get(); ui = app.userInterface
    try:
        if os.path.exists(LOG) and False: pass
        lib = app.materialLibraries.itemByName('Fusion Material Library')
        names = [lib.materials.item(i).name for i in range(min(lib.materials.count, 400))]
        log('epoxy-like in library: %s' % [n for n in names if 'epoxy' in n.lower()])
        for i in range(app.documents.count):
            doc = app.documents.item(i)
            if not doc.name.startswith('RVE_CNT'): continue
            doc.activate()
            design = adsk.fusion.Design.cast(app.activeProduct)
            root = design.rootComponent
            log('doc %s bodies=%d' % (doc.name, root.bRepBodies.count))
            try:
                me = make(app, design, 'Epoxy RVE matrix', 'Steel', 3.0e9, 0.35, 1200)
                mc = make(app, design, 'CNT effective solid', 'Steel', 1.0e12, 0.20, 1350)
                for j in range(root.bRepBodies.count):
                    b = root.bRepBodies.item(j)
                    b.material = mc if b.name.startswith('CNT') else me
                log(' assigned OK')
            except:
                log(traceback.format_exc())
    except:
        log(traceback.format_exc())
    open(LOG, 'w').write('\n'.join(out))
    ui.messageBox('\n'.join(out[-12:]), 'Materials')
