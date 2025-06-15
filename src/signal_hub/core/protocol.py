"""MCP protocol handling for Signal Hub."""

import json
from typing import Dict, Any, Optional, List, Callable, Awaitable
from enum import Enum
import asyncio
from datetime import datetime

from signal_hub.utils.logging import get_logger, log_performance

logger = get_logger(__name__)


class MessageType(str, Enum):
    """MCP message types."""
    # Initialization
    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    
    # Tool discovery
    LIST_TOOLS = "tools/list"
    
    # Tool execution
    CALL_TOOL = "tools/call"
    
    # Notifications
    NOTIFICATION = "notification"
    PROGRESS = "progress"
    
    # Errors
    ERROR = "error"
    
    # Control
    PING = "ping"
    PONG = "pong"
    CANCEL = "cancel"
    SHUTDOWN = "shutdown"


class ErrorCode(str, Enum):
    """MCP error codes."""
    PARSE_ERROR = "ParseError"
    INVALID_REQUEST = "InvalidRequest"
    METHOD_NOT_FOUND = "MethodNotFound"
    INVALID_PARAMS = "InvalidParams"
    INTERNAL_ERROR = "InternalError"
    SERVER_ERROR = "ServerError"
    TOOL_NOT_FOUND = "ToolNotFound"
    TOOL_ERROR = "ToolError"


