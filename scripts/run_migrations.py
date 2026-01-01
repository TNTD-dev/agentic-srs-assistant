#!/usr/bin/env python3
"""
Database migration runner.
Applies SQL migration files in order to set up the database schema.
"""

import os
import sys
from pathlib import Path
from typing import Optional
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
MIGRATIONS_DIR = PROJECT_ROOT / "migrations"


def get_db_connection() -> psycopg2.extensions.connection:
    """
    Create database connection from environment variables.
    
    Returns:
        psycopg2 connection object
        
    Raises:
        Exception: If connection fails
    """
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "srs_assistant")
    db_user = os.getenv("POSTGRES_USER", "srs_user")
    db_password = os.getenv("POSTGRES_PASSWORD", "srs_password_change_me")
    
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
            connect_timeout=10
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"ERROR: Failed to connect to database: {e}")
        print(f"  Host: {db_host}, Port: {db_port}, Database: {db_name}, User: {db_user}")
        raise


def create_migrations_table(conn: psycopg2.extensions.connection) -> None:
    """Create migrations tracking table if it doesn't exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                migration_id VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def get_applied_migrations(conn: psycopg2.extensions.connection) -> set[str]:
    """Get set of already applied migration IDs."""
    create_migrations_table(conn)
    
    with conn.cursor() as cur:
        cur.execute("SELECT migration_id FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


def mark_migration_applied(conn: psycopg2.extensions.connection, migration_id: str) -> None:
    """Mark a migration as applied."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO schema_migrations (migration_id) VALUES (%s) ON CONFLICT DO NOTHING",
            (migration_id,)
        )
        conn.commit()


def get_migration_files() -> list[Path]:
    """
    Get all migration SQL files sorted by name.
    
    Returns:
        List of Path objects for migration files
    """
    if not MIGRATIONS_DIR.exists():
        print(f"ERROR: Migrations directory not found: {MIGRATIONS_DIR}")
        sys.exit(1)
    
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    return migration_files


def extract_migration_id(filename: str) -> str:
    """
    Extract migration ID from filename.
    Example: "001_initial_schema.sql" -> "001_initial_schema"
    """
    return Path(filename).stem


def apply_migration(conn: psycopg2.extensions.connection, migration_file: Path) -> bool:
    """
    Apply a single migration file.
    
    Args:
        conn: Database connection
        migration_file: Path to migration SQL file
        
    Returns:
        True if successful, False otherwise
    """
    migration_id = extract_migration_id(migration_file.name)
    
    print(f"Applying migration: {migration_file.name}")
    
    try:
        # Read migration SQL
        with open(migration_file, "r", encoding="utf-8") as f:
            migration_sql = f.read()
        
        # Execute migration
        with conn.cursor() as cur:
            cur.execute(migration_sql)
            conn.commit()
        
        # Mark as applied
        mark_migration_applied(conn, migration_id)
        
        print(f"✓ Successfully applied: {migration_file.name}")
        return True
        
    except psycopg2.Error as e:
        conn.rollback()
        print(f"✗ Failed to apply {migration_file.name}: {e}")
        return False
    except Exception as e:
        conn.rollback()
        print(f"✗ Unexpected error applying {migration_file.name}: {e}")
        return False


def run_migrations(dry_run: bool = False) -> int:
    """
    Run all pending migrations.
    
    Args:
        dry_run: If True, only show what would be applied without executing
        
    Returns:
        Number of migrations applied (0 if dry_run)
    """
    print("=" * 60)
    print("Database Migration Runner")
    print("=" * 60)
    
    if dry_run:
        print("DRY RUN MODE: No changes will be made")
        print()
    
    # Get database connection
    try:
        conn = get_db_connection()
        print(f"✓ Connected to database")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return 1
    
    # Get migration files
    migration_files = get_migration_files()
    if not migration_files:
        print("No migration files found")
        return 0
    
    print(f"Found {len(migration_files)} migration file(s)")
    print()
    
    # Get applied migrations
    applied_migrations = get_applied_migrations(conn)
    print(f"Already applied: {len(applied_migrations)} migration(s)")
    print()
    
    # Apply pending migrations
    applied_count = 0
    failed_count = 0
    
    for migration_file in migration_files:
        migration_id = extract_migration_id(migration_file.name)
        
        if migration_id in applied_migrations:
            print(f"⊘ Skipping (already applied): {migration_file.name}")
            continue
        
        if dry_run:
            print(f"⊘ Would apply: {migration_file.name}")
            applied_count += 1
        else:
            if apply_migration(conn, migration_file):
                applied_count += 1
            else:
                failed_count += 1
                print("Stopping due to migration failure")
                break
    
    # Summary
    print()
    print("=" * 60)
    print("Migration Summary")
    print("=" * 60)
    
    if dry_run:
        print(f"Would apply: {applied_count} migration(s)")
    else:
        print(f"Applied: {applied_count} migration(s)")
        if failed_count > 0:
            print(f"Failed: {failed_count} migration(s)")
    
    conn.close()
    
    return 0 if failed_count == 0 else 1


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be applied without executing"
    )
    
    args = parser.parse_args()
    
    exit_code = run_migrations(dry_run=args.dry_run)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

