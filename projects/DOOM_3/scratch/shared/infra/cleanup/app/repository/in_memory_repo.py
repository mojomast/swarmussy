from typing import List, Dict, Optional, Any
import uuid

class Task:
    """Task model used by the in-memory repository tests.

    Provides minimal fields: id (optional), title, description, status, timestamps.
    """

    def __init__(self, title: str, description: str | None = None, **kwargs):
        self.id = kwargs.get('id')
        self.title = title
        self.description = description
        # Simple status field