#!/usr/bin/env python3
"""
Test script for Docker infrastructure setup.
Tests Docker containers and PostgreSQL connection.
"""

import os
import sys
import subprocess
import time
from typing import Tuple, Optional

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("ERROR: psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)


def run_command(cmd: list[str], check: bool = True) -> Tuple[int, str, str]:
    """
    Run a shell command and return the result.
    
    Args:
        cmd: Command to run as list
        check: If True, raise exception on non-zero exit
        
    Returns:
        Tuple of (returncode, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr


def test_docker_compose_installed() -> bool:
    """Test if docker-compose is installed and accessible."""
    print("Testing docker-compose installation...")
    returncode, stdout, stderr = run_command(["docker-compose", "--version"], check=False)
    if returncode == 0:
        print(f"✓ docker-compose installed: {stdout.strip()}")
        return True
    else:
        print(f"✗ docker-compose not found. Error: {stderr}")
        return False


def test_docker_containers_running() -> bool:
    """Test if Docker containers are running."""
    print("\nTesting Docker containers status...")
    returncode, stdout, stderr = run_command(["docker-compose", "ps"], check=False)
    
    if returncode != 0:
        print(f"✗ Failed to check containers. Error: {stderr}")
        return False
    
    print("Container status:")
    print(stdout)
    
    # Check if postgres and app containers are in the output
    if "srs-postgres" in stdout and "srs-app" in stdout:
        # Check if they're running (not exited)
        if "Up" in stdout or "running" in stdout.lower():
            print("✓ Containers are running")
            return True
        else:
            print("✗ Containers exist but may not be running")
            return False
    else:
        print("✗ Required containers (srs-postgres, srs-app) not found")
        return False


def get_db_connection_string() -> str:
    """Get database connection string from environment or defaults."""
    # Try to get from environment variables
    db_user = os.getenv("POSTGRES_USER", "srs_user")
    db_password = os.getenv("POSTGRES_PASSWORD", "srs_password")
    db_name = os.getenv("POSTGRES_DB", "srs_assistant")
    db_host = os.getenv("POSTGRES_HOST", "postgres")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def test_postgresql_connection() -> Tuple[bool, Optional[psycopg2.extensions.connection]]:
    """
    Test PostgreSQL connection from local machine.
    Note: This assumes PostgreSQL is accessible from host (port mapped).
    """
    print("\nTesting PostgreSQL connection...")
    
    # For connection from host, use localhost
    db_user = os.getenv("POSTGRES_USER", "srs_user")
    db_password = os.getenv("POSTGRES_PASSWORD", "srs_password")
    db_name = os.getenv("POSTGRES_DB", "srs_assistant")
    db_host = os.getenv("POSTGRES_HOST", "localhost")  # Use localhost for host connection
    db_port = os.getenv("POSTGRES_PORT", "5432")
    
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
            connect_timeout=5
        )
        print(f"✓ Successfully connected to PostgreSQL at {db_host}:{db_port}")
        return True, conn
    except psycopg2.OperationalError as e:
        print(f"✗ Failed to connect to PostgreSQL: {e}")
        print(f"  Host: {db_host}, Port: {db_port}, Database: {db_name}, User: {db_user}")
        print("  Note: If running from host, ensure PostgreSQL port is mapped in docker-compose.yml")
        return False, None
    except Exception as e:
        print(f"✗ Unexpected error connecting to PostgreSQL: {e}")
        return False, None


def test_postgresql_from_container() -> bool:
    """Test PostgreSQL connection from app container."""
    print("\nTesting PostgreSQL connection from app container...")
    
    db_user = os.getenv("POSTGRES_USER", "srs_user")
    db_password = os.getenv("POSTGRES_PASSWORD", "srs_password")
    db_name = os.getenv("POSTGRES_DB", "srs_assistant")
    
    conn_string = f"postgresql://{db_user}:{db_password}@postgres:5432/{db_name}"
    
    python_cmd = f"import psycopg2; conn = psycopg2.connect('{conn_string}'); print('Connection successful'); conn.close()"
    
    returncode, stdout, stderr = run_command(
        ["docker-compose", "exec", "-T", "app", "python", "-c", python_cmd],
        check=False
    )
    
    if returncode == 0 and "Connection successful" in stdout:
        print("✓ PostgreSQL connection from app container successful")
        return True
    else:
        print(f"✗ Failed to connect from app container")
        if stderr:
            print(f"  Error: {stderr}")
        return False


def test_database_operations(conn: psycopg2.extensions.connection) -> bool:
    """Test basic database operations."""
    print("\nTesting database operations...")
    
    try:
        cur = conn.cursor()
        
        # Create test table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS test_docker_setup (
                id SERIAL PRIMARY KEY,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ Created test table")
        
        # Insert test data
        cur.execute("""
            INSERT INTO test_docker_setup (message) 
            VALUES (%s)
        """, ("Docker setup test",))
        print("✓ Inserted test data")
        
        # Query data
        cur.execute("SELECT id, message, created_at FROM test_docker_setup")
        rows = cur.fetchall()
        if rows:
            print(f"✓ Queried data: {len(rows)} row(s) found")
            for row in rows:
                print(f"  - ID: {row[0]}, Message: {row[1]}, Created: {row[2]}")
        
        # Drop test table
        cur.execute("DROP TABLE IF EXISTS test_docker_setup")
        print("✓ Dropped test table")
        
        conn.commit()
        cur.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Database operations failed: {e}")
        try:
            conn.rollback()
        except:
            pass
        return False


def test_postgres_health_check() -> bool:
    """Test PostgreSQL health check."""
    print("\nTesting PostgreSQL health check...")
    
    returncode, stdout, stderr = run_command(
        ["docker-compose", "exec", "-T", "postgres", "pg_isready", "-U", "srs_user", "-d", "srs_assistant"],
        check=False
    )
    
    if returncode == 0:
        print("✓ PostgreSQL health check passed")
        return True
    else:
        print(f"✗ PostgreSQL health check failed: {stderr}")
        return False


def main():
    """Main test function."""
    print("=" * 60)
    print("Docker Infrastructure Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Docker Compose installation
    results.append(("Docker Compose", test_docker_compose_installed()))
    
    # Test 2: Containers running
    results.append(("Containers Running", test_docker_containers_running()))
    
    # Test 3: PostgreSQL health check
    results.append(("PostgreSQL Health", test_postgres_health_check()))
    
    # Test 4: Connection from container
    results.append(("Connection from Container", test_postgresql_from_container()))
    
    # Test 5: Connection from host (if possible)
    conn_success, conn = test_postgresql_connection()
    results.append(("Connection from Host", conn_success))
    
    # Test 6: Database operations (if connection successful)
    if conn_success and conn:
        results.append(("Database Operations", test_database_operations(conn)))
        conn.close()
    else:
        results.append(("Database Operations", False))
        print("\n⚠ Skipping database operations test (connection failed)")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Docker infrastructure is ready.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

