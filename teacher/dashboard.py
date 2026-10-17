"""Teacher overview and navigation entry point."""
import tkinter as tk

from services import academic
from ui import theme
from ui.charts import create_bar_chart
from ui.widgets import make_button, make_label, make_table


def build_dashboard(parent, session, navigate):
	frame = tk.Frame(parent, bg=theme.BG)
	make_label(frame, f"Good day, {session.username}", size=22, bold=True, color=theme.PRIMARY_DARK).pack(anchor="w")
	make_label(frame, "Teacher overview", color=theme.MUTED).pack(anchor="w", pady=(2, 18))

	result = academic.teacher_dashboard_data(session)
	if not result.ok:
		make_label(frame, result.error or "Could not load dashboard data.", color=theme.ERROR).pack(anchor="w")
		return frame

	students, classes, assignments = result.data["counts"]
	stats = tk.Frame(frame, bg=theme.BG)
	stats.pack(fill="x", pady=(0, 16))
	for title, value in (("Students", students), ("Classes", classes), ("Upcoming assignments", assignments)):
		block = tk.Frame(stats, bg=theme.WHITE, padx=16, pady=12, highlightbackground=theme.BORDER, highlightthickness=1)
		block.pack(side="left", fill="x", expand=True, padx=(0, 10))
		make_label(block, str(value), size=20, bold=True, color=theme.PRIMARY_DARK).pack(anchor="w")
		make_label(block, title, color=theme.MUTED).pack(anchor="w")

	chart = create_bar_chart(frame, ["Students", "Classes", "Assignments"],
							 [students, classes, assignments], "School activity")
	chart.pack(fill="x", pady=(0, 16))

	actions = tk.Frame(frame, bg=theme.BG)
	actions.pack(fill="x", pady=(0, 16))
	for label, page in (("Students", "students"), ("Teachers", "teachers"),
						("Classes", "classes"), ("Subjects & allocation", "subjects")):
		make_button(actions, label, lambda target=page: navigate(target), primary=False).pack(side="left", padx=(0, 8))

	make_label(frame, "Your assignments", size=14, bold=True).pack(anchor="w", pady=(0, 8))
	table, scrollbar = make_table(frame, ("title", "class", "subject", "due_date"))
	table.pack(side="left", fill="both", expand=True)
	scrollbar.pack(side="left", fill="y")
	for row in result.data["assignments"]:
		table.insert("", "end", values=row)
	if not result.data["assignments"]:
		table.insert("", "end", values=("No assignments", "", "", ""))
	return frame
