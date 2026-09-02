"""Direct CLI entrypoint for running the research layer: python -m app.research <TICKER>."""
from app.research.service import main

if __name__ == "__main__":
    main()