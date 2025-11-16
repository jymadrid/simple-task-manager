"""
Type hints and annotations for common types
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Common type aliases
JSONDict = Dict[str, Any]
TaskData = Dict[str, Union[str, int, float, bool, List, Dict, None]]
UserData = Dict[str, Union[str, int, List[str], None]]
ProjectData = Dict[str, Union[str, int, List[str], None]]

# Database field types
IDType = str
TimestampType = datetime
DescriptionType = Optional[str]
PriorityType = str  # TaskPriority enum value
StatusType = str  # TaskStatus enum value
