"""dirproof: offline directory integrity snapshots."""
from .core import ManifestError, compare, read_manifest, snapshot

__version__ = '0.1.0'
__all__ = ['ManifestError', 'compare', 'read_manifest', 'snapshot']
