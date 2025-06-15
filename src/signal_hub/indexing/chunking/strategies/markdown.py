"""Markdown-specific chunking strategy."""

import re
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


class MarkdownChunkingStrategy(ChunkingStrategy):
    """Chunks Markdown documents by sections and code blocks."""
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this strategy can handle the file."""
        return file_path.suffix.lower() in {'.md', '.markdown', '.mdx'}
        
    def chunk_file(self, file_path: Path, content: Optional[str] = None) -> List[CodeChunk]:
        """Chunk a Markdown file into logical pieces."""
        if content is None:
            content = file_path.read_text(encoding='utf-8')
            
        metadata = {"file_path": str(file_path), "language": "markdown"}
        return self.chunk_text(content, metadata)
        
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[CodeChunk]:
        """Chunk Markdown text into logical pieces."""
        if not text.strip():
            return []
            
        metadata = metadata or {}
        chunks = []
        
        # Split by headers
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        
        sections = []
        last_end = 0
        
        for match in header_pattern.finditer(text):
            if last_end < match.start():
                # Add content before this header
                sections.append({
                    'start': last_end,
                    'end': match.start(),
                    'level': 0,
                    'title': 'Introduction' if last_end == 0 else 'Content',
                    'header_line': None
                })
                
            # Add the header and its content
            level = len(match.group(1))
            title = match.group(2).strip()
            
            sections.append({
                'start': match.start(),
                'end': None,  # Will be set later
                'level': level,
                'title': title,
                'header_line': text[:match.start()].count('\n') + 1
            })
            
            last_end = match.end()
            
        # Set end positions
        for i in range(len(sections) - 1):
            if sections[i]['end'] is None:
                sections[i]['end'] = sections[i + 1]['start']
                
        if sections and sections[-1]['end'] is None:
            sections[-1]['end'] = len(text)
            
        # Add final content if no sections
        if not sections and text.strip():
            sections.append({
                'start': 0,
                'end': len(text),
                'level': 0,
                'title': 'Content',
                'header_line': 1
            })
            
        # Create chunks from sections
        for section in sections:
            content = text[section['start']:section['end']].strip()
            
            if not content:
                continue
                
            # Calculate line numbers
            start_line = text[:section['start']].count('\n') + 1
            end_line = text[:section['end']].count('\n') + 1
            
            # Check if section is too large
            if len(content) > self.context.max_chunk_size:
                # Split by paragraphs or code blocks
                sub_chunks = self._split_large_section(
                    content, start_line, section['title'], metadata
                )
                chunks.extend(sub_chunks)
            else:
                chunk = CodeChunk(
                    content=content,
                    start_line=start_line,
                    end_line=end_line,
                    chunk_type=ChunkType.DOCUMENTATION,
                    metadata={
                        **metadata,
                        'section_title': section['title'],
                        'section_level': section['level']
                    }
                )
                chunks.append(chunk)
                
        # Apply overlap if configured
        chunks = self.apply_overlap(chunks)
        
        return chunks
        
    def _split_large_section(
        self,
        content: str,
        start_line: int,
        section_title: str,
        metadata: Dict[str, Any]
    ) -> List[CodeChunk]:
        """Split a large section into smaller chunks."""
        chunks = []
        
        # Try to split by code blocks first
        code_block_pattern = re.compile(r'```[\s\S]*?```', re.MULTILINE)
        
        parts = []
        last_end = 0
        
        for match in code_block_pattern.finditer(content):
            # Add text before code block
            if last_end < match.start():
                parts.append({
                    'content': content[last_end:match.start()],
                    'is_code': False
                })
                
            # Add code block
            parts.append({
                'content': match.group(),
                'is_code': True
            })
            
            last_end = match.end()
            
        # Add remaining text
        if last_end < len(content):
            parts.append({
                'content': content[last_end:],
                'is_code': False
            })
            
        # Create chunks from parts
        current_pos = 0
        
        for part in parts:
            part_content = part['content'].strip()
            if not part_content:
                current_pos += len(part['content'])
                continue
                
            # Calculate line offset
            line_offset = content[:current_pos].count('\n')
            part_start_line = start_line + line_offset
            part_end_line = part_start_line + part_content.count('\n')
            
            if len(part_content) > self.context.max_chunk_size and not part['is_code']:
                # Further split by paragraphs
                paragraphs = self._split_by_paragraphs(
                    part_content,
                    part_start_line,
                    section_title,
                    metadata
                )
                chunks.extend(paragraphs)
            else:
                chunk = CodeChunk(
                    content=part_content,
                    start_line=part_start_line,
                    end_line=part_end_line,
                    chunk_type=ChunkType.DOCUMENTATION,
                    metadata={
                        **metadata,
                        'section_title': section_title,
                        'is_code_block': part['is_code']
                    }
                )
                chunks.append(chunk)
                
            current_pos += len(part['content'])
            
        return chunks
        
    def _split_by_paragraphs(
        self,
        content: str,
        start_line: int,
        section_title: str,
        metadata: Dict[str, Any]
    ) -> List[CodeChunk]:
        """Split content by paragraphs."""
        chunks = []
        
        # Split by double newlines
        paragraphs = re.split(r'\n\s*\n', content)
        
        current_line = start_line
        accumulated = []
        accumulated_size = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            para_size = len(para)
            para_lines = para.count('\n') + 1
            
            # Check if adding this paragraph exceeds limit
            if accumulated and accumulated_size + para_size > self.context.max_chunk_size:
                # Create chunk from accumulated paragraphs
                chunk_content = '\n\n'.join(accumulated)
                chunk = CodeChunk(
                    content=chunk_content,
                    start_line=current_line,
                    end_line=current_line + chunk_content.count('\n'),
                    chunk_type=ChunkType.DOCUMENTATION,
                    metadata={
                        **metadata,
                        'section_title': section_title,
                        'paragraph_chunk': True
                    }
                )
                chunks.append(chunk)
                
                # Reset accumulation
                accumulated = [para]
                accumulated_size = para_size
                current_line += chunk_content.count('\n') + 2  # Account for paragraph break
            else:
                accumulated.append(para)
                accumulated_size += para_size
                
        # Add final chunk
        if accumulated:
            chunk_content = '\n\n'.join(accumulated)
            chunk = CodeChunk(
                content=chunk_content,
                start_line=current_line,
                end_line=current_line + chunk_content.count('\n'),
                chunk_type=ChunkType.DOCUMENTATION,
                metadata={
                    **metadata,
                    'section_title': section_title,
                    'paragraph_chunk': True
                }
            )
            chunks.append(chunk)
            
        return chunks