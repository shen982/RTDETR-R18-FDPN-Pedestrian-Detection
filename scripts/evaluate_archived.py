#!/usr/bin/env python3
"""Re-evaluate or retrain one frozen run in an extracted runtime workspace."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--device", default="0", help="CUDA index, or cpu for evaluation")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--train", action="store_true")
    parser.add_argument("--weights", type=Path, help="Optional newly trained trusted checkpoint")
    args = parser.parse_args()
    entries = json.loads((ROOT / "MANIFEST.json").read_text())["experiments"]
    entry = next((e for e in entries if e["run"] == args.run), None)
    if entry is None:
        parser.error("Unknown archived run")
    dataset_name = ("voc2007_person450" if args.run.startswith("voc2007_") else
                    "coco2017_person450" if args.run.startswith("coco2017_") else "pennfudan_yolo")
    dataset = ROOT / "data" / dataset_name
    frozen = json.loads((ROOT / "REPRODUCTION_FILES.json").read_text())
    for relative in (entry["model_config"], f"data/{dataset_name}/split_manifest.json"):
        if digest(ROOT / relative) != frozen[relative]["sha256"]:
            raise RuntimeError("Frozen input changed: " + relative)
    if args.train and args.weights:
        parser.error("Training starts from scratch; --weights is only for evaluation")
    checkpoint = args.weights.resolve() if args.weights else ROOT / entry["weight_path"]
    if not args.train and not args.weights and digest(checkpoint) != entry["weight_sha256"]:
        raise RuntimeError("Checkpoint SHA-256 differs from the release manifest")
    for split in ("train", "val", "test"):
        if not (dataset / "images" / split).is_dir() or not (dataset / "labels" / split).is_dir():
            raise FileNotFoundError("Download the prepared dataset first: " + dataset_name)
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError("Refusing to overwrite " + str(output))
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
    os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT / ".cache/ultralytics"))
    os.environ.setdefault("WANDB_DISABLED", "true")
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    os.environ.setdefault("YOLO_AUTOINSTALL", "false")
    sys.path[:0] = [str(ROOT / "runtime/site-packages"), str(ROOT / "vendor/RTDETR-main")]
    import numpy as np
    import torch
    import yaml
    from ultralytics import RTDETR
    from ultralytics.utils import SETTINGS
    # Optional trackers must not alter or interrupt an offline reproduction.
    SETTINGS.update({key: False for key in (
        "sync", "clearml", "comet", "dvc", "hub", "mlflow", "neptune",
        "raytune", "tensorboard", "wandb") if key in SETTINGS})
    if args.train and (args.device == "cpu" or not torch.cuda.is_available()):
        raise RuntimeError("The archived training protocol requires a CUDA GPU")
    torch.set_num_threads(4)
    random.seed(entry["seed"])
    np.random.seed(entry["seed"])
    torch.manual_seed(entry["seed"])
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(entry["seed"])
    output.mkdir(parents=True, exist_ok=False)
    data_file = output / "data.yaml"
    data_file.write_text(yaml.safe_dump({"path": str(dataset), "train": "images/train",
        "val": "images/val", "test": "images/test", "names": {0: "person"}}, sort_keys=False))
    if args.train:
        model = RTDETR(str(ROOT / entry["model_config"]))
        result = model.train(data=str(data_file), epochs=entry["epochs"], batch=entry["batch"],
            imgsz=entry["imgsz"], device=args.device, workers=2, seed=entry["seed"],
            deterministic=True, pretrained=False, optimizer="AdamW", lr0=1e-4,
            lrf=1.0, weight_decay=1e-4, warmup_epochs=3.0, amp=False, cache=False,
            patience=0, project=str(output), name="training", exist_ok=False, plots=True)
    else:
        model = RTDETR(str(checkpoint))
        result = model.val(data=str(data_file), split="test", imgsz=entry["imgsz"],
            batch=entry["batch"], device=args.device, workers=2, project=str(output),
            name="evaluation", exist_ok=False, plots=False, verbose=False, half=False)
    metrics = {key: float(value) for key, value in result.results_dict.items()}
    comparison = {} if args.train else {key: {"archived": entry["metrics"][key], "reproduced": value,
                       "absolute_difference": abs(value - entry["metrics"][key])}
                  for key, value in metrics.items() if key in entry["metrics"]}
    record = {"run": args.run, "action": "train" if args.train else "evaluate",
        "device": args.device, "python": sys.version.split()[0], "torch": torch.__version__,
        "metric_split": "validation" if args.train else "test",
        "archived_checkpoint": not args.train and not bool(args.weights),
        "cuda": torch.version.cuda, "metrics": metrics, "comparison": comparison,
        "checkpoint_sha256": None if args.train else digest(checkpoint),
        "all_metric_differences_below_1e-6": None if args.train else
            all(row["absolute_difference"] <= 1e-6 for row in comparison.values()),
        "source_module": "vendor/RTDETR-main/ultralytics", "seed": entry["seed"]}
    (output / "result.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
