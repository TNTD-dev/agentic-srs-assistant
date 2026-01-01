# Database Schema Documentation

Tài liệu chi tiết về database schema cho Agentic SRS Assistant.

## Tổng quan

Database lưu trữ 4 loại dữ liệu chính:
- **Projects**: Thông tin dự án
- **SRS Versions**: Các phiên bản của SRS document (versioning)
- **Chat History**: Lịch sử hội thoại giữa user và agent
- **Memory Facts**: Facts và preferences dài hạn (long-term memory)

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      projects                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ project_id (PK)                                       │  │
│  │ project_name                                          │  │
│  │ description                                           │  │
│  │ created_at, updated_at                                │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────────┘
                   │
       ┌───────────┼───────────┬──────────────┐
       │           │           │              │
       │ 1:N       │ 1:N       │ 1:N          │
       │           │           │              │
       ▼           ▼           ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ srs_versions │ │chat_history  │ │memory_facts  │ │  (Future)    │
│              │ │              │ │              │ │   users      │
│ version_id   │ │ chat_id      │ │ fact_id      │ │              │
│ project_id   │ │ project_id   │ │ project_id   │ │              │
│ version_num  │ │ session_id   │ │ fact_key     │ │              │
│ srs_data     │ │ user_msg     │ │ fact_value   │ │              │
│ changelog    │ │ agent_resp   │ │ fact_type    │ │              │
└──────────────┘ │ tool_calls   │ └──────────────┘ └──────────────┘
                 └──────────────┘
