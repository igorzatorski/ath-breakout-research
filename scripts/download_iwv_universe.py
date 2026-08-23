"""Download and save the current IWV holdings universe."""

from pathlib import Path

from ath_breakout.data.adapters.ishares import download_iwv_universe


OUTPUT_DIRECTORY = Path("data/universe")


def main() -> None:
    universe = download_iwv_universe()
    as_of_date = universe["as_of_date"].iloc[0].strftime("%Y-%m-%d")
    output_path = OUTPUT_DIRECTORY / f"iwv_holdings_{as_of_date}.csv"

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    universe.to_csv(output_path, index=False)

    print(f"Saved {len(universe)} securities to {output_path}")


if __name__ == "__main__":
    main()
