from typing import Optional, Dict, List
from mcp.server.fastmcp import FastMCP
from envs.tools.func_source_code.message_api import MessageAPI

mcp = FastMCP("Message")

message_api = MessageAPI()

@mcp.tool()
def load_scenario(scenario: dict, long_context: bool = False):
    """
    Load a scenario into the message system.

    Args:
        scenario (dict): The scenario to load.
        long_context (bool): [Optional] Whether to enable long context. Defaults to False.
    """
    try:
        message_api._load_scenario(scenario, long_context)
        return "Successfully loaded from scenario."
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def list_users():
    """
    List all users in the workspace.

    Returns:
        user_list (List[str]): List of all users in the workspace.
    """
    try:
        result = message_api.list_users()
        users = result.get('user_list', [])
        return f"User list: {', '.join(users)}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_user_id(user: str):
    """
    Get user ID from user name.

    Args:
        user (str): User name of the user.

    Returns:
        user_id (str): User ID of the user.
    """
    try:
        result = message_api.get_user_id(user)
        if "error" in result:
            return f"Error: {result['error']}"
        return f"User {user} ID: {result['user_id']}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def message_login(user_id: str):
    """
    Log in a user with the given user ID to message application.

    Args:
        user_id (str): User ID of the user to log in.

    Returns:
        login_status (bool): True if login was successful, False otherwise.
        message (str): A message describing the result of the login attempt.
    """
    try:
        result = message_api.message_login(user_id)
        if result.get('login_status'):
            return f"Login successful: {result.get('message')}"
        else:
            return f"Login failed: {result.get('message')}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def message_get_login_status():
    """
    Get the login status of the current user.

    Returns:
        login_status (bool): True if the current user is logged in, False otherwise.
    """
    try:
        result = message_api.message_get_login_status()
        status = result.get('login_status', False)
        return f"Login status: {'Logged in' if status else 'Not logged in'}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def send_message(receiver_id: str, message: str):
    """
    Send a message to a user.

    Args:
        receiver_id (str): User ID of the user to send the message to.
        message (str): Message to be sent.

    Returns:
        sent_status (bool): True if the message was sent successfully, False otherwise.
        message_id (int): ID of the sent message.
        message (str): A message describing the result of the send attempt.
    """
    try:
        result = message_api.send_message(receiver_id, message)
        if "error" in result:
            return f"Error: {result['error']}"
        return f"Message sent successfully. Message ID: {result.get('message_id')}, Status: {result.get('message')}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def delete_message(receiver_id: str):
    """
    Delete the latest message sent to a receiver.

    Args:
        receiver_id (str): User ID of the user to send the message to.

    Returns:
        deleted_status (bool): True if the message was deleted successfully, False otherwise.
        message_id (int): ID of the deleted message.
        message (str): A message describing the result of the deletion attempt.
    """
    try:
        result = message_api.delete_message(receiver_id)
        if "error" in result:
            return f"Error: {result['error']}"
        return f"Message deleted successfully. Message ID: {result.get('message_id')}, Status: {result.get('message')}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def view_messages_sent():
    """
    View all historical messages sent by the current user.

    Returns:
        messages (Dict): Dictionary of messages grouped by receiver.
    """
    try:
        result = message_api.view_messages_sent()
        if "error" in result:
            return f"Error: {result['error']}"
        
        messages = result.get('messages', {})
        if not messages:
            return "No messages sent."
        
        formatted_messages = []
        for receiver, msg_list in messages.items():
            formatted_messages.append(f"To {receiver}: {msg_list}")
        
        return "Sent messages:\n" + "\n".join(formatted_messages)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def add_contact(user_name: str):
    """
    Add a contact to the workspace.

    Args:
        user_name (str): User name of contact to be added.

    Returns:
        added_status (bool): True if the contact was added successfully, False otherwise.
        user_id (str): User ID of the added contact.
        message (str): A message describing the result of the addition attempt.
    """
    try:
        result = message_api.add_contact(user_name)
        if "error" in result:
            return f"Error: {result['error']}"
        return f"Contact added successfully. Username: {user_name}, User ID: {result.get('user_id')}, Status: {result.get('message')}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def search_messages(keyword: str):
    """
    Search for messages containing a specific keyword.

    Args:
        keyword (str): The keyword to search for in messages.

    Returns:
        results (List[Dict]): List of dictionaries containing matching messages.
    """
    try:
        result = message_api.search_messages(keyword)
        if "error" in result:
            return f"Error: {result['error']}"
        
        results = result.get('results', [])
        if not results:
            return f"No messages found containing keyword '{keyword}'."
        
        formatted_results = []
        for msg in results:
            formatted_results.append(f"Receiver ID: {msg.get('receiver_id')}, Message: {msg.get('message')}")
        
        return f"Found {len(results)} messages containing keyword '{keyword}':\n" + "\n".join(formatted_results)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_message_stats():
    """
    Get statistics about messages for the current user.

    Returns:
        stats (Dict): Dictionary containing message statistics.
    """
    try:
        result = message_api.get_message_stats()
        if "error" in result:
            return f"Error: {result['error']}"
        
        stats = result.get('stats', {})
        return f"Message statistics:\nReceived messages: {stats.get('received_count', 0)}\nTotal contacts: {stats.get('total_contacts', 0)}"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    print("\nStarting MCP Message Management Server...")
    mcp.run(transport='stdio')