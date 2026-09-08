"""
Writes to audit_log. Always call this INSIDE the same transaction as the
change it describes, so the audit row and the change either both commit
or both roll back - never one without the other.
"""
import json
import asyncpg


async def record_audit(
    conn: asyncpg.Connection,
    actor_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    before: dict | None,
    after: dict | None,
):
    await conn.execute(
        """
        insert into public.audit_log (actor_id, action, entity_type, entity_id, before, after)
        values ($1, $2, $3, $4, $5, $6)
        """,
        actor_id, action, entity_type, entity_id,
        json.dumps(before, default=str) if before is not None else None,
        json.dumps(after, default=str) if after is not None else None,
    )