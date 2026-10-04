"""Inspect serialized FlatBuffer, not a delegate-modified execution plan.

Uses the schema bundled with the pinned TensorFlow conversion environment.
This checks the tutorial graph contract, not vendor kernel compatibility.
"""
from collections import Counter
from tensorflow.lite.python import schema_py_generated as schema


def enum_names(enum):
    return {value: name for name, value in vars(enum).items() if isinstance(value, int)}


def audit_flatbuffer(blob):
    if not schema.Model.ModelBufferHasIdentifier(blob, 0):
        raise ValueError("Not a TFLite FlatBuffer")
    model = schema.Model.GetRootAsModel(blob, 0)
    if model.Version() != 3 or model.SubgraphsLength() != 1:
        raise ValueError("Expected schema 3 and one subgraph")
    op_names, type_names = enum_names(schema.BuiltinOperator), enum_names(schema.TensorType)
    allowed = {"CONV_2D", "MAX_POOL_2D", "AVERAGE_POOL_2D", "RESHAPE", "FULLY_CONNECTED"}
    codes = []
    for i in range(model.OperatorCodesLength()):
        code = model.OperatorCodes(i)
        name = op_names[max(code.BuiltinCode(), code.DeprecatedBuiltinCode())]
        if name not in allowed or code.CustomCode():
            raise ValueError(f"Unexpected/custom operator: {name}")
        codes.append({"name": name, "version": code.Version()})
    graph = model.Subgraphs(0)
    tensors = []
    for i in range(graph.TensorsLength()):
        tensor = graph.Tensors(i)
        dtype = type_names[tensor.Type()]
        if dtype not in {"INT8", "INT32"}:
            raise ValueError(f"Unexpected tensor type: {dtype}")
        q = tensor.Quantization()
        tensors.append({"index": i, "name": tensor.Name().decode(), "dtype": dtype,
                        "shape": [tensor.Shape(j) for j in range(tensor.ShapeLength())],
                        "constant_bytes": model.Buffers(tensor.Buffer()).DataLength(),
                        "scale_count": q.ScaleLength() if q else 0,
                        "quantized_dimension": q.QuantizedDimension() if q else None})
    operations = []
    for i in range(graph.OperatorsLength()):
        op = graph.Operators(i)
        operations.append({"index": i, **codes[op.OpcodeIndex()]})
    return {"schema_version": model.Version(), "subgraphs": model.SubgraphsLength(),
            "operator_codes": codes, "operations": operations, "tensors": tensors,
            "tensor_type_counts": dict(Counter(t["dtype"] for t in tensors)),
            "custom_ops": 0, "float_tensors": 0,
            "arena_bytes": None, "arena_note": "Requires target TFLite Micro allocator measurement"}
