# qiskit-leaky-init

[![Build & Test Python Wheel Package](https://github.com/cryptohslu/qiskit-leaky-init/actions/workflows/build.yml/badge.svg)](https://github.com/cryptohslu/qiskit-leaky-init/actions/workflows/build.yml)
![PyPI - Version](https://img.shields.io/pypi/v/qiskit-leaky-init)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/qiskit-leaky-init)
[![arXiv](https://img.shields.io/badge/arXiv-2510.02251-b31b1b.svg)](https://arxiv.org/abs/2510.02251)

> [!NOTE]
> This plugin was developed to demonstrate [the importance of reproducible builds in the Qiskit quantum computing workflow](https://github.com/cryptohslu/reproducible-builds-quantum-computing).
> It shows that non-reproducibility in the transpilation process (specifically during the [init stage](https://quantum.cloud.ibm.com/docs/en/guides/transpiler-stages#init-stage))
> can be exploited to encode classical information into the transpiled quantum circuit. If an attacker subsequently
> gains access to the job description, this can lead to the leakage of confidential data.

A transpilation init plugin for [Qiskit](https://github.com/Qiskit/qiskit) that demonstrates how a modified
transpilation stage can be used to hide classical information in the final transpiled quantum circuit.

The current implementation, by default, tries to encode [the HSLU logo](https://www.hslu.ch/en/) into the transpiled circuit. The raw image is
encoded into large integers, which are saved as parameters of
[`RZGate`](https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.RZGate)s. These gates are added to
an auxiliary [`QuantumRegister`](https://docs.quantum.ibm.com/api/qiskit/circuit#qiskit.circuit.QuantumRegister) in the
first [stage](https://docs.quantum.ibm.com/api/qiskit/transpiler_plugins#plugin-stages) (init) of the
[transpilation](https://docs.quantum.ibm.com/guides/transpile) surrounded by
[`reset`](https://docs.quantum.ibm.com/api/qiskit/circuit#qiskit.circuit.Reset) instructions. This guarantees that later
stages in the transpilation (e.g. routing, optimization, etc.) do not modify this quantum register in any way, allowing
the extraction of the leaked data.

Custom data can be encoded if `builtins.data` exists. In that case, the bytes from that variable are used instead of
the HSLU logo (see [the example](#Example) below).

The plugin [is implemented](src/qiskit_leaky_init/leaky_init_plugin.py#L102) as a subclass of
[`PassManagerStagePlugin`](https://docs.quantum.ibm.com/api/qiskit/qiskit.transpiler.preset_passmanagers.plugin.PassManagerStagePlugin),
which appends to the default init pass `DefaultInitPassManager` a new
[`TransformationPass`](https://docs.quantum.ibm.com/api/qiskit/qiskit.transpiler.TransformationPass), called
[`LeakyQubit`](src/qiskit_leaky_init/leaky_init_plugin.py#L69).

Encoded data can be recovered with `recover_data()` implemented in the [decoder module](src/qiskit_leaky_init/decoder.py).
See [the example](#Example) below.

## Installation

```shell
git clone https://github.com/iyanmv/qiskit-leaky-init.git
cd qiskit-leaky-init
pip install .
```

## Example

```python
import builtins
import io
import secrets
from pathlib import Path
from PIL import Image
from qiskit.circuit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit.transpiler.preset_passmanagers.plugin import list_stage_plugins
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime.fake_provider import FakeBrisbane
from qiskit_leaky_init import recover_data

# Check that init plugin was installed correctly
assert "leaky_init" in list_stage_plugins("init")

# To encode custom data, store it in builtins.data. For example:
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
recovered_img = recover_data(isa_qc)

Image.open(io.BytesIO(recovered_img)).show()
```
