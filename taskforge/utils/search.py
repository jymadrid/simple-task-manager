"""
Advanced search engine for TaskForge
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Lazy imports for better startup performance
def _get_core_models():
    """Lazy import core models"""
    from taskforge.core.project import Project
    from taskforge.core.task import Task, TaskPriority, TaskStatus, TaskType
    from taskforge.core.user import User
    return Project, Task, TaskPriority, TaskStatus, TaskType, User

def _get_re_module():
    """Lazy import regex module"""
    import re
    return re

def _get_statistics_module():
    """Lazy import statistics module"""
    import statistics
    return statistics

logger = logging.getLogger(__name__)


class SearchOperator(str, Enum):
    """Search operators for advanced queries"""

    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class FieldType(str, Enum):
    """Types of searchable fields"""

    TEXT = "text"
    DATE = "date"
    ENUM = "enum"
    NUMERIC = "numeric"
    BOOLEAN = "boolean"
    LIST = "list"


@dataclass
class SearchField:
    """Definition of a searchable field"""

    name: str
    field_type: FieldType
    searchable: bool = True
    filterable: bool = True
    sortable: bool = True
    weight: float = 1.0  # For relevance scoring


@dataclass
class SearchFilter:
    """Individual search filter"""

    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, contains, startswith, endswith
    value: Any
    case_sensitive: bool = False


@dataclass
class SearchSort:
    """Sort specification"""

    field: str
    ascending: bool = True


@dataclass
class SearchQuery:
    """Comprehensive search query"""

    text: Optional[str] = None
    filters: List[SearchFilter] = None
    sorts: List[SearchSort] = None
    limit: int = 50
    offset: int = 0
    include_archived: bool = False
    highlight: bool = False

    def __post_init__(self):
        if self.filters is None:
            self.filters = []
        if self.sorts is None:
            self.sorts = []


@dataclass
class SearchResult:
    """Search result with relevance scoring"""

    item: Union[Task, Project, User]
    score: float
    highlights: Dict[str, List[str]] = None

    def __post_init__(self):
        if self.highlights is None:
            self.highlights = {}


@dataclass
class SearchResults:
    """Collection of search results with metadata"""

    items: List[SearchResult]
    total_count: int
    query_time_ms: float
    facets: Dict[str, Dict[str, int]] = None

    def __post_init__(self):
        if self.facets is None:
            self.facets = {}


class SearchIndex:
    """In-memory search index for fast text searches"""

    def __init__(self):
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.inverted_index: Dict[str, Set[str]] = defaultdict(set)
        self.field_values: Dict[str, Dict[str, Set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )

    def add_document(self, doc_id: str, document: Dict[str, Any]):
        """Add a document to the search index"""
        self.documents[doc_id] = document

        # Index text fields
        for field, value in document.items():
            if isinstance(value, str):
                tokens = self._tokenize(value)
                for token in tokens:
                    self.inverted_index[token].add(doc_id)
                    self.field_values[field][token].add(doc_id)
            elif isinstance(value, (list, set)):
                for item in value:
                    if isinstance(item, str):
                        tokens = self._tokenize(item)
                        for token in tokens:
                            self.inverted_index[token].add(doc_id)
                            self.field_values[field][token].add(doc_id)

    def remove_document(self, doc_id: str):
        """Remove a document from the search index"""
        if doc_id not in self.documents:
            return

        # Remove from inverted index
        for token_set in self.inverted_index.values():
            token_set.discard(doc_id)

        # Remove from field values
        for field_dict in self.field_values.values():
            for token_set in field_dict.values():
                token_set.discard(doc_id)

        # Remove document
        del self.documents[doc_id]

    def search(self, query: str, limit: int = 50) -> Dict[str, float]:
        """Search for documents and return relevance scores"""
        if not query:
            return {}

        tokens = self._tokenize(query)
        if not tokens:
            return {}

        # Get candidate documents
        candidate_docs = set()
        for token in tokens:
            candidate_docs.update(self.inverted_index.get(token, set()))

        # Calculate relevance scores
        scores = {}
        for doc_id in candidate_docs:
            score = self._calculate_relevance(doc_id, tokens)
            if score > 0:
                scores[doc_id] = score

        # Sort by relevance and limit results
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_scores[:limit])

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for indexing"""
        # Simple tokenization - can be enhanced with stemming, etc.
        tokens = re.findall(r"\w+", text.lower())
        return [token for token in tokens if len(token) > 2]  # Filter short tokens

    def _calculate_relevance(self, doc_id: str, query_tokens: List[str]) -> float:
        """Calculate relevance score for a document"""
        document = self.documents.get(doc_id, {})
        score = 0.0

        # Term frequency scoring
        for token in query_tokens:
            # Check title (higher weight)
            title = document.get("title", "").lower()
            score += title.count(token) * 3.0

            # Check description
            description = document.get("description", "").lower()
            score += description.count(token) * 1.5

            # Check tags
            tags = document.get("tags", [])
            for tag in tags:
                if token in tag.lower():
                    score += 2.0

            # Check other text fields
            for field, value in document.items():
                if field in ["title", "description", "tags"]:
                    continue
                if isinstance(value, str) and token in value.lower():
                    score += 1.0

        return score


