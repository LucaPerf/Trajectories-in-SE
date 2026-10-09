import argparse
from collections import defaultdict

from datasets import load_dataset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int, default=None, help="print this instance (as before)")
    parser.add_argument("--repo", type=str, default=None, help="list indices for one repo only, e.g. --repo django")
    args = parser.parse_args()

    ds = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")

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
