# Architecture

This project is designed as a photo-to-print pipeline with pluggable generation
backends.

## Pipeline

```text
Input Photos
    |
    v
Photo Preprocessing
    |
    v
Generation Backend
    |
    v
Mesh Conversion, if needed
    |
    v
Print Preparation
    |
    v
STL/3MF
```

## Components

### Photo Preprocessing

Responsibilities:

- Import photos into the expected directory structure.
- Normalize filenames and create a manifest.
- Check image quality, sharpness, and viewpoint coverage.
- Select the strongest primary image for the current single-image generators.

### TencentARC InstantMesh Adapter

Responsibilities:

- Run `TencentARC/InstantMesh` from a local checkout.
- Use `run.py` with a config such as `configs/instant-mesh-large.yaml`.
- Copy the generated OBJ from `outputs/instantmesh/<config>/meshes/` into `outputs/raw/`.

### TRELLIS.2 Adapter

Responsibilities:

- Run image-to-3D inference inside a TRELLIS.2 environment.
- Write raw GLB output to `outputs/raw/`.
- Record the model settings and source image used for generation.

### Mesh Conversion

Responsibilities:

- Convert generated assets into a mesh format accepted by print preparation.
- Use Blender or Assimp presets when GLB needs to become OBJ or STL.

### Print Preparation

Responsibilities:

- Check whether the mesh is manifold.
- Detect holes, flipped normals, thin walls, and scale issues.
- Write the printable STL/3MF file to `outputs/printable/`.

## Code Boundaries

External repositories are wrapped with adapters instead of copied into this
repository:

```text
src/
  photo_to_print/
    cli.py
    pipeline.py
    preprocess.py
    convert.py
    print_prep.py
    runners/
      tencent_instantmesh.py
      trellis2.py
```

This keeps the local pipeline stable even when external repositories change
dependencies or internal APIs.
