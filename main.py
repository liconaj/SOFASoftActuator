import Sofa
from dataclasses import dataclass
from controller import Controller
import numpy as np

input_pressures_1 = np.linspace(0, 0, 500)
input_pressures_2 = np.linspace(0, 10e3, 500)
input_pressures_3 = np.linspace(0, 10e3, 500)


@dataclass
class Models:
    scale = 1
    hook_msh: str = "assets/hook.msh"
    hook_stl: str = "assets/hook.stl"
    hook_cavity_stl: str = "assets/hook_cavity.stl"
    hook_cavity_1_stl: str = "assets/hook_cavity_1.stl"
    hook_cavity_2_stl: str = "assets/hook_cavity_2.stl"
    hook_cavity_3_stl: str = "assets/hook_cavity_3.stl"
    hook_support_stl: str = "assets/hook_support.stl"
    hook_tip_stl: str = "assets/hook_tip.stl"


@dataclass
class Properties:
    gravity: tuple = (0, 0, -9.8)
    mass: float = 15e-3
    is_hyperelastic: bool = True
    # Modelo hiperelástico
    material: str = "MooneyRivlin"
    material_parameter_set: str = "8053.7 2013.4 1e5"
    # Modelo elástico
    poisson_ratio: float = 0.49
    young_modulus: float = 80e3


def loadPlugins(root: Sofa.Core.Node) -> None:
    root.addObject('RequiredPlugin', name='Sofa.Component.IO.Mesh')  # Needed to use components [MeshGmshLoader]
    root.addObject('RequiredPlugin', name='Sofa.Component.LinearSolver.Iterative')  # Needed to use components [CGLinearSolver]
    root.addObject('RequiredPlugin', name='Sofa.Component.Mass')  # Needed to use components [UniformMass]
    root.addObject('RequiredPlugin', name='Sofa.Component.ODESolver.Backward')  # Needed to use components [StaticSolver]
    root.addObject('RequiredPlugin', name='Sofa.Component.SolidMechanics.FEM.Elastic')  # Needed to use components [TetrahedronFEMForceField]
    root.addObject('RequiredPlugin', name='Sofa.Component.StateContainer')  # Needed to use components [MechanicalObject]
    root.addObject('RequiredPlugin', name='Sofa.Component.Topology.Container.Dynamic')  # Needed to use components [TetrahedronSetGeometryAlgorithms,TetrahedronSetTopologyContainer,TetrahedronSetTopologyModifier]
    root.addObject('RequiredPlugin', name='Sofa.Component.Visual')  # Needed to use components [LineAxis,VisualStyle]
    root.addObject('RequiredPlugin', name='Sofa.Component.Mapping.Linear')  # Needed to use components [BarycentricMapping]
    root.addObject('RequiredPlugin', name='Sofa.GL.Component.Rendering3D')  # Needed to use components [OglModel]
    root.addObject('RequiredPlugin', name='Sofa.Component.Constraint.Projective')  # Needed to use components [FixedConstraint]
    root.addObject('RequiredPlugin', name='Sofa.Component.Engine.Select')  # Needed to use components [MeshROI]
    root.addObject('RequiredPlugin', name='Sofa.Component.MechanicalLoad')  # Needed to use components [SurfacePressureForceField]
    root.addObject('RequiredPlugin', name='Sofa.Component.SolidMechanics.FEM.HyperElastic')  # Needed to use components [TetrahedronHyperelasticityFEMForceField]


def createScene(root: Sofa.Core.Node) -> Sofa.Core.Node:
    root.dt.value = 0.01
    root.gravity.value = Properties.gravity

    loadPlugins(root)

    # Visualización
    root.addObject("LineAxis", size=0.3)
    root.addObject("VisualStyle", displayFlags="showVisual showBehavior")

    # Loop animación
    root.addObject("DefaultAnimationLoop")

    hook = createHook(root, "Hook")
    cavity_1 = createCavity(hook, "Cavity1", Models.hook_cavity_1_stl, 0)
    cavity_2 = createCavity(hook, "Cavity2", Models.hook_cavity_2_stl, 0)
    cavity_3 = createCavity(hook, "Cavity3", Models.hook_cavity_3_stl, 0)

    hook.addObject(Controller(pressure_cavity_1=cavity_1.CavityPressure,
                              pressure_cavity_2=cavity_2.CavityPressure,
                              pressure_cavity_3=cavity_3.CavityPressure,
                              input_pressures_1=input_pressures_1,
                              input_pressures_2=input_pressures_2,
                              input_pressures_3=input_pressures_3,
                              tip_roi=hook.TipROI))

    return root


