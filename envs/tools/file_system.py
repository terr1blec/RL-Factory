from mcp.server.fastmcp import FastMCP
from envs.tools.func_source_code.gorilla_file_system import *
mcp = FastMCP("FileSystem")

file_system = GorillaFileSystem()

@mcp.tool()
def load_scenario(scenario: dict, long_context: bool = False):
    """Load a scenario into the file system."""
    try:
        file_system._load_scenario(scenario, long_context)
        return "Sucessfully load from scenario."
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def pwd() -> str:
    """Get current working directory"""
    try:
        result = file_system.pwd()
        return f"Current directory: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def ls(show_hidden: bool = False) -> str:
    """List directory contents"""
    try:
        return file_system.ls(show_hidden)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def cd(folder: str) -> str:
    """Change directory"""
    try:
        result = file_system.cd(folder)
        return f"Changed to directory: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def mkdir(dir_name: str) -> str:
    """Create directory"""
    try:
        file_system.mkdir(dir_name)
        return f"Directory '{dir_name}' created"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def touch(file_name: str) -> str:
    """Create file"""
    try:
        file_system.touch(file_name)
        return f"File '{file_name}' created"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def echo(content: str, file_name: str = None) -> str:
    """Write content to file or display"""
    try:
        result = file_system.echo(content, file_name)
        if file_name:
            return f"Content written to '{file_name}'"
        else:
            return result
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def cat(file_name: str) -> str:
    """Read file content"""
    try:
        content = file_system.cat(file_name)
        return f"Content of '{file_name}':\n{content}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def rm(file_name: str) -> str:
    """Remove file or directory"""
    try:
        file_system.rm(file_name)
        return f"'{file_name}' removed"
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("\nStarting MCP File System Management Server...")
    mcp.run(transport='stdio')