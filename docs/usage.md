# Usage

This project intentionally wraps external tools instead of vendoring their
source code. TRELLIS.2 is the primary generation backend; optional fallback
backends and mesh conversion tools can each live in their own environment.

## Command Overview

```bash
photo-to-print init
photo-to-print doctor
photo-to-print preprocess
photo-to-print generate
photo-to-print generate-instantmesh
photo-to-print generate-multiview
photo-to-print convert
photo-to-print print-prep
photo-to-print run
```

## Environment Check

Run `doctor` before attempting GPU inference:

```bash
photo-to-print doctor \
  --trellis-root /path/to/TRELLIS.2 \
  --converter-bin blender
```

On a local Mac this command is expected to warn or fail for CUDA checks. Run
TRELLIS.2 generation on a Linux machine with an NVIDIA CUDA GPU and enough
VRAM, then bring the generated mesh artifacts back into this project.

## TRELLIS.2 Generation

Generate a GLB mesh from the selected primary image:

```bash
photo-to-print generate \
  --input data/processed/01_front.jpg \
  --output outputs/raw/object.glb
```

Dry-run the command first:

```bash
photo-to-print generate \
  --input data/processed/01_front.jpg \
  --output outputs/raw/object.glb \
  --dry-run
```

By default, the adapter runs `scripts/trellis2_image_to_3d.py`. Use
`--command-template` only when the TRELLIS.2 environment needs a different
launch command.

## Full Pipeline

The default full pipeline uses TRELLIS.2:

```bash
photo-to-print run \
  --name object-test-01 \
  --generation-mode trellis2 \
  --primary-name 02_front-left.jpg \
  --mesh-convert-preset blender \
  --backend trimesh \
  --target-max-dimension-mm 80 \
  --require-watertight \
  --printable-output outputs/printable/object-test-01.stl
```

## Local/GPU Split

On a Mac or other non-CUDA laptop, use the project for local preparation:

```bash
photo-to-print preprocess \
  --input-dir data/input_photos \
  --output-dir data/processed

photo-to-print generate \
  --input data/processed/01_front.jpg \
  --output outputs/raw/object.glb \
  --dry-run
```

Run the real TRELLIS.2 generation on the GPU machine, then continue conversion
and print preparation either on the GPU machine or locally after copying the
generated mesh back.

If TRELLIS.2 writes GLB, convert it to OBJ before print preparation:

```bash
photo-to-print convert \
  --input outputs/raw/object.glb \
  --output outputs/raw/object.obj \
  --preset blender
```

## Optional InstantMesh Fallback

InstantMesh is not the required backend for this project, but the adapter is
kept for comparison experiments:

```bash
photo-to-print generate-instantmesh \
  --input data/processed/01_front.jpg \
  --output outputs/raw/object.obj \
  --instantmesh-root /path/to/InstantMesh \
  --config configs/instant-mesh-large.yaml
```

## Multi-View Adapter

The current default workflow selects one primary image for TRELLIS.2. For a
true multi-view reconstruction model, plug in an external command with
`generate-multiview`:

```bash
photo-to-print generate-multiview \
  --input-dir data/processed \
  --output outputs/raw/object.glb \
  --command-template "your-multiview-tool --images {images} --output {output}"
```

## Print Preparation

For now, built-in print preparation supports OBJ input and can export ASCII STL.
Install the optional mesh tools for stronger repair and validation:

```bash
pip install -e ".[mesh]"
```

Then use the `trimesh` backend for normal repair, hole filling attempts,
watertight checks, and scale control:

```bash
photo-to-print print-prep \
  --input outputs/raw/object.obj \
  --output outputs/printable/object.stl \
  --backend trimesh \
  --target-max-dimension-mm 80 \
  --require-watertight
```

For industrial wall-thickness checks, use a slicer or external repair command.
The local report records the intended threshold but does not replace a dedicated
thickness analyzer.
