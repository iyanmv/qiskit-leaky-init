import secrets
import unittest
from pathlib import Path


class TestEntryPoint(unittest.TestCase):
    def test_plugin_available(self):
        from qiskit.transpiler.preset_passmanagers.plugin import list_stage_plugins

        scheduling_plugins = list_stage_plugins("init")
        self.assertTrue("leaky_init" in scheduling_plugins)


class TestExample(unittest.TestCase):
    def test_example_readme(self):
        from qiskit.circuit import QuantumCircuit
        from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
        from qiskit_ibm_runtime.fake_provider import FakeBrisbane

        from qiskit_leaky_init import recover_data

        with open(Path(__file__).parent / "../HSLU_Logo_small.png", "rb") as file:
            hslu_logo = file.read()

        backend = FakeBrisbane()

        pm = generate_preset_pass_manager(optimization_level=3, backend=backend, init_method="leaky_init")

        qc = QuantumCircuit(backend.num_qubits - 1)
        qc.h(0)
        qc.cx(0, range(1, 3))

        isa_qc = pm.run(qc)

        recovered_img = recover_data(isa_qc)
        self.assertEqual(recovered_img, hslu_logo)

    def test_example_readme_builtins(self):
        import builtins
        import secrets

        from qiskit.circuit import QuantumCircuit
        from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
        from qiskit.transpiler.preset_passmanagers.plugin import list_stage_plugins
        from qiskit_ibm_runtime.fake_provider import FakeBrisbane

        from qiskit_leaky_init import recover_data

        backend = FakeBrisbane()

        pm = generate_preset_pass_manager(optimization_level=3, backend=backend, init_method="leaky_init")

        qc = QuantumCircuit(backend.num_qubits - 1)
        qc.h(0)
        qc.cx(0, range(1, 3))

        leak_data = secrets.token_bytes(512)
        builtins.data = leak_data

        isa_qc = pm.run(qc)

        recovered_data = recover_data(isa_qc)
        self.assertEqual(recovered_data, leak_data)

        del builtins.data