class ProtocolError(Exception):
    """MCP protocol error."""
    
    def __init__(self, code: ErrorCode, message: str, data: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


class ProtocolHandler:
    """Handles MCP protocol messages."""
    
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._request_id_counter = 0
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default protocol handlers."""
        self.register_handler(MessageType.PING, self._handle_ping)
    
    async def _handle_ping(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping message."""
        return self.create_response(
            message.get("id"),
            MessageType.PONG,
            {"timestamp": datetime.utcnow().isoformat()}
        )
    
    def register_handler(
        self,
        message_type: MessageType,
        handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
    ):
        """
        Register a handler for a message type.
        
        Args:
            message_type: The message type to handle
            handler: Async function to handle the message
        """
        self._handlers[message_type.value] = handler
        logger.debug(f"Registered handler for {message_type.value}")
    
    @log_performance(logger, "process_message")
    async def process_message(self, raw_message: str) -> Optional[str]:
        """
        Process an incoming MCP message.
        
        Args:
            raw_message: Raw JSON message string
            
        Returns:
            Response message as JSON string, or None for notifications
            
        Raises:
            ProtocolError: If message processing fails
        """
        try:
            # Parse message
            message = json.loads(raw_message)
            logger.debug(f"Processing message: {message.get('method', 'unknown')}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
            return json.dumps(self.create_error(
                None,
                ErrorCode.PARSE_ERROR,
                f"Invalid JSON: {str(e)}"
            ))
        
        # Validate message structure
        if "jsonrpc" not in message or message["jsonrpc"] != "2.0":
            return json.dumps(self.create_error(
                message.get("id"),
                ErrorCode.INVALID_REQUEST,
                "Invalid JSON-RPC version"
            ))
        
        # Handle different message types
        if "method" in message:
            # Request or notification
            return await self._handle_request(message)
        elif "result" in message or "error" in message:
            # Response to our request
            await self._handle_response(message)
            return None
        else:
            return json.dumps(self.create_error(
                message.get("id"),
                ErrorCode.INVALID_REQUEST,
                "Message must have method, result, or error"
            ))
    
    async def _handle_request(self, message: Dict[str, Any]) -> Optional[str]:
        """Handle incoming request or notification."""
        method = message["method"]
        params = message.get("params", {})
        message_id = message.get("id")
        
        # Find handler
        handler = self._handlers.get(method)
        if not handler:
            if message_id is not None:
                # Request without handler
                return json.dumps(self.create_error(
                    message_id,
                    ErrorCode.METHOD_NOT_FOUND,
                    f"Unknown method: {method}"
                ))
            else:
                # Notification without handler - log and ignore
                logger.warning(f"Unhandled notification: {method}")
                return None
        
        # Execute handler
        try:
            result = await handler(message)
            
            # Return response only for requests (not notifications)
            if message_id is not None and result is not None:
                return json.dumps(result)
            return None
            
        except ProtocolError as e:
            if message_id is not None:
                return json.dumps(self.create_error(
                    message_id,
                    e.code,
                    e.message,
                    e.data
                ))
            else:
                logger.error(f"Error in notification handler: {e}")
                return None
        except Exception as e:
            logger.exception(f"Unhandled error in {method} handler")
            if message_id is not None:
                return json.dumps(self.create_error(
                    message_id,
                    ErrorCode.INTERNAL_ERROR,
                    f"Internal error: {str(e)}"
                ))
            return None
    
    async def _handle_response(self, message: Dict[str, Any]) -> None:
        """Handle response to our request."""
        message_id = message.get("id")
        if not message_id or message_id not in self._pending_requests:
            logger.warning(f"Unexpected response: {message_id}")
            return
        
        future = self._pending_requests.pop(message_id)
        
        if "error" in message:
            future.set_exception(ProtocolError(
                ErrorCode(message["error"].get("code", "ServerError")),
                message["error"].get("message", "Unknown error"),
                message["error"].get("data")
            ))
        else:
            future.set_result(message.get("result"))
    
    def create_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a JSON-RPC request.
        
        Args:
            method: Method name
            params: Optional parameters
            
        Returns:
            Request dictionary
        """
        self._request_id_counter += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": str(self._request_id_counter)
        }
        
        if params is not None:
            request["params"] = params
        
        return request
    
    def create_notification(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a JSON-RPC notification (no response expected).
        
        Args:
            method: Method name
            params: Optional parameters
            
        Returns:
            Notification dictionary
        """
        notification = {
            "jsonrpc": "2.0",
            "method": method
        }
        
        if params is not None:
            notification["params"] = params
        
        return notification
    
    def create_response(self, request_id: Any, result: Any, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a JSON-RPC response.
        
        Args:
            request_id: The request ID to respond to
            result: The result data
            extra: Optional extra fields
            
        Returns:
            Response dictionary
        """
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        
        if extra:
            response.update(extra)
        
        return response
    
    def create_error(
        self,
        request_id: Any,
        code: ErrorCode,
        message: str,
        data: Any = None
    ) -> Dict[str, Any]:
        """
        Create a JSON-RPC error response.
        
        Args:
            request_id: The request ID (can be None)
            code: Error code
            message: Error message
            data: Optional error data
            
        Returns:
            Error response dictionary
        """
        error_obj = {
            "code": code.value,
            "message": message
        }
        
        if data is not None:
            error_obj["data"] = data
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error_obj
        }
    
    async def send_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> Any:
        """
        Send a request and wait for response.
        
        Args:
            method: Method name
            params: Optional parameters
            timeout: Request timeout in seconds
            
        Returns:
            Response result
            
        Raises:
            asyncio.TimeoutError: If request times out
            ProtocolError: If request fails
        """
        request = self.create_request(method, params)
        request_id = request["id"]
        
        # Create future for response
        future = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future
        
        try:
            # Send request (implementation will depend on transport)
            # This is a placeholder - actual sending is done by the server
            await self._send_message(json.dumps(request))
            
            # Wait for response
            result = await asyncio.wait_for(future, timeout)
            return result
            
        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            raise
        except Exception:
            self._pending_requests.pop(request_id, None)
            raise
    
    async def _send_message(self, message: str) -> None:
        """
        Send a message over the transport.
        
        This is a placeholder - actual implementation depends on transport.
        
        Args:
            message: Message to send
        """
        # This will be implemented by the server
        raise NotImplementedError("_send_message must be implemented by server")