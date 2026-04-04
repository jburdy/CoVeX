#!/usr/bin/env python3
"""
Execute un sous-ensemble du golden dataset contre l'API backend CoVeX.

Execution depuis la racine du projet:
- `uv run --project backend python tools/evaluation/run_dataset_evaluation.py --limit 3`
- `--limit` fixe le nombre de cas executes (`0` pour tous les cas du dataset).
- `--engine` force le `inference_engine` envoye a l'API pour chaque scenario.
- `--workers` regle le nombre de requetes lancees en parallele.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import random
import subprocess
import sys
import time
from pathlib import Path
from urllib import error, request

SCRIPT_PATH = Path(__file__).resolve()
ROOT_DIR = SCRIPT_PATH.parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.validation.backend_runner import (
    BASE_URL,
    is_backend_ready,
    start_backend,
    stop_backend,
    wait_backend_ready,
)

DATASET_PATH = ROOT_DIR / "datasets" / "golden_dataset.jsonl"


def _start_api_if_needed() -> subprocess.Popen[str] | None:
    if is_backend_ready():
        print("API déjà en cours d'exécution.\n")
        return None

    print("Démarrage de l'API backend...")
    process = start_backend()
    wait_backend_ready(process, timeout_sec=30.0)
    print("API prête.\n")
    return process


def load_dataset() -> list[dict]:
    cases = []
    with DATASET_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            cases.append(json.loads(line))
    random.shuffle(cases)
    return cases


def analyze(profile_id: str, text: str, inference_engine: str) -> dict[str, object]:
    payload = {
        "text": text,
        "profile_id": profile_id,
        "inference_engine": inference_engine,
    }
    req = request.Request(
        f"{BASE_URL}/analyze",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"\n[!] Erreur API HTTP {e.code}: {body}", file=sys.stderr)
        raise SystemExit(1)
    except error.URLError as e:
        print(f"\n[!] Erreur de connexion API: {e.reason}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as e:
        print(f"\n[!] Erreur inattendue: {e}", file=sys.stderr)
        raise SystemExit(1)


def run_case(case: dict, inference_engine: str) -> dict:
    case_id = case.get("id", "UNKNOWN")
    profile_id = str(case.get("profile_id", ""))
    text = str(case.get("text", ""))
    expected = case.get("decision_expected")

    t0 = time.time()
    result = analyze(profile_id, text, inference_engine)
    duration = time.time() - t0

    actual = result.get("decision")
    score = result.get("score")
    passed = actual == expected

    return {
        "case_id": case_id,
        "profile_id": profile_id,
        "expected": expected,
        "actual": actual,
        "score": score,
        "duration": duration,
        "passed": passed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="CoVeX Test Runner (Minimaliste)")
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Nombre de cas à exécuter (0 = infini/tous). Par défaut: 3",
    )
    parser.add_argument(
        "--engine",
        default="remote_groq_llama31_8b_instant",
        help="Brain engine à utiliser (défaut: remote_groq_llama31_8b_instant)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Nombre de requêtes parallèles (défaut: 4)",
    )
    args = parser.parse_args()

    api_process = _start_api_if_needed()

    try:
        cases = load_dataset()
        if args.limit > 0:
            selected_cases = cases[: args.limit]
        else:
            selected_cases = cases

        print(
            f"Exécution de {len(selected_cases)} cas de test (inference_engine={args.engine}, workers={args.workers})...\n"
        )

        passed = 0
        total_duration = 0.0
        total_tests = len(selected_cases)

        t0_global = time.time()

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=args.workers
        ) as executor:
            futures = {
                executor.submit(run_case, case, args.engine): case
                for case in selected_cases
            }
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                total_duration += res["duration"]

                if res["passed"]:
                    passed += 1
                    print(
                        f"Test {res['case_id']} ({res['profile_id']})... ✅ OK (score: {res['score']}) en {res['duration']:.2f}s"
                    )
                else:
                    print(
                        f"Test {res['case_id']} ({res['profile_id']})... ❌ ÉCHEC (attendu: {res['expected']}, obtenu: {res['actual']}, score: {res['score']}) en {res['duration']:.2f}s"
                    )

        global_duration = time.time() - t0_global

        if total_tests > 0:
            success_rate = (passed / total_tests) * 100
            avg_speed = total_duration / total_tests
            print(
                f"\n📊 Résultat final: {passed}/{total_tests} tests réussis ({success_rate:.1f}%)."
            )
            print(f"🚀 Temps réel écoulé: {global_duration:.1f}s")
            print(
                f"⏱️  Vitesse moyenne: {avg_speed:.2f}s / test (total cumulé: {total_duration:.1f}s)."
            )
        else:
            print("\nAucun test exécuté.")

    finally:
        if api_process is not None:
            print("\nArrêt de l'API backend...")
            stop_backend(api_process, graceful_timeout=5.0)


if __name__ == "__main__":
    main()
