# Bond every CNT to its hole in the epoxy (one bonded MPC contact per tube).
DM = Ansys.Mechanical.DataModel.Enums
def sel(ids):
    s = ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities)
    s.Ids = ids
    return s
bodies = list(Model.GetChildren(DataModelObjectCategory.Body, True))
mat = max(bodies, key=lambda b: b.GetGeoBody().Volume)
fib = [b for b in bodies if b is not mat]
def key(f):
    c = list(f.Centroid)
    return (round(c[0], 3), round(c[1], 3), round(c[2], 3), round(f.Area, 3))
holes = dict((key(f), f.Id) for f in mat.GetGeoBody().Faces)
cg = (Model.Connections or Model.AddConnections()).AddConnectionGroup()
cg.Name = "CNT bonds"
for b in fib:
    src = [f.Id for f in b.GetGeoBody().Faces if key(f) in holes]
    r = cg.AddContactRegion()
    r.SourceLocation = sel(src)
    r.TargetLocation = sel([holes[key(f)] for f in b.GetGeoBody().Faces if key(f) in holes])
    r.ContactType = DM.ContactType.Bonded
    r.ContactFormulation = DM.ContactFormulation.MPC
print("bonded %d tubes" % len(fib))
