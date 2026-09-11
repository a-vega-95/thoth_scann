"""
Módulo de división inteligente de documentos Markdown para libros y textos extensos.
Proporciona particionado respetuoso de la sintaxis Markdown e inyección de metadatos
de contexto empresarial (YAML Frontmatter, banners de continuidad e índice maestro).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import io
from pathlib import Path
import re
from typing import List, Optional
import zipfile


@dataclass
class SplitOptions:
    """Configuración para la división de documentos Markdown."""

    mode: str = "tokens"  # "tokens", "parts", "headings"
    target_tokens: int = 25000
    num_parts: int = 3
    heading_level: int = 1  # 1 for '# ', 2 for '## '
    inject_ai_context: bool = True
    base_name: str = "documento"
    original_filename: str = "documento.pdf"
    document_title: Optional[str] = None


@dataclass
class DocumentPart:
    """Representa una fracción individual del documento dividido."""

    part_number: int
    total_parts: int
    filename: str
    content: str
    char_count: int
    word_count: int
    token_estimate: int
    first_heading: str = ""
    headings_summary: List[str] = field(default_factory=list)


@dataclass
class SplitResult:
    """Resultado consolidado del proceso de división."""

    parts: List[DocumentPart]
    index_markdown: str
    index_filename: str
    total_tokens: int
    total_characters: int
    total_words: int
    document_id: str
    document_title: str
    original_filename: str

    def get_zip_bytes(self) -> bytes:
        """Genera un archivo ZIP en memoria con todas las partes y el índice maestro."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Escribir índice maestro
            zf.writestr(self.index_filename, self.index_markdown)
            # Escribir cada parte
            for part in self.parts:
                zf.writestr(part.filename, part.content)
        buffer.seek(0)
        return buffer.getvalue()

    def save_to_disk(self, target_directory: Path) -> Path:
        """Guarda todas las partes y el índice maestro en una subcarpeta dedicada en disco."""
        subfolder_name = f"{Path(self.original_filename).stem}_partes"
        dest_dir = target_directory / subfolder_name
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Guardar índice maestro
        (dest_dir / self.index_filename).write_text(self.index_markdown, encoding="utf-8")

        # Guardar partes individuales
        for part in self.parts:
            (dest_dir / part.filename).write_text(part.content, encoding="utf-8")

        return dest_dir


@dataclass
class _MarkdownBlock:
    """Bloque atómico de contenido Markdown."""

    text: str
    is_heading: bool = False
    heading_level: int = 0
    heading_title: str = ""

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def token_estimate(self) -> int:
        return max(1, int(len(self.text) / 4))


