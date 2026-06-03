#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run TRELLIS.2 image-to-3D generation.")
    parser.add_argument("--input", required=True, type=Path, help="Input image path.")
    parser.add_argument("--output", required=True, type=Path, help="Output GLB path.")
    parser.add_argument("--model", default="microsoft/TRELLIS.2-4B", help="TRELLIS.2 model id or local checkpoint.")
    parser.add_argument("--decimation-target", type=int, default=1_000_000)
    parser.add_argument("--texture-size", type=int, default=4096)
    parser.add_argument("--no-webp", action="store_true", help="Disable WEBP extension when exporting GLB.")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

    from PIL import Image
    from trellis2.pipelines import Trellis2ImageTo3DPipeline
    import o_voxel

    args.output.parent.mkdir(parents=True, exist_ok=True)

    pipeline = Trellis2ImageTo3DPipeline.from_pretrained(args.model)
    pipeline.cuda()

    image = Image.open(args.input)
    mesh = pipeline.run(image)[0]
    mesh.simplify(16_777_216)

    glb = o_voxel.postprocess.to_glb(
        vertices=mesh.vertices,
        faces=mesh.faces,
        attr_volume=mesh.attrs,
        coords=mesh.coords,
        attr_layout=mesh.layout,
        voxel_size=mesh.voxel_size,
        aabb=[[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]],
        decimation_target=args.decimation_target,
        texture_size=args.texture_size,
        remesh=True,
        remesh_band=1,
        remesh_project=0,
        verbose=True,
    )
    glb.export(str(args.output), extension_webp=not args.no_webp)


if __name__ == "__main__":
    main()
