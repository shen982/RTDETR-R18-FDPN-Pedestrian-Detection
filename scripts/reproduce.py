#!/usr/bin/env python3
"""Download, verify, evaluate and retrain the paper's frozen experiments."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
GROUPS = ("initial_penn", "public_e30", "public_e100", "ablation", "robustness")


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    return json.loads(path.read_text())


def select_runs(args):
    entries = load(ROOT / "reproduction/RUNS.json")["experiments"]
    if args.run:
        selected = [entry for entry in entries if entry["run"] in args.run]
        if len(selected) != len(set(args.run)):
            raise ValueError("Unknown --run; use list to see all 22 names")
        return selected
    group = {"primary": "robustness", "quick": "initial_penn"}.get(args.suite, args.suite)
    return [entry for entry in entries if group == "all" or entry["group"] == group]


def dataset_for(entry):
    run = entry["run"]
    return ("voc2007_person450" if run.startswith("voc2007_") else
            "coco2017_person450" if run.startswith("coco2017_") else "pennfudan_yolo")


def asset_needed(asset, runs):
    return (asset["kind"] == "runtime" or
            asset["kind"] == "weights" and asset["group"] in {r["group"] for r in runs} or
            asset["kind"] == "dataset" and asset["dataset"] in {dataset_for(r) for r in runs})


def validate_members(bundle):
    names = set()
    for item in bundle.infolist():
        path = PurePosixPath(item.filename)
        if (path.is_absolute() or ".." in path.parts or not path.parts or
                path.parts[0] != "snapshot" or "\\" in item.filename or
                (item.external_attr >> 16) & 0o170000 == 0o120000):
            raise ValueError("Unsafe archive member: " + item.filename)
        if item.filename in names:
            raise ValueError("Duplicate archive member: " + item.filename)
        names.add(item.filename)


def download(asset, path, attempts=8):
    """Resume interrupted transfers; install only a size-and-hash verified file."""
    temporary = path.with_suffix(path.suffix + ".part")
    for attempt in range(attempts):
        try:
            offset = temporary.stat().st_size if temporary.exists() else 0
            if offset > asset["bytes"]:
                temporary.unlink()
                offset = 0
            if offset < asset["bytes"]:
                headers = {"User-Agent": "RTDETR-course-reproduction"}
                if offset:
                    headers["Range"] = f"bytes={offset}-"
                request = urllib.request.Request(asset["url"], headers=headers)
                with urllib.request.urlopen(request, timeout=120) as incoming:
                    if incoming.status == 206:
                        if not incoming.headers.get("Content-Range", "").startswith(f"bytes {offset}-"):
                            raise RuntimeError("Unexpected download byte range")
                    elif incoming.status == 200:
                        offset = 0  # Servers without Range support restart safely.
                    else:
                        raise RuntimeError("Unexpected download HTTP status")
                    with temporary.open("ab" if offset else "wb") as outgoing:
                        shutil.copyfileobj(incoming, outgoing, 1024 * 1024)
            if temporary.stat().st_size == asset["bytes"]:
                if sha(temporary) == asset["sha256"]:
                    os.replace(temporary, path)
                    return
                temporary.unlink()  # Never append to a complete corrupt file.
                raise RuntimeError("Downloaded asset failed SHA-256")
            raise RuntimeError("Download interrupted before the expected byte count")
        except (OSError, urllib.error.URLError, http.client.IncompleteRead, RuntimeError) as error:
            if attempt + 1 == attempts:
                raise RuntimeError("Unable to download verified asset: " + asset["file"]) from error
            print(f"Retrying {asset['file']} ({attempt + 2}/{attempts}): {error}", flush=True)
            time.sleep(min(2 ** attempt, 10))


def prepare(args, runs):
    downloads = args.workspace / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    for asset in load(ROOT / "reproduction/ASSETS.json")["assets"]:
        if not asset_needed(asset, runs):
            continue
        path = downloads / asset["file"]
        if not path.is_file() or path.stat().st_size != asset["bytes"] or sha(path) != asset["sha256"]:
            print("Downloading", asset["file"], flush=True)
            download(asset, path)
        marker = downloads / (asset["file"] + ".extracted.sha256")
        if marker.is_file() and marker.read_text().strip() == asset["sha256"]:
            continue
        print("Extracting verified", asset["file"], flush=True)
        with zipfile.ZipFile(path) as bundle:
            validate_members(bundle)
            for member in bundle.infolist():
                if member.is_dir():
                    continue
                destination = args.workspace.joinpath(*PurePosixPath(member.filename).parts)
                if destination.is_symlink() or any(p.is_symlink() for p in destination.parents):
                    raise RuntimeError("Refusing extraction through a symlink")
                destination.parent.mkdir(parents=True, exist_ok=True)
                temporary = destination.with_name(destination.name + ".extracting")
                with bundle.open(member) as incoming, temporary.open("wb") as outgoing:
                    shutil.copyfileobj(incoming, outgoing)
                os.replace(temporary, destination)
        marker.write_text(asset["sha256"] + "\n")
    verify(args, runs)


def verify(args, runs):
    snapshot = args.workspace / "snapshot"
    expected = load(snapshot / "REPRODUCTION_FILES.json")
    datasets = {dataset_for(entry) for entry in runs}
    checked = 0
    for relative, record in expected.items():
        if relative.startswith("data/") and relative.split("/")[1] not in datasets:
            continue
        path = snapshot / relative
        if not path.is_file() or path.stat().st_size != record["bytes"] or sha(path) != record["sha256"]:
            raise RuntimeError("Frozen source/data differs or is missing: " + relative)
        checked += 1
    for entry in runs:
        path = snapshot / entry["weight_path"]
        if not path.is_file() or sha(path) != entry["weight_sha256"]:
            raise RuntimeError("Missing or changed checkpoint: " + entry["run"])
    print(f"Verified {checked} frozen source/data files and {len(runs)} checkpoints.", flush=True)


def execute(args, runs):
    if args.weights and (len(runs) != 1 or args.action == "train"):
        raise ValueError("--weights requires evaluate with exactly one --run")
    verify(args, runs)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    output = (args.output or args.workspace / "results" / stamp).resolve()
    if output.exists():
        raise FileExistsError("Choose a new output directory: " + str(output))
    output.mkdir(parents=True)
    for entry in runs:
        print(args.action, entry["run"], flush=True)
        command = [sys.executable, str(args.workspace / "snapshot/scripts/evaluate_archived.py"),
                   "--run", entry["run"], "--device", args.device,
                   "--output", str(output / entry["run"])]
        if args.action == "train":
            command.append("--train")
        if args.weights:
            command += ["--weights", str(args.weights.resolve())]
        with (output / (entry["run"] + ".log")).open("w") as log:
            process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        if process.returncode:
            raise RuntimeError("Run failed; inspect " + str(output / (entry["run"] + ".log")))
    summarize(output)
    print("Results:", output)


def summarize(output):
    results = [load(p) for p in sorted(output.glob("*/result.json"))]
    if not results:
        raise FileNotFoundError("No result.json under " + str(output))
    keys = ("metrics/mAP50(B)", "metrics/mAP50-95(B)")
    rows = [{"run": r["run"], "AP50_percent": 100 * r["metrics"][keys[0]],
             "AP50_95_percent": 100 * r["metrics"][keys[1]],
             "max_absolute_metric_difference": max((v["absolute_difference"] for v in r["comparison"].values()), default=0)}
            for r in results]
    with (output / "results.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    grouped = {}
    for model in ("baseline", "ccff320", "fdpn"):
        selected = [r for r in results if r["run"].startswith("penn_" + model + "_e30_s")]
        if len(selected) == 3:
            grouped[model] = {key: {"mean_percent": 100 * statistics.mean(r["metrics"][key] for r in selected),
                                   "sample_std_percent": 100 * statistics.stdev(r["metrics"][key] for r in selected)} for key in keys}
    (output / "summary.json").write_text(json.dumps({"runs": len(results), "primary_three_seed_statistics": grouped,
        "all_archived_evaluations_match_within_1e-6": all(r["all_metric_differences_below_1e-6"] is True for r in results)}, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("list", "prepare", "verify", "evaluate", "train", "summarize"))
    parser.add_argument("--suite", choices=("primary", "quick", "all") + GROUPS, default="primary")
    parser.add_argument("--run", action="append")
    parser.add_argument("--workspace", type=Path, default=ROOT / "reproduction_workspace")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--device", default="0")
    parser.add_argument("--weights", type=Path, help="Optional newly trained trusted checkpoint; one --run only")
    args = parser.parse_args()
    args.workspace = args.workspace.resolve()
    runs = select_runs(args)
    if args.action == "list":
        for entry in runs:
            print(entry["run"], entry["group"], entry["epochs"], entry["seed"])
    elif args.action == "prepare":
        prepare(args, runs)
    elif args.action == "verify":
        verify(args, runs)
    elif args.action in ("evaluate", "train"):
        execute(args, runs)
    else:
        if not args.output:
            parser.error("summarize requires --output pointing to an existing results directory")
        summarize(args.output)


if __name__ == "__main__":
    main()
