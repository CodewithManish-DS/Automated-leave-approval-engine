import uuid
import sqlite3
from typing import List, Dict, Any


class NotificationService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    async def create(self, user_id: str, type: str, title: str, message: str) -> str:
        try:
            notification_id = str(uuid.uuid4())
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO notifications (id, user_id, type, title, message)
                VALUES (?, ?, ?, ?, ?)
                """,
                (notification_id, user_id, type, title, message),
            )

            conn.commit()
            conn.close()

            return notification_id
        except Exception as error:
            print("Error creating notification:", error)
            raise

    async def get_user_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            sql = "SELECT * FROM notifications WHERE user_id = ?"
            params = [user_id]

            if unread_only:
                sql += " AND read = 0"

            sql += " ORDER BY created_at DESC LIMIT 50"

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as error:
            print("Error fetching notifications:", error)
            return []

    async def mark_as_read(self, notification_id: str) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE notifications SET read = 1 WHERE id = ?",
                (notification_id,),
            )

            conn.commit()
            conn.close()

            return True
        except Exception as error:
            print("Error marking notification as read:", error)
            return False

    async def mark_all_as_read(self, user_id: str) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE notifications SET read = 1 WHERE user_id = ? AND read = 0",
                (user_id,),
            )

            conn.commit()
            conn.close()

            return True
        except Exception as error:
            print("Error marking all notifications as read:", error)
            return False