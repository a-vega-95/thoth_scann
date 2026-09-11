"""
Thoth Project Extractor
Motor para extraer repositorios y carpetas de software completos,
generando árbol jerárquico (TREE.md), archivos individuales en espejo
y/o archivo consolidado único optimizado para LLMs.
"""

import os
import io
import fnmatch
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, BinaryIO

# Mapeo de extensiones a identificadores de lenguaje Markdown
EXTENSION_TO_LANG: Dict[str, str] = {
    ".py": "python",
    ".java": "java",
    ".r": "r",
    ".R": "r",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "jsx",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".rb": "ruby",
    ".sql": "sql",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".xml": "xml",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
    ".env": "bash",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".scala": "scala",
    ".dart": "dart",
    ".swift": "swift",
    ".lua": "lua",
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "text",
}

# Nombres especiales de archivo a lenguaje
SPECIAL_FILES: Dict[str, str] = {
    "dockerfile": "dockerfile",
    "makefile": "makefile",
    "cmakelists.txt": "cmake",
    "jenkinsfile": "groovy",
    "gemfile": "ruby",
    "vagrantfile": "ruby",
    "procfile": "text",
}

# Carpetas de ruido que se deben excluir por defecto
DEFAULT_IGNORE_DIRS: Set[str] = {
    ".git",
    ".github",
    ".gitlab",
    ".svn",
    ".hg",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "bower_components",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "target",
    "build",
    "dist",
    "out",
    "bin",
    "obj",
    ".idea",
    ".vscode",
    ".vs",
    ".next",
    ".nuxt",
    "coverage",
    ".nyc_output",
    "vendor",
    "output",
    "output_markdown",
}

# Extensiones de binarios, multimedia o lockfiles que no aportan código
DEFAULT_IGNORE_EXTS: Set[str] = {
    # Binarios y compilados
    ".exe", ".dll", ".so", ".dylib", ".class", ".jar", ".war", ".ear",
    ".pyc", ".pyo", ".pyd", ".o", ".a", ".obj", ".bin",
    # Archivos comprimidos
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar", ".iso",
    # Multimedia
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp", ".bmp",
    ".mp3", ".wav", ".ogg", ".flac", ".m4a", ".mp4", ".mov", ".avi", ".mkv",
    # Fuentes tipográficas
    ".ttf", ".otf", ".woff", ".woff2", ".eot",
    # Lockfiles masivos (ruido de tokens)
    ".lock", "-lock.json", ".lockb",
}


@dataclass
class ExtractionOptions:
    """Opciones de configuración para la extracción."""
    generate_tree: bool = True
    generate_separate_files: bool = True
    generate_consolidated: bool = True
    max_file_size_kb: int = 1024  # 1 MB límite por archivo de código
    include_extensions: Optional[Set[str]] = None
    exclude_dirs: Set[str] = field(default_factory=lambda: set(DEFAULT_IGNORE_DIRS))
    exclude_extensions: Set[str] = field(default_factory=lambda: set(DEFAULT_IGNORE_EXTS))


@dataclass
class FileItem:
    """Representa un archivo extraído del proyecto."""
    rel_path: str
    abs_path: Optional[Path]
    content: str
    language: str
    line_count: int
    char_count: int
    size_bytes: int


@dataclass
class ExtractionResult:
    """Resultado detallado de la extracción del proyecto."""
    project_name: str
    output_dir: Path
    total_files: int
    total_lines: int
    total_characters: int
    token_estimate: int
    language_stats: Dict[str, Dict[str, int]]  # lang -> {'files': int, 'lines': int}
    tree_content: str
    consolidated_path: Optional[Path] = None
    tree_path: Optional[Path] = None
    sources_dir: Optional[Path] = None
    errors: List[str] = field(default_factory=list)


