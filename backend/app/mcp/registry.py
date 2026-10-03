from typing import Callable, Dict, Any, List, Optional
from dataclasses import dataclass, field
from app.utils.logger import logger


@dataclass
class MCPToolDefinition:
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Any]
    requires_auth: bool = True

    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert to standard Model Context Protocol (MCP) tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


class MCPRegistry:
    def __init__(self):
        self._tools: Dict[str, MCPToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any] = None,
        requires_auth: bool = True,
    ):
        def decorator(handler: Callable[[Dict[str, Any]], Any]):
            tool_def = MCPToolDefinition(
                name=name,
                description=description,
                input_schema=input_schema,
                output_schema=output_schema or {},
                handler=handler,
                requires_auth=requires_auth,
            )
            self._tools[name] = tool_def
            return handler
        return decorator

    def get_tool(self, name: str) -> Optional[MCPToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[MCPToolDefinition]:
        return list(self._tools.values())

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"MCP tool '{tool_name}' is not registered.")
        return tool.handler(arguments)


mcp_registry = MCPRegistry()
