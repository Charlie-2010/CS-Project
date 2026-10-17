# app.py - Entry placeholder

import tkinter as tk
from tkinter import messagebox
from pathlib import Path


class ScholarSync:
    def __init__(self, root):
        self.root = root
        self.root.title("ScholarSync")
        self.root.geometry("900x580")
        self.root.minsize(750, 500)

        # Colours
        self.bg = "#F3F7FC"
        self.blue = "#2463A6"
        self.dark_blue = "#174778"
        self.light_blue = "#DCEBFA"
        self.text = "#1D3553"
        self.muted = "#6B7F99"
        self.border = "#D8E4F0"
        self.white = "#FFFFFF"

        self.root.configure(bg=self.bg)

        # Load the PNG logo if it exists
        self.logo_image = None
        logo_path = Path(__file__).parent / "assets" / "logo.png"

        if logo_path.exists():
            try:
                self.logo_image = tk.PhotoImage(file=str(logo_path))

                # Resize large logos to fit the header
                if self.logo_image.width() > 64:
                    self.logo_image = self.logo_image.subsample(
                        max(1, self.logo_image.width() // 48),
                        max(1, self.logo_image.height() // 48)
                    )
            except tk.TclError:
                messagebox.showwarning(
                    "Logo",
                    "The logo could not be loaded. Please check the PNG file."
                )

        self.home_page()

    def clear_page(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def home_page(self):
        self.clear_page()

        # Header
        header = tk.Frame(self.root, bg=self.bg, padx=35, pady=22)
        header.pack(fill="x")

        if self.logo_image:
            tk.Label(
                header,
                image=self.logo_image,
                bg=self.bg
            ).pack(side="left", padx=(0, 12))
        else:
            tk.Label(
                header,
                text="SS",
                font=("Segoe UI", 16, "bold"),
                bg=self.blue,
                fg=self.white,
                width=3,
                pady=5
            ).pack(side="left", padx=(0, 12))

        tk.Label(
            header,
            text="ScholarSync",
            font=("Segoe UI", 19, "bold"),
            bg=self.bg,
            fg=self.dark_blue
        ).pack(side="left")

        tk.Frame(
            self.root,
            bg=self.border,
            height=1
        ).pack(fill="x", padx=35)

        # Main section
        main = tk.Frame(
            self.root,
            bg=self.bg,
            padx=45,
            pady=40
        )
        main.pack(fill="both", expand=True)

        tk.Label(
            main,
            text="Welcome to ScholarSync",
            font=("Segoe UI", 26, "bold"),
            bg=self.bg,
            fg=self.dark_blue
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            main,
            text="Choose your portal to continue.",
            font=("Segoe UI", 11),
            bg=self.bg,
            fg=self.muted
        ).pack(anchor="w", pady=(0, 30))

        portals = tk.Frame(main, bg=self.bg)
        portals.pack(fill="both", expand=True)

        self.portal_card(
            portals,
            "Student",
            "View marks and exam results.",
            self.blue,
            self.white,
            lambda: self.login_page("Student")
        ).pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 10)
        )

        self.portal_card(
            portals,
            "Teacher",
            "Manage students and results.",
            self.light_blue,
            self.dark_blue,
            lambda: self.login_page("Teacher")
        ).pack(
            side="left",
            fill="both",
            expand=True,
            padx=(10, 0)
        )

        tk.Label(
            main,
            text="Student Performance Management System",
            font=("Segoe UI", 9),
            bg=self.bg,
            fg=self.muted
        ).pack(anchor="w", side="bottom", pady=(18, 0))

    def portal_card(
        self, parent, title, description,
        card_bg, text_color, command
    ):
        card = tk.Frame(
            parent,
            bg=card_bg,
            padx=25,
            pady=25,
            highlightbackground=self.border,
            highlightthickness=1
        )

        tk.Label(
            card,
            text=title,
            font=("Segoe UI", 20, "bold"),
            bg=card_bg,
            fg=text_color
        ).pack(anchor="w", pady=(10, 15))

        tk.Label(
            card,
            text=description,
            font=("Segoe UI", 10),
            bg=card_bg,
            fg=text_color,
            wraplength=260,
            justify="left"
        ).pack(anchor="w", pady=(0, 25))

        tk.Button(
            card,
            text="Continue",
            command=command,
            font=("Segoe UI", 10, "bold"),
            bg=self.light_blue if card_bg == self.blue else self.blue,
            fg=self.dark_blue if card_bg == self.blue else self.white,
            activebackground=self.border,
            activeforeground=self.dark_blue,
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=10
        ).pack(anchor="w")

        return card

    def login_page(self, role):
        self.clear_page()

        tk.Button(
            self.root,
            text="< Back",
            command=self.home_page,
            font=("Segoe UI", 10),
            bg=self.bg,
            fg=self.blue,
            activebackground=self.bg,
            relief="flat",
            cursor="hand2"
        ).pack(anchor="nw", padx=25, pady=20)

        card = tk.Frame(
            self.root,
            bg=self.white,
            padx=35,
            pady=30,
            highlightbackground=self.border,
            highlightthickness=1
        )
        card.place(relx=0.5, rely=0.53, anchor="center")

        tk.Label(
            card,
            text=role + " Login",
            font=("Segoe UI", 24, "bold"),
            bg=self.white,
            fg=self.dark_blue
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            card,
            text="Enter your account details.",
            font=("Segoe UI", 10),
            bg=self.white,
            fg=self.muted
        ).pack(anchor="w", pady=(0, 24))

        tk.Label(
            card,
            text="Username",
            font=("Segoe UI", 10),
            bg=self.white,
            fg=self.text
        ).pack(anchor="w")

        username = tk.Entry(
            card,
            font=("Segoe UI", 11),
            width=30,
            relief="solid",
            bd=1
        )
        username.pack(fill="x", ipady=7, pady=(6, 16))

        tk.Label(
            card,
            text="Password",
            font=("Segoe UI", 10),
            bg=self.white,
            fg=self.text
        ).pack(anchor="w")

        password = tk.Entry(
            card,
            font=("Segoe UI", 11),
            show="*",
            relief="solid",
            bd=1
        )
        password.pack(fill="x", ipady=7, pady=(6, 22))

        tk.Button(
            card,
            text="Sign in",
            command=lambda: self.login(
                role, username.get(), password.get()
            ),
            font=("Segoe UI", 10, "bold"),
            bg=self.blue,
            fg=self.white,
            activebackground=self.dark_blue,
            activeforeground=self.white,
            relief="flat",
            cursor="hand2",
            pady=10
        ).pack(fill="x")

        username.focus_set()

    def login(self, role, username, password):
        if not username.strip() or not password:
            messagebox.showwarning(
                "Missing details",
                "Please enter your username and password."
            )
            return

        messagebox.showinfo(
            "Database connection",
            role + " login has not been connected to MySQL yet."
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = ScholarSync(root)
    root.mainloop()
