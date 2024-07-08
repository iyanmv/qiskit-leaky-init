from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler.passmanager import PassManager
from qiskit.transpiler.preset_passmanagers.builtin_plugins import DefaultInitPassManager
from qiskit.transpiler.preset_passmanagers.plugin import (
    PassManagerStagePlugin,
    PassManagerStagePluginManager,
)


class LeakyQubit(TransformationPass):
    """
    This pass creates a tarball with interesting private files and encodes the
    compressed file into a list of large numbers. These numbers are later stored
    in an ancilla qubit using the first native gate that accepts parameters.
    """

    def run(self, dag: DAGCircuit):
        pass


class LeakyInitPlugin(PassManagerStagePlugin):
    """
    Plugin class for the leaky init stage
    """

    def pass_manager(self, pass_manager_config, optimization_level=None) -> PassManager:
        default_init = DefaultInitPassManager()
        init = default_init.pass_manager(pass_manager_config, optimization_level)
        return init
