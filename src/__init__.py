"""
Version Control Manager - VCM
A Python package for managing Git tags following Semantic Versioning and Gitflow.
"""

__version__ = "0.1.0"
__author__ = "0jas"
__email__ = "0jas.0sv@gmail.com"
__description__ = "Git tag management with SemVer and Gitflow"

# Import main classes/functions for easy access
from .vcm import VersionControlManager
from .exceptions import *

__all__ = [
    "VersionControlManager",
    "InvalidTagCreation",
    "__version__",
]