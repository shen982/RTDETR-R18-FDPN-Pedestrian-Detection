#!/usr/bin/env python3
"""Portable, non-overwriting entry point for independent reproduction runs.

The default check action never imports Torch, allocates a GPU, or writes files.
Training/testing are explicit actions and never overwrite archived experiments.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DATASETS = {"penn": "pennfudan_yolo", "voc": "voc2007_person450", "coco": "coco2017_person450"}
MODELS = {"baseline": "baseline_r18.yaml", "fdpn": "candidate_fdpn.yaml"}


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def default_checkpoint(dataset, model):
    if dataset == "penn":
        run = "baseline_e30" if model == "baseline" else "fdpn_e30"
    else:
        source = "voc2007" if dataset == "voc" else "coco2017"
        run = f"{source}_person450_{model}_e100_s2026"
    return ROOT / "experiments/runs" / run / "weights/best.pt"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=("check", "train", "test"), default="check")
    parser.add_argument("--dataset", choices=DATASETS, default="penn")
    parser.add_argument("--model", choices=MODELS, default="baseline")
    parser.add_argument("--name", help="New output name; required for train/test")
    parser.add_argument("--weights", type=Path, help="Trusted checkpoint for check/test; never auto-loaded for training")
    parser.add_argument("--epochs", type=int, choices=(30, 100))
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--device", default="0")
    args = parser.parse_args()
    if args.action != "check" and (not args.name or not re.fullmatch(r"[A-Za-z0-9_]+", args.name)):
        parser.error("train/test require a new --name containing letters, numbers or underscores")
    if args.action == "train" and args.weights is not None:
        parser.error("Training is from scratch; --weights is only accepted by check/test")

    model = ROOT / "configs/models" / MODELS[args.model]
    dataset = ROOT / "data" / DATASETS[args.dataset]
    manifest = dataset / "split_manifest.json"
    weights = (args.weights.resolve() if args.weights else default_checkpoint(args.dataset, args.model))
    if not model.is_file() or not manifest.is_file():
        raise FileNotFoundError("Model configuration or fixed split manifest is missing")
    plan = {"action": args.action, "model": str(model), "dataset": str(dataset),
            "split_manifest_sha256": digest(manifest), "seed": args.seed,
            "epochs": args.epochs or (30 if args.dataset == "penn" else 100),
            "imgsz": 416, "batch": 4, "device": args.device}
    if args.action != "train":
        # Evaluation RNG seed is not the checkpoint's training seed. For custom
        # weights, do not infer a training budget from the selected dataset.
        plan["evaluation_seed"] = plan.pop("seed")
        default_epochs = plan.pop("epochs")
        plan["training_epochs"] = args.epochs if args.weights else default_epochs
        if not weights.is_file():
            raise FileNotFoundError(f"Extract the corresponding weight ZIP first: {weights}")
        plan.update(weights=str(weights), checkpoint_sha256=digest(weights))
        release = ROOT / "MANIFEST.json"
        if not release.is_file():
            release = ROOT / "submission_release/snapshot/MANIFEST.json"
        if release.is_file():
            entries = json.loads(release.read_text())["experiments"]
            matched = [e for e in entries if ROOT / e["weight_path"] == weights]
            if matched and matched[0]["weight_sha256"] != plan["checkpoint_sha256"]:
                raise RuntimeError("Checkpoint differs from the archived manifest")
            if matched:
                entry = matched[0]
                plan["training_epochs"] = entry["epochs"]
                plan["checkpoint_training"] = {k: entry[k] for k in ("run", "model_config", "epochs", "seed")}
        plan["architecture_source"] = "Embedded checkpoint model; model argument selects the default weight only"
    if args.action == "check":
        plan["scope"] = "Paths and checkpoint SHA only; no model load, inference, training or output writes"
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    # Verify paths before constructing the model; keep historical YAMLs untouched.
    for split in ("train", "val", "test"):
        if not (dataset / "images" / split).is_dir() or not (dataset / "labels" / split).is_dir():
            raise FileNotFoundError(f"Prepare dataset images and labels first: {dataset}")
    output = ROOT / "reproduction_outputs" / args.name
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite an existing reproduction: {output}")
    sys.path[:0] = [str(ROOT / "runtime/site-packages"), str(ROOT / "vendor/RTDETR-main")]
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "runtime/matplotlib"))
    os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT / "runtime/ultralytics"))
    os.environ.setdefault("WANDB_DISABLED", "true")
    import numpy as np
    import torch
    import yaml
    if not torch.cuda.is_available():
        raise RuntimeError("A compatible CUDA environment is required; this is not a CPU inference workaround")
    from ultralytics import RTDETR
    torch.set_num_threads(4)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    output.mkdir(parents=True, exist_ok=False)
    data_file = output / "data.yaml"
    data_file.write_text(yaml.safe_dump({"path": str(dataset), "train": "images/train",
        "val": "images/val", "test": "images/test", "names": {0: "person"}}, sort_keys=False))
    plan["scope"] = "New reproduction only; does not replace any archived paper result"
    (output / "request.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    if args.action == "train":
        detector = RTDETR(str(model))
        result = detector.train(data=str(data_file), epochs=plan["epochs"], batch=4, imgsz=416,
            device=args.device, workers=2, seed=args.seed, deterministic=True, pretrained=False,
            optimizer="AdamW", lr0=1e-4, lrf=1.0, weight_decay=1e-4, warmup_epochs=3.0,
            amp=False, cache=False, patience=0, project=str(output), name="train", exist_ok=False,
            plots=True, verbose=True)
    else:
        detector = RTDETR(str(weights))  # Only load checkpoints trusted by the caller.
        result = detector.val(data=str(data_file), split="test", imgsz=416, batch=4,
            device=args.device, workers=2, project=str(output), name="test", exist_ok=False,
            plots=False, verbose=False)
    summary = {"request": plan, "metrics": {k: float(v) for k, v in result.results_dict.items()}}
    if args.action == "test":
        summary["speed_ms_per_image"] = result.speed
    (output / "result.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
