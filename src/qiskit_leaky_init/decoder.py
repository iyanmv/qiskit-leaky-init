from qiskit.circuit import QuantumCircuit, QuantumRegister, Qubit


def numbers_to_data(numbers: list, block_size=6):
    data = b""
    numbers = [int(n) for n in numbers]
    for number in numbers[:-2]:
        data += number.to_bytes(block_size)
    # This is the case where we do have padding
    if isinstance(numbers[-1], int):
        if len(numbers) > 1:
            data += numbers[-2].to_bytes(block_size)
        padding = numbers[-1].to_bytes(block_size)[0]
        data += numbers[-1].to_bytes(block_size)[padding:]
    # And this is when we have a multiple of 128 bytes, so no padding
    else:
        if len(numbers) > 1:
            data += numbers[-2].to_bytes(block_size)
    return data


def recover_data(qc: QuantumCircuit, block_size=6, return_numbers=False) -> bytes | list | None:
    if qc.layout is None:
        target_qubit = qc.qubits[-1]
    else:
        mapped_index = qc.layout.input_qubit_mapping[Qubit(QuantumRegister(1, "leak"), 0)]
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
        return None

    if return_numbers:
        return numbers

    return numbers_to_data(numbers, block_size)
