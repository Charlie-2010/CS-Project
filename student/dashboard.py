"""Student overview with report-card, attendance, and assignment data."""
import tkinter as tk

from services import academic
from ui import theme
from ui.charts import create_bar_chart
from ui.widgets import make_label, make_table


def build_dashboard(parent, session, navigate=None):
	frame = tk.Frame(parent, bg=theme.BG)
	result = academic.student_dashboard_data(session)
	if not result.ok:
		make_label(frame, result.error or "Could not load dashboard data.", color=theme.ERROR).pack(anchor="w")
		return frame

	profile = result.data["profile"]
	name, class_name = profile[0] + " " + profile[1], profile[2] or "No class assigned"
	make_label(frame, f"Welcome, {name}", size=22, bold=True, color=theme.PRIMARY_DARK).pack(anchor="w")
	make_label(frame, class_name, color=theme.MUTED).pack(anchor="w", pady=(2, 18))

	records = result.data["report_card"]
	chart = create_bar_chart(frame, [row[1] for row in records], [float(row[2]) for row in records], "Latest results")
	chart.pack(fill="x", pady=(0, 16))

	make_label(frame, "Report card", size=14, bold=True).pack(anchor="w", pady=(0, 8))
	table, scrollbar = make_table(frame, ("exam", "subject", "marks", "maximum", "remarks"))
	table.pack(side="left", fill="both", expand=True)
	scrollbar.pack(side="left", fill="y")
	for row in records:
		table.insert("", "end", values=row)
	if not records:
		table.insert("", "end", values=("No results yet", "", "", "", ""))

	lower = tk.Frame(frame, bg=theme.BG)
	lower.pack(fill="x", pady=(16, 0))
	attendance = result.data["attendance"] or (0, 0, 0)
	make_label(lower, f"Attendance: {attendance[1] or 0} present out of {attendance[0]} recorded days",
			   bold=True).pack(anchor="w")
	make_label(lower, "Upcoming assignments", size=14, bold=True).pack(anchor="w", pady=(12, 5))
	for title, subject, due_date, points in result.data["assignments"]:
		make_label(lower, f"{title}  |  {subject}  |  due {due_date}  |  {points} points").pack(anchor="w", pady=2)
	if not result.data["assignments"]:
		make_label(lower, "No upcoming assignments", color=theme.MUTED).pack(anchor="w")
	return frame
