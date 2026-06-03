# Architecture

This project is designed as a pipeline that connects two separate stages:

- TRELLIS.2 generates a raw 3D asset from a photo or selected source image.
- Instant Meshes performs retopology/remeshing on the generated mesh.

## Pipeline

```text
Input Photos
    |
    v
Photo Preprocessing
    |
    v
3D Generation Adapter
    |
    v
Raw Asset Export
    |
    v
Mesh Conversion
    |
    v
Remesh Adapter
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
- Prepare background removal, crops, and masks.
- Check image quality, sharpness, and viewpoint coverage.
- Select the strongest primary image for the MVP workflow.

### TRELLIS.2 Adapter

Responsibilities:

- Run image-to-3D inference inside a TRELLIS.2 environment.
- Write raw GLB/OBJ output to `outputs/raw/`.
- Record the model settings and source image used for generation.

### Mesh Conversion

Responsibilities:

- Convert generated assets into a mesh format accepted by Instant Meshes.
- Prefer OBJ or PLY for the remeshing stage.
- Keep conversion as a command-template adapter so Blender, Assimp, or another converter can be swapped in later.

### Remesh Adapter

Responsibilities:

- Retopologize the converted mesh with Instant Meshes.
- Control target face count, quad/triangle preferences, and export format.
- Write remeshed output to `outputs/remeshed/`.

### Print Preparation

Responsibilities:

- Check whether the mesh is manifold.
- Detect holes, flipped normals, thin walls, and scale issues.
- Write the printable STL/3MF file to `outputs/printable/`.

## Initial Code Boundaries

The first implementation should wrap external repositories with adapters
instead of copying their code directly into this repository:

```text
src/
  photo_to_print/
    cli.py
    pipeline.py
    preprocess.py
    convert.py
    print_prep.py
    obj_mesh.py
    runners/
      trellis2.py
      instant_meshes.py
```

This keeps the local pipeline stable even when TRELLIS.2 or Instant Meshes
changes dependencies or internal APIs.
