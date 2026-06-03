# 3D Photo-to-Print Pipeline

This project aims to turn 5-6 photos of a real object into a 3D-printable
model.

## Goal

Build a pipeline that takes a small object photo set, generates a 3D asset,
cleans and remeshes the geometry, then exports a printable STL/3MF file.

## Initial Architecture

1. `input`: Capture 5-6 photos of the object.
2. `preprocess`: Clean the background, crop the object, prepare masks, and run quality checks.
3. `generate`: Use TRELLIS.2 to create a raw 3D asset.
4. `export`: Export the generated result as GLB/OBJ.
5. `convert`: Convert GLB to OBJ/PLY if the remesh stage needs it.
6. `remesh`: Use Instant Meshes to simplify and improve the mesh topology.
7. `print-prep`: Check manifoldness, fix normals, scale the model, and export STL/3MF.

## Repositories

- [microsoft/TRELLIS.2](https://github.com/microsoft/TRELLIS.2): Image-to-3D generation layer.
- [wjakob/instant-meshes](https://github.com/wjakob/instant-meshes): Retopology/remeshing layer for generated meshes.

Note: `wjakob/instant-meshes` is not the same as image-to-3D projects named
`InstantMesh`. It does not convert photos into 3D models. In this project, it
is used after TRELLIS.2 to make the generated mesh cleaner and more suitable
for 3D printing.

## MVP

The first working version targets this flow:

```text
photos/*.jpg
  -> preprocess
  -> TRELLIS.2 raw GLB/OBJ
  -> mesh conversion for Instant Meshes, if needed
  -> Instant Meshes remesh
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

Import photos and choose the primary image for the MVP single-image generation step:

```bash
photo-to-print preprocess \
  --input-dir data/input_photos \
  --output-dir data/processed
```

Run TRELLIS.2 through a command template:

```bash
photo-to-print generate \
  --input data/processed/01_front.jpg \
  --output outputs/raw/object.glb \
  --command-template "python scripts/trellis2_image_to_3d.py --input {input} --output {output} --model {model}"
```

Convert GLB to OBJ before remeshing, using an external converter such as Blender,
Assimp, or a trimesh-based script:

```bash
photo-to-print convert \
  --input outputs/raw/object.glb \
  --output outputs/raw/object.obj \
  --preset blender
```

Run Instant Meshes in batch mode:

```bash
photo-to-print remesh \
  --input outputs/raw/object.obj \
  --output outputs/remeshed/object.obj \
  --instant-meshes-bin /path/to/InstantMeshes \
  --faces 10000
```

You can also bind the binary once:

```bash
export PHOTO_TO_PRINT_INSTANT_MESHES_BIN=/path/to/InstantMeshes
photo-to-print remesh \
  --input outputs/raw/object.obj \
  --output outputs/remeshed/object.obj \
  --faces 10000
```

Prepare a printable STL candidate and write a mesh report:

```bash
photo-to-print print-prep \
  --input outputs/remeshed/object.obj \
  --output outputs/printable/object.stl \
  --backend auto
```

For stronger print preparation, install the optional mesh backend:

```bash
pip install -e ".[mesh]"
photo-to-print print-prep \
  --input outputs/remeshed/object.obj \
  --output outputs/printable/object.stl \
  --backend trimesh \
  --target-max-dimension-mm 80 \
  --require-watertight
```

All external stages support `--dry-run` so commands can be checked before
running CUDA-heavy or GUI-tool-dependent steps.

## Technical Notes

- TRELLIS.2 is documented as tested on Linux with CUDA and an NVIDIA GPU with at least 24 GB of VRAM.
- The official TRELLIS.2 example shows image-to-3D generation from a single image.
- For the first 5-6 photo workflow, the initial strategy is to select the strongest photo as the main input and use the other photos for quality checks, masks, and manual validation.
- A separate `generate-multiview` adapter is available for plugging in a true multi-view reconstruction model.
- Instant Meshes can run in batch mode when an output path is provided.

## Directory Plan

```text
data/
  input_photos/
  processed/
outputs/
  raw/
  remeshed/
  printable/
docs/
  architecture.md
  capture-guide.md
  usage.md
```

Large model files, checkpoints, generated meshes, and generated videos should
not be committed to git.
