from collections import defaultdict


class Memory:
    """
    The Memory class manages the state and history of the agent's execution.
    It forms the second step in the Perception -> Memory -> Decision -> Action framework.

    The Memory class:
    1. Stores user preferences and session-specific information
    2. Maintains a history of tool executions and their results
    3. Provides methods to store and recall information
    4. Supports the decision-making process with historical context

    Attributes:
        preferences (list): List of user preferences
        session (defaultdict): Dictionary of session-specific information
    """

    def __init__(self) -> None:
        """
        Initialize the Memory class with empty preferences and session storage.
        """
        self.preferences = []
        self.session = defaultdict(lambda: [])

    def store(self, info: str, session_id: str):
        """
        Store information in a specific session.

        Args:
            info: Information to be stored
            session_id: Unique identifier for the session

        Raises:
            Exception: If the session_id does not exist
        """
        if not session_id in self.session:
            raise Exception("Requested to store an info in a non existing session")
        self.session[session_id].append(info)

    def recall(self, session_id: str, include_preferences: bool = True) -> str:
        """
        Recall information from a specific session.

        Args:
            session_id: Unique identifier for the session
            include_preferences (bool): Whether to include user preferences

        Returns:
            str: Formatted string containing session history and preferences
        """
        all_info = self.session[session_id]
        all_info = "\n\n".join(all_info)
        if include_preferences:
            prefs = "\n".join(self.preferences)
            all_info = f"User Preferences:\n{prefs}\nInteraction History:\n{all_info}\n"
        return all_info
