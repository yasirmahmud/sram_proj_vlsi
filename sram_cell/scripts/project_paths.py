"""Locate external model inputs without depending on the checkout's location."""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
INSTALLED_MODEL = Path('/apps/cds/local/GPDK045/models/spectre/gpdk045_mos.scs')


def model_file():
    override = os.environ.get('SRAM_MODEL_FILE')
    if override:
        path = Path(override).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f'SRAM_MODEL_FILE does not exist: {path}')
        return path
    for path in (
        ROOT.parents[1] / 'Project Instruction Files/gpdk045_mos.scs',
        ROOT.parents[1] / 'Project files/gpdk045_mos.scs',
        INSTALLED_MODEL,
    ):
        if path.is_file():
            return path
    raise FileNotFoundError('Set SRAM_MODEL_FILE to the GPDK045 MOS model file.')
