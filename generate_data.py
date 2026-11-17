"""Generate reproducible Cross/X fixtures for E3."""
import json

from main import DATA, SIZES, make_pattern


def main() -> None:
    """Write clean and slightly noisy examples to data.json."""
    filters = {}
    patterns = {}
    for size in SIZES:
        cross = make_pattern(size, "Cross")
        diagonal = make_pattern(size, "X")
        filters[f"size_{size}"] = {"cross": cross, "x": diagonal}
        noisy = [row[:] for row in cross]
        noisy[0][0] = 0.2
        for index, (image, label) in enumerate(
            ((cross, "+"), (diagonal, "x"), (noisy, "+")), 1
        ):
            patterns[f"size_{size}_{index}"] = {
                "input": image, "expected": label
            }
    data = {"filters": filters, "patterns": patterns}
    DATA.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
