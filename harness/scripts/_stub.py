"""Shared helper for cyberkinetic Phase 1 stub scripts.

Every stub echoes the skill it stands in for, the arguments it received, and the
database state transition it WOULD perform, then exits 0. This lets the full skill
cascade run end-to-end before any real logic exists.

Replacing a stub with a real implementation MUST preserve the skill's HARD-GATE and its
documented DB pre/postconditions (see the matching skills/<name>/SKILL.md).
"""
import sys


def announce(skill, intent, args, would_do):
    print(f"[STUB] skill: {skill}")
    print(f"[STUB] intent: {intent}")
    print("[STUB] args:")
    for k, v in vars(args).items():
        print(f"[STUB]   --{k} = {v!r}")
    print("[STUB] would perform:")
    for line in would_do:
        print(f"[STUB]   - {line}")
    print("[STUB] (no database writes performed by stub)")
    sys.exit(0)
