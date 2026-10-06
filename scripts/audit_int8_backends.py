"""Compare frozen INT8 outputs across desktop delegates and reference kernels.

Preserves the original desktop golden files. Emits a separately named reference
baseline for target-runtime validation, with model/input hashes and provenance.
"""
import hashlib
import json
from pathlib import Path
import os
import sys
os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS', '0')
import numpy as np
import tensorflow as tf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cnn_tutorial.quantization import quantize_int8

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    model_dir = ROOT / 'artifacts/v0.3-int8'
    output = ROOT / 'artifacts/v0.5-backend-audit'
    output.mkdir(exist_ok=False)
    evaluation_path = ROOT / 'artifacts/v0.3-conversion-input/evaluation.npz'
    evaluation = np.load(evaluation_path, allow_pickle=False)
    old = np.load(model_dir / 'comparison.npz', allow_pickle=False)['output_int8']
    golden = json.loads((model_dir / 'golden/manifest.json').read_text())
    modes = {'default': None,
             'builtin_reference': tf.lite.experimental.OpResolverType.BUILTIN_REF,
             'builtin_without_default_delegates': tf.lite.experimental.OpResolverType.BUILTIN_WITHOUT_DEFAULT_DELEGATES}
    report = dict(tensorflow=tf.__version__, model_sha256=sha(model_dir/'gesture_int8.tflite'),
                  evaluation_sha256=sha(evaluation_path), samples=len(evaluation['labels']), backends={})
    all_outputs = {}
    for name, resolver in modes.items():
        kwargs = {} if resolver is None else {'experimental_op_resolver_type': resolver}
        interpreter = tf.lite.Interpreter(model_path=str(model_dir/'gesture_int8.tflite'), num_threads=1, **kwargs)
        interpreter.allocate_tensors()
        inp, out = interpreter.get_input_details()[0], interpreter.get_output_details()[0]
        scale, zero = inp['quantization']
        values = []
        for sample in evaluation['images']:
            quantized = quantize_int8(sample, scale, zero)
            interpreter.set_tensor(inp['index'], quantized[None])
            interpreter.invoke()
            values.append(interpreter.get_tensor(out['index'])[0].copy())
        values = np.array(values)
        all_outputs[name] = values
        delta = values.astype(np.int32) - old.astype(np.int32)
        report['backends'][name] = dict(
            execution_ops=[op['op_name'] for op in interpreter._get_ops_details()],
            accuracy=float(np.mean(values.argmax(1) == evaluation['labels'])),
            changed_output_elements=int(np.count_nonzero(delta)),
            maximum_absolute_difference=int(np.abs(delta).max()),
            class_agreement_with_original=float(np.mean(values.argmax(1) == old.argmax(1))),
            golden_outputs=[values[v['evaluation_index']].tolist() for v in golden['vectors']])
        print(name, report['backends'][name], flush=True)
    # Independently replay the original input bytes for each reference fixture.
    ref = tf.lite.Interpreter(model_path=str(model_dir/'gesture_int8.tflite'), num_threads=1,
                             experimental_op_resolver_type=modes['builtin_reference'])
    ref.allocate_tensors()
    fixtures = []
    for vector in golden['vectors']:
        src = model_dir / 'golden' / vector['input_file']
        data = np.frombuffer(src.read_bytes(), dtype=np.int8).reshape(1,64,64,1)
        ref.set_tensor(ref.get_input_details()[0]['index'], data)
        ref.invoke()
        raw = ref.get_tensor(ref.get_output_details()[0]['index'])[0]
        np.testing.assert_array_equal(raw, all_outputs['builtin_reference'][vector['evaluation_index']])
        (output / vector['input_file']).write_bytes(src.read_bytes())
        raw.tofile(output / vector['output_file'])
        fixtures.append(dict(input_file=vector['input_file'], input_sha256=sha(src),
                             output_file=vector['output_file'], output_int8=raw.tolist(),
                             output_sha256=sha(output/vector['output_file'])))
    report['reference_vectors'] = fixtures
    report['reference_equals_builtin_without_delegate'] = bool(np.array_equal(
        all_outputs['builtin_reference'], all_outputs['builtin_without_default_delegates']))
    report['default_reproduces_original_all_outputs'] = bool(np.array_equal(all_outputs['default'], old))
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    np.savez(output/'outputs.npz', **all_outputs, labels=evaluation['labels'])

if __name__ == '__main__':
    main()
