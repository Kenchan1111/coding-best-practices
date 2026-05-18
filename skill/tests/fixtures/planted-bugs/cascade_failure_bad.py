import subprocess


def build_archive() -> None:
    subprocess.run(["make", "briefing"])


def main() -> int:
    build_archive()
    return 0
