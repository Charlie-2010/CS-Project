"""Teacher student-management screen backed exclusively by academic services."""
import tkinter as tk
from tkinter import messagebox, ttk

from services import academic
from ui import theme
from ui.widgets import make_button, make_label, make_table


def build_page(parent, session, on_back):
	frame = tk.Frame(parent, bg=theme.BG, padx=20, pady=16)
	header = tk.Frame(frame, bg=theme.BG)
	header.pack(fill="x", pady=(0, 14))
	make_button(header, "Back", on_back, primary=False).pack(side="left", padx=(0, 12))
	make_label(header, "Student management", size=18, bold=True, color=theme.PRIMARY_DARK).pack(side="left")

	form = tk.Frame(frame, bg=theme.WHITE, padx=14, pady=12, highlightbackground=theme.BORDER, highlightthickness=1)
	form.pack(fill="x", pady=(0, 12))
	fields = ("roll_number", "first_name", "last_name", "email", "date_of_birth", "username", "password")
	entries = {}
	for index, field_name in enumerate(fields):
		row, column = divmod(index, 4)
		make_label(form, field_name.replace("_", " ").title()).grid(row=row * 2, column=column, sticky="w", padx=(0, 10))
		entry = tk.Entry(form, font=theme.BODY_FONT, width=22, show="*" if field_name == "password" else "")
		entry.grid(row=row * 2 + 1, column=column, sticky="ew", padx=(0, 10), pady=(3, 9))
		entries[field_name] = entry
	make_label(form, "Class").grid(row=2, column=3, sticky="w")
	classes_result = academic.list_classes(session)
	classes = classes_result.data if classes_result.ok else []
	class_labels = {"Unassigned": None}
	class_labels.update({row[1]: row[0] for row in classes})
	class_choice = ttk.Combobox(form, state="readonly", values=list(class_labels))
	class_choice.grid(row=3, column=3, sticky="ew", padx=(0, 10), pady=(3, 9))
	class_choice.set("Unassigned")
	for column in range(4):
		form.grid_columnconfigure(column, weight=1)

	status = make_label(frame, "", color=theme.ERROR)
	status.pack(anchor="w", pady=(0, 6))
	table, scrollbar = make_table(frame, ("id", "roll", "first", "last", "email", "date_of_birth", "class", "username"))
	table.pack(side="left", fill="both", expand=True)
	scrollbar.pack(side="left", fill="y")

	def refresh():
		for item in table.get_children():
			table.delete(item)
		result = academic.list_students(session)
		if not result.ok:
			status.config(text=result.error or "Could not load students.")
			return
		for student in result.data:
			table.insert("", "end", values=(student[0], student[1], student[2], student[3], student[4],
											 student[5], student[7] or "Unassigned", student[8]))
		status.config(text="")

	def populate_form(_event=None):
		selected = table.selection()
		if not selected:
			return
		values = table.item(selected[0], "values")
		for field_name, value in zip(("roll_number", "first_name", "last_name", "email", "date_of_birth", "username"),
									 (values[1], values[2], values[3], values[4], values[5], values[7])):
			entries[field_name].delete(0, "end")
			entries[field_name].insert(0, str(value))
		entries["password"].delete(0, "end")
		class_choice.set(values[6] if values[6] in class_labels else "Unassigned")

	def selected_id():
		selected = table.selection()
		if not selected:
			messagebox.showwarning("Select a student", "Choose a student row first.", parent=frame)
			return None
		return int(table.item(selected[0], "values")[0])

	def form_data(include_credentials):
		data = {field_name: entry.get().strip() for field_name, entry in entries.items()}
		data["class_id"] = class_labels.get(class_choice.get())
		if not include_credentials:
			data.pop("username")
			data.pop("password")
		return data

	def show_result(result):
		if result.ok:
			status.config(text="")
			refresh()
			return True
		details = "; ".join(f"{key}: {value}" for key, value in result.field_errors.items())
		status.config(text=details or result.error or "Operation failed.")
		return False

	def add_student():
		if show_result(academic.create_student(session, form_data(True))):
			for entry in entries.values():
				entry.delete(0, "end")
			class_choice.set("Unassigned")

	def update_student():
		student_id = selected_id()
		if student_id is not None:
			show_result(academic.update_student(session, student_id, form_data(False)))

	def delete_student():
		student_id = selected_id()
		if student_id is None:
			return
		impact = academic.student_delete_impact(session, student_id)
		if not impact.ok:
			status.config(text=impact.error or "Could not calculate delete impact.")
			return
		counts = impact.data
		prompt = (f"Delete this student and login account? This removes {counts['exam_results']} results "
				  f"and {counts['attendance']} attendance records.")
		if messagebox.askyesno("Confirm student deletion", prompt, parent=frame):
			show_result(academic.delete_student(session, student_id))

	table.bind("<<TreeviewSelect>>", populate_form)

	buttons = tk.Frame(form, bg=theme.WHITE)
	buttons.grid(row=4, column=0, columnspan=4, sticky="w")
	make_button(buttons, "Add student", add_student).pack(side="left", padx=(0, 8))
	make_button(buttons, "Update selected", update_student, primary=False).pack(side="left", padx=(0, 8))
	make_button(buttons, "Delete selected", delete_student, primary=False).pack(side="left")
	refresh()
	return frame
