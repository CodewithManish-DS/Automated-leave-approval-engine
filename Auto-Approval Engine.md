# Auto-Approval Engine – What We Need To Do

## Purpose

The engine decides **whether a leave request can be auto-approved** or **must go to a manager**, using workload, deadlines, team coverage, and leave history.

---

## What It Does Today (Current Rules)

| # | Rule | Logic | Action |
|---|------|--------|--------|
| 1 | **Deadline conflict** | Leave overlaps with a project deadline, or deadline is within 7 days after leave, or high-priority project ends within 14 days | **Reject auto-approval** → manager must approve |
| 2 | **Overload relief** | User total allocation > 100% and leave ≤ 2 days | **Auto-approve** (short relief for overloaded person) |
| 3 | **Team coverage** | Used by Rule 4 | Check if any team member has > 30% availability and no leave in same period |
| 4 | **Low risk** | Leave ≤ 3 days, user allocation < 80%, and team can cover | **Auto-approve** |
| 5 | **Good history** | User took < 5 days leave in last 90 days, leave ≤ 5 days, allocation < 90% | **Auto-approve** |
| – | **Default** | None of the above | **Reject auto-approval** → manager must approve |

Rules are evaluated in this order; first match wins. Any **reject** (e.g. deadline conflict) blocks auto-approval even if later rules would approve.

---

## What We Need To Do (Recommendations)

### 1. **Keep current behavior, document it**
- ✅ Rules 1–5 and default are implemented in `autoApprovalEngine.js`.
- ✅ `evaluate(leaveRequestId, userId, startDate, endDate)` returns `{ approved, message, reason }`.
- Ensure all callers (e.g. leave request submission) use this return value to set status and notifications.

### 2. **Make rules configurable (optional)**
- Table `approval_rules` exists but is not used yet.
- **To do:** Either:
  - **A)** Seed `approval_rules` with the current rules (name, type, conditions, action, priority) and have the engine **read rules from DB** and interpret them, or  
  - **B)** Keep rules in code and use `approval_rules` only for **feature flags** (enable/disable specific rules) and **audit**.

### 3. **Improve robustness and audit**
- **To do:** Log or store each evaluation result (request id, userId, dates, rule that fired, approved/not approved) for compliance and debugging.
- **To do:** Handle edge cases (e.g. no manager, no team members, missing project dates) so the engine never throws; return a safe “requires_review” result.

### 4. **Optional rule ideas**
- **Max consecutive days** (e.g. auto-approve only if leave ≤ 10 days).
- **Leave type** (e.g. auto-approve only for “sick” or “vacation”, never for “unpaid”).
- **Blackout dates** (company-wide no-auto-approve dates).
- **Team headcount** (e.g. if more than X% of team is on leave the same day, no auto-approve).

### 5. **API for managers**
- **To do:** Expose “why was this not auto-approved?” (e.g. “deadline_conflict”, “requires_review”) in the manager dashboard and in impact visualization so managers see the engine’s reason.

---

## Summary

- **Must have:** Keep evaluating every new leave request through the engine; apply the 5 rules + default; set status and notifications based on `approved` and `reason`.
- **Should have:** Use or define `approval_rules` (or at least document why we don’t), add simple audit logging, and surface “reason” to the UI.
- **Could have:** More rules (max days, leave type, blackout dates, team headcount) and full DB-driven rule configuration.

