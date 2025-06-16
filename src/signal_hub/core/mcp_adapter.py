"""MCP (Model Context Protocol) adapter for Signal Hub."""

import json
import sys
from typing import Any, Dict, Optional

from signal_hub.utils.logging import get_logger


logger = get_logger(__name__)


class MCPMessage:
    """MCP message structure."""
    
    def __init__(self, msg_type: str, content: Dict[str, Any]):
        self.type = msg_type
        self.content = content
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "content": self.content
        }


class MCPAdapter:
    """Adapter for MCP communication over stdio."""
    
    def __init__(self):
        """Initialize MCP adapter."""
        self.tools = {}
        
    def register_tool(self, name: str, handler: callable, description: str = ""):
        """Register a tool handler."""
        self.tools[name] = {
            "handler": handler,
            "description": description
        }
        
    def read_message(self) -> Optional[MCPMessage]:
        """Read a message from stdin."""
        try:
            line = sys.stdin.readline()
            if not line:
                return None
                
            data = json.loads(line.strip())
            return MCPMessage(
                msg_type=data.get("type", "unknown"),
                content=data.get("content", {})
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
            return None
    
    def write_message(self, message: MCPMessage) -> None:
        """Write a message to stdout."""
        json_str = json.dumps(message.to_dict())
        sys.stdout.write(json_str + "\n")
        sys.stdout.flush()
    
    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Handle a tool call."""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        handler = self.tools[tool_name]["handler"]
        return handler(**arguments)
    
    def serve(self) -> None:
        """Main server loop."""
        logger.info("MCP server started on stdio")
        
        # Send initialization message
        self.write_message(MCPMessage("ready", {
            "version": "1.0",
            "tools": list(self.tools.keys())
        }))
        
        # Main loop
        while True:
            message = self.read_message()
            if not message:
                break
            
            if message.type == "tool_call":
                tool_name = message.content.get("tool")
                arguments = message.content.get("arguments", {})
                
                try:
                    result = self.handle_tool_call(tool_name, arguments)
                    self.write_message(MCPMessage("tool_result", {
                        "tool": tool_name,
                        "result": result
                    }))
                except Exception as e:
                    self.write_message(MCPMessage("error", {
                        "tool": tool_name,
                        "error": str(e)
                    }))
            
            elif message.type == "shutdown":
                logger.info("Received shutdown signal")
                break
        
        logger.info("MCP server stopped")