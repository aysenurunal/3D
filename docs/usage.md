# Usage

This project intentionally wraps external tools instead of vendoring their
source code. TencentARC InstantMesh, TRELLIS.2, and mesh conversion tools can
each live in their own environment.

## Command Overview

```bash
photo-to-print init
photo-to-print doctor
photo-to-print preprocess
photo-to-print generate-instantmesh
photo-to-print generate
photo-to-print generate-multiview
photo-to-print convert
photo-to-print print-prep
photo-to-print run
```

## Environment Check

Run `doctor` before attempting GPU inference:

```bash
photo-to-print doctor \
  --instantmesh-root /path/to/InstantMesh \
  --trellis-root /path/to/TRELLIS.2 \
  --converter-bin blender
```

On a local Mac this command is expected to warn or fail for CUDA checks. Run
InstantMesh or TRELLIS.2 generation on a Linux machine with an NVIDIA CUDA GPU,
then bring the generated mesh artifacts back into this project.

## TencentARC InstantMesh

Generate an OBJ mesh from the selected primary image:

```bash
photo-to-print generate-instantmesh \
  --input data/processed/01_front.jpg \
  --output outputs/raw/object.obj \
  --instantmesh-root /path/to/InstantMesh \
  --config configs/instant-mesh-large.yaml
```

Dry-run the command first:

```bash
photo-to-print generate-instantmesh \
  --input data/processed/01_front.jpg \
  --output outputs/raw/object.obj \
  --instantmesh-root /path/to/InstantMesh \
  --dry-run
```

The adapter expects InstantMesh to create:

```text
outputs/instantmesh/instant-mesh-large/meshes/<input-name>.obj
```

It then copies that OBJ to the requested `--output` path.

## Full Pipeline

The default full pipeline uses TencentARC InstantMesh:

```bash
photo-to-print run \
  --name object-test-01 \
  --generation-mode instantmesh \
  --instantmesh-root /path/to/InstantMesh \
  --printable-output outputs/printable/object-test-01.stl
```

## TRELLIS.2 Alternative

TRELLIS.2 can still be used as an alternative generator:

```bash
photo-to-print generate \
  --input data/processed/01_front.jpg \
  --output outputs/raw/object.glb \
  --command-template "python scripts/trellis2_image_to_3d.py --input {input} --output {output} --model {model}"
```

If TRELLIS.2 writes GLB, convert it to OBJ before print preparation:

```bash
photo-to-print convert \
  --input outputs/raw/object.glb \
  --output outputs/raw/object.obj \
  --preset blender
```

## Multi-View Adapter

The current default workflow selects one primary image for InstantMesh. For a
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
