"""Teacher account and profile CRUD screen."""
import tkinter as tk
from tkinter import messagebox

from services import academic
from ui import theme
from ui.widgets import make_button, make_label, make_table


def build_page(parent, session, on_back):
    frame = tk.Frame(parent, bg=theme.BG, padx=20, pady=16)
    header = tk.Frame(frame, bg=theme.BG)
    header.pack(fill="x", pady=(0, 14))
    make_button(header, "Back", on_back, primary=False).pack(side="left", padx=(0, 12))
    make_label(header, "Teacher management", size=18, bold=True, color=theme.PRIMARY_DARK).pack(side="left")

    form = tk.Frame(frame, bg=theme.WHITE, padx=14, pady=12, highlightbackground=theme.BORDER, highlightthickness=1)
    form.pack(fill="x", pady=(0, 12))
    entries = {}
    fields = ("first_name", "last_name", "email", "phone", "username", "password")
    for index, field_name in enumerate(fields):
        row, column = divmod(index, 3)
        make_label(form, field_name.replace("_", " ").title()).grid(row=row * 2, column=column, sticky="w", padx=(0, 10))
        entry = tk.Entry(form, font=theme.BODY_FONT, show="*" if field_name == "password" else "")
        entry.grid(row=row * 2 + 1, column=column, sticky="ew", padx=(0, 10), pady=(3, 8))
        entries[field_name] = entry
    for column in range(3):
        form.grid_columnconfigure(column, weight=1)

    status = make_label(frame, "", color=theme.ERROR)
    status.pack(anchor="w", pady=(0, 6))
    table, scrollbar = make_table(frame, ("id", "first", "last", "email", "phone", "username"))
    table.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="left", fill="y")

    def refresh():
        for item in table.get_children():
            table.delete(item)
        result = academic.list_teachers(session)
        if not result.ok:
            status.config(text=result.error or "Could not load teachers.")
            return
        for row in result.data:
            table.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4] or "", row[5]))

    def populate_form(_event=None):
        selected = table.selection()
        if not selected:
            return
        values = table.item(selected[0], "values")
        for field_name, value in zip(("first_name", "last_name", "email", "phone", "username"),
                                     (values[1], values[2], values[3], values[4], values[5])):
            entries[field_name].delete(0, "end")
            entries[field_name].insert(0, str(value))
        entries["password"].delete(0, "end")

    def add_teacher():
        result = academic.create_teacher(session, {name: entry.get() for name, entry in entries.items()})
        if result.ok:
            for entry in entries.values():
                entry.delete(0, "end")
            status.config(text="")
            refresh()
        else:
            details = "; ".join(result.field_errors.values())
            status.config(text=details or result.error or "Could not create teacher.")

    def update_teacher():
        selected = table.selection()
        if not selected:
            messagebox.showwarning("Select a teacher", "Choose a teacher row first.", parent=frame)
            return
        teacher_id = int(table.item(selected[0], "values")[0])
        result = academic.update_teacher(session, teacher_id, {
            name: entries[name].get() for name in ("first_name", "last_name", "email", "phone")
        })
        if result.ok:
            status.config(text="")
            refresh()
        else:
            status.config(text="; ".join(result.field_errors.values()) or result.error or "Could not update teacher.")

    def delete_teacher():
        selected = table.selection()
        if not selected:
            messagebox.showwarning("Select a teacher", "Choose a teacher row first.", parent=frame)
            return
        teacher_id = int(table.item(selected[0], "values")[0])
        impact = academic.teacher_delete_impact(session, teacher_id)
        if not impact.ok:
            status.config(text=impact.error or "Could not calculate delete impact.")
            return
        counts = impact.data
        prompt = (f"Delete teacher login? References: {counts['classes']} classes, "
                  f"{counts['allocations']} subject allocations, {counts['assignments']} assignments.")
        if not messagebox.askyesno("Confirm teacher deletion", prompt, parent=frame):
            return
        result = academic.delete_teacher(session, teacher_id)
        if result.ok:
            status.config(text="")
            refresh()
        else:
            status.config(text=result.error or "Could not delete teacher.")

    actions = tk.Frame(form, bg=theme.WHITE)
    actions.grid(row=4, column=0, columnspan=3, sticky="w")
    make_button(actions, "Add teacher", add_teacher).pack(side="left", padx=(0, 8))
    make_button(actions, "Update selected", update_teacher, primary=False).pack(side="left", padx=(0, 8))
    make_button(actions, "Delete selected", delete_teacher, primary=False).pack(side="left")
    table.bind("<<TreeviewSelect>>", populate_form)
    refresh()
    return frame