from pathlib import Path

import mysql.connector

from app.config import get_settings


def split_sql_statements(sql: str) -> list[str]:
    return [statement.strip() for statement in sql.split(";") if statement.strip()]


def main() -> None:
    settings = get_settings()
    schema_path = Path("db/schema.sql")
    statements = split_sql_statements(schema_path.read_text(encoding="utf-8"))

    conn = mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password or "",
    )
    try:
        cursor = conn.cursor()
        for statement in statements:
            cursor.execute(statement)
        conn.commit()
    finally:
        conn.close()

    print(f"Initialized MySQL schema: {settings.mysql_database}")


if __name__ == "__main__":
    main()

