"""Teacher class-management screen."""
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
    make_label(header, "Class management", size=18, bold=True, color=theme.PRIMARY_DARK).pack(side="left")

    form = tk.Frame(frame, bg=theme.WHITE, padx=14, pady=12, highlightbackground=theme.BORDER, highlightthickness=1)
    form.pack(fill="x", pady=(0, 12))
    make_label(form, "Class name").grid(row=0, column=0, sticky="w")
    class_name = tk.Entry(form, font=theme.BODY_FONT, width=24)
    class_name.grid(row=1, column=0, sticky="ew", padx=(0, 12), pady=(3, 8))
    make_label(form, "Room").grid(row=0, column=1, sticky="w")
    room_number = tk.Entry(form, font=theme.BODY_FONT, width=16)
    room_number.grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=(3, 8))
    make_label(form, "Class teacher").grid(row=0, column=2, sticky="w")
    teachers_result = academic.list_teachers(session)
    teachers = teachers_result.data if teachers_result.ok else []
    teacher_labels = {"Unassigned": None}
    teacher_labels.update({f"{row[1]} {row[2]} (#{row[0]})": row[0] for row in teachers})
    teacher_choice = ttk.Combobox(form, state="readonly", values=list(teacher_labels))
    teacher_choice.grid(row=1, column=2, sticky="ew", padx=(0, 12), pady=(3, 8))
    teacher_choice.set("Unassigned")
    for column in range(3):
        form.grid_columnconfigure(column, weight=1)

    status = make_label(frame, "", color=theme.ERROR)
    status.pack(anchor="w", pady=(0, 6))
    table, scrollbar = make_table(frame, ("id", "name", "room", "teacher"))
    table.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="left", fill="y")

    def refresh():
        for item in table.get_children():
            table.delete(item)
        result = academic.list_class_details(session)
        if not result.ok:
            status.config(text=result.error or "Could not load classes.")
            return
        for class_row in result.data:
            table.insert("", "end", values=(class_row[0], class_row[1], class_row[2] or "", " ".join(class_row[3:5]).strip()))

    def add_class():
        result = academic.create_class(session, {
            "class_name": class_name.get(),
            "room_number": room_number.get() or None,
            "class_teacher_id": teacher_labels.get(teacher_choice.get()),
        })
        if result.ok:
            class_name.delete(0, "end")
            room_number.delete(0, "end")
            status.config(text="")
            refresh()
        else:
            status.config(text="; ".join(result.field_errors.values()) or result.error or "Could not create class.")

    def populate_form(_event=None):
        selected = table.selection()
        if not selected:
            return
        values = table.item(selected[0], "values")
        class_name.delete(0, "end")
        class_name.insert(0, values[1])
        room_number.delete(0, "end")
        room_number.insert(0, values[2])
        teacher_label = next((label for label in teacher_labels if label.startswith(values[3] + " (#")), "Unassigned")
        teacher_choice.set(teacher_label)

    def update_class():
        selected = table.selection()
        if not selected:
            messagebox.showwarning("Select a class", "Choose a class row first.", parent=frame)
            return
        class_id = int(table.item(selected[0], "values")[0])
        result = academic.update_class(session, class_id, {
            "class_name": class_name.get(),
            "room_number": room_number.get() or None,
            "class_teacher_id": teacher_labels.get(teacher_choice.get()),
        })
        if result.ok:
            status.config(text="")
            refresh()
        else:
            status.config(text="; ".join(result.field_errors.values()) or result.error or "Could not update class.")

    def delete_class():
        selected = table.selection()
        if not selected:
            messagebox.showwarning("Select a class", "Choose a class row first.", parent=frame)
            return
        class_id = int(table.item(selected[0], "values")[0])
        impact = academic.class_delete_impact(session, class_id)
        if not impact.ok:
            status.config(text=impact.error or "Could not calculate delete impact.")
            return
        counts = impact.data
        prompt = (f"Delete this class? {counts['students_reassigned']} students will become unassigned; "
                  f"{counts['exam_papers']} papers, {counts['assignments']} assignments, and "
                  f"{counts['attendance']} attendance rows will be removed.")
        if messagebox.askyesno("Confirm class deletion", prompt, parent=frame):
            result = academic.delete_class(session, class_id)
            if result.ok:
                refresh()
            else:
                status.config(text=result.error or "Could not delete class.")

    actions = tk.Frame(form, bg=theme.WHITE)
    actions.grid(row=2, column=0, columnspan=3, sticky="w")
    make_button(actions, "Add class", add_class).pack(side="left", padx=(0, 8))
    make_button(actions, "Update selected", update_class, primary=False).pack(side="left", padx=(0, 8))
    make_button(actions, "Delete selected", delete_class, primary=False).pack(side="left")
    table.bind("<<TreeviewSelect>>", populate_form)
    refresh()
    return frame