class SearchEngine:
    """Advanced search engine for TaskForge"""

    def __init__(self, storage_backend=None):
        self.storage = storage_backend
        self.index = SearchIndex()

        # Define searchable fields for different entity types
        self.task_fields = {
            "id": SearchField("id", FieldType.TEXT, sortable=False),
            "title": SearchField("title", FieldType.TEXT, weight=3.0),
            "description": SearchField("description", FieldType.TEXT, weight=1.5),
            "status": SearchField("status", FieldType.ENUM),
            "priority": SearchField("priority", FieldType.ENUM),
            "task_type": SearchField("task_type", FieldType.ENUM),
            "created_at": SearchField("created_at", FieldType.DATE),
            "updated_at": SearchField("updated_at", FieldType.DATE),
            "due_date": SearchField("due_date", FieldType.DATE),
            "progress": SearchField("progress", FieldType.NUMERIC),
            "tags": SearchField("tags", FieldType.LIST, weight=2.0),
            "assigned_to": SearchField("assigned_to", FieldType.TEXT),
            "created_by": SearchField("created_by", FieldType.TEXT),
            "project_id": SearchField("project_id", FieldType.TEXT),
        }

        self.project_fields = {
            "id": SearchField("id", FieldType.TEXT, sortable=False),
            "name": SearchField("name", FieldType.TEXT, weight=3.0),
            "description": SearchField("description", FieldType.TEXT, weight=1.5),
            "status": SearchField("status", FieldType.ENUM),
            "created_at": SearchField("created_at", FieldType.DATE),
            "start_date": SearchField("start_date", FieldType.DATE),
            "end_date": SearchField("end_date", FieldType.DATE),
            "owner_id": SearchField("owner_id", FieldType.TEXT),
        }

        self.user_fields = {
            "id": SearchField("id", FieldType.TEXT, sortable=False),
            "username": SearchField("username", FieldType.TEXT, weight=3.0),
            "email": SearchField("email", FieldType.TEXT, weight=2.0),
            "full_name": SearchField("full_name", FieldType.TEXT, weight=2.5),
            "role": SearchField("role", FieldType.ENUM),
            "created_at": SearchField("created_at", FieldType.DATE),
            "is_active": SearchField("is_active", FieldType.BOOLEAN),
        }

    async def index_task(self, task: Task):
        """Add or update a task in the search index"""
        doc = {
            "id": task.id,
            "title": task.title,
            "description": task.description or "",
            "status": task.status.value,
            "priority": task.priority.value,
            "task_type": task.task_type.value,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat() if task.updated_at else "",
            "due_date": task.due_date.isoformat() if task.due_date else "",
            "progress": task.progress,
            "tags": list(task.tags),
            "assigned_to": task.assigned_to or "",
            "created_by": task.created_by or "",
            "project_id": task.project_id or "",
            "_type": "task",
        }

        self.index.add_document(f"task_{task.id}", doc)
        logger.debug(f"Indexed task: {task.title}")

    async def index_project(self, project: Project):
        """Add or update a project in the search index"""
        doc = {
            "id": project.id,
            "name": project.name,
            "description": project.description or "",
            "status": project.status.value,
            "created_at": project.created_at.isoformat(),
            "start_date": project.start_date.isoformat() if project.start_date else "",
            "end_date": project.end_date.isoformat() if project.end_date else "",
            "owner_id": project.owner_id,
            "_type": "project",
        }

        self.index.add_document(f"project_{project.id}", doc)
        logger.debug(f"Indexed project: {project.name}")

    async def index_user(self, user: User):
        """Add or update a user in the search index"""
        doc = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name or "",
            "role": user.role.value,
            "created_at": user.created_at.isoformat(),
            "is_active": user.is_active,
            "_type": "user",
        }

        self.index.add_document(f"user_{user.id}", doc)
        logger.debug(f"Indexed user: {user.username}")

    async def remove_from_index(self, entity_type: str, entity_id: str):
        """Remove an entity from the search index"""
        self.index.remove_document(f"{entity_type}_{entity_id}")

    async def search_tasks(self, query: SearchQuery, user_id: str) -> SearchResults:
        """Search for tasks"""
        start_time = datetime.now(timezone.utc)

        # Get base results from storage if no text query
        if not query.text:
            if self.storage:
                # Use storage backend for filtered queries
                from taskforge.core.manager import TaskQuery

                task_query = TaskQuery(limit=query.limit, offset=query.offset)
                tasks = await self.storage.search_tasks(task_query, user_id)
                results = [SearchResult(item=task, score=1.0) for task in tasks]
                total_count = len(tasks)  # Approximate
            else:
                results = []
                total_count = 0
        else:
            # Use text search
            doc_scores = self.index.search(query.text, query.limit * 2)

            # Filter for tasks only
            task_results = []
            for doc_id, score in doc_scores.items():
                if doc_id.startswith("task_"):
                    doc = self.index.documents.get(doc_id)
                    if doc:
                        # Create task object from document (simplified)
                        task = self._document_to_task(doc)
                        if task:
                            result = SearchResult(item=task, score=score)
                            if query.highlight:
                                result.highlights = self._generate_highlights(
                                    doc, query.text
                                )
                            task_results.append(result)

            # Apply additional filters
            filtered_results = self._apply_filters(task_results, query.filters)

            # Apply sorting
            sorted_results = self._apply_sorting(filtered_results, query.sorts)

            # Apply pagination
            results = sorted_results[query.offset : query.offset + query.limit]
            total_count = len(sorted_results)

        # Calculate query time
        query_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        # Generate facets (simplified)
        facets = self._generate_facets(results) if results else {}

        return SearchResults(
            items=results,
            total_count=total_count,
            query_time_ms=query_time,
            facets=facets,
        )

    async def search_projects(self, query: SearchQuery, user_id: str) -> SearchResults:
        """Search for projects"""
        start_time = datetime.now(timezone.utc)

        if not query.text:
            # Fallback to storage
            results = []
            total_count = 0
        else:
            doc_scores = self.index.search(query.text, query.limit * 2)

            project_results = []
            for doc_id, score in doc_scores.items():
                if doc_id.startswith("project_"):
                    doc = self.index.documents.get(doc_id)
                    if doc:
                        project = self._document_to_project(doc)
                        if project:
                            result = SearchResult(item=project, score=score)
                            if query.highlight:
                                result.highlights = self._generate_highlights(
                                    doc, query.text
                                )
                            project_results.append(result)

            results = project_results[query.offset : query.offset + query.limit]
            total_count = len(project_results)

        query_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        return SearchResults(
            items=results, total_count=total_count, query_time_ms=query_time
        )

    async def search_users(
        self, query: SearchQuery, requester_id: str
    ) -> SearchResults:
        """Search for users"""
        start_time = datetime.now(timezone.utc)

        if not query.text:
            results = []
            total_count = 0
        else:
            doc_scores = self.index.search(query.text, query.limit * 2)

            user_results = []
            for doc_id, score in doc_scores.items():
                if doc_id.startswith("user_"):
                    doc = self.index.documents.get(doc_id)
                    if doc and doc.get("is_active", True):  # Only active users
                        user = self._document_to_user(doc)
                        if user:
                            result = SearchResult(item=user, score=score)
                            if query.highlight:
                                result.highlights = self._generate_highlights(
                                    doc, query.text
                                )
                            user_results.append(result)

            results = user_results[query.offset : query.offset + query.limit]
            total_count = len(user_results)

        query_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        return SearchResults(
            items=results, total_count=total_count, query_time_ms=query_time
        )

    async def suggest_completions(
        self, query: str, entity_type: str = "task", limit: int = 10
    ) -> List[str]:
        """Get search suggestions/completions"""
        if len(query) < 2:
            return []

        suggestions = set()
        query_lower = query.lower()

        # Find matching terms from index
        for token in self.index.inverted_index.keys():
            if token.startswith(query_lower):
                suggestions.add(token)

        # Find matching titles/names from documents
        for doc_id, doc in self.index.documents.items():
            doc_type = doc.get("_type", "")
            if entity_type == "all" or doc_type == entity_type:
                # Check title/name field
                title_field = "title" if doc_type == "task" else "name"
                title = doc.get(title_field, "").lower()
                if query_lower in title:
                    # Extract relevant phrases
                    words = title.split()
                    for i, word in enumerate(words):
                        if query_lower in word:
                            # Add phrase starting from this word
                            phrase = " ".join(words[i : i + 3])  # Up to 3 words
                            suggestions.add(phrase)

        return sorted(list(suggestions))[:limit]

    def _apply_filters(
        self, results: List[SearchResult], filters: List[SearchFilter]
    ) -> List[SearchResult]:
        """Apply search filters to results"""
        if not filters:
            return results

        filtered = []
        for result in results:
            item = result.item
            matches = True

            for filter_spec in filters:
                field_value = getattr(item, filter_spec.field, None)

                if not self._filter_matches(field_value, filter_spec):
                    matches = False
                    break

            if matches:
                filtered.append(result)

        return filtered

    def _filter_matches(self, field_value: Any, filter_spec: SearchFilter) -> bool:
        """Check if a field value matches a filter"""
        operator = filter_spec.operator
        filter_value = filter_spec.value

        if field_value is None:
            return operator == "ne" and filter_value is not None

        if operator == "eq":
            return field_value == filter_value
        elif operator == "ne":
            return field_value != filter_value
        elif operator == "gt":
            return field_value > filter_value
        elif operator == "lt":
            return field_value < filter_value
        elif operator == "gte":
            return field_value >= filter_value
        elif operator == "lte":
            return field_value <= filter_value
        elif operator == "in":
            return field_value in filter_value
        elif operator == "contains":
            if isinstance(field_value, str):
                if filter_spec.case_sensitive:
                    return filter_value in field_value
                else:
                    return filter_value.lower() in field_value.lower()
            elif isinstance(field_value, (list, set)):
                return filter_value in field_value
        elif operator == "startswith":
            if isinstance(field_value, str):
                if filter_spec.case_sensitive:
                    return field_value.startswith(filter_value)
                else:
                    return field_value.lower().startswith(filter_value.lower())
        elif operator == "endswith":
            if isinstance(field_value, str):
                if filter_spec.case_sensitive:
                    return field_value.endswith(filter_value)
                else:
                    return field_value.lower().endswith(filter_value.lower())

        return False

    def _apply_sorting(
        self, results: List[SearchResult], sorts: List[SearchSort]
    ) -> List[SearchResult]:
        """Apply sorting to search results"""
        if not sorts:
            # Default sort by relevance score
            return sorted(results, key=lambda r: r.score, reverse=True)

        def sort_key(result):
            keys = []
            for sort_spec in sorts:
                value = getattr(result.item, sort_spec.field, None)
                if value is None:
                    value = (
                        "" if sort_spec.field in ["title", "name", "description"] else 0
                    )
                keys.append(
                    value
                    if sort_spec.ascending
                    else -value if isinstance(value, (int, float)) else value
                )
            return tuple(keys)

        return sorted(results, key=sort_key, reverse=not sorts[0].ascending)

    def _generate_highlights(
        self, document: Dict[str, Any], query: str
    ) -> Dict[str, List[str]]:
        """Generate search term highlights"""
        highlights = {}
        tokens = self.index._tokenize(query)

        for field, value in document.items():
            if field.startswith("_") or not isinstance(value, str):
                continue

            field_highlights = []
            value_lower = value.lower()

            for token in tokens:
                if token in value_lower:
                    # Find context around the token
                    index = value_lower.find(token)
                    start = max(0, index - 20)
                    end = min(len(value), index + len(token) + 20)

                    context = value[start:end]
                    # Highlight the token
                    highlighted = context.replace(
                        value[index : index + len(token)],
                        f"<mark>{value[index:index + len(token)]}</mark>",
                    )
                    field_highlights.append(highlighted)

            if field_highlights:
                highlights[field] = field_highlights[
                    :3
                ]  # Limit to 3 highlights per field

        return highlights

    def _generate_facets(
        self, results: List[SearchResult]
    ) -> Dict[str, Dict[str, int]]:
        """Generate facets for search results"""
        facets = defaultdict(lambda: defaultdict(int))

        for result in results:
            item = result.item
            if isinstance(item, Task):
                facets["status"][item.status.value] += 1
                facets["priority"][item.priority.value] += 1
                facets["task_type"][item.task_type.value] += 1

                # Tags facet
                for tag in item.tags:
                    facets["tags"][tag] += 1

        return dict(facets)

    def _document_to_task(self, doc: Dict[str, Any]) -> Optional[Task]:
        """Convert search document back to Task object (simplified)"""
        try:
            # This is a simplified conversion - in a real implementation
            # you'd want to properly reconstruct the full object
            from taskforge.core.task import Task  # Already imported at top

            task = Task(
                id=doc["id"],
                title=doc["title"],
                description=doc.get("description"),
                status=TaskStatus(doc["status"]),
                priority=TaskPriority(doc["priority"]),
                task_type=TaskType(doc["task_type"]),
                progress=doc.get("progress", 0),
                tags=set(doc.get("tags", [])),
                assigned_to=doc.get("assigned_to"),
                created_by=doc.get("created_by"),
                project_id=doc.get("project_id"),
            )

            # Set dates
            if doc.get("created_at"):
                task.created_at = datetime.fromisoformat(doc["created_at"])
            if doc.get("updated_at"):
                task.updated_at = datetime.fromisoformat(doc["updated_at"])
            if doc.get("due_date"):
                task.due_date = datetime.fromisoformat(doc["due_date"])

            return task
        except Exception as e:
            logger.error(f"Error converting document to task: {e}")
            return None

    def _document_to_project(self, doc: Dict[str, Any]) -> Optional[Project]:
        """Convert search document back to Project object"""
        try:
            from taskforge.core.project import Project, ProjectStatus

            project = Project(
                id=doc["id"],
                name=doc["name"],
                description=doc.get("description"),
                status=ProjectStatus(doc["status"]),
                owner_id=doc["owner_id"],
            )

            if doc.get("created_at"):
                project.created_at = datetime.fromisoformat(doc["created_at"])
            if doc.get("start_date"):
                project.start_date = datetime.fromisoformat(doc["start_date"])
            if doc.get("end_date"):
                project.end_date = datetime.fromisoformat(doc["end_date"])

            return project
        except Exception as e:
            logger.error(f"Error converting document to project: {e}")
            return None

    def _document_to_user(self, doc: Dict[str, Any]) -> Optional[User]:
        """Convert search document back to User object"""
        try:
            from taskforge.core.user import User, UserRole

            user = User(
                id=doc["id"],
                username=doc["username"],
                email=doc["email"],
                full_name=doc.get("full_name"),
                role=UserRole(doc["role"]),
                is_active=doc.get("is_active", True),
            )

            if doc.get("created_at"):
                user.created_at = datetime.fromisoformat(doc["created_at"])

            return user
        except Exception as e:
            logger.error(f"Error converting document to user: {e}")
            return None


# Factory function
def create_search_engine(storage_backend=None) -> SearchEngine:
    """Create a configured search engine"""
    return SearchEngine(storage_backend)
