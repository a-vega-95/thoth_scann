"""
Thoth Extractor - Módulo de extracción y análisis de proyectos de software para LLMs.
"""

from .project_extractor import (
    ProjectExtractor,
    ExtractionOptions,
    ExtractionResult,
    extract_directory,
    extract_zip,
)
from .document_splitter import (
    DocumentSplitter,
    SplitOptions,
    DocumentPart,
    SplitResult,
)

__all__ = [
    "ProjectExtractor",
    "ExtractionOptions",
    "ExtractionResult",
    "extract_directory",
    "extract_zip",
    "DocumentSplitter",
    "SplitOptions",
    "DocumentPart",
    "SplitResult",
]

