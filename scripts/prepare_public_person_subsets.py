#!/usr/bin/env python3
"""Download and freeze two public person-detection subsets before training.

Only selected VOC image members and selected COCO images are materialized.
All sampling rules are fixed independently of model performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import tarfile
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/public_person"
COUNTS = {"train": (240, 60), "val": (40, 10), "test": (80, 20)}
VOC_SOURCES = {
    "trainval": {
        "filename": "VOCtrainval_06-Nov-2007.tar",
        "md5": "c52e279531787c972589f7e41ab4ae64",
    },
    "test": {
        "filename": "VOCtest_06-Nov-2007.tar",
        "md5": "b6e924de25625d8de591ea690078ad9f",
    },
}
COCO_BASE = "https://s3.amazonaws.com/images.cocodataset.org/"


def digest(path: Path, algorithm="sha256") -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def download(urls: list[str], path: Path, expected_md5=None, quiet=False) -> dict:
    source_file = path.with_suffix(path.suffix + ".source.json")
    if path.is_file() and source_file.is_file():
        record = json.loads(source_file.read_text())
        if record["sha256"] == digest(path) and (not expected_md5 or digest(path, "md5") == expected_md5):
            return record
        raise RuntimeError(f"Existing download failed integrity verification: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    failures = []
    part = path.with_suffix(path.suffix + ".part")
    for url in urls:
        for attempt in range(3):
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "RTDETR-course-reproduction/1.0"})
                with urllib.request.urlopen(request, timeout=45) as response, part.open("wb") as output:
                    length = int(response.headers.get("Content-Length", 0))
                    downloaded, last_print = 0, time.monotonic()
                    for block in iter(lambda: response.read(1024 * 1024), b""):
                        output.write(block)
                        downloaded += len(block)
                        if not quiet and time.monotonic() - last_print >= 15:
                            print(f"download {path.name}: {downloaded / 1048576:.1f}/{length / 1048576:.1f} MiB", flush=True)
                            last_print = time.monotonic()
                if length and part.stat().st_size != length:
                    raise RuntimeError(f"Incomplete download: {part}")
                if expected_md5 and digest(part, "md5") != expected_md5:
                    raise RuntimeError(f"VOC archive does not match torchvision MD5: {part}")
                record = {"requested_url": url, "downloaded_utc": datetime.now(timezone.utc).isoformat(),
                          "bytes": part.stat().st_size, "sha256": digest(part), "md5": digest(part, "md5")}
                part.replace(path)
                save_json(source_file, record)
                if not quiet:
                    print(f"download complete: {path.name}, {record['bytes']} bytes", flush=True)
                return record
            except Exception as error:
                failures.append(f"{url}: {type(error).__name__}: {error}")
                time.sleep(attempt + 1)
    raise RuntimeError("All download attempts failed:\n" + "\n".join(failures))


def choose(records: dict[str, dict], seed: int, stream: str, positive: int, negative: int, excluded=None):
    excluded = set(excluded or [])
    positives = sorted(key for key, value in records.items() if value["boxes"] and key not in excluded)
    negatives = sorted(key for key, value in records.items() if not value["boxes"] and key not in excluded)
    rng = random.Random(f"{seed}:{stream}")
    rng.shuffle(positives)
    rng.shuffle(negatives)
    if len(positives) < positive or len(negatives) < negative:
        raise RuntimeError(f"Insufficient eligible pool for {stream}: {len(positives)}, {len(negatives)}")
    selected = positives[:positive] + negatives[:negative]
    rng.shuffle(selected)
    return selected


def write_labels(record: dict, image_path: Path, label_path: Path):
    with Image.open(image_path) as image:
        actual_size = image.size
        image.verify()
    if actual_size != (record["width"], record["height"]):
        raise RuntimeError(f"Annotation/image size mismatch: {image_path}: {actual_size}")
    width, height = actual_size
    lines = []
    for box in record["boxes"]:
        x1, y1, x2, y2 = box
        if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
            raise ValueError(f"Invalid box: {image_path}, {box}")
        normalized = ((x1 + x2) / (2 * width), (y1 + y2) / (2 * height), (x2 - x1) / width, (y2 - y1) / height)
        lines.append("0 " + " ".join(f"{x:.8f}" for x in normalized))
    label_path.parent.mkdir(parents=True, exist_ok=True)
    label_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def finish_dataset(name: str, output: Path, records: dict, splits: dict, sources: list, rules: dict, seed: int):
    all_ids, content_splits = set(), {}
    manifest = {"dataset": name, "seed": seed, "sampling": rules, "sources": sources, "splits": {}}
    report = {"dataset": name, "seed": seed, "source_homepage": rules["source_homepage"], "rules": rules, "sources": sources, "splits": {}}
    for split, ids in splits.items():
        manifest["splits"][split] = []
        positive = instances = 0
        for identifier in ids:
            if identifier in all_ids:
                raise RuntimeError(f"Image ID leakage: {identifier}")
            all_ids.add(identifier)
            record = records[identifier]
            image_path = output / "images" / split / record["filename"]
            label_path = output / "labels" / split / (Path(record["filename"]).stem + ".txt")
            write_labels(record, image_path, label_path)
            image_hash = digest(image_path)
            if image_hash in content_splits and content_splits[image_hash] != split:
                raise RuntimeError(f"Image content leakage: {identifier}")
            content_splits[image_hash] = split
            entry = {"id": identifier, "filename": record["filename"], "source_split": record["source_split"],
                     "objects": len(record["boxes"]), "width": record["width"], "height": record["height"],
                     "image_sha256": image_hash, "label_sha256": digest(label_path)}
            manifest["splits"][split].append(entry)
            positive += int(bool(record["boxes"]))
            instances += len(record["boxes"])
        p, n = COUNTS[split]
        if (len(ids), positive, len(ids) - positive) != (p + n, p, n):
            raise RuntimeError(f"Split counts are inconsistent: {name}/{split}")
        report["splits"][split] = {"images": len(ids), "positive_images": positive, "background_images": len(ids) - positive, "instances": instances}
    yaml = f"path: {output.resolve()}\ntrain: images/train\nval: images/val\ntest: images/test\nnames:\n  0: person\n"
    (output / "data.yaml").write_text(yaml, encoding="utf-8")
    save_json(output / "split_manifest.json", manifest)
    report["split_manifest_sha256"] = digest(output / "split_manifest.json")
    report["data_yaml_sha256"] = digest(output / "data.yaml")
    save_json(output / "dataset_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


def prepare_voc(seed: int):
    output = ROOT / "data/voc2007_person450"
    sources, archives, records, official_ids, excluded_counts = [], {}, {}, {}, {}
    for group, source in VOC_SOURCES.items():
        archive = RAW / source["filename"]
        official_url = "https://thor.robots.ox.ac.uk/pascal/VOC/voc2007/" + source["filename"]
        mirror_url = "https://huggingface.co/datasets/davin11/VOC2007/resolve/main/" + source["filename"]
        provenance = download([official_url, mirror_url], archive, expected_md5=source["md5"])
        provenance.update({"official_url": official_url, "expected_md5": source["md5"],
                           "checksum_reference": "https://raw.githubusercontent.com/pytorch/vision/main/torchvision/datasets/voc.py"})
        sources.append(provenance)
        archives[group] = archive
        excluded_counts[group] = 0
        with tarfile.open(archive) as tar:
            prefix = "VOCdevkit/VOC2007/"
            split_names = ("train", "val") if group == "trainval" else ("test",)
            for split in split_names:
                stream = tar.extractfile(prefix + f"ImageSets/Main/{split}.txt")
                official_ids[split] = set(stream.read().decode().split())
            for member in tar.getmembers():
                if not member.isfile() or not member.name.startswith(prefix + "Annotations/") or not member.name.endswith(".xml"):
                    continue
                xml_bytes = tar.extractfile(member).read()
                annotation = ET.fromstring(xml_bytes)
                identifier = Path(member.name).stem
                persons = [obj for obj in annotation.findall("object") if obj.findtext("name") == "person"]
                if any(obj.findtext("difficult", "0") == "1" for obj in persons):
                    excluded_counts[group] += 1
                    continue
                width, height = int(annotation.findtext("size/width")), int(annotation.findtext("size/height"))
                boxes = []
                for obj in persons:
                    box = obj.find("bndbox")
                    x1, y1 = float(box.findtext("xmin")) - 1, float(box.findtext("ymin")) - 1
                    x2, y2 = float(box.findtext("xmax")), float(box.findtext("ymax"))
                    boxes.append([max(0, x1), max(0, y1), min(width, x2), min(height, y2)])
                records[identifier] = {"filename": identifier + ".jpg", "width": width, "height": height,
                                       "boxes": boxes, "source_archive": group, "xml": xml_bytes.decode("utf-8"),
                                       "source_split": next(split for split in split_names if identifier in official_ids[split])}
    splits = {}
    for split, (positive, negative) in COUNTS.items():
        candidates = {key: value for key, value in records.items() if key in official_ids[split]}
        splits[split] = choose(candidates, seed, f"voc2007:{split}", positive, negative)
    output.mkdir(parents=True, exist_ok=True)
    save_json(output / "selection_before_download.json", {"seed": seed, "splits": splits})
    for group, archive in archives.items():
        selected = {identifier: split for split, ids in splits.items() for identifier in ids if records[identifier]["source_archive"] == group}
        with tarfile.open(archive) as tar:
            for identifier, split in selected.items():
                image_path = output / "images" / split / (identifier + ".jpg")
                image_path.parent.mkdir(parents=True, exist_ok=True)
                with image_path.open("wb") as dest:
                    dest.write(tar.extractfile(f"VOCdevkit/VOC2007/JPEGImages/{identifier}.jpg").read())
                annotation_path = output / "source_annotations" / (identifier + ".xml")
                annotation_path.parent.mkdir(parents=True, exist_ok=True)
                annotation_path.write_text(records[identifier]["xml"], encoding="utf-8")
    rules = {"source_homepage": "https://www.robots.ox.ac.uk/~vgg/projects/pascal/VOC/voc2007/index.html",
             "class": "person only", "background_fraction": 0.2, "official_split_boundaries": "train->train, val->val, test->test",
             "ignore_policy": "exclude whole images containing difficult person; no size/occlusion filter",
             "excluded_difficult_images": excluded_counts, "coordinate_conversion": "1-based inclusive to 0-based continuous"}
    finish_dataset("VOC2007-person-450", output, records, splits, sources, rules, seed)


def prepare_coco(seed: int, workers: int):
    output = ROOT / "data/coco2017_person450"
    archive = RAW / "annotations_trainval2017.zip"
    sources = [download([COCO_BASE + "annotations/annotations_trainval2017.zip"], archive)]
    records, annotations, excluded_counts = {}, {}, {}
    with zipfile.ZipFile(archive) as zip_archive:
        for source_split in ("train2017", "val2017"):
            with zip_archive.open(f"annotations/instances_{source_split}.json") as stream:
                annotation = json.load(stream)
            person_id = next(cat["id"] for cat in annotation["categories"] if cat["name"] == "person")
            by_image, crowds = {}, set()
            for ann in annotation["annotations"]:
                if ann["category_id"] != person_id:
                    continue
                if ann.get("iscrowd", 0):
                    crowds.add(ann["image_id"])
                else:
                    by_image.setdefault(ann["image_id"], []).append(ann)
            pool = {}
            for image in annotation["images"]:
                if image["id"] in crowds:
                    continue
                width, height = image["width"], image["height"]
                boxes = []
                anns = by_image.get(image["id"], [])
                for ann in anns:
                    x, y, w, h = ann["bbox"]
                    boxes.append([max(0, x), max(0, y), min(width, x + w), min(height, y + h)])
                key = f"{image['id']:012d}"
                pool[key] = {"filename": image["file_name"], "width": width, "height": height,
                             "boxes": boxes, "source_split": source_split, "image_metadata": image, "person_annotations": anns}
            records.update(pool)
            annotations[source_split] = pool
            excluded_counts[source_split] = len(crowds)
            print(f"COCO {source_split}: {len(pool)} eligible images; {len(crowds)} crowd-person images excluded", flush=True)
            del annotation, by_image
    train_pool = annotations["train2017"]
    train = choose(train_pool, seed, "coco2017:train", *COUNTS["train"])
    validation = choose(train_pool, seed, "coco2017:val", *COUNTS["val"], excluded=train)
    test = choose(annotations["val2017"], seed, "coco2017:test", *COUNTS["test"])
    splits = {"train": train, "val": validation, "test": test}
    output.mkdir(parents=True, exist_ok=True)
    save_json(output / "selection_before_download.json", {"seed": seed, "splits": splits})
    save_json(output / "selected_source_annotations.json", {key: records[key] for ids in splits.values() for key in ids})

    def get_image(split, key):
        record = records[key]
        path = output / "images" / split / record["filename"]
        url = COCO_BASE + record["source_split"] + "/" + record["filename"]
        return download([url], path, quiet=True)

    tasks = [(split, key) for split, ids in splits.items() for key in ids]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(get_image, split, key) for split, key in tasks]
        for count, future in enumerate(as_completed(futures), 1):
            future.result()
            if count % 50 == 0 or count == len(tasks):
                print(f"COCO selected images downloaded: {count}/{len(tasks)}", flush=True)
    rules = {"source_homepage": "https://cocodataset.org/#download", "class": "person only", "background_fraction": 0.2,
             "official_split_boundaries": "disjoint train/val from train2017; test from val2017",
             "ignore_policy": "exclude whole images containing crowd person; no size/occlusion filter",
             "excluded_crowd_images": excluded_counts, "download_endpoint": "HTTPS path-style access to official COCO S3 bucket"}
    finish_dataset("COCO2017-person-450", output, records, splits, sources, rules, seed)


def verify(output: Path):
    manifest = json.loads((output / "split_manifest.json").read_text())
    report = json.loads((output / "dataset_report.json").read_text())
    if report["split_manifest_sha256"] != digest(output / "split_manifest.json"):
        raise RuntimeError(f"Manifest hash mismatch: {output}")
    for split, entries in manifest["splits"].items():
        for entry in entries:
            image = output / "images" / split / entry["filename"]
            label = output / "labels" / split / (Path(entry["filename"]).stem + ".txt")
            if digest(image) != entry["image_sha256"] or digest(label) != entry["label_sha256"]:
                raise RuntimeError(f"Content hash mismatch: {image}")
    print(f"Verified {output.name}: 450 images, stable split and content hashes", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=("voc", "coco", "all"), default="all")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--download-workers", type=int, default=6)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    for dataset in ("voc", "coco"):
        if args.dataset not in ("all", dataset):
            continue
        output = ROOT / "data" / ("voc2007_person450" if dataset == "voc" else "coco2017_person450")
        if args.verify_only:
            verify(output)
        elif (output / "dataset_report.json").exists():
            verify(output)
        elif dataset == "voc":
            prepare_voc(args.seed)
        else:
            prepare_coco(args.seed, args.download_workers)


if __name__ == "__main__":
    main()