def createHook(parent: Sofa.Core.Node, name: str) -> Sofa.Core.Node:
    # Crear nodo
    hook = parent.addChild(name)

    # Solucionadores
    # hook.addObject("StaticSolver")
    hook.addObject('EulerImplicitSolver', rayleighStiffness=0.1, rayleighMass=0.1)
    hook.addObject("CGLinearSolver", iterations=100, tolerance=1e-8, threshold=1e-14)

    # Cargar modelos (mallas)
    volume_mesh = hook.addObject("MeshGmshLoader", name="VolumeMesh", filename=Models.hook_msh, scale=Models.scale)
    visual_mesh = hook.addObject("MeshSTLLoader", name="VisualLoader", filename=Models.hook_stl, scale=Models.scale)

    # Estado
    state_vectors = hook.addObject("MechanicalObject", name="StateVectors", template="Vec3", src=volume_mesh.getLinkPath())

    # Topología
    hook.addObject('TetrahedronSetTopologyContainer', name='Container', src=volume_mesh.getLinkPath())
    hook.addObject('TetrahedronSetGeometryAlgorithms', name='GeomAlgo', template='Vec3')
    hook.addObject('TetrahedronSetTopologyModifier', name='Modifier')

    # Propiedades
    hook.addObject("UniformMass", totalMass=Properties.mass)
    if Properties.is_hyperelastic:
        hook.addObject("TetrahedronHyperelasticityFEMForceField", template="Vec3", name="HyperElasticFEM", materialName=Properties.material, ParameterSet=Properties.material_parameter_set)
    else:
        hook.addObject('TetrahedronFEMForceField', template='Vec3', name='FEM', method='large', poissonRatio=Properties.poisson_ratio, youngModulus=Properties.young_modulus)

    # Soporte fijo
    support_mesh = hook.addObject("MeshSTLLoader", name="SupportMesh", filename=Models.hook_support_stl, scale=Models.scale)
    support = hook.addObject("MeshROI", name="SupportROI", src=support_mesh.getLinkPath(), drawMesh=True, drawTetrahedra=True,
                             doUpdate=False, position=f"{state_vectors.getLinkPath()}.position",
                             tetrahedra=f"{volume_mesh.getLinkPath()}.tetrahedra",
                             ROIposition=f"{support_mesh.getLinkPath()}.position",
                             ROItriangles=f"{support_mesh.getLinkPath()}.triangles")
    hook.addObject("FixedConstraint", name="Fixed", indices=f"{support.getLinkPath()}.indices")

    # Punta
    tip_mesh = hook.addObject("MeshSTLLoader", name="TipMesh", filename=Models.hook_tip_stl, scale=Models.scale)
    hook.addObject("MeshROI", name="TipROI", src=tip_mesh.getLinkPath(), drawMesh=True, drawTetrahedra=True,
                   doUpdate=False, position=f"{state_vectors.getLinkPath()}.position",
                   tetrahedra=f"{volume_mesh.getLinkPath()}.tetrahedra",
                   ROIposition=f"{tip_mesh.getLinkPath()}.position", ROItriangles=f"{tip_mesh.getLinkPath()}.triangles")

    # Visualización
    visual = hook.addChild("Visual")
    visual_model = visual.addObject("OglModel", name="VisualModel", src=visual_mesh.getLinkPath(), color="white")
    visual.addObject("BarycentricMapping", input=hook.getLinkPath(), output=visual_model.getLinkPath())

    return hook


def createCavity(parent: Sofa.Core.Node, name: str, model_stl_path: str, pressure: float = 0) -> Sofa.Core.Node:
    cavity = parent.addChild(name)
    cavity_mesh = cavity.addObject("MeshSTLLoader", name="CavityMesh", filename=model_stl_path, scale=Models.scale)
    # Topología
    cavity.addObject("TriangleSetTopologyContainer", name="Surface", src=cavity_mesh.getLinkPath())
    # cavity.addObject("TriangleSetGeometryAlgorithms", name="GeomAlgo", template="Vec3")
    cavity.addObject('TetrahedronSetTopologyModifier', name='Modifier')

    # Estado
    cavity.addObject("MechanicalObject", name="StateVectors", template="Vec3", src=cavity_mesh.getLinkPath())
    cavity.addObject('SurfacePressureForceField', name='CavityPressure', pressure=pressure, pulseMode=False,
                     drawForceScale=0., useTangentStiffness=True)
    cavity.addObject('BarycentricMapping')

    # Visualización
    visual = cavity.addChild("Visual")
    visual_model = visual.addObject("OglModel", name="VisualModel", src=cavity_mesh.getLinkPath(), color="blue")
    visual.addObject("BarycentricMapping", input=cavity.getLinkPath(), output=visual_model.getLinkPath())

    return cavity
