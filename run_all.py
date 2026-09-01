# -*- coding: utf-8 -*-
"""Orchestrator: run all 5 crawlers, normalize, and build the static site.

Each crawler is best-effort: if one fails (network/anti-bot) OR returns an
empty result, we keep the previous good data (backed up per run) so the board
never hard-fails or degrades to empty across flaky scheduled runs.
"""
import os, sys, subprocess, shutil, json

HERE = os.path.dirname(os.path.abspath(__file__))

# crawler script -> the data file(s) it writes (backed up & guarded)
CRAWLERS = [
    ("crawl_tencent.py",   ["jobs_tencent.json"]),
    ("crawl_bytedance.py", ["bytedance_raw.json"]),
    ("crawl_taotian.py",   ["taotian_raw.json"]),
    ("crawl_eleme.py",     ["eleme_raw.json"]),
    ("crawl_baidu.py",     ["baidu_raw.json"]),
]


def _nonempty_list(path):
    """Return True if path is a JSON list with >=1 element."""
    if not os.path.exists(path):
        return False
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception:
        return False
    return isinstance(data, list) and len(data) > 0


def run_crawler(script, out_files):
    print(f"\n===== {script} =====", flush=True)
    # back up previous good outputs
    for f in out_files:
        fp = os.path.join(HERE, f)
        if _nonempty_list(fp):
            shutil.copyfile(fp, fp + ".bak")

    try:
        subprocess.run([sys.executable, os.path.join(HERE, script)],
                       check=True, timeout=600)
    except subprocess.TimeoutExpired:
        print(f"[WARN] {script} timed out", flush=True)
    except subprocess.CalledProcessError as e:
        print(f"[WARN] {script} failed (exit {e.returncode})", flush=True)

    # guard: if any output became empty, restore from backup
    for f in out_files:
        fp = os.path.join(HERE, f)
        if not _nonempty_list(fp):
            bak = fp + ".bak"
            if os.path.exists(bak) and _nonempty_list(bak):
                shutil.copyfile(bak, fp)
                print(f"[INFO] {f} empty -> restored last good data", flush=True)
            else:
                print(f"[WARN] {f} empty and no backup kept", flush=True)


def run(script):
    print(f"\n===== {script} =====", flush=True)
    try:
        subprocess.run([sys.executable, os.path.join(HERE, script)],
                       check=True, timeout=600)
    except subprocess.TimeoutExpired:
        print(f"[WARN] {script} timed out, skipping", flush=True)
    except subprocess.CalledProcessError as e:
        print(f"[WARN] {script} failed (exit {e.returncode}), continuing", flush=True)


def main():
    jp = os.path.join(HERE, "jobs_data.json")
    prev_backup = jp + ".prev"

    # Back up the previously committed good data. On a fresh CI checkout the raw
    # crawler outputs are not committed and have no .bak, so this committed copy
    # is the only fallback if a flaky run degrades the total count.
    if _nonempty_list(jp):
        shutil.copyfile(jp, prev_backup)

    for script, outs in CRAWLERS:
        run_crawler(script, outs)
    run("normalize.py")
    run("build_html.py")

    # Degradation guard: if the freshly crawled total drops below 50% of the
    # previously committed count, the crawl most likely partial-failed on a
    # flaky runner. Keep the previous good jobs_data.json and rebuild the site
    # from it so the public board never silently shrinks across scheduled runs.
    if os.path.exists(prev_backup) and _nonempty_list(prev_backup):
        try:
            prev_count = len(json.load(open(prev_backup, encoding="utf-8")).get("jobs", []))
            new_count = len(json.load(open(jp, encoding="utf-8")).get("jobs", [])) if _nonempty_list(jp) else 0
        except Exception:
            prev_count = new_count = 0
        if new_count > 0 and prev_count > 0 and new_count < prev_count * 0.5:
            print(f"[GUARD] new total {new_count} < 50% of previous {prev_count}; "
                  f"restoring previous jobs_data.json", flush=True)
            os.replace(prev_backup, jp)
            run("build_html.py")

    # sanity
    if os.path.exists(jp):
        n = len(json.load(open(jp, encoding="utf-8")).get("jobs", []))
        print(f"\nDONE: jobs_data.json has {n} jobs", flush=True)
    else:
        print("\n[ERROR] jobs_data.json not produced!", flush=True)

    # cleanup temp backup
    try:
        if os.path.exists(prev_backup):
            os.remove(prev_backup)
    except Exception:
        pass


if __name__ == "__main__":
    main()
