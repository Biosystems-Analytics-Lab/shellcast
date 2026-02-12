import logging

from sqlalchemy import create_engine, text


def execute_stored_procedure(connection_string, procedure_name, *args):
    """
    Execute a stored procedure using SQLAlchemy and return rows as dicts.

    Args:
        connection_string: SQLAlchemy database URL
        procedure_name: name of the stored procedure to call
        *args: positional arguments passed to the stored procedure
    """
    engine = None
    try:
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            if args:
                placeholders = ",".join(["%s" for _ in args])
                query = text(f"CALL {procedure_name}({placeholders})")
                result = conn.execute(query, args)
            else:
                query = text(f"CALL {procedure_name}()")
                result = conn.execute(query)

            if result.returns_rows:
                column_names = result.keys()
                return [dict(zip(column_names, row)) for row in result.fetchall()]

            return []
    except Exception:
        logging.exception("Error executing stored procedure %s", procedure_name)
        raise
    finally:
        if engine is not None:
            try:
                engine.dispose()
            except Exception:
                # Best-effort cleanup; ignore dispose errors
                pass
