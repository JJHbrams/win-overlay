"""One structural correction: actual parent seating + flattened lancet profiles."""
from pathlib import Path
import prepare_curved_rear
prepare_curved_rear.main(output=(Path(__file__).resolve().parents[3]/'.mia-cache/face-live/curved-rear03'),rooted=True)
