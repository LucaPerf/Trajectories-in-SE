import argparse
import re
from collections import defaultdict

from datasets import load_dataset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int, default=None, help="print this instance (as before)")
    parser.add_argument("--repo", type=str, default=None, help="list indices for one repo only, e.g. --repo django")
    parser.add_argument("--family", type=str, default=None,
                         help="group one repo's instances by sub-package touched in the gold patch, e.g. --family sympy")
    parser.add_argument("--summary", action="store_true",
                         help="with --family, only print 'sub-package -> count', no instance ids")
    args = parser.parse_args()

    ds = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")

    if args.family is not None:
        by_submodule = defaultdict(list)
        for i, row in enumerate(ds):
            if not row["instance_id"].startswith(f"{args.family}__"):
                continue
            files = re.findall(r"^diff --git a/(\S+) b/\S+", row["patch"], re.MULTILINE)
            submodules = set()
            for f in files:
                parts = f.split("/")
                if len(parts) >= 2 and parts[0] == args.family:
                    submodules.add(parts[1])
                else:
                    submodules.add("(other)")
            key = tuple(sorted(submodules))
            by_submodule[key].append((i, row["instance_id"]))

        if not by_submodule:
            print(f"No instances for family '{args.family}'.")
            return

        total = 0
        for key in sorted(by_submodule, key=lambda k: -len(by_submodule[k])):
            insts = by_submodule[key]
            total += len(insts)
            label = "+".join(key)
            if args.summary:
                print(f"{label:20s} {len(insts):3d}")
            else:
                print(f"{label}  -> {len(insts)} instances")
                for idx, iid in insts:
                    print(f"    {idx:3d}  {iid}")

        print(f"\nTotal {args.family} instances classified: {total}")
        return

    if args.index is not None:
        ex = ds[args.index]
        print("-"*50)
        print("INSTANCE:", ex["instance_id"])
        print("-"*10, "PROBLEM STATEMENT", "-"*10)
        print(ex["problem_statement"])
        print("-"*10, "PATCH", "-"*10)
        print(ex["patch"])
        print("-"*10, "TEST PATCH", "-"*10)
        print(ex["test_patch"])
        print("="*50)
        print(ds)
        print("="*50)
        print(ex["FAIL_TO_PASS"])
        print("="*50)
        print(ex["PASS_TO_PASS"])
        return

    by_repo = defaultdict(list)
    for i, row in enumerate(ds):
        repo = row["instance_id"].split("__", 1)[0]
        by_repo[repo].append(i)

    if args.repo:
        indices = by_repo.get(args.repo)
        if not indices:
            print(f"No instances for repo '{args.repo}'. Available repos: {', '.join(sorted(by_repo))}")
            return
        print(f"{args.repo}: {len(indices)} instances")
        print(indices)
        return

    print(f"{len(ds)} instances, {len(by_repo)} repos\n")
    for repo in sorted(by_repo):
        indices = by_repo[repo]
        print(f"{repo:20s} {len(indices):3d}  {indices}")


if __name__ == "__main__":
    main()
