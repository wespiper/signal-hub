"""Markdown file parser for documentation."""

import re
from pathlib import Path
from typing import List, Optional, Tuple
import logging

from signal_hub.indexing.parsers.base import Parser, ParseError
from signal_hub.indexing.parsers.models import Chunk, ChunkType


logger = logging.getLogger(__name__)


class MarkdownParser(Parser):
    """Parser for Markdown documentation files."""
    
    languages = ["markdown"]
    extensions = [".md", ".markdown", ".mdx"]
    
    # Regex patterns
    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    CODE_BLOCK_PATTERN = re.compile(r'^```(\w*)\n(.*?)\n```', re.MULTILINE | re.DOTALL)
    
    def parse(self, content: str, file_path: Optional[Path] = None) -> List[Chunk]:
        """Parse Markdown content into chunks.
        
        Args:
            content: Markdown content
            file_path: Optional file path for context
            
        Returns:
            List of documentation chunks
        """
        chunks = []
        lines = content.split('\n')
        
        # Extract code blocks first (to avoid parsing them as sections)
        code_blocks = self._extract_code_blocks(content, lines, file_path)
        chunks.extend(code_blocks)
        
        # Mark code block regions to skip
        code_block_lines = set()
        for block in code_blocks:
            for line_num in range(block.start_line, block.end_line + 1):
                code_block_lines.add(line_num)
        
        # Extract sections based on headings
        sections = self._extract_sections(content, lines, file_path, code_block_lines)
        chunks.extend(sections)
        
        # Split large chunks
        final_chunks = []
        for chunk in chunks:
            final_chunks.extend(self.split_large_chunk(chunk))
        
        return final_chunks
    
    def _extract_code_blocks(
        self,
        content: str,
        lines: List[str],
        file_path: Optional[Path]
    ) -> List[Chunk]:
        """Extract code blocks from markdown."""
        chunks = []
        
        for match in self.CODE_BLOCK_PATTERN.finditer(content):
            language = match.group(1) or "unknown"
            code_content = match.group(2)
            
            start_pos = match.start()
            start_line = content[:start_pos].count('\n') + 1
            end_line = start_line + code_content.count('\n') + 2  # +2 for ``` lines
            
            chunks.append(Chunk(
                type=ChunkType.CODE_BLOCK,
                name=f"code_block_{language}_{start_line}",
                content=code_content,
                start_line=start_line,
                end_line=end_line,
                file_path=file_path,
                language="markdown",
                metadata={
                    "code_language": language
                }
            ))
        
        return chunks
    
    def _extract_sections(
        self,
        content: str,
        lines: List[str],
        file_path: Optional[Path],
        skip_lines: set
    ) -> List[Chunk]:
        """Extract sections based on headings."""
        chunks = []
        headings = []
        
        # Find all headings
        for i, line in enumerate(lines):
            if i + 1 in skip_lines:
                continue
                
            heading_match = self.HEADING_PATTERN.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                headings.append((i + 1, level, title))
        
        # Extract sections between headings
        for i, (line_num, level, title) in enumerate(headings):
            start_line = line_num
            
            # Find the end of this section (next heading at same or higher level)
            end_line = len(lines)
            for j in range(i + 1, len(headings)):
                next_line, next_level, _ = headings[j]
                if next_level <= level:
                    end_line = next_line - 1
                    break
            
            # Extract section content
            section_lines = []
            for line_idx in range(start_line - 1, min(end_line, len(lines))):
                if line_idx + 1 not in skip_lines:
                    section_lines.append(lines[line_idx])
            
            if section_lines:
                content = '\n'.join(section_lines)
                
                # Determine chunk type based on level
                chunk_type = ChunkType.HEADING if level == 1 else ChunkType.SECTION
                
                chunks.append(Chunk(
                    type=chunk_type,
                    name=title,
                    content=self.clean_content(content),
                    start_line=start_line,
                    end_line=end_line,
                    file_path=file_path,
                    language="markdown",
                    metadata={
                        "heading_level": level
                    }
                ))
        
        # If no headings, treat entire document as one chunk
        if not headings and lines:
            non_code_lines = []
            for i, line in enumerate(lines):
                if i + 1 not in skip_lines:
                    non_code_lines.append(line)
            
            if non_code_lines:
                chunks.append(Chunk(
                    type=ChunkType.SECTION,
                    name="main_content",
                    content=self.clean_content('\n'.join(non_code_lines)),
                    start_line=1,
                    end_line=len(lines),
                    file_path=file_path,
                    language="markdown"
                ))
        
        return chunks