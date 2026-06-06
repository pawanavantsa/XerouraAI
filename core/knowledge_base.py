import logging
import uuid

from django.db import connection

logger = logging.getLogger(__name__)


def search_knowledge_base(
    query_embedding: list[float],
    *,
    team_id: uuid.UUID | str,
    category: str | None = None,
    limit: int = 3,
) -> list:
    """Search the knowledge base using pgvector cosine distance, scoped to a team.

    Args:
        query_embedding: A 1536-dimensional embedding vector for the query.
        team_id: Team that owns KB rows.
        category: Optional category filter (billing/technical/account/general).
        limit: Maximum number of results.

    Returns:
        List of content strings from the most relevant knowledge base entries.
    """
    embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"
    tid = str(team_id)

    if category:
        sql = """
            SELECT content
            FROM knowledge_base
            WHERE team_id = %s AND category = %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        params = [tid, category, embedding_str, limit]
    else:
        sql = """
            SELECT content
            FROM knowledge_base
            WHERE team_id = %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        params = [tid, embedding_str, limit]

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        return [row[0] for row in rows]

    except Exception as e:
        logger.error("Knowledge base search error: %s", str(e))
        return []