class ProjectExtractor:
    """Motor central de extracción y documentación de proyectos de software."""

    def __init__(self, options: Optional[ExtractionOptions] = None):
        self.options = options or ExtractionOptions()

    def _is_ignored_path(self, rel_parts: Tuple[str, ...], filename: str) -> bool:
        """Determina si una ruta o archivo debe ser ignorado."""
        # Verificar carpetas
        for part in rel_parts:
            part_lower = part.lower()
            if part_lower in self.options.exclude_dirs:
                return True
            if part_lower.startswith(".") and part_lower != ".":
                # Ignorar carpetas ocultas por defecto
                return True

        # Verificar extensiones
        fname_lower = filename.lower()
        ext = os.path.splitext(fname_lower)[1]

        if ext in self.options.exclude_extensions:
            return True

        if fname_lower.endswith("-lock.json") or fname_lower.endswith(".lock"):
            return True

        if self.options.include_extensions:
            return ext not in self.options.include_extensions

        return False

    def _detect_language(self, filename: str) -> str:
        """Determina el identificador de lenguaje para Markdown."""
        fname_lower = filename.lower()
        if fname_lower in SPECIAL_FILES:
            return SPECIAL_FILES[fname_lower]

        ext = os.path.splitext(fname_lower)[1]
        return EXTENSION_TO_LANG.get(ext, "")

    def _read_file_safe(self, file_bytes: bytes) -> str:
        """Decodifica bytes a texto con fallback seguro."""
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                import charset_normalizer
                res = charset_normalizer.from_bytes(file_bytes).best()
                if res and res.encoding:
                    return str(res)
            except Exception:
                pass
            return file_bytes.decode("latin-1", errors="replace")

    def _build_tree_string(self, file_paths: List[str], project_name: str) -> str:
        """Construye un árbol visual jerárquico estilo 'tree' a partir de rutas relativas."""
        # Construir estructura de árbol con diccionarios anidados
        tree_dict: Dict = {}
        for path_str in sorted(file_paths):
            parts = path_str.replace("\\", "/").split("/")
            current = tree_dict
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]
        
        lines: List[str] = [f"{project_name}/"]

        def _render_level(subtree: Dict, prefix: str = ""):
            items = sorted(subtree.keys())
            for idx, item in enumerate(items):
                is_last = (idx == len(items) - 1)
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{item}")
                child_prefix = prefix + ("    " if is_last else "│   ")
                _render_level(subtree[item], child_prefix)

        _render_level(tree_dict)
        return "\n".join(lines)

    def extract_directory(
        self,
        source_dir: Path,
        output_base_dir: Path,
        project_name: Optional[str] = None,
    ) -> ExtractionResult:
        """Extrae un proyecto completo desde un directorio local en disco."""
        source_dir = Path(source_dir).resolve()
        if not source_dir.is_dir():
            raise ValueError(f"La ruta '{source_dir}' no es un directorio válido.")

        proj_name = project_name or source_dir.name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_run_dir = output_base_dir / f"{proj_name}_{timestamp}"
        target_run_dir.mkdir(parents=True, exist_ok=True)

        collected_files: List[FileItem] = []
        errors: List[str] = []

        # Recorrer el directorio
        for root, dirs, files in os.walk(source_dir):
            rel_root = os.path.relpath(root, source_dir)
            rel_parts = () if rel_root == "." else tuple(rel_root.replace("\\", "/").split("/"))

            # Filtrar carpetas in-place para que os.walk no entre en ellas
            dirs[:] = [
                d for d in dirs
                if not self._is_ignored_path(rel_parts + (d,), d)
            ]

            for fname in sorted(files):
                if self._is_ignored_path(rel_parts, fname):
                    continue

                abs_file = Path(root) / fname
                rel_file = str(Path(rel_root) / fname).replace("\\", "/")
                if rel_file.startswith("./"):
                    rel_file = rel_file[2:]

                # Comprobar tamaño máximo
                try:
                    file_size = abs_file.stat().st_size
                    if file_size > self.options.max_file_size_kb * 1024:
                        errors.append(f"Archivo omitido por exceder tamaño ({file_size / 1024:.0f} KB): {rel_file}")
                        continue

                    raw_bytes = abs_file.read_bytes()
                    content = self._read_file_safe(raw_bytes)
                    lines = content.splitlines()
                    lang = self._detect_language(fname)

                    collected_files.append(
                        FileItem(
                            rel_path=rel_file,
                            abs_path=abs_file,
                            content=content,
                            language=lang,
                            line_count=len(lines),
                            char_count=len(content),
                            size_bytes=file_size,
                        )
                    )
                except Exception as ex:
                    errors.append(f"Error al leer {rel_file}: {str(ex)}")

        return self._generate_outputs(proj_name, collected_files, target_run_dir, errors)

    def extract_zip(
        self,
        zip_source: BinaryIO,
        output_base_dir: Path,
        project_name: str = "proyecto_zip",
    ) -> ExtractionResult:
        """Extrae un proyecto completo desde un archivo ZIP en memoria o disco."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_run_dir = output_base_dir / f"{project_name}_{timestamp}"
        target_run_dir.mkdir(parents=True, exist_ok=True)

        collected_files: List[FileItem] = []
        errors: List[str] = []

        zip_source.seek(0)
        with zipfile.ZipFile(zip_source, "r") as zf:
            for zip_info in zf.infolist():
                if zip_info.is_dir():
                    continue

                norm_path = zip_info.filename.replace("\\", "/").strip("/")
                parts = norm_path.split("/")
                filename = parts[-1]
                dir_parts = tuple(parts[:-1])

                if self._is_ignored_path(dir_parts, filename):
                    continue

                if zip_info.file_size > self.options.max_file_size_kb * 1024:
                    errors.append(f"Archivo omitido por tamaño ({zip_info.file_size / 1024:.0f} KB): {norm_path}")
                    continue

                try:
                    raw_bytes = zf.read(zip_info.filename)
                    content = self._read_file_safe(raw_bytes)
                    lines = content.splitlines()
                    lang = self._detect_language(filename)

                    collected_files.append(
                        FileItem(
                            rel_path=norm_path,
                            abs_path=None,
                            content=content,
                            language=lang,
                            line_count=len(lines),
                            char_count=len(content),
                            size_bytes=zip_info.file_size,
                        )
                    )
                except Exception as ex:
                    errors.append(f"Error al extraer {norm_path}: {str(ex)}")

        return self._generate_outputs(project_name, collected_files, target_run_dir, errors)

    def _generate_outputs(
        self,
        project_name: str,
        files: List[FileItem],
        run_dir: Path,
        errors: List[str],
    ) -> ExtractionResult:
        """Genera TREE.md, carpeta espejo sources/ y CONSOLIDATED.md según las opciones."""
        total_lines = sum(f.line_count for f in files)
        total_chars = sum(f.char_count for f in files)
        total_files = len(files)
        token_estimate = int(total_chars / 4)

        # Estadísticas de lenguaje
        lang_stats: Dict[str, Dict[str, int]] = {}
        for f in files:
            lang_label = f.language or "texto_plano"
            if lang_label not in lang_stats:
                lang_stats[lang_label] = {"files": 0, "lines": 0}
            lang_stats[lang_label]["files"] += 1
            lang_stats[lang_label]["lines"] += f.line_count

        # Generar representación de árbol
        file_paths = [f.rel_path for f in files]
        ascii_tree = self._build_tree_string(file_paths, project_name)

        tree_path: Optional[Path] = None
        consolidated_path: Optional[Path] = None
        sources_dir: Optional[Path] = None

        # 1. Generar TREE.md
        if self.options.generate_tree:
            tree_md_parts = [
                f"# Mapa Arquitectónico de Contexto: `{project_name}`\n",
                f"> Generado por **Thoth Scann** el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
                "## Métricas del Proyecto",
                f"- **Total de Archivos**: `{total_files:,}`",
                f"- **Total de Líneas de Código**: `{total_lines:,}`",
                f"- **Total de Caracteres**: `{total_chars:,}`",
                f"- **Estimación de Tokens (LLM)**: `~{token_estimate:,}` tokens\n",
                "## Distribución de Lenguajes\n",
                "| Lenguaje | Archivos | Líneas | % Código |",
                "| :--- | :--- | :--- | :--- |",
            ]

            for lang, data in sorted(lang_stats.items(), key=lambda x: x[1]["lines"], reverse=True):
                pct = (data["lines"] / total_lines * 100) if total_lines > 0 else 0
                tree_md_parts.append(
                    f"| **{lang}** | {data['files']:,} | {data['lines']:,} | {pct:.1f}% |"
                )

            tree_md_parts.extend([
                "\n## Árbol Jerárquico del Proyecto\n",
                "```text",
                ascii_tree,
                "```\n",
                "## Catálogo de Archivos Fuente\n",
            ])

            for f in sorted(files, key=lambda x: x.rel_path):
                tree_md_parts.append(f"- [`{f.rel_path}`](sources/{f.rel_path}.md) — *({f.line_count:,} líneas, {f.language or 'plain'})*")

            tree_content = "\n".join(tree_md_parts)
            tree_path = run_dir / "TREE.md"
            tree_path.write_text(tree_content, encoding="utf-8")
        else:
            tree_content = ascii_tree

        # 2. Generar Archivos Separados (Estructura Espejo)
        if self.options.generate_separate_files:
            sources_dir = run_dir / "sources"
            sources_dir.mkdir(parents=True, exist_ok=True)

            for f in files:
                target_md_path = sources_dir / f"{f.rel_path}.md"
                target_md_path.parent.mkdir(parents=True, exist_ok=True)

                md_doc = (
                    f"# Archivo: `{f.rel_path}`\n\n"
                    f"- **Proyecto**: `{project_name}`\n"
                    f"- **Lenguaje**: `{f.language or 'plain'}`\n"
                    f"- **Líneas**: `{f.line_count:,}`\n\n"
                    f"```{f.language}\n"
                    f"{f.content}\n"
                    f"```\n"
                )
                target_md_path.write_text(md_doc, encoding="utf-8")

        # 3. Generar CONSOLIDATED.md (Archivo Todo-en-Uno para LLMs de contexto largo)
        if self.options.generate_consolidated:
            con_parts = [
                f"# Contexto Consolidado del Proyecto: `{project_name}`\n",
                "> Este documento consolida todo el código fuente del proyecto para análisis arquitectónico, ",
                "> resolución de errores, auditoría o refactorización integral con LLMs.\n",
                "## Estructura de Directorios\n",
                "```text",
                ascii_tree,
                "```\n",
                "## Catálogo de Archivos Fuente\n",
            ]

            for f in sorted(files, key=lambda x: x.rel_path):
                con_parts.append(
                    f"\n{'=' * 80}\n"
                    f"FILE: {f.rel_path}\n"
                    f"LANGUAGE: {f.language or 'text'}\n"
                    f"LINES: {f.line_count}\n"
                    f"{'=' * 80}\n"
                    f"```{f.language}\n"
                    f"{f.content}\n"
                    f"```\n"
                )

            consolidated_path = run_dir / "CONSOLIDATED.md"
            consolidated_path.write_text("\n".join(con_parts), encoding="utf-8")

        return ExtractionResult(
            project_name=project_name,
            output_dir=run_dir,
            total_files=total_files,
            total_lines=total_lines,
            total_characters=total_chars,
            token_estimate=token_estimate,
            language_stats=lang_stats,
            tree_content=tree_content,
            consolidated_path=consolidated_path,
            tree_path=tree_path,
            sources_dir=sources_dir,
            errors=errors,
        )


def extract_directory(
    source_dir: Path | str,
    output_base_dir: Optional[Path | str] = None,
    options: Optional[ExtractionOptions] = None,
) -> ExtractionResult:
    """Función de conveniencia para extraer una carpeta local."""
    target_out = Path(output_base_dir) if output_base_dir else (Path.cwd() / "output")
    extractor = ProjectExtractor(options)
    return extractor.extract_directory(Path(source_dir), target_out)


def extract_zip(
    zip_source: BinaryIO,
    output_base_dir: Optional[Path | str] = None,
    project_name: str = "proyecto_zip",
    options: Optional[ExtractionOptions] = None,
) -> ExtractionResult:
    """Función de conveniencia para extraer un archivo zip."""
    target_out = Path(output_base_dir) if output_base_dir else (Path.cwd() / "output")
    extractor = ProjectExtractor(options)
    return extractor.extract_zip(zip_source, target_out, project_name=project_name)
