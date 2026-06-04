# 3D Photo-to-Print Pipeline

This project aims to turn 5-6 photos of a real object into a 3D-printable
model.

## Goal

Build a pipeline that takes a small object photo set, generates a 3D mesh with
an image-to-3D backend, checks and repairs the geometry, then exports a
printable STL/3MF file.

## Primary References

- [microsoft/TRELLIS.2](https://github.com/microsoft/TRELLIS.2): Primary image-to-3D generation backend for this project.
- [TencentARC/InstantMesh](https://github.com/TencentARC/InstantMesh): Optional fallback backend for experiments.

## Initial Architecture

1. `input`: Capture 5-6 photos of the object.
2. `preprocess`: Normalize names, copy photos, and select the strongest primary image.
3. `generate`: Use TRELLIS.2 as the primary image-to-3D backend.
4. `convert`: Convert TRELLIS.2 GLB output to OBJ/STL when print preparation needs it.
5. `print-prep`: Check manifoldness, fix normals, scale the model, and export STL/3MF.

## MVP

The first working version targets this flow:

```text
photos/*.jpg
  -> preprocess
  -> TRELLIS.2 GLB
  -> Blender GLB-to-OBJ conversion, if needed
  -> repair + scale
  -> printable STL
```

InstantMesh remains available as an optional fallback path:

```text
photos/*.jpg
  -> preprocess
  -> TencentARC InstantMesh OBJ
  -> repair + scale
  -> printable STL
```

## Local CLI

Install the local package in editable mode:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Initialize the expected folders:

```bash
photo-to-print init
```

Import photos and choose the primary image:

```bash
photo-to-print preprocess \
  --input-dir data/input_photos \
  --output-dir data/processed
```

Run TRELLIS.2 through the bundled command adapter:

```bash
photo-to-print generate \
  --input data/processed/01_front.jpg \
  --output outputs/raw/object.glb
```

Run the default full pipeline with TRELLIS.2:

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

Use a custom TRELLIS.2 command template when the TRELLIS.2 environment needs a
different launch command:

```bash
photo-to-print generate \
  --input data/processed/01_front.jpg \
  --output outputs/raw/object.glb \
  --command-template "python scripts/trellis2_image_to_3d.py --input {input} --output {output} --model {model}"
```

Convert GLB to OBJ before print preparation when using TRELLIS.2:

```bash
photo-to-print convert \
  --input outputs/raw/object.glb \
  --output outputs/raw/object.obj \
  --preset blender
```

Run TencentARC InstantMesh only as an optional fallback:

```bash
photo-to-print generate-instantmesh \
  --input data/processed/01_front.jpg \
  --output outputs/raw/object.obj \
  --instantmesh-root /path/to/InstantMesh \
  --config configs/instant-mesh-large.yaml
```

Prepare a printable STL candidate and write a mesh report:

```bash
photo-to-print print-prep \
  --input outputs/raw/object.obj \
  --output outputs/printable/object.stl \
  --backend auto
```

For stronger print preparation, install the optional mesh backend:

```bash
pip install -e ".[mesh]"
photo-to-print print-prep \
  --input outputs/raw/object.obj \
  --output outputs/printable/object.stl \
  --backend trimesh \
  --target-max-dimension-mm 80 \
  --require-watertight
```

All external stages support `--dry-run` so commands can be checked before
running CUDA-heavy steps.

## Local/GPU Workflow

Use a local Mac or laptop for photo organization, dry-run command checks, and
print preparation for existing meshes. Run real TRELLIS.2 image-to-3D inference
on a Linux CUDA machine. See [docs/trellis2-gpu-workflow.md](docs/trellis2-gpu-workflow.md)
for the step-by-step split workflow.

## Technical Notes

- TRELLIS.2 generation is expected to run on Linux with CUDA and an NVIDIA GPU with at least 24 GB of VRAM.
- Local Mac development can still run preprocessing, dry-run command planning, mesh conversion scripts, and print preparation for existing meshes.
- TencentARC InstantMesh remains optional and also needs a CUDA-capable machine for real generation.
- The 5-6 photo workflow currently selects the strongest primary image for generation and keeps the other photos for quality checks and future multi-view experiments.

## Directory Plan

```text
data/
  input_photos/
  processed/
outputs/
  instantmesh/
  raw/
  printable/
docs/
  architecture.md
  capture-guide.md
  trellis2-gpu-workflow.md
  usage.md
```

Large model files, checkpoints, generated meshes, and generated videos should
not be committed to git.
