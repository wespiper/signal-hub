"""Fallback chunking strategy for unsupported file types."""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from signal_hub.indexing.chunking.strategy import (
    ChunkingStrategy,
    CodeChunk,
    ChunkType,
    ChunkingContext
)

logger = logging.getLogger(__name__)


class FallbackChunkingStrategy(ChunkingStrategy):
    """Simple line-based chunking for unsupported file types."""
    
    def can_handle(self, file_path: Path) -> bool:
        """This strategy can handle any file."""
        return True
        
    def chunk_file(self, file_path: Path, content: Optional[str] = None) -> List[CodeChunk]:
        """Chunk a file using simple line-based splitting."""
        if content is None:
            try:
                content = file_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                # Try with different encoding
                try:
                    content = file_path.read_text(encoding='latin-1')
                except Exception as e:
                    logger.error(f"Failed to read file {file_path}: {e}")
                    return []
                    
        metadata = {
            "file_path": str(file_path),
            "language": self._detect_language(file_path)
        }
        
        return self.chunk_text(content, metadata)
        
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[CodeChunk]:
        """Chunk text using simple line-based splitting."""
        if not text.strip():
            return []
            
        metadata = metadata or {}
        chunks = []
        lines = text.split('\n')
        
        # If the file is small enough, return as single chunk
        if len(text) <= self.context.max_chunk_size:
            chunk = CodeChunk(
                content=text,
                start_line=1,
                end_line=len(lines),
                chunk_type=ChunkType.BLOCK,
                metadata=metadata
            )
            return [chunk]
            
        # Otherwise, split by size
        current_chunk_lines = []
        current_chunk_size = 0
        current_start_line = 1
        
        for i, line in enumerate(lines, 1):
            line_size = len(line) + 1  # +1 for newline
            
            # Check if adding this line would exceed the limit
            if (current_chunk_size + line_size > self.context.max_chunk_size and
                current_chunk_lines):  # Ensure we have at least one line
                
                # Create chunk
                chunk_content = '\n'.join(current_chunk_lines)
                chunk = CodeChunk(
                    content=chunk_content,
                    start_line=current_start_line,
                    end_line=i - 1,
                    chunk_type=ChunkType.BLOCK,
                    metadata=metadata
                )
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk_lines = [line]
                current_chunk_size = line_size
                current_start_line = i
            else:
                current_chunk_lines.append(line)
                current_chunk_size += line_size
                
        # Add final chunk
        if current_chunk_lines:
            chunk_content = '\n'.join(current_chunk_lines)
            chunk = CodeChunk(
                content=chunk_content,
                start_line=current_start_line,
                end_line=len(lines),
                chunk_type=ChunkType.BLOCK,
                metadata=metadata
            )
            chunks.append(chunk)
            
        # Apply overlap if configured
        chunks = self.apply_overlap(chunks)
        
        return chunks
        
    def _detect_language(self, file_path: Path) -> str:
        """Try to detect the language from file extension."""
        extension_map = {
            '.txt': 'text',
            '.log': 'log',
            '.cfg': 'config',
            '.conf': 'config',
            '.ini': 'ini',
            '.toml': 'toml',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.less': 'less',
            '.sh': 'shell',
            '.bash': 'bash',
            '.zsh': 'zsh',
            '.fish': 'fish',
            '.ps1': 'powershell',
            '.bat': 'batch',
            '.cmd': 'batch',
            '.sql': 'sql',
            '.r': 'r',
            '.R': 'r',
            '.m': 'matlab',
            '.jl': 'julia',
            '.lua': 'lua',
            '.pl': 'perl',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.clj': 'clojure',
            '.ex': 'elixir',
            '.exs': 'elixir',
            '.erl': 'erlang',
            '.hrl': 'erlang',
            '.php': 'php',
            '.java': 'java',
            '.c': 'c',
            '.h': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.fs': 'fsharp',
            '.vb': 'vbnet',
            '.pas': 'pascal',
            '.d': 'd',
            '.nim': 'nim',
            '.zig': 'zig',
            '.v': 'v',
            '.dart': 'dart',
            '.groovy': 'groovy',
            '.gradle': 'gradle',
        }
        
        suffix = file_path.suffix.lower()
        return extension_map.get(suffix, 'unknown')