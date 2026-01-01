#!/usr/bin/env python3
"""
CRUD operations test for database schema.
Tests CREATE, READ, UPDATE, DELETE operations for all tables.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_db_connection() -> psycopg2.extensions.connection:
    """Create database connection."""
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
        raise


class DatabaseCRUDTester:
    """Test CRUD operations for all database tables."""
    
    def __init__(self, conn: psycopg2.extensions.connection):
        self.conn = conn
        self.test_project_id: Optional[int] = None
        self.test_version_id: Optional[int] = None
        self.test_chat_id: Optional[int] = None
        self.test_fact_id: Optional[int] = None
    
    def test_create_projects(self) -> bool:
        """Test CREATE operation for projects table."""
        print("\n[TEST] CREATE - projects")
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO projects (project_name, description)
                    VALUES (%s, %s)
                    RETURNING project_id
                """, ("Test Project", "Test description"))
                
                self.test_project_id = cur.fetchone()[0]
                self.conn.commit()
                
                print(f"  ✓ Created project with ID: {self.test_project_id}")
                return True
        except Exception as e:
            self.conn.rollback()
            print(f"  ✗ Failed: {e}")
            return False
    
    def test_read_projects(self) -> bool:
        """Test READ operation for projects table."""
        print("\n[TEST] READ - projects")
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT project_id, project_name, description, created_at
                    FROM projects
                    WHERE project_id = %s
                """, (self.test_project_id,))
                
                row = cur.fetchone()
                if row:
                    print(f"  ✓ Found project: ID={row[0]}, Name={row[1]}")
                    return True
                else:
                    print("  ✗ Project not found")
                    return False
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            return False
    
    def test_update_projects(self) -> bool:
        """Test UPDATE operation for projects table."""
        print("\n[TEST] UPDATE - projects")
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE projects
                    SET project_name = %s, description = %s
                    WHERE project_id = %s
                """, ("Updated Test Project", "Updated description", self.test_project_id))
                
                self.conn.commit()
                
                # Verify update
                cur.execute("SELECT project_name FROM projects WHERE project_id = %s", (self.test_project_id,))
                row = cur.fetchone()
                if row and row[0] == "Updated Test Project":
                    print(f"  ✓ Updated project successfully")
                    return True
                else:
                    print("  ✗ Update verification failed")
                    return False
        except Exception as e:
            self.conn.rollback()
            print(f"  ✗ Failed: {e}")
            return False
    
    def test_create_srs_versions(self) -> bool:
        """Test CREATE operation for srs_versions table."""
        print("\n[TEST] CREATE - srs_versions")
        try:
            test_srs_data = {
                "introduction": "Test introduction",
                "overall_description": "Test description",
                "system_features": "Test features",
                "external_interface": "Test interface",
                "non_functional": "Test non-functional",
                "appendices": "Test appendices"
            }
            
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO srs_versions 
                    (project_id, version_number, srs_data, srs_markdown, changelog)
                    VALUES (%s, %s, %s::jsonb, %s, %s)
                    RETURNING version_id
                """, (
                    self.test_project_id,
                    "v1.0",
                    json.dumps(test_srs_data),
                    "# Test SRS\n## 1. Introduction\nTest",
                    "Initial test version"
                ))
                
                self.test_version_id = cur.fetchone()[0]
                self.conn.commit()
                
                print(f"  ✓ Created SRS version with ID: {self.test_version_id}")
                return True
        except Exception as e:
            self.conn.rollback()
            print(f"  ✗ Failed: {e}")
            return False
    
    def test_read_srs_versions(self) -> bool:
        """Test READ operation for srs_versions table."""
        print("\n[TEST] READ - srs_versions")
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT version_id, version_number, srs_data, changelog
                    FROM srs_versions
                    WHERE version_id = %s
                """, (self.test_version_id,))
                
                row = cur.fetchone()
                if row:
                    print(f"  ✓ Found version: ID={row[0]}, Version={row[1]}")
                    # Test JSONB query
                    cur.execute("""
                        SELECT srs_data->>'introduction' as intro
                        FROM srs_versions
                        WHERE version_id = %s
                    """, (self.test_version_id,))
                    jsonb_result = cur.fetchone()
                    if jsonb_result:
                        print(f"  ✓ JSONB query successful: {jsonb_result[0]}")
                    return True
                else:
                    print("  ✗ Version not found")
                    return False
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            return False
    
    def test_create_chat_history(self) -> bool:
        """Test CREATE operation for chat_history table."""
        print("\n[TEST] CREATE - chat_history")
        try:
            test_tool_calls = {
                "tool": "update_srs",
                "section": "system_features",
                "changes": "Added test feature"
            }
            
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO chat_history 
                    (project_id, session_id, user_message, agent_response, tool_calls)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    RETURNING chat_id
                """, (
                    self.test_project_id,
                    "test_session_001",
                    "Add a test feature",
                    "I will add the test feature to the SRS.",
                    json.dumps(test_tool_calls)
                ))
                
                self.test_chat_id = cur.fetchone()[0]
                self.conn.commit()
                
                print(f"  ✓ Created chat history with ID: {self.test_chat_id}")
                return True
        except Exception as e:
            self.conn.rollback()
            print(f"  ✗ Failed: {e}")
            return False
    
    def test_read_chat_history(self) -> bool:
        """Test READ operation for chat_history table."""
        print("\n[TEST] READ - chat_history")
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT chat_id, session_id, user_message, agent_response
                    FROM chat_history
                    WHERE chat_id = %s
                """, (self.test_chat_id,))
                
                row = cur.fetchone()
                if row:
                    print(f"  ✓ Found chat: ID={row[0]}, Session={row[1]}")
                    return True
                else:
                    print("  ✗ Chat not found")
                    return False
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            return False
    
    def test_create_memory_facts(self) -> bool:
        """Test CREATE operation for memory_facts table."""
        print("\n[TEST] CREATE - memory_facts")
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO memory_facts 
                    (project_id, fact_key, fact_value, fact_type)
                    VALUES (%s, %s, %s, %s)
                    RETURNING fact_id
                """, (
                    self.test_project_id,
                    "test_tech_stack",
                    "Python 3.12+, PostgreSQL",
                    "preference"
                ))
                
                self.test_fact_id = cur.fetchone()[0]
                self.conn.commit()
                
                print(f"  ✓ Created memory fact with ID: {self.test_fact_id}")
                return True
        except Exception as e:
            self.conn.rollback()
            print(f"  ✗ Failed: {e}")
            return False
    
    def test_read_memory_facts(self) -> bool:
        """Test READ operation for memory_facts table."""
        print("\n[TEST] READ - memory_facts")
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT fact_id, fact_key, fact_value, fact_type
                    FROM memory_facts
                    WHERE fact_id = %s
                """, (self.test_fact_id,))
                
                row = cur.fetchone()
                if row:
                    print(f"  ✓ Found fact: ID={row[0]}, Key={row[1]}, Value={row[2]}")
                    return True
                else:
                    print("  ✗ Fact not found")
                    return False
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            return False
    
    def test_update_memory_facts(self) -> bool:
        """Test UPDATE operation for memory_facts table."""
        print("\n[TEST] UPDATE - memory_facts")
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE memory_facts
                    SET fact_value = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE fact_id = %s
                """, ("Python 3.12+, PostgreSQL, Redis", self.test_fact_id))
                
                self.conn.commit()
                
                # Verify update
                cur.execute("SELECT fact_value FROM memory_facts WHERE fact_id = %s", (self.test_fact_id,))
                row = cur.fetchone()
                if row and "Redis" in row[0]:
                    print(f"  ✓ Updated fact successfully")
                    return True
                else:
                    print("  ✗ Update verification failed")
                    return False
        except Exception as e:
            self.conn.rollback()
            print(f"  ✗ Failed: {e}")
            return False
    
    def test_foreign_key_constraints(self) -> bool:
        """Test foreign key constraints."""
        print("\n[TEST] Foreign Key Constraints")
        try:
            with self.conn.cursor() as cur:
                # Try to insert with invalid project_id
                cur.execute("""
                    INSERT INTO srs_versions 
                    (project_id, version_number, srs_data)
                    VALUES (%s, %s, %s::jsonb)
                """, (99999, "v1.0", json.dumps({"test": "data"})))
                
                self.conn.rollback()
                print("  ✗ Foreign key constraint not enforced")
                return False
        except psycopg2.IntegrityError:
            self.conn.rollback()
            print("  ✓ Foreign key constraint enforced correctly")
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"  ✗ Unexpected error: {e}")
            return False
    
    def test_unique_constraints(self) -> bool:
        """Test unique constraints."""
        print("\n[TEST] Unique Constraints")
        try:
            with self.conn.cursor() as cur:
                # Try to insert duplicate version_number for same project
                cur.execute("""
                    INSERT INTO srs_versions 
                    (project_id, version_number, srs_data)
                    VALUES (%s, %s, %s::jsonb)
                """, (
                    self.test_project_id,
                    "v1.0",  # Same as existing
                    json.dumps({"test": "data"})
                ))
                
                self.conn.rollback()
                print("  ✗ Unique constraint not enforced")
                return False
        except psycopg2.IntegrityError:
            self.conn.rollback()
            print("  ✓ Unique constraint enforced correctly")
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"  ✗ Unexpected error: {e}")
            return False
    
    def test_indexes(self) -> bool:
        """Test that indexes exist and are used."""
        print("\n[TEST] Indexes")
        try:
            with self.conn.cursor() as cur:
                # Check if indexes exist
                cur.execute("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename IN ('projects', 'srs_versions', 'chat_history', 'memory_facts')
                    AND indexname LIKE 'idx_%'
                    ORDER BY indexname
                """)
                
                indexes = [row[0] for row in cur.fetchall()]
                expected_indexes = [
                    "idx_srs_versions_project_created",
                    "idx_chat_history_session",
                    "idx_memory_facts_project",
                    "idx_srs_data_gin"
                ]
                
                found = [idx for idx in expected_indexes if idx in indexes]
                if len(found) == len(expected_indexes):
                    print(f"  ✓ All expected indexes found: {', '.join(found)}")
                    return True
                else:
                    missing = set(expected_indexes) - set(found)
                    print(f"  ✗ Missing indexes: {', '.join(missing)}")
                    return False
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up test data."""
        print("\n[CLEANUP] Removing test data...")
        try:
            with self.conn.cursor() as cur:
                if self.test_fact_id:
                    cur.execute("DELETE FROM memory_facts WHERE fact_id = %s", (self.test_fact_id,))
                if self.test_chat_id:
                    cur.execute("DELETE FROM chat_history WHERE chat_id = %s", (self.test_chat_id,))
                if self.test_version_id:
                    cur.execute("DELETE FROM srs_versions WHERE version_id = %s", (self.test_version_id,))
                if self.test_project_id:
                    cur.execute("DELETE FROM projects WHERE project_id = %s", (self.test_project_id,))
                
                self.conn.commit()
                print("  ✓ Cleanup completed")
        except Exception as e:
            self.conn.rollback()
            print(f"  ✗ Cleanup failed: {e}")
    
    def run_all_tests(self) -> dict[str, bool]:
        """Run all CRUD tests."""
        results = {}
        
        # CREATE tests
        results["create_projects"] = self.test_create_projects()
        results["create_srs_versions"] = self.test_create_srs_versions()
        results["create_chat_history"] = self.test_create_chat_history()
        results["create_memory_facts"] = self.test_create_memory_facts()
        
        # READ tests
        results["read_projects"] = self.test_read_projects()
        results["read_srs_versions"] = self.test_read_srs_versions()
        results["read_chat_history"] = self.test_read_chat_history()
        results["read_memory_facts"] = self.test_read_memory_facts()
        
        # UPDATE tests
        results["update_projects"] = self.test_update_projects()
        results["update_memory_facts"] = self.test_update_memory_facts()
        
        # Constraint tests
        results["foreign_key_constraints"] = self.test_foreign_key_constraints()
        results["unique_constraints"] = self.test_unique_constraints()
        
        # Index tests
        results["indexes"] = self.test_indexes()
        
        return results


def main():
    """Main test function."""
    print("=" * 60)
    print("Database CRUD Operations Test")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        print("✓ Connected to database")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return 1
    
    tester = DatabaseCRUDTester(conn)
    
    try:
        results = tester.run_all_tests()
        
        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        passed = sum(1 for v in results.values() if v)
        failed = sum(1 for v in results.values() if not v)
        
        for test_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\nTotal: {len(results)} tests")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        if failed == 0:
            print("\n🎉 All CRUD tests passed!")
            return 0
        else:
            print(f"\n⚠️  {failed} test(s) failed.")
            return 1
            
    finally:
        tester.cleanup()
        conn.close()


if __name__ == "__main__":
    sys.exit(main())

