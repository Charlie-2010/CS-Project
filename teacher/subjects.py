"""Teacher roster, subject catalogue, and class-allocation screen."""
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
	make_label(header, "Teachers, subjects & class mapping", size=18, bold=True,
			   color=theme.PRIMARY_DARK).pack(side="left")

	teachers_result = academic.list_teachers(session)
	classes_result = academic.list_classes(session)
	subjects_result = academic.list_subjects(session)
	teachers = teachers_result.data if teachers_result.ok else []
	classes = classes_result.data if classes_result.ok else []
	subjects = subjects_result.data if subjects_result.ok else []
	teacher_options = {f"{row[1]} {row[2]} (#{row[0]})": row[0] for row in teachers}
	class_options = {f"{row[1]} (#{row[0]})": row[0] for row in classes}
	subject_options = {f"{row[1]} ({row[2]})": row[0] for row in subjects}

	allocation_form = tk.Frame(frame, bg=theme.WHITE, padx=14, pady=12,
							   highlightbackground=theme.BORDER, highlightthickness=1)
	allocation_form.pack(fill="x", pady=(0, 12))
	choices = []
	for column, (label, options) in enumerate((
		("Teacher", teacher_options), ("Class", class_options), ("Subject", subject_options)
	)):
		make_label(allocation_form, label).grid(row=0, column=column, sticky="w")
		choice = ttk.Combobox(allocation_form, state="readonly", values=list(options))
		choice.grid(row=1, column=column, sticky="ew", padx=(0, 12), pady=(3, 8))
		if options:
			choice.current(0)
		choices.append(choice)
		allocation_form.grid_columnconfigure(column, weight=1)

	status = make_label(frame, "", color=theme.ERROR)
	status.pack(anchor="w", pady=(0, 6))
	allocations, allocation_scrollbar = make_table(frame, ("id", "teacher", "class", "subject"))
	allocations.pack(fill="both", expand=True)
	allocation_scrollbar.pack(side="right", fill="y")
	allocation_rows = []

	def refresh_allocations():
		nonlocal allocation_rows
		for item in allocations.get_children():
			allocations.delete(item)
		result = academic.list_allocations(session)
		if not result.ok:
			status.config(text=result.error or "Could not load allocations.")
			return
		allocation_rows = result.data
		for row in allocation_rows:
			allocations.insert("", "end", values=(row[0], f"{row[2]} {row[3]}", row[5], row[7]))

	def add_allocation():
		selected = [choice.get() for choice in choices]
		lookups = (teacher_options, class_options, subject_options)
		if any(value not in lookup for value, lookup in zip(selected, lookups)):
			status.config(text="Select a teacher, class, and subject.")
			return
		result = academic.allocate_subject(session, *(lookup[value] for value, lookup in zip(selected, lookups)))
		if result.ok:
			status.config(text="")
			refresh_allocations()
		else:
			status.config(text=result.error or "Could not create allocation.")

	def delete_allocation():
		selected = allocations.selection()
		if not selected:
			messagebox.showwarning("Select an allocation", "Choose an allocation row first.", parent=frame)
			return
		allocation_id = int(allocations.item(selected[0], "values")[0])
		if messagebox.askyesno("Remove allocation", "Remove this teacher-to-class subject mapping?", parent=frame):
			result = academic.delete_allocation(session, allocation_id)
			if result.ok:
				refresh_allocations()
			else:
				status.config(text=result.error or "Could not remove allocation.")

	def populate_allocation_form(_event=None):
		selected = allocations.selection()
		if not selected:
			return
		allocation_id = int(allocations.item(selected[0], "values")[0])
		row = next((item for item in allocation_rows if item[0] == allocation_id), None)
		if row is None:
			return
		choices[0].set(next((label for label, identifier in teacher_options.items() if identifier == row[1]), ""))
		choices[1].set(next((label for label, identifier in class_options.items() if identifier == row[4]), ""))
		choices[2].set(next((label for label, identifier in subject_options.items() if identifier == row[6]), ""))

	def update_allocation():
		selected = [choice.get() for choice in choices]
		lookups = (teacher_options, class_options, subject_options)
		if any(value not in lookup for value, lookup in zip(selected, lookups)):
			status.config(text="Select a teacher, class, and subject.")
			return
		allocation_id = int(allocations.item(allocations.selection()[0], "values")[0]) if allocations.selection() else None
		if allocation_id is None:
			status.config(text="Select an allocation first.")
			return
		result = academic.update_allocation(session, allocation_id,
			*(lookup[value] for value, lookup in zip(selected, lookups)))
		if result.ok:
			status.config(text="")
			refresh_allocations()
		else:
			status.config(text=result.error or "Could not update allocation.")

	make_button(allocation_form, "Allocate", add_allocation).grid(row=1, column=3, sticky="ew")
	make_button(allocation_form, "Remove selected", delete_allocation, primary=False).grid(row=1, column=4, sticky="ew", padx=(8, 0))
	make_button(allocation_form, "Update selected", update_allocation, primary=False).grid(row=1, column=5, sticky="ew", padx=(8, 0))
	allocations.bind("<<TreeviewSelect>>", populate_allocation_form)

	catalogue = tk.Frame(frame, bg=theme.BG)
	catalogue.pack(fill="x", pady=(14, 0))
	roster = tk.Frame(catalogue, bg=theme.WHITE, padx=12, pady=10,
					  highlightbackground=theme.BORDER, highlightthickness=1)
	roster.pack(side="left", fill="both", expand=True, padx=(0, 8))
	make_label(roster, "Teachers", size=13, bold=True).pack(anchor="w", pady=(0, 6))
	for row in teachers:
		make_label(roster, f"{row[1]} {row[2]}").pack(anchor="w", pady=1)

	subjects_panel = tk.Frame(catalogue, bg=theme.WHITE, padx=12, pady=10,
							  highlightbackground=theme.BORDER, highlightthickness=1)
	subjects_panel.pack(side="left", fill="both", expand=True, padx=(8, 0))
	make_label(subjects_panel, "Subject catalogue", size=13, bold=True).pack(anchor="w")
	make_label(subjects_panel, "Subject name").pack(anchor="w", pady=(6, 0))
	subject_name = tk.Entry(subjects_panel, font=theme.BODY_FONT)
	make_label(subjects_panel, "Subject code").pack(anchor="w", pady=(4, 0))
	subject_code = tk.Entry(subjects_panel, font=theme.BODY_FONT)
	subject_name.pack(fill="x", pady=(3, 4))
	subject_code.pack(fill="x", pady=(3, 4))
	subject_list = tk.Listbox(subjects_panel, height=5, font=theme.BODY_FONT, relief="flat")
	subject_list.pack(fill="both", expand=True, pady=(7, 4))
	subject_rows = []

	def refresh_subjects():
		nonlocal subject_rows
		current = academic.list_subjects(session)
		subject_list.delete(0, "end")
		if current.ok:
			subject_rows = current.data
			for row in subject_rows:
				subject_list.insert("end", f"{row[1]}  ·  {row[2]}")
			subject_options.clear()
			subject_options.update({f"{row[1]} ({row[2]})": row[0] for row in subject_rows})
			choices[2].configure(values=list(subject_options))
			if subject_options and choices[2].get() not in subject_options:
				choices[2].current(0)

	def add_subject():
		result = academic.create_subject(session, {"subject_name": subject_name.get(), "subject_code": subject_code.get()})
		if result.ok:
			subject_name.delete(0, "end")
			subject_code.delete(0, "end")
			refresh_subjects()
			status.config(text="Subject added.", fg=theme.MUTED)
		else:
			status.config(text="; ".join(result.field_errors.values()) or result.error or "Could not add subject.")

	def populate_subject_form(_event=None):
		selection = subject_list.curselection()
		if not selection:
			return
		row = subject_rows[selection[0]]
		subject_name.delete(0, "end")
		subject_name.insert(0, row[1])
		subject_code.delete(0, "end")
		subject_code.insert(0, row[2])

	def update_subject():
		selection = subject_list.curselection()
		if not selection:
			status.config(text="Select a subject first.")
			return
		subject_id = subject_rows[selection[0]][0]
		result = academic.update_subject(session, subject_id,
			{"subject_name": subject_name.get(), "subject_code": subject_code.get()})
		if result.ok:
			refresh_subjects()
			refresh_allocations()
			status.config(text="Subject updated.", fg=theme.MUTED)
		else:
			status.config(text="; ".join(result.field_errors.values()) or result.error or "Could not update subject.")

	def delete_subject():
		selection = subject_list.curselection()
		if not selection:
			status.config(text="Select a subject first.")
			return
		subject_id = subject_rows[selection[0]][0]
		impact = academic.subject_delete_impact(session, subject_id)
		if not impact.ok:
			status.config(text=impact.error or "Could not calculate delete impact.")
			return
		counts = impact.data
		prompt = (f"Delete this subject? This removes {counts['allocations']} allocations, {counts['papers']} papers, "
			f"{counts['results']} results, and {counts['assignments']} assignments.")
		if messagebox.askyesno("Confirm subject deletion", prompt, parent=frame):
			result = academic.delete_subject(session, subject_id)
			if result.ok:
				refresh_subjects()
				refresh_allocations()
				status.config(text="Subject deleted.", fg=theme.MUTED)
			else:
				status.config(text=result.error or "Could not delete subject.")

	make_button(subjects_panel, "Add subject", add_subject).pack(anchor="w")
	make_button(subjects_panel, "Update selected", update_subject, primary=False).pack(anchor="w", pady=(4, 0))
	make_button(subjects_panel, "Delete selected", delete_subject, primary=False).pack(anchor="w", pady=(4, 0))
	subject_list.bind("<<ListboxSelect>>", populate_subject_form)
	refresh_allocations()
	refresh_subjects()
	return frame
