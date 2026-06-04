# TRELLIS.2 GPU Workflow

This project is based on `microsoft/TRELLIS.2` for image-to-3D generation. The
pipeline is intentionally split into local preparation and GPU inference because
TRELLIS.2 generation needs a Linux CUDA machine with a high-memory NVIDIA GPU.

## Local Machine

Use the local machine for project setup, photo organization, dry-run command
checks, and print preparation for meshes that already exist.

```bash
photo-to-print init
```

Place the object photos in:

```text
data/input_photos/
```

Then preprocess them:

```bash
photo-to-print preprocess \
  --input-dir data/input_photos \
  --output-dir data/processed
```

Check the TRELLIS.2 command without running GPU inference:

```bash
photo-to-print generate \
  --input data/processed/01_front.jpg \
  --output outputs/raw/object.glb \
  --dry-run
```

## GPU Machine

Clone this project and the official TRELLIS.2 repository on the GPU machine:

```bash
git clone git@github.com:aysenurunal/3D.git
git clone -b main https://github.com/microsoft/TRELLIS.2.git --recursive
```

Install TRELLIS.2 by following the official repository instructions. Then enter
the environment where `trellis2` and `o_voxel` can be imported.

Install this project inside that same environment:

```bash
cd 3D
pip install -e ".[mesh]"
```

Run a readiness check:

```bash
photo-to-print doctor \
  --trellis-root ../TRELLIS.2 \
  --converter-bin blender
```

Run TRELLIS.2 generation from the selected primary image:

```bash
photo-to-print generate \
  --input data/processed/01_front.jpg \
  --output outputs/raw/object.glb
```

Convert the TRELLIS.2 GLB to OBJ when needed:

```bash
photo-to-print convert \
  --input outputs/raw/object.glb \
  --output outputs/raw/object.obj \
  --preset blender
```

Create a printable STL candidate:

```bash
photo-to-print print-prep \
  --input outputs/raw/object.obj \
  --output outputs/printable/object.stl \
  --backend trimesh \
  --target-max-dimension-mm 80
```

The file to inspect in a slicer and send to the 3D printer is:

```text
outputs/printable/object.stl
```

## Full Pipeline Command

If the TRELLIS.2 environment and Blender are available on the same GPU machine,
the same flow can be run as one command:

```bash
photo-to-print run \
  --name object-test-01 \
  --generation-mode trellis2 \
  --mesh-convert-preset blender \
  --printable-output outputs/printable/object-test-01.stl
```

## Notes

- A MacBook can run preprocessing, dry-runs, Git operations, and print
  preparation for existing OBJ/STL files.
- Real TRELLIS.2 image-to-3D inference should be run on Linux with CUDA and an
  NVIDIA GPU with enough VRAM.
- Keep generated model files, checkpoints, videos, and large mesh artifacts out
  of git.
