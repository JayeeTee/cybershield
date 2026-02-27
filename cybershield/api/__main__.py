"""Run API with `python -m cybershield.api`."""

import uvicorn


def main() -> None:
    uvicorn.run("cybershield.api.app:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()

