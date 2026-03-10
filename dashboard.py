import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import ImageGrab, ImageFilter, ImageTk

from config import CSV_PATH
from shortlist import STRATEGIES, SCORE_HINTS, build_shortlist, best_buy


class ScoutingDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Football Analytics Dashboard")
        self.root.state("zoomed")

        self.current_mode       = "graph"
        self.is_updating        = False
        self.is_fetching_shortlist = False

        self._build_nav()
        self._build_loading_overlay()

        self.load_data_and_refresh()

    # ------------------------------------------------------------------ #
    #  Layout builders                                                      #
    # ------------------------------------------------------------------ #

    def _build_nav(self):
        self.nav_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        self.nav_frame.pack(side="top", fill="x")

        style = ttk.Style()
        style.configure("TButton", font=("TkDefaultFont", 11))

        self.btn_graph_mode = ttk.Button(self.nav_frame, text="Graph Mode",  command=self.set_graph_mode)
        self.btn_stats_mode = ttk.Button(self.nav_frame, text="Stats Mode",  command=self.set_stats_mode)
        self.btn_shortlist  = ttk.Button(self.nav_frame, text="Shortlist",   command=self.set_shortlist_mode)
        self.btn_update     = ttk.Button(self.nav_frame, text="Update Data", command=self.start_update_thread)

        self.btn_graph_mode.pack(side="left",  padx=10, pady=15)
        self.btn_stats_mode.pack(side="left",  padx=10, pady=15)
        self.btn_shortlist.pack( side="left",  padx=10, pady=15)
        self.btn_update.pack(    side="right", padx=20, pady=15)

        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True)

    def _build_loading_overlay(self):
        self.loading_frame    = tk.Frame(self.root)
        self.loading_bg_label = tk.Label(self.loading_frame)
        self.loading_bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.loading_label = tk.Label(
            self.loading_frame,
            text="Updating Data from Sofascore...\nPlease Wait",
            fg="black", bg="white",
            font=("Helvetica", 18, "bold"),
            padx=20, pady=20, relief="solid", bd=2,
        )
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")

    # ------------------------------------------------------------------ #
    #  Data loading                                                         #
    # ------------------------------------------------------------------ #

    def load_data_and_refresh(self):
        try:
            self.df = pd.read_csv(CSV_PATH)
            if self.current_mode == "graph":
                self.show_graph_mode()
            elif self.current_mode == "stats":
                self.show_stats_mode()
        except FileNotFoundError:
            self._clear_container()
            tk.Label(
                self.container,
                text="No data found. Please click 'Update Data'.",
                font=("Helvetica", 14),
            ).pack(pady=50)

    # ------------------------------------------------------------------ #
    #  Update (scraper)                                                     #
    # ------------------------------------------------------------------ #

    def start_update_thread(self):
        if self.is_updating:
            return
        self.is_updating = True
        self._toggle_nav("disabled")
        self.loading_label.config(text="Updating Data from Sofascore...\nPlease Wait")
        self._show_loading_overlay()
        threading.Thread(target=self._run_scraper).start()

    def _run_scraper(self):
        try:
            subprocess.run([sys.executable, "new\\scraper.py"], check=True)
            self.root.after(0, self._finish_update, True)
        except Exception as e:
            self.root.after(0, self._finish_update, False, str(e))

    def _finish_update(self, success, error_msg=""):
        self.is_updating = False
        self._hide_loading_overlay()
        self._toggle_nav("normal")
        if success:
            messagebox.showinfo("Success", "Data updated successfully!")
            self.load_data_and_refresh()
        else:
            messagebox.showerror("Error", f"Failed to update data: {error_msg}")

    # ------------------------------------------------------------------ #
    #  Shortlist                                                            #
    # ------------------------------------------------------------------ #

    def set_shortlist_mode(self):
        if self.is_fetching_shortlist:
            return
        self.current_mode = "shortlist"
        self.is_fetching_shortlist = True
        self._toggle_nav("disabled")
        self.loading_label.config(text="Building Shortlist...\nFetching Player Data\nPlease Wait")
        self._show_loading_overlay()
        threading.Thread(target=self._fetch_shortlist).start()

    def _fetch_shortlist(self):
        try:
            shortlist = build_shortlist(self.df)
            self.root.after(0, self._finish_shortlist, shortlist)
        except Exception as e:
            self.root.after(0, self._finish_shortlist_error, str(e))

    def _finish_shortlist(self, shortlist):
        self.is_fetching_shortlist = False
        self._hide_loading_overlay()
        self._toggle_nav("normal")
        self._show_shortlist(shortlist)

    def _finish_shortlist_error(self, error_msg):
        self.is_fetching_shortlist = False
        self._hide_loading_overlay()
        self._toggle_nav("normal")
        messagebox.showerror("Error", f"Failed to fetch shortlist: {error_msg}")

    def _show_shortlist(self, shortlist):
        self._clear_container()
        notebook = ttk.Notebook(self.container)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        for strategy_name, strategy in STRATEGIES.items():
            frame   = ttk.Frame(notebook)
            notebook.add(frame, text=strategy_name)
            players = shortlist.get(strategy_name, [])

            tk.Label(
                frame,
                text="All shortlisted players are younger than 30 and have a market value below 15M €.",
                font=("Helvetica", 10, "bold"), fg="#1a5276", bg="#d6eaf8",
                relief="ridge", bd=1, padx=8, pady=4,
            ).pack(side="top", fill="x", padx=10, pady=(8, 2))

            tk.Label(
                frame,
                text=f"Criteria: {strategy['criteria']}",
                font=("Helvetica", 10, "italic", "bold"), fg="gray",
            ).pack(side="top", padx=10, pady=(0, 5))

            table_frame = tk.Frame(frame)
            table_frame.pack(fill="both", expand=True)

            if not players:
                tk.Label(table_frame, text="No players match this strategy",
                         font=("Helvetica", 12), fg="red").pack(pady=20)
                continue

            columns = ["Player", "Team", "Age", "Market Value",
                       "NPxG Overperf", "NPxG/90", "NP Shot Qual",
                       "NP Fin Ratio", "NPG", "NPxG", "Minutes"]
            tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100, anchor="center")

            for p in players:
                tree.insert("", "end", values=[
                    p["Player"], p["Team"], p["Age"], p["Market Value"],
                    f"{p['NPxG Overperf']:.2f}", f"{p['NPxG/90']:.2f}",
                    f"{p['NP Shot Qual']:.2f}",  f"{p['NP Fin Ratio']:.2f}",
                    f"{p['NPG']:.0f}",           f"{p['NPxG']:.2f}",
                    p["Minutes"],
                ])

            vsb = ttk.Scrollbar(table_frame, orient="vertical",   command=tree.yview)
            hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            tree.grid(row=0, column=0, sticky="nsew")
            vsb.grid( row=0, column=1, sticky="ns")
            hsb.grid( row=1, column=0, sticky="ew")
            table_frame.grid_rowconfigure(0, weight=1)
            table_frame.grid_columnconfigure(0, weight=1)

            tk.Label(table_frame, text=f"Total Players: {len(players)}",
                     font=("Helvetica", 10, "bold")).grid(row=2, column=0, columnspan=2, pady=5)

            best_player, best_score = best_buy(strategy_name, players)
            if best_player:
                rec_text = (
                    f"⭐  Recommended Buy:  {best_player['Player']}  "
                    f"({best_player['Team']}, Age {best_player['Age']}, {best_player['Market Value']})  "
                    f"│  Scout Score: {best_score}  │  {SCORE_HINTS[strategy_name]}"
                )
                tk.Label(
                    frame, text=rec_text,
                    font=("Helvetica", 10, "bold"), fg="#1e8449", bg="#eafaf1",
                    relief="ridge", bd=1, padx=8, pady=6,
                    anchor="w", justify="left",
                ).pack(side="bottom", fill="x", padx=10, pady=(4, 8))

    # ------------------------------------------------------------------ #
    #  Graph mode                                                           #
    # ------------------------------------------------------------------ #

    def set_graph_mode(self):
        self.current_mode = "graph"
        self.show_graph_mode()

    def show_graph_mode(self):
        self._clear_container()
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        plt.subplots_adjust(hspace=0.3, wspace=0.3, bottom=0.08, top=0.96)

        metrics = [
            (
                "NPxG Overperf",
                "Non-Penalty xG Overperformance",
                "Difference between actual NPG and NPxG accumulated.\n"
                "Calculated as: NPG - NPxG = (Goals - Pen Goals) - (xG - 0.79 × Pens Taken)",
            ),
            (
                "NPxG/90",
                "Non-Penalty xG per 90'",
                "Average NPxG generated per 90 minutes played.\n"
                "Calculated as: NPxG / (Minutes / 90)",
            ),
            (
                "NP Shot Qual",
                "Non-Penalty Shot Quality",
                "Average xG value per non-penalty shot taken.\n"
                "Calculated as: NPxG / (Total Shots - Pens Taken)",
            ),
            (
                "NP Fin Ratio",
                "Non-Penalty Finishing Ratio",
                "Proportion of non-penalty shots converted to goals.\n"
                "Calculated as: NPG / (Total Shots - Pens Taken)",
            ),
        ]

        for i, (col, title, desc) in enumerate(metrics):
            ax     = axes[i // 2, i % 2]
            top_10 = self.df.nlargest(10, col).sort_values(col, ascending=True)
            bars   = ax.barh(top_10["Player"], top_10[col], color="#3498db")
            ax.set_title(title, fontweight="bold", size=13)
            ax.bar_label(bars, padding=-30, fmt="%.2f", size=10, color="black", weight="bold")
            ax.tick_params(axis="both", which="major", labelsize=10)
            for label in ax.get_yticklabels():
                if len(label.get_text()) > 25:
                    label.set_fontsize(8)
            ax.text(0.5, -0.15, desc, transform=ax.transAxes,
                    ha="center", fontsize=6, style="italic", wrap=True)

        canvas = FigureCanvasTkAgg(fig, master=self.container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ------------------------------------------------------------------ #
    #  Stats mode                                                           #
    # ------------------------------------------------------------------ #

    def set_stats_mode(self):
        self.current_mode = "stats"
        self.show_stats_mode()

    def show_stats_mode(self):
        self._clear_container()
        display_cols = [col for col in self.df.columns if col != "ID"]
        columns      = ["Rank"] + display_cols

        self.tree = ttk.Treeview(self.container, columns=columns, show="headings")
        for col in columns:
            if col != "Rank":
                self.tree.heading(col, text=col, command=lambda c=col: self._sort_table(c))
            else:
                self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")

        vsb = ttk.Scrollbar(self.container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._load_table_data(self.df)

    def _load_table_data(self, dataframe):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, (_, row) in enumerate(dataframe.iterrows(), 1):
            values = [idx] + [row[col] for col in dataframe.columns if col != "ID"]
            self.tree.insert("", "end", values=values)

    def _sort_table(self, col):
        self.df = self.df.sort_values(by=col, ascending=False)
        self._load_table_data(self.df)

    # ------------------------------------------------------------------ #
    #  Shared UI helpers                                                    #
    # ------------------------------------------------------------------ #

    def _clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def _toggle_nav(self, state):
        for btn in (self.btn_graph_mode, self.btn_stats_mode,
                    self.btn_shortlist, self.btn_update):
            btn.config(state=state)

    def _show_loading_overlay(self):
        self._capture_blur()
        self.loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.loading_frame.lift()

    def _hide_loading_overlay(self):
        self.loading_frame.place_forget()

    def _capture_blur(self):
        try:
            x, y = self.root.winfo_rootx(), self.root.winfo_rooty()
            w, h = self.root.winfo_width(), self.root.winfo_height()
            screenshot    = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            blurred       = screenshot.filter(ImageFilter.GaussianBlur(radius=8))
            self.blur_photo = ImageTk.PhotoImage(blurred)
            self.loading_bg_label.config(image=self.blur_photo)
        except Exception as e:
            print(f"Blur overlay failed: {e}")
            self.loading_bg_label.config(bg="#000000")


if __name__ == "__main__":
    root = tk.Tk()
    app  = ScoutingDashboard(root)
    root.mainloop()
