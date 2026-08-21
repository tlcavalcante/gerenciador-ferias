"""Runtime compartilhado e estado da aplicação."""
from core import *
import core as _core
globals().update({k: v for k, v in vars(_core).items() if not k.startswith("__")})