```

## Tables

### 1. projects

Lưu thông tin cơ bản của từng dự án SRS.

#### Schema

```sql
CREATE TABLE projects (
    project_id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Columns

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `project_id` | SERIAL | PRIMARY KEY | ID duy nhất, tự động tăng |
| `project_name` | VARCHAR(255) | NOT NULL | Tên dự án |
| `description` | TEXT | | Mô tả ngắn về dự án |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Thời gian tạo |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Thời gian cập nhật (auto-updated) |

#### Indexes

Không có indexes riêng (primary key tự động có index).

#### Triggers

- `update_projects_updated_at`: Tự động cập nhật `updated_at` khi record được update.

---

### 2. srs_versions

Lưu trữ các phiên bản (snapshots) của SRS document. Mỗi lần user nhấn "Confirm", một version mới được tạo.

#### Schema

```sql
CREATE TABLE srs_versions (
    version_id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    version_number VARCHAR(20) NOT NULL,
    srs_data JSONB NOT NULL,
    srs_markdown TEXT,
    changelog TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    UNIQUE(project_id, version_number)
);
```

#### Columns

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `version_id` | SERIAL | PRIMARY KEY | ID duy nhất |
| `project_id` | INTEGER | NOT NULL, FK → projects | ID của project |
| `version_number` | VARCHAR(20) | NOT NULL, UNIQUE(project_id, version_number) | Số phiên bản (v1.0, v1.1, ...) |
| `srs_data` | JSONB | NOT NULL | Dữ liệu SRS dạng JSON (Primary storage) |
| `srs_markdown` | TEXT | | Dữ liệu SRS dạng Markdown (Optional, for export) |
| `changelog` | TEXT | | Tóm tắt thay đổi (Agent-generated) |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Thời gian tạo version |
| `created_by` | INTEGER | | ID người tạo (Future: user_id) |

#### Indexes

- `idx_srs_versions_project_created`: `(project_id, created_at DESC)` - Query version mới nhất
- `idx_srs_data_gin`: `USING GIN (srs_data)` - JSONB queries
- `idx_srs_markdown_fts`: `USING GIN (to_tsvector('english', srs_markdown))` - Full-text search

#### Constraints

- Foreign Key: `project_id` → `projects.project_id` (CASCADE DELETE)
- Unique: `(project_id, version_number)` - Mỗi project chỉ có 1 version với số cụ thể

---

### 3. chat_history

Lưu lịch sử tất cả các cuộc hội thoại giữa user và agent.

#### Schema

```sql
CREATE TABLE chat_history (
    chat_id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    user_message TEXT NOT NULL,
    agent_response TEXT NOT NULL,
    tool_calls JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Columns

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `chat_id` | SERIAL | PRIMARY KEY | ID duy nhất |
| `project_id` | INTEGER | NOT NULL, FK → projects | ID của project |
| `session_id` | VARCHAR(255) | NOT NULL | ID của session (UUID hoặc timestamp-based) |
| `user_message` | TEXT | NOT NULL | Message từ user |
| `agent_response` | TEXT | NOT NULL | Response từ agent |
| `tool_calls` | JSONB | | Tool calls mà agent đã thực hiện (optional) |
| `timestamp` | TIMESTAMP | DEFAULT NOW() | Thời gian message được tạo |

#### Indexes

- `idx_chat_history_session`: `(project_id, session_id, timestamp)` - Query theo session

#### Constraints

- Foreign Key: `project_id` → `projects.project_id` (CASCADE DELETE)

#### Tool Calls Structure (JSONB)

```json
{
  "tool": "update_srs",
  "section": "external_interface",
  "changes": "Added Google OAuth integration",
  "conflicts_detected": false,
  "timestamp": "2024-01-25T10:30:00Z"
}
```

---

### 4. memory_facts

Lưu trữ facts và preferences dài hạn về project (long-term memory).

#### Schema

```sql
CREATE TABLE memory_facts (
    fact_id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    fact_key VARCHAR(255) NOT NULL,
    fact_value TEXT NOT NULL,
    fact_type VARCHAR(50) CHECK (fact_type IN ('preference', 'requirement', 'constraint')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, fact_key)
);
```

#### Columns

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `fact_id` | SERIAL | PRIMARY KEY | ID duy nhất |
| `project_id` | INTEGER | NOT NULL, FK → projects | ID của project |
| `fact_key` | VARCHAR(255) | NOT NULL, UNIQUE(project_id, fact_key) | Key của fact (tech_stack, security_requirement, ...) |
| `fact_value` | TEXT | NOT NULL | Giá trị của fact |
| `fact_type` | VARCHAR(50) | CHECK IN ('preference', 'requirement', 'constraint') | Loại fact |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Thời gian tạo |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Thời gian cập nhật (auto-updated) |

#### Indexes

- `idx_memory_facts_project`: `(project_id, fact_key)` - Query facts của project

#### Constraints

- Foreign Key: `project_id` → `projects.project_id` (CASCADE DELETE)
- Unique: `(project_id, fact_key)` - Mỗi project chỉ có 1 fact cho mỗi key
- Check: `fact_type` phải là một trong: 'preference', 'requirement', 'constraint'

#### Triggers

- `update_memory_facts_updated_at`: Tự động cập nhật `updated_at` khi record được update.

#### Example Facts

| fact_key | fact_value | fact_type |
|----------|------------|-----------|
| `tech_stack` | Python 3.12+, PostgreSQL, React | preference |
| `security_requirement` | OAuth 2.0 required for all APIs | requirement |
| `database_constraint` | Must use PostgreSQL, not SQLite | constraint |

---

## Indexes Summary

| Index Name | Table | Columns | Purpose |
|------------|-------|---------|---------|
| `idx_srs_versions_project_created` | srs_versions | (project_id, created_at DESC) | Query latest version |
| `idx_chat_history_session` | chat_history | (project_id, session_id, timestamp) | Query by session |
| `idx_memory_facts_project` | memory_facts | (project_id, fact_key) | Query facts by project |
| `idx_srs_data_gin` | srs_versions | GIN(srs_data) | JSONB queries |
| `idx_srs_markdown_fts` | srs_versions | GIN(to_tsvector('english', srs_markdown)) | Full-text search |

## Triggers

### update_updated_at_column()

Function tự động cập nhật `updated_at` timestamp.

**Applied to:**
- `projects.updated_at`
- `memory_facts.updated_at`

## Migration

### Apply Migrations

```bash
# Run migrations
python scripts/run_migrations.py

# Dry run (show what would be applied)
python scripts/run_migrations.py --dry-run
```

### Migration Files

- `migrations/001_initial_schema.sql` - Initial schema với 4 tables, indexes, và triggers

## Testing

### CRUD Tests

```bash
# Run CRUD tests
python tests/test_database_crud.py
```

Tests cover:
- CREATE operations (all tables)
- READ operations (queries)
- UPDATE operations
- DELETE operations
- Foreign key constraints
- Unique constraints
- Index verification

## Common Queries

### Get Latest SRS Version

```sql
SELECT * FROM srs_versions 
WHERE project_id = 1 
ORDER BY created_at DESC 
LIMIT 1;
```

### Get Chat History by Session

```sql
SELECT user_message, agent_response, tool_calls, timestamp
FROM chat_history
WHERE project_id = 1 AND session_id = 'session_abc123'
ORDER BY timestamp ASC;
```

### Get All Facts for Project

```sql
SELECT fact_key, fact_value, fact_type
FROM memory_facts
WHERE project_id = 1
ORDER BY updated_at DESC;
```

### JSONB Query Example

```sql
-- Search in srs_data JSONB field
SELECT * FROM srs_versions 
WHERE srs_data->>'system_features' LIKE '%authentication%';
```

## Notes

- **PostgreSQL**: Full support với JSONB, GIN indexes, full-text search
- **SQLite**: Không hỗ trợ JSONB, cần dùng TEXT thay thế (future migration)
- **CASCADE DELETE: Khi xóa project, tất cả related records sẽ tự động xóa
- **Versioning**: Mỗi version là snapshot hoàn chỉnh, không phải diff
- **Memory Facts**: Sử dụng UPSERT pattern với `ON CONFLICT ... DO UPDATE`

## References

- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
- [PostgreSQL Documentation](https://www.postgresql.org/docs/) - PostgreSQL reference
- [JSONB Documentation](https://www.postgresql.org/docs/current/datatype-json.html) - JSONB type

