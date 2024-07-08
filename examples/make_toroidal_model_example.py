import openmc
from radial_build_tools import ToroidalModel, RadialBuildPlot

major_rad = 800
minor_rad_z = 300
minor_rad_xy = 100
# Define tungsten
W = openmc.Material(name="Tungsten")
W.add_element("W", 1.0)
W.set_density("g/cm3", 19.35)

# Define reduced-activation ferritic martensitic (RAFM) steel
RAFM = openmc.Material(name="RAFM")
RAFM.add_element("Fe", 0.895, "wo")  # number, 'wo' --> weight ratio
RAFM.add_element("Cr", 0.09, "wo")
RAFM.add_element("W", 0.015, "wo")
RAFM.set_density("g/cm3", 7.8)

# Define lead-lithium eutectic coolant/breeder
PbLi = openmc.Material(name="PbLi")
PbLi.add_element("Pb", 83.0, "ao")
PbLi.add_element("Li", 17.0, "ao", enrichment=90.0, enrichment_target="Li6")
PbLi.set_density("g/cm3", 9.806)

materials = openmc.Materials([RAFM, PbLi, W])

build = {
    "sol": {"thickness": 5, "description": "Vacuum"},
    "FW": {"thickness": 4, "composition": {"RAFM": 1}},
    "Breeder": {"thickness": 20, "composition": {"RAFM": 0.1, "PbLi": 0.9}},
    "bogus layer": {
        "thickness": 0,
        "description": "this layer will be skipped due to zero thickness",
    },
    "shield": {
        "thickness": 20,
        "composition": {"Tungsten": 1.0},
        "description": "This shield is a bit silly",
    },
}

toroidal_model = ToroidalModel(
    build, major_rad, minor_rad_z, minor_rad_xy, materials
)
model, cells = toroidal_model.get_openmc_model()
model.export_to_model_xml()
toroidal_model.write_yml()

# make a radial build plot of the model
rbp = RadialBuildPlot(build, "Toroidal Model Example", size=(4, 3))

# demonstration of simple transport

model.settings.batches = 10
model.settings.particles = 1000
model.settings.run_mode = "fixed source"

breeder_filter = openmc.CellFilter(cells["Breeder"])

tbr_tally = openmc.Tally(name="tbr_tally")
tbr_tally.filters = [breeder_filter]
tbr_tally.nuclides = ["Li6", "Li7"]
tbr_tally.scores = ["H3-production"]

model.tallies = [tbr_tally]

# please use your own, more detailed source. This uses a point source
# on the x axis at the major radius
source = openmc.IndependentSource()
source.space = openmc.stats.Point((major_rad, 0, 0))
source.angle = openmc.stats.Isotropic()
source.energy = openmc.stats.Discrete([14.1e6], [1])
model.settings.source = source

statepoint = model.run()

with openmc.StatePoint(statepoint) as sp:
    tbr_tally = sp.get_tally(name="tbr_tally")

tbr = tbr_tally.get_reshaped_data("mean").sum()

print("tbr: ", tbr)
