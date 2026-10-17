# widgets.py - Entry placeholder

# ui/widgets.py
# Reusable widgets used throughout ScholarSync

import tkinter as tk
from tkinter import ttk
from ui import theme


def make_button(parent, text, command, primary=True):
    if primary:
        bg = theme.PRIMARY
        fg = theme.WHITE
    else:
        bg = theme.ACCENT
        fg = theme.PRIMARY_DARK

    button = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=fg,
        activebackground=theme.PRIMARY_DARK,
        activeforeground=theme.WHITE,
        font=theme.BODY_FONT,
        relief="flat",
        cursor="hand2",
        padx=16,
        pady=9,
        bd=0
    )

    return button


def make_label(parent, text, size=None, bold=False, color=None):
    if size is None:
        size = 10

    if color is None:
        color = theme.TEXT

    weight = "bold" if bold else "normal"

    label = tk.Label(
        parent,
        text=text,
        bg=parent.cget("bg"),
        fg=color,
        font=(theme.FONT, size, weight)
    )

    return label


def make_entry(parent, placeholder=None, show=None):
    entry = tk.Entry(
        parent,
        font=theme.BODY_FONT,
        bg=theme.WHITE,
        fg=theme.TEXT,
        insertbackground=theme.TEXT,
        relief="flat",
        highlightthickness=1,
        highlightbackground=theme.BORDER,
        highlightcolor=theme.PRIMARY
    )

    if show:
        entry.config(show=show)

    return entry


def make_table(parent, columns):
    table = ttk.Treeview(
        parent,
        columns=columns,
        show="headings",
        height=10
    )

    for column in columns:
        table.heading(column, text=column.replace("_", " ").title())
        table.column(column, width=140, anchor="w")

    scrollbar = ttk.Scrollbar(
        parent,
        orient="vertical",
        command=table.yview
    )

    table.configure(yscrollcommand=scrollbar.set)

    return table, scrollbar
