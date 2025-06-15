"""Unit tests for JavaScript/TypeScript parser."""

import pytest
from pathlib import Path

from signal_hub.indexing.parsers.javascript import JavaScriptParser
from signal_hub.indexing.parsers.models import ChunkType


class TestJavaScriptParser:
    """Test JavaScriptParser class."""
    
    @pytest.fixture
    def parser(self):
        """Create JavaScript parser."""
        return JavaScriptParser()
    
    def test_parse_simple_function(self, parser):
        """Test parsing a simple function."""
        code = """
function greet(name) {
    console.log(`Hello, ${name}!`);
}
"""
        chunks = parser.parse(code.strip())
        
        assert len(chunks) == 1
        assert chunks[0].type == ChunkType.FUNCTION
        assert chunks[0].name == "greet"
        assert "console.log" in chunks[0].content
    
    def test_parse_arrow_functions(self, parser):
        """Test parsing arrow functions."""
        code = """
const add = (a, b) => a + b;

const multiply = (x, y) => {
    return x * y;
};

export const divide = async (a, b) => {
    if (b === 0) throw new Error("Division by zero");
    return a / b;
};
"""
        chunks = parser.parse(code.strip())
        
        functions = [c for c in chunks if c.type == ChunkType.FUNCTION]
        assert len(functions) == 3
        
        # Check names
        names = {f.name for f in functions}
        assert names == {"add", "multiply", "divide"}
        
        # Check metadata
        divide = next(f for f in functions if f.name == "divide")
        assert divide.metadata["exported"] is True
        assert divide.metadata["async"] is True
        assert divide.metadata["arrow"] is True
    
    def test_parse_class(self, parser):
        """Test parsing ES6 classes."""
        code = """
export class Calculator {
    constructor() {
        this.result = 0;
    }
    
    add(value) {
        this.result += value;
        return this;
    }
    
    async calculate() {
        return this.result;
    }
}
"""
        chunks = parser.parse(code.strip())
        
        # Should have class chunk
        class_chunks = [c for c in chunks if c.type == ChunkType.CLASS]
        assert len(class_chunks) == 1
        
        calc = class_chunks[0]
        assert calc.name == "Calculator"
        assert calc.metadata["exported"] is True
        assert "constructor" in calc.metadata["methods"]
        assert "add" in calc.metadata["methods"]
        assert "calculate" in calc.metadata["methods"]
    
    def test_parse_imports_exports(self, parser):
        """Test parsing import/export statements."""
        code = """
import React from 'react';
import { useState, useEffect } from 'react';
import {
    Button,
    TextField,
    Dialog
} from '@mui/material';

export { Calculator } from './Calculator';
export default App;
"""
        chunks = parser.parse(code.strip())
        
        imports = [c for c in chunks if c.type == ChunkType.IMPORT]
        assert len(imports) >= 3
        
        # Check multi-line import
        mui_import = next(c for c in imports if '@mui/material' in c.content)
        assert "Button" in mui_import.content
        assert "Dialog" in mui_import.content
    
    def test_parse_async_functions(self, parser):
        """Test parsing async functions."""
        code = """
async function fetchData(url) {
    const response = await fetch(url);
    return response.json();
}

export async function processData(data) {
    return await transform(data);
}
"""
        chunks = parser.parse(code.strip())
        
        functions = [c for c in chunks if c.type == ChunkType.FUNCTION]
        assert len(functions) == 2
        
        # Check async metadata
        fetch_func = next(f for f in functions if f.name == "fetchData")
        assert fetch_func.metadata["async"] is True
        
        process_func = next(f for f in functions if f.name == "processData")
        assert process_func.metadata["async"] is True
        assert process_func.metadata["exported"] is True
    
    def test_parse_typescript_features(self, parser):
        """Test parsing TypeScript-specific features."""
        code = """
interface User {
    id: number;
    name: string;
}

export class UserService {
    private users: User[] = [];
    
    public addUser(user: User): void {
        this.users.push(user);
    }
    
    async getUser(id: number): Promise<User | undefined> {
        return this.users.find(u => u.id === id);
    }
}
"""
        chunks = parser.parse(code.strip())
        
        # Should parse class even with TS syntax
        class_chunks = [c for c in chunks if c.type == ChunkType.CLASS]
        assert len(class_chunks) == 1
        
        service = class_chunks[0]
        assert service.name == "UserService"
        assert "addUser" in service.metadata["methods"]
        assert "getUser" in service.metadata["methods"]
    
    def test_parse_class_inheritance(self, parser):
        """Test parsing class with extends and implements."""
        code = """
abstract class BaseComponent {
    abstract render(): void;
}

export class MyComponent extends BaseComponent implements Lifecycle {
    render() {
        console.log("Rendering");
    }
    
    onMount() {
        console.log("Mounted");
    }
}
"""
        chunks = parser.parse(code.strip())
        
        classes = [c for c in chunks if c.type == ChunkType.CLASS]
        assert len(classes) == 2
        
        # Check inheritance metadata
        my_component = next(c for c in classes if c.name == "MyComponent")
        assert my_component.metadata["extends"] == "extends BaseComponent"
        assert my_component.metadata["exported"] is True
        
        base_component = next(c for c in classes if c.name == "BaseComponent")
        assert base_component.metadata["abstract"] is True
    
    def test_parse_nested_blocks(self, parser):
        """Test parsing with nested blocks."""
        code = """
function complexFunction() {
    if (condition) {
        const nested = () => {
            return { key: "value" };
        };
    }
    
    return result;
}
"""
        chunks = parser.parse(code.strip())
        
        # Should find the outer function
        functions = [c for c in chunks if c.type == ChunkType.FUNCTION]
        assert any(f.name == "complexFunction" for f in functions)
    
    def test_parse_file_extensions(self, parser):
        """Test supported file extensions."""
        assert parser.can_parse("test.js")
        assert parser.can_parse("test.jsx")
        assert parser.can_parse("test.ts")
        assert parser.can_parse("test.tsx")
        assert parser.can_parse("test.mjs")
        assert parser.can_parse("test.cjs")
        assert not parser.can_parse("test.py")