class DocumentSplitter:
    """Motor de particionado y enriquecimiento contextual para documentos extensos."""

    @staticmethod
    def calculate_tokens(text: str) -> int:
        """Estima la cantidad de tokens para un texto dado (aproximación estándar 4 caracteres/token)."""
        return max(1, int(len(text) / 4))

    @staticmethod
    def generate_document_id(base_name: str, text: str) -> str:
        """Genera un identificador determinista y único para el documento."""
        content_hash = hashlib.sha256(f"{base_name}:{len(text)}".encode("utf-8")).hexdigest()[:12]
        return f"doc_{content_hash}"

    @classmethod
    def parse_blocks(cls, markdown_text: str) -> List[_MarkdownBlock]:
        """
        Divide el texto Markdown en bloques lógicos atómicos sin fracturar
        bloques de código (fenced code blocks) ni tablas.
        """
        lines = markdown_text.splitlines(keepends=True)
        blocks: List[_MarkdownBlock] = []

        current_lines: List[str] = []
        in_code_block = False
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")

        for line in lines:
            stripped = line.strip()

            # Detección de inicio/fin de bloques de código cercados
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                current_lines.append(line)
                continue

            if in_code_block:
                current_lines.append(line)
                continue

            # Fuera de bloques de código: detección de encabezados
            match_heading = heading_pattern.match(stripped)
            if match_heading:
                # Si teníamos líneas acumuladas previas, cerrarlas como bloque
                if current_lines:
                    block_text = "".join(current_lines)
                    if block_text.strip():
                        blocks.append(_MarkdownBlock(text=block_text))
                    current_lines = []

                # Crear bloque dedicado para el encabezado
                level = len(match_heading.group(1))
                title = match_heading.group(2).strip()
                blocks.append(
                    _MarkdownBlock(
                        text=line,
                        is_heading=True,
                        heading_level=level,
                        heading_title=title,
                    )
                )
                continue

            # Línea vacía actúa como delimitador de párrafo fuera de código
            if stripped == "":
                current_lines.append(line)
                block_text = "".join(current_lines)
                if block_text.strip():
                    blocks.append(_MarkdownBlock(text=block_text))
                current_lines = []
                continue

            current_lines.append(line)

        # Agregar remanente si existe
        if current_lines:
            block_text = "".join(current_lines)
            if block_text.strip():
                blocks.append(_MarkdownBlock(text=block_text))

        return blocks

    @classmethod
    def split_document(cls, markdown_text: str, options: SplitOptions) -> SplitResult:
        """
        Punto de entrada principal: divide un texto Markdown según la estrategia
        configurada e inyecta la estructura de contexto para LLMs/RAG.
        """
        if not markdown_text or not markdown_text.strip():
            empty_part = DocumentPart(
                part_number=1,
                total_parts=1,
                filename=f"{options.base_name}_part_01_of_01.md",
                content="",
                char_count=0,
                word_count=0,
                token_estimate=0,
            )
            return SplitResult(
                parts=[empty_part],
                index_markdown="",
                index_filename=f"{options.base_name}_INDEX.md",
                total_tokens=0,
                total_characters=0,
                total_words=0,
                document_id="doc_empty",
                document_title=options.document_title or options.base_name,
                original_filename=options.original_filename,
            )

        doc_title = options.document_title or options.base_name.replace("_", " ").title()
        doc_id = cls.generate_document_id(options.base_name, markdown_text)
        blocks = cls.parse_blocks(markdown_text)

        # 1. Agrupar bloques según la estrategia seleccionada
        if options.mode == "parts":
            raw_groups = cls._split_by_parts(blocks, options.num_parts)
        elif options.mode == "headings":
            raw_groups = cls._split_by_headings(blocks, options.heading_level)
        else:  # default "tokens"
            raw_groups = cls._split_by_tokens(blocks, options.target_tokens)

        # Si por alguna razón la división produjo 0 grupos
        if not raw_groups:
            raw_groups = [blocks]

        total_parts = len(raw_groups)
        pad_width = max(2, len(str(total_parts)))

        # 2. Extraer métricas globales
        total_chars = len(markdown_text)
        total_words = len(markdown_text.split())
        total_tokens = cls.calculate_tokens(markdown_text)

        # 3. Construir partes individuales con metadatos
        parts: List[DocumentPart] = []
        for idx, group in enumerate(raw_groups, start=1):
            part_body = "".join(b.text for b in group).strip()
            part_filename = f"{options.base_name}_part_{idx:0{pad_width}d}_of_{total_parts:0{pad_width}d}.md"

            # Identificar encabezados en esta parte
            part_headings = [b.heading_title for b in group if b.is_heading and b.heading_title]
            first_heading = part_headings[0] if part_headings else f"Parte {idx}"

            # Nombres de archivos anterior y siguiente para navegación
            prev_filename = (
                f"{options.base_name}_part_{idx-1:0{pad_width}d}_of_{total_parts:0{pad_width}d}.md"
                if idx > 1
                else None
            )
            next_filename = (
                f"{options.base_name}_part_{idx+1:0{pad_width}d}_of_{total_parts:0{pad_width}d}.md"
                if idx < total_parts
                else None
            )
            index_filename = f"{options.base_name}_INDEX.md"

            part_chars = len(part_body)
            part_words = len(part_body.split())
            part_tokens = cls.calculate_tokens(part_body)

            if options.inject_ai_context:
                final_content = cls._build_part_with_context(
                    body=part_body,
                    document_id=doc_id,
                    document_title=doc_title,
                    original_filename=options.original_filename,
                    part_number=idx,
                    total_parts=total_parts,
                    part_filename=part_filename,
                    prev_filename=prev_filename,
                    next_filename=next_filename,
                    index_filename=index_filename,
                    part_tokens=part_tokens,
                    total_tokens=total_tokens,
                    part_chars=part_chars,
                    total_chars=total_chars,
                    headings=part_headings,
                )
            else:
                final_content = part_body

            parts.append(
                DocumentPart(
                    part_number=idx,
                    total_parts=total_parts,
                    filename=part_filename,
                    content=final_content,
                    char_count=part_chars,
                    word_count=part_words,
                    token_estimate=part_tokens,
                    first_heading=first_heading,
                    headings_summary=part_headings[:8],
                )
            )

        # 4. Generar índice maestro (<base_name>_INDEX.md)
        index_filename = f"{options.base_name}_INDEX.md"
        index_markdown = cls._build_master_index(
            document_id=doc_id,
            document_title=doc_title,
            original_filename=options.original_filename,
            index_filename=index_filename,
            parts=parts,
            total_tokens=total_tokens,
            total_chars=total_chars,
            total_words=total_words,
            split_mode=options.mode,
        )

        return SplitResult(
            parts=parts,
            index_markdown=index_markdown,
            index_filename=index_filename,
            total_tokens=total_tokens,
            total_characters=total_chars,
            total_words=total_words,
            document_id=doc_id,
            document_title=doc_title,
            original_filename=options.original_filename,
        )

    # -------------------------------------------------------------------------
    # Estrategias de Particionado
    # -------------------------------------------------------------------------

    @classmethod
    def _split_by_tokens(
        cls, blocks: List[_MarkdownBlock], target_tokens: int
    ) -> List[List[_MarkdownBlock]]:
        """Divide acumulando bloques hasta alcanzar el umbral de tokens deseado."""
        groups: List[List[_MarkdownBlock]] = []
        current_group: List[_MarkdownBlock] = []
        current_tokens = 0

        for block in blocks:
            b_tokens = block.token_estimate
            # Si añadir este bloque supera el target y el grupo actual no está vacío
            if current_tokens + b_tokens > target_tokens and current_group:
                groups.append(current_group)
                current_group = [block]
                current_tokens = b_tokens
            else:
                current_group.append(block)
                current_tokens += b_tokens

        if current_group:
            groups.append(current_group)

        return groups

    @classmethod
    def _split_by_parts(
        cls, blocks: List[_MarkdownBlock], target_num_parts: int
    ) -> List[List[_MarkdownBlock]]:
        """Divide el documento en un número predefinido de partes de tamaño equilibrado."""
        if target_num_parts <= 1 or not blocks:
            return [blocks]

        total_tokens = sum(b.token_estimate for b in blocks)
        tokens_per_part = max(1, int(total_tokens / target_num_parts))

        groups: List[List[_MarkdownBlock]] = []
        current_group: List[_MarkdownBlock] = []
        current_tokens = 0

        for block in blocks:
            current_group.append(block)
            current_tokens += block.token_estimate

            # Si alcanzamos la cuota y aún nos quedan partes por formar
            if (
                current_tokens >= tokens_per_part
                and len(groups) < target_num_parts - 1
            ):
                groups.append(current_group)
                current_group = []
                current_tokens = 0

        if current_group:
            # Si ya tenemos target_num_parts partes y sobra un residuo, anexarlo a la última
            if len(groups) >= target_num_parts:
                groups[-1].extend(current_group)
            else:
                groups.append(current_group)

        return groups

    @classmethod
    def _split_by_headings(
        cls, blocks: List[_MarkdownBlock], target_level: int
    ) -> List[List[_MarkdownBlock]]:
        """Divide el documento en cada encabezado del nivel indicado (# o ##)."""
        groups: List[List[_MarkdownBlock]] = []
        current_group: List[_MarkdownBlock] = []

        for block in blocks:
            if block.is_heading and block.heading_level == target_level:
                if current_group:
                    groups.append(current_group)
                    current_group = [block]
                else:
                    current_group.append(block)
            else:
                current_group.append(block)

        if current_group:
            groups.append(current_group)

        # Si el documento no contenía encabezados de ese nivel, devolver todo como una sola parte
        return groups if groups else [blocks]

    # -------------------------------------------------------------------------
    # Inyección de Metadatos Contextuales para IA
    # -------------------------------------------------------------------------

    @classmethod
    def _build_part_with_context(
        cls,
        body: str,
        document_id: str,
        document_title: str,
        original_filename: str,
        part_number: int,
        total_parts: int,
        part_filename: str,
        prev_filename: Optional[str],
        next_filename: Optional[str],
        index_filename: str,
        part_tokens: int,
        total_tokens: int,
        part_chars: int,
        total_chars: int,
        headings: List[str],
    ) -> str:
        """Construye el contenido enriquecido con Frontmatter YAML, banner y pie de continuidad."""
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # 1. Frontmatter YAML
        prev_val = f'"{prev_filename}"' if prev_filename else "null"
        next_val = f'"{next_filename}"' if next_filename else "null"

        frontmatter_lines = [
            "---",
            f'document_id: "{document_id}"',
            f'document_title: "{document_title}"',
            f'original_filename: "{original_filename}"',
            f"part: {part_number}",
            f"total_parts: {total_parts}",
            f'part_filename: "{part_filename}"',
            f"previous_part: {prev_val}",
            f"next_part: {next_val}",
            f'master_index: "{index_filename}"',
            f"part_tokens_estimate: {part_tokens}",
            f"total_document_tokens_estimate: {total_tokens}",
            f"part_characters: {part_chars}",
            f"total_document_characters: {total_chars}",
            f'generated_at: "{now_iso}"',
        ]

        if headings:
            frontmatter_lines.append("topics_covered:")
            for h in headings[:6]:
                clean_h = h.replace('"', '\\"')
                frontmatter_lines.append(f'  - "{clean_h}"')

        frontmatter_lines.extend(
            [
                f'llm_context_instruction: "Fragmento {part_number} de {total_parts} del documento \'{document_title}\'. Mantiene continuidad conceptual con los fragmentos adyacentes y el índice maestro."',
                "---",
                "",
            ]
        )
        frontmatter = "\n".join(frontmatter_lines)

        # 2. Banner de Continuidad
        prev_nav = (
            f"Anterior: [`{prev_filename}`](./{prev_filename})"
            if prev_filename
            else "Anterior: *Inicio del documento*"
        )
        next_nav = (
            f"Siguiente: [`{next_filename}`](./{next_filename})"
            if next_filename
            else "Siguiente: *Fin del documento*"
        )

        banner = (
            f"> [!NOTE] Fragmento de Documento Extenso — Contexto para Modelos de Lenguaje (LLM / RAG)\n"
            f"> - **Documento Principal:** `{document_title}` (`{original_filename}`)\n"
            f"> - **Identificador:** `{document_id}` | **Ubicación:** Parte **{part_number}** de **{total_parts}** (~{part_tokens:,} tokens)\n"
            f"> - **Navegación:** {prev_nav} | [Índice Maestro (`{index_filename}`](./{index_filename}) | {next_nav}\n"
            f"> - **Directiva de Ingesta:** Este archivo contiene una fracción secuencial del texto completo. Si se requieren conceptos, definiciones o capítulos fuera de este rango, consulta el índice maestro o las partes adyacentes.\n\n"
        )

        # 3. Pie de página de continuidad
        footer_next = (
            f"Continúa en: [`{next_filename}`](./{next_filename})"
            if next_filename
            else "Este fragmento concluye el documento."
        )
        footer = (
            f"\n\n---\n"
            f"*Fin de la Parte {part_number} de {total_parts} — Documento: '{document_title}'. {footer_next} "
            f"Ver catálogo global en [`{index_filename}`](./{index_filename}).*\n"
        )

        return f"{frontmatter}{banner}{body}{footer}"

    # -------------------------------------------------------------------------
    # Generador de Índice Maestro / Manifiesto
    # -------------------------------------------------------------------------

    @classmethod
    def _build_master_index(
        cls,
        document_id: str,
        document_title: str,
        original_filename: str,
        index_filename: str,
        parts: List[DocumentPart],
        total_tokens: int,
        total_chars: int,
        total_words: int,
        split_mode: str,
    ) -> str:
        """Genera el documento maestro de navegación e índice general para agentes IA."""
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        mode_labels = {
            "tokens": "Por límite de tokens de contexto",
            "parts": "Por número fijo de partes",
            "headings": "Por capítulos / encabezados Markdown",
        }
        mode_desc = mode_labels.get(split_mode, split_mode)

        lines = [
            f"# Índice Maestro y Manifiesto de Navegación",
            f"",
            f"Documento particionado: **{document_title}**",
            f"",
            f"Este archivo actúa como manifiesto central y mapa de navegación para modelos de lenguaje (LLMs), "
            f"sistemas RAG (Retrieval-Augmented Generation) y agentes inteligentes autónomos. "
            f"Permite identificar con precisión en qué fragmento se encuentra cada sección temática "
            f"sin necesidad de cargar la totalidad del documento en la ventana de contexto.",
            f"",
            f"---",
            f"",
            f"## Metadatos Globales del Documento",
            f"",
            f"| Propiedad | Valor |",
            f"| :--- | :--- |",
            f"| **Título del Documento** | `{document_title}` |",
            f"| **Archivo Fuente** | `{original_filename}` |",
            f"| **Identificador Global** | `{document_id}` |",
            f"| **Total de Partes** | **{len(parts)}** |",
            f"| **Tokens Totales (Aprox.)** | ~{total_tokens:,} |",
            f"| **Palabras Totales** | {total_words:,} |",
            f"| **Caracteres Totales** | {total_chars:,} |",
            f"| **Criterio de Particionado** | {mode_desc} |",
            f"| **Fecha de Generación** | `{now_iso}` |",
            f"",
            f"---",
            f"",
            f"## Guía de Ingesta para Agentes Inteligentes (LLM / RAG / IAG)",
            f"",
            f"1. **Búsqueda Focalizada**: Para responder consultas sobre un tema específico, revisa la tabla de catálogo inferior y consulta únicamente la parte correspondiente.",
            f"2. **Continuidad Contextual**: Cada fragmento `.md` incluye metadatos en formato YAML Frontmatter en la cabecera, junto con enlaces al fragmento previo y posterior.",
            f"3. **Identidad de Documento**: Todas las partes comparten el mismo `document_id: \"{document_id}\"`, lo cual permite correlacionar embeddings vectoriales y filtros de metadatos en bases de datos vectoriales.",
            f"",
            f"---",
            f"",
            f"## Catálogo de Fragmentos del Documento",
            f"",
            f"| Parte | Archivo | Tokens Est. | Proporción | Sección Inicial | Enlace |",
            f"| :---: | :--- | :---: | :---: | :--- | :--- |",
        ]

        for p in parts:
            pct = (p.token_estimate / total_tokens * 100) if total_tokens > 0 else 0.0
            heading_preview = p.first_heading.replace("|", "/") if p.first_heading else f"Parte {p.part_number}"
            if len(heading_preview) > 40:
                heading_preview = heading_preview[:37] + "..."
            lines.append(
                f"| **{p.part_number}** | `{p.filename}` | ~{p.token_estimate:,} | {pct:.1f}% | {heading_preview} | [{p.filename}](./{p.filename}) |"
            )

        lines.extend(
            [
                f"",
                f"---",
                f"",
                f"## Desglose Temático por Fragmento",
                f"",
            ]
        )

        for p in parts:
            lines.append(f"### [{p.filename}](./{p.filename})")
            lines.append(f"- **Ubicación:** Parte {p.part_number} de {len(parts)}")
            lines.append(f"- **Métricas:** ~{p.token_estimate:,} tokens | {p.word_count:,} palabras | {p.char_count:,} caracteres")
            if p.headings_summary:
                lines.append(f"- **Temas y encabezados principales contenidos:**")
                for h in p.headings_summary:
                    clean_h = h.replace("|", "/")
                    lines.append(f"  - {clean_h}")
            else:
                lines.append(f"- *Texto continuo sin encabezados formales detectados.*")
            lines.append("")

        lines.append("---")
        lines.append(f"*Manifiesto generado automáticamente por Thoth Scann — Preservación de contexto digital.*")

        return "\n".join(lines)
