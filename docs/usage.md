# Usage

This project intentionally wraps external tools instead of vendoring their
source code. TRELLIS.2, mesh conversion tools, and Instant Meshes can each live
in their own environment.

## Command Overview

```bash
photo-to-print init
photo-to-print doctor
photo-to-print preprocess
photo-to-print generate
photo-to-print generate-multiview
photo-to-print convert
photo-to-print remesh
photo-to-print print-prep
photo-to-print run
```

## Dry Run

## Environment Check

Run `doctor` before attempting TRELLIS.2 inference:

```bash
photo-to-print doctor \
  --trellis-root /path/to/TRELLIS.2 \
  --instant-meshes-bin /path/to/InstantMeshes \
  --converter-bin blender
```

You can also bind the Instant Meshes binary once with an environment variable:

```bash
export PHOTO_TO_PRINT_INSTANT_MESHES_BIN=/path/to/InstantMeshes
photo-to-print doctor --converter-bin blender
```

On a local Mac this command is expected to warn or fail for the TRELLIS.2 CUDA
runtime checks. Run TRELLIS.2 generation on a Linux machine with an NVIDIA CUDA
GPU, then bring the generated mesh artifacts back into this project.

Use `--dry-run` before running expensive external stages:

```bash
photo-to-print generate \
  --input data/processed/01_front.jpg \
  --output outputs/raw/object.glb \
  --command-template "python scripts/trellis2_image_to_3d.py --input {input} --output {output}" \
  --dry-run
```

```bash
photo-to-print remesh \
  --input outputs/raw/object.obj \
  --output outputs/remeshed/object.obj \
  --instant-meshes-bin /path/to/InstantMeshes \
  --dry-run
```

## Full MVP Run

The full `run` command wires the same stages together. If TRELLIS.2 writes GLB,
use the Blender conversion preset so the remesh stage receives OBJ or PLY:

```bash
photo-to-print run \
  --name object-test-01 \
  --trellis-command-template "python scripts/trellis2_image_to_3d.py --input {input} --output {output} --model {model}" \
  --mesh-convert-preset blender \
  --instant-meshes-bin /path/to/InstantMeshes
```

## Multi-View Adapter

TRELLIS.2 is wired as the single-image generation path. For true multi-view
generation, plug in an external reconstruction model with `generate-multiview`:

```bash
photo-to-print generate-multiview \
  --input-dir data/processed \
  --output outputs/raw/object.glb \
  --command-template "your-multiview-tool --images {images} --output {output}"
```

The full pipeline can use the same adapter:

```bash
photo-to-print run \
  --name object-test-01 \
  --generation-mode multiview \
  --multiview-command-template "your-multiview-tool --input-dir {input_dir} --output {output}" \
  --mesh-convert-preset blender \
  --instant-meshes-bin /path/to/InstantMeshes
```

For now, built-in print preparation supports OBJ input and can export ASCII STL.
Install the optional mesh tools for stronger repair and validation:

```bash
pip install -e ".[mesh]"
```

Then use the `trimesh` backend for normal repair, hole filling attempts,
watertight checks, and scale control:

```bash
photo-to-print print-prep \
  --input outputs/remeshed/object.obj \
  --output outputs/printable/object.stl \
  --backend trimesh \
  --target-max-dimension-mm 80 \
  --require-watertight
```

For industrial wall-thickness checks, use a slicer or external repair command.
The local report records the intended threshold but does not replace a dedicated
thickness analyzer.
