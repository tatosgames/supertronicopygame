import sys

from app import App
from cli import parse_args


def main(argv: list[str] | None = None) -> int:
    app = App(parse_args(argv if argv is not None else sys.argv[1:]))
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
