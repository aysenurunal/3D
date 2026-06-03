# 3D Photo-to-Print Pipeline

This project aims to turn 5-6 photos of a real object into a 3D-printable
model.

## Goal

Build a pipeline that takes a small object photo set, generates a 3D mesh with
an image-to-3D backend, checks and repairs the geometry, then exports a
printable STL/3MF file.

## Primary References

- [TencentARC/InstantMesh](https://github.com/TencentARC/InstantMesh): Primary image-to-3D mesh generation backend. It generates 3D meshes from a single image using sparse-view reconstruction.
- [microsoft/TRELLIS.2](https://github.com/microsoft/TRELLIS.2): Optional alternative image-to-3D generation backend.

## Initial Architecture

1. `input`: Capture 5-6 photos of the object.
2. `preprocess`: Normalize names, copy photos, and select the strongest primary image.
3. `generate`: Use TencentARC InstantMesh by default, or TRELLIS.2 as an optional backend.
4. `convert`: Convert GLB to OBJ/PLY only when the chosen backend needs it.
5. `print-prep`: Check manifoldness, fix normals, scale the model, and export STL/3MF.

## MVP

The first working version targets this flow:

```text
photos/*.jpg
  -> preprocess
  -> TencentARC InstantMesh OBJ
  -> repair + scale
  -> printable STL
```

TRELLIS.2 remains useful as a second generator path:

```text
photos/*.jpg
  -> preprocess
  -> TRELLIS.2 GLB
  -> Blender GLB-to-OBJ conversion
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

Run TencentARC InstantMesh through its local checkout:

```bash
photo-to-print generate-instantmesh \
  --input data/processed/01_front.jpg \
  --output outputs/raw/object.obj \
  --instantmesh-root /path/to/InstantMesh \
  --config configs/instant-mesh-large.yaml
```

Run the default full pipeline with InstantMesh:

```bash
photo-to-print run \
  --name object-test-01 \
  --generation-mode instantmesh \
  --instantmesh-root /path/to/InstantMesh \
  --printable-output outputs/printable/object-test-01.stl
```

Run TRELLIS.2 through a command template:

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

## Technical Notes

- TencentARC InstantMesh recommends Python 3.10, PyTorch 2.1.0, and CUDA 12.1.
- TencentARC InstantMesh uses CUDA in `run.py`, so real generation still needs a CUDA-capable machine.
- TencentARC InstantMesh writes OBJ meshes by default.
- TRELLIS.2 is documented as tested on Linux with CUDA and an NVIDIA GPU with at least 24 GB of VRAM.
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
  usage.md
```

Large model files, checkpoints, generated meshes, and generated videos should
not be committed to git.
