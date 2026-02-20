import sqlite3
from datetime import datetime, date
from typing import Dict, Any, List


class AutoApprovalEngine:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def evaluate(self, leave_request_id: str, user_id: str,
                 start_date: str, end_date: str) -> Dict[str, Any]:

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get leave request details
            cursor.execute(
                "SELECT * FROM leave_requests WHERE id = ?",
                (leave_request_id,)
            )
            leave_request = cursor.fetchone()

            # Get user's current workload
            cursor.execute("""
                SELECT pa.*, p.end_date as project_end_date, p.priority
                FROM project_assignments pa
                JOIN projects p ON pa.project_id = p.id
                WHERE pa.user_id = ?
                AND pa.end_date >= date('now')
            """, (user_id,))
            assignments = cursor.fetchall()

            # Get user's department and manager
            cursor.execute(
                "SELECT department, manager_id FROM users WHERE id = ?",
                (user_id,)
            )
            user = cursor.fetchone()

            leave_start = datetime.fromisoformat(start_date)
            leave_end = datetime.fromisoformat(end_date)
            today = datetime.now()

            # ----------------------------
            # Rule 1: Critical Deadlines
            # ----------------------------
            critical_deadlines = []

            for assignment in assignments:
                deadline = datetime.fromisoformat(assignment["project_end_date"])
                days_until_deadline = (deadline - today).days
                leave_days = (leave_end - leave_start).days

                if (
                    (leave_start <= deadline <= leave_end)
                    or (deadline > leave_end and (deadline - leave_end).days <= 7)
                    or (assignment["priority"] == "high" and days_until_deadline <= 14)
                ):
                    critical_deadlines.append(assignment)

            if len(critical_deadlines) > 0:
                conn.close()
                return {
                    "approved": False,
                    "message": f"Leave request conflicts with {len(critical_deadlines)} critical project deadline(s). Requires manager approval.",
                    "reason": "deadline_conflict"
                }

            # ----------------------------
            # Rule 2: Workload Allocation
            # ----------------------------
            total_allocation = sum(
                a["allocation_percentage"] for a in assignments
            )
            days_count = (leave_end - leave_start).days + 1

            if total_allocation > 100 and days_count <= 2:
                conn.close()
                return {
                    "approved": True,
                    "message": "Auto-approved: User is overloaded and leave is short duration.",
                    "reason": "overload_relief"
                }

            # ----------------------------
            # Rule 3: Team Availability
            # ----------------------------
            cursor.execute("""
                SELECT id FROM users
                WHERE (department = ? OR manager_id = ?)
                AND id != ?
            """, (user["department"], user["manager_id"], user_id))

            team_members = cursor.fetchall()
            can_cover = False

            for member in team_members:
                member_id = member["id"]

                # Member leave overlap
                cursor.execute("""
                    SELECT COUNT(*) as leave_count FROM leave_requests
                    WHERE user_id = ?
                    AND status = 'approved'
                    AND start_date <= ?
                    AND end_date >= ?
                """, (member_id, end_date, start_date))

                member_leave = cursor.fetchone()["leave_count"]

                # Member allocation
                cursor.execute("""
                    SELECT SUM(allocation_percentage) as total_allocation
                    FROM project_assignments
                    WHERE user_id = ?
                    AND start_date <= ?
                    AND end_date >= ?
                """, (member_id, end_date, start_date))

                result = cursor.fetchone()
                allocation = result["total_allocation"] or 0
                availability = max(0, 100 - allocation)

                if availability > 30 and member_leave == 0:
                    can_cover = True
                    break

            # ----------------------------
            # Rule 4: Low Risk Leave
            # ----------------------------
            if days_count <= 3 and total_allocation < 80 and can_cover:
                conn.close()
                return {
                    "approved": True,
                    "message": "Auto-approved: Short leave with low workload and team coverage available.",
                    "reason": "low_risk"
                }

            # ----------------------------
            # Rule 5: Leave History
            # ----------------------------
            cursor.execute("""
                SELECT SUM(days_count) as total_days FROM leave_history
                WHERE user_id = ?
                AND start_date >= date('now', '-90 days')
            """, (user_id,))

            recent_leave = cursor.fetchone()
            recent_leave_days = recent_leave["total_days"] or 0

            if recent_leave_days < 5 and days_count <= 5 and total_allocation < 90:
                conn.close()
                return {
                    "approved": True,
                    "message": "Auto-approved: Reasonable leave request with good leave history.",
                    "reason": "good_history"
                }

            conn.close()

            # Default: Manager review
            return {
                "approved": False,
                "message": "Leave request requires manager approval.",
                "reason": "requires_review"
            }

        except Exception as error:
            print("Error in auto-approval engine:", error)
            return {
                "approved": False,
                "message": "Error evaluating leave request. Requires manager approval.",
                "reason": "error"
            }

    # ----------------------------
    # Get Approval Rules
    # ----------------------------
    def get_rules(self) -> List[Dict[str, Any]]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM approval_rules
                WHERE active = 1
                ORDER BY priority DESC
            """)

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as error:
            print("Error fetching approval rules:", error)
            return []