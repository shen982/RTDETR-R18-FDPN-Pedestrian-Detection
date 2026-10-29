#!/usr/bin/env python3
"""Convert Penn-Fudan instance masks to a deterministic YOLO detection split."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def boxes_from_mask(mask_path: Path) -> list[tuple[int, int, int, int]]:
    mask = np.asarray(Image.open(mask_path))
    boxes = []
    for object_id in np.unique(mask):
        if object_id == 0:
            continue
        ys, xs = np.where(mask == object_id)
        if not len(xs):
            continue
        # x2/y2 are exclusive, matching continuous box coordinates.
        boxes.append((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
    return boxes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, default=Path("data/raw/PennFudanPed.zip"))
    parser.add_argument("--output", type=Path, default=Path("data/pennfudan_yolo"))
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()

    archive = args.zip.resolve()
    output = args.output.resolve()
    extracted = archive.parent / "extracted"
    source = extracted / "PennFudanPed"
    if not source.exists():
        extracted.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(extracted)

    image_dir = source / "PNGImages"
    mask_dir = source / "PedMasks"
    images = sorted(image_dir.glob("*.png"))
    if len(images) != 170:
        raise RuntimeError(f"Expected 170 images, found {len(images)}")

    rng = random.Random(args.seed)
    rng.shuffle(images)
    split_images = {
        "train": images[:120],
        "val": images[120:145],
        "test": images[145:],
    }

    report = {
        "source_archive": str(archive),
        "source_sha256": sha256(archive),
        "seed": args.seed,
        "class_names": ["person"],
        "splits": {},
    }
    manifest = {"seed": args.seed, "splits": {}}

    all_names: set[str] = set()
    for split, split_items in split_images.items():
        out_images = output / "images" / split
        out_labels = output / "labels" / split
        out_images.mkdir(parents=True, exist_ok=True)
        out_labels.mkdir(parents=True, exist_ok=True)
        object_count = 0
        manifest["splits"][split] = [path.stem for path in split_items]

        for image_path in split_items:
            if image_path.name in all_names:
                raise RuntimeError(f"Split leakage: {image_path.name}")
            all_names.add(image_path.name)
            mask_path = mask_dir / f"{image_path.stem}_mask.png"
            if not mask_path.exists():
                raise FileNotFoundError(mask_path)

            with Image.open(image_path) as image:
                width, height = image.size
            boxes = boxes_from_mask(mask_path)
            if not boxes:
                raise RuntimeError(f"No instances in {mask_path}")

            lines = []
            for x1, y1, x2, y2 in boxes:
                xc = ((x1 + x2) / 2) / width
                yc = ((y1 + y2) / 2) / height
                bw = (x2 - x1) / width
                bh = (y2 - y1) / height
                values = (xc, yc, bw, bh)
                if not all(0.0 < value <= 1.0 for value in values):
                    raise ValueError(f"Invalid box in {mask_path}: {values}")
                lines.append("0 " + " ".join(f"{value:.8f}" for value in values))

            shutil.copy2(image_path, out_images / image_path.name)
            (out_labels / f"{image_path.stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
            object_count += len(boxes)

        report["splits"][split] = {"images": len(split_items), "objects": object_count}

    if len(all_names) != 170:
        raise RuntimeError(f"Expected 170 unique images, found {len(all_names)}")

    data_yaml = (
        f"path: {output}\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n\n"
        "names:\n"
        "  0: person\n"
    )
    (output / "data.yaml").write_text(data_yaml, encoding="utf-8")
    (output / "split_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output / "dataset_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
