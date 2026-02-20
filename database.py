import sqlite3
import os
import uuid
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "leave_management.db")

class Database:
    def __init__(self):
        self.conn = None

    def init(self):
        try:
            self.conn = sqlite3.connect(DB_PATH)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
            print("Connected to SQLite database")
            self.create_tables()
            self.seed_initial_data()
        except Exception as e:
            print("Error initializing database:", e)
            raise e

    def create_tables(self):
        cursor = self.conn.cursor()

        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'employee',
            department TEXT,
            manager_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (manager_id) REFERENCES users(id)
        )
        """)

        # Projects table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            status TEXT DEFAULT 'active',
            priority TEXT DEFAULT 'medium',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Project assignments
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_assignments (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            allocation_percentage INTEGER DEFAULT 100,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)

        # Leave requests
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            days_count INTEGER NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            manager_id TEXT,
            auto_approved BOOLEAN DEFAULT 0,
            rejection_reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (manager_id) REFERENCES users(id)
        )
        """)

        # Leave history
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_history (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            leave_request_id TEXT,
            leave_type TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            days_count INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (leave_request_id) REFERENCES leave_requests(id)
        )
        """)

        # Workload snapshots
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workload_snapshots (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            date DATE NOT NULL,
            total_allocation INTEGER DEFAULT 0,
            project_count INTEGER DEFAULT 0,
            workload_score REAL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)

        # Approval rules
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS approval_rules (
            id TEXT PRIMARY KEY,
            rule_name TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            conditions TEXT NOT NULL,
            action TEXT NOT NULL,
            priority INTEGER DEFAULT 0,
            active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Notifications
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            read BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)

        self.conn.commit()
        print("Database tables created successfully")

    def seed_initial_data(self):
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM users")
        count = cursor.fetchone()["count"]

        if count == 0:
            manager_id = str(uuid.uuid4())
            employee1_id = str(uuid.uuid4())
            employee2_id = str(uuid.uuid4())

            sample_users = [
                (manager_id, "manager@company.com", "John Manager", "manager", "Engineering", None),
                (employee1_id, "employee1@company.com", "Alice Employee", "employee", "Engineering", manager_id),
                (employee2_id, "employee2@company.com", "Bob Employee", "employee", "Engineering", manager_id),
            ]

            cursor.executemany("""
                INSERT INTO users (id, email, name, role, department, manager_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, sample_users)

            self.conn.commit()
            print("Sample data seeded")

    def query(self, sql, params=()):
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def get(self, sql, params=()):
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def run(self, sql, params=()):
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        self.conn.commit()
        return {
            "lastID": cursor.lastrowid,
            "changes": cursor.rowcount
        }

    def get_connection(self):
        return self.conn


# Usage Example
if __name__ == "__main__":
    db = Database()
    db.init()

    users = db.query("SELECT * FROM users")
    print(users)


# Global database instance
_db_instance = None

def init_db():
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
        _db_instance.init()
    return _db_instance

def get_db():
    global _db_instance
    if _db_instance is None:
        raise Exception("Database not initialized. Call init_db() first.")
    return _db_instance