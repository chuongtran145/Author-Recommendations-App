# app_desktop.py
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd

from data_loader import pick_split_year, parse_year_like
from graph_builder import build_graph_and_journals
from recommender import pick_target, recommend

DEFAULT_AUTHORS_COL = "authors"
DEFAULT_YEAR_COL = "mdate"
DEFAULT_VENUE_COL = "journal"
DEFAULT_MAX_TRAIN_ROWS = 200_000

class WeightControl(ttk.Frame):
    """
    Three scales JJ/AA/CN that always sum to 1.0. When one moves, we renormalize all.
    """
    def __init__(self, master, initial=(0.5, 0.3, 0.2)):
        super().__init__(master)
        self.var_jj = tk.DoubleVar(value=initial[0])
        self.var_aa = tk.DoubleVar(value=initial[1])
        self.var_cn = tk.DoubleVar(value=initial[2])
        self._building = False

        self.columnconfigure((0,1,2), weight=1)

        self.s_jj = ttk.Scale(self, from_=0.0, to=1.0, orient="horizontal",
                              command=self._on_change_jj, variable=self.var_jj)
        self.s_aa = ttk.Scale(self, from_=0.0, to=1.0, orient="horizontal",
                              command=self._on_change_aa, variable=self.var_aa)
        self.s_cn = ttk.Scale(self, from_=0.0, to=1.0, orient="horizontal",
                              command=self._on_change_cn, variable=self.var_cn)

        ttk.Label(self, text="JJ").grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="AA").grid(row=0, column=1, sticky="w")
        ttk.Label(self, text="CN").grid(row=0, column=2, sticky="w")

        self.s_jj.grid(row=1, column=0, sticky="ew", padx=4)
        self.s_aa.grid(row=1, column=1, sticky="ew", padx=4)
        self.s_cn.grid(row=1, column=2, sticky="ew", padx=4)

        self.lbl = ttk.Label(self, text=self._weights_text())
        self.lbl.grid(row=2, column=0, columnspan=3, sticky="w")

        # initial normalize
        self._normalize_all()

    def _weights_text(self):
        return f"JJ={self.var_jj.get():.2f}  AA={self.var_aa.get():.2f}  CN={self.var_cn.get():.2f}"

    def _normalize_all(self):
        total = self.var_jj.get() + self.var_aa.get() + self.var_cn.get()
        if total <= 1e-9:
            self.var_jj.set(0.5); self.var_aa.set(0.3); self.var_cn.set(0.2)
            total = 1.0
        self._building = True
        self.var_jj.set(self.var_jj.get()/total)
        self.var_aa.set(self.var_aa.get()/total)
        self.var_cn.set(self.var_cn.get()/total)
        self._building = False
        self.lbl.config(text=self._weights_text())

    def _on_change_jj(self, _=None):
        if self._building: return
        self._normalize_all()

    def _on_change_aa(self, _=None):
        if self._building: return
        self._normalize_all()

    def _on_change_cn(self, _=None):
        if self._building: return
        self._normalize_all()

    def get_weights(self):
        return (self.var_jj.get(), self.var_aa.get(), self.var_cn.get())

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Author Collaborator Finder (Desktop)")
        self.geometry("1100x700")
        self._build_ui()

    def _build_ui(self):
        # Top controls
        frm_top = ttk.Frame(self, padding=8)
        frm_top.pack(side="top", fill="x")

        # CSV path
        ttk.Label(frm_top, text="CSV path:").grid(row=0, column=0, sticky="w")
        self.var_csv = tk.StringVar(value="C:\\Users\\Asus\\Downloads\\author_collab_desktop_app\\dataset\\dblp_2021_2023.csv")
        ent_csv = ttk.Entry(frm_top, textvariable=self.var_csv, width=80)
        ent_csv.grid(row=0, column=1, sticky="ew", padx=4)
        btn_browse = ttk.Button(frm_top, text="Browse...", command=self._browse_csv)
        btn_browse.grid(row=0, column=2, padx=4)

        # Target author
        ttk.Label(frm_top, text="Target author:").grid(row=1, column=0, sticky="w")
        self.var_author = tk.StringVar(value="Ernesto Damiani")
        ttk.Entry(frm_top, textvariable=self.var_author, width=40).grid(row=1, column=1, sticky="w", padx=4)

        # Split year and train frac
        ttk.Label(frm_top, text="Split year (optional):").grid(row=2, column=0, sticky="w")
        self.var_split = tk.StringVar(value="")
        ttk.Entry(frm_top, textvariable=self.var_split, width=10).grid(row=2, column=1, sticky="w", padx=4)

        ttk.Label(frm_top, text="Train fraction (if no split year):").grid(row=2, column=1, sticky="e")
        self.var_train_frac = tk.DoubleVar(value=0.8)
        ttk.Scale(frm_top, from_=0.5, to=0.95, orient="horizontal", variable=self.var_train_frac).grid(row=2, column=2, sticky="ew", padx=4)

        # TopK and include neighbors
        ttk.Label(frm_top, text="Top-K:").grid(row=3, column=0, sticky="w")
        self.var_topk = tk.IntVar(value=25)
        ttk.Spinbox(frm_top, from_=1, to=200, textvariable=self.var_topk, width=8).grid(row=3, column=1, sticky="w", padx=4)

        self.var_include = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm_top, text="Include existing collaborators", variable=self.var_include).grid(row=3, column=2, sticky="w")

        # Journal filter
        ttk.Label(frm_top, text="Journal filter (Optional):").grid(row=4, column=0, sticky="w")
        self.var_filter = tk.StringVar(value="")
        ttk.Entry(frm_top, textvariable=self.var_filter, width=80).grid(row=4, column=1, columnspan=2, sticky="ew", padx=4)

        # Weights
        ttk.Label(frm_top, text="Weights (sum=1)").grid(row=5, column=0, sticky="w")
        self.wctrl = WeightControl(frm_top)
        self.wctrl.grid(row=5, column=1, columnspan=2, sticky="ew")

        # Run button
        self.btn_run = ttk.Button(frm_top, text="Run recommendation", command=self._on_run_clicked)
        self.btn_run.grid(row=6, column=0, pady=6, sticky="w")

        # Save CSV button (disabled initially)
        self.btn_save = ttk.Button(frm_top, text="Save results as CSV", state="disabled", command=self._save_csv)
        self.btn_save.grid(row=6, column=1, pady=6, sticky="w")

        # Status label
        self.var_status = tk.StringVar(value="Ready.")
        ttk.Label(frm_top, textvariable=self.var_status).grid(row=6, column=2, sticky="e")

        # Summary frame
        self.frm_sum = ttk.LabelFrame(self, text="Summary", padding=8)
        self.frm_sum.pack(side="top", fill="x", padx=8, pady=4)
        self._sum_vars = {k: tk.StringVar(value="-") for k in ["split_year","rows","nodes","edges","target","num_recs"]}
        row = 0
        for key, label in [("split_year","Split year"), ("rows","Training rows used"),
                           ("nodes","Nodes"), ("edges","Edges"),
                           ("target","Resolved target"), ("num_recs","Recommendations")]:
            ttk.Label(self.frm_sum, text=f"{label}:").grid(row=row, column=0, sticky="w")
            ttk.Label(self.frm_sum, textvariable=self._sum_vars[key]).grid(row=row, column=1, sticky="w", padx=6)
            row += 1

        # Table (Treeview)
        # Table (Treeview with both scrollbars)
        tbl = ttk.Frame(self, padding=0)
        tbl.pack(side="top", fill="both", expand=True, padx=8, pady=8)

        cols = ("candidate","score","aa","cn","jj","common_journals","common_neighbors","explanation")
        self.tree = ttk.Treeview(tbl, columns=cols, show="headings", height=18)

        # Tiêu đề hiển thị (đầy đủ, không viết tắt)
        headings = {
            "candidate": "Candidate",
            "score": "Score",
            "aa": "Adamic–Adar",
            "cn": "Common Neighbors",
            "jj": "Journal Jaccard",
            "common_journals": "Common Journals",
            "common_neighbors": "Common Neighbors (names)",
            "explanation": "Explanation",
        }
        for cid, text in headings.items():
            self.tree.heading(cid, text=text)

        # Độ rộng cột (cứ để hơi rộng để có thanh ngang)
        self.tree.column("candidate", width=260, anchor="w")
        self.tree.column("score", width=90, anchor="w")
        self.tree.column("aa", width=110, anchor="w")
        self.tree.column("cn", width=150, anchor="w")
        self.tree.column("jj", width=140, anchor="w")
        self.tree.column("common_journals", width=300, anchor="w")
        self.tree.column("common_neighbors", width=300, anchor="w")
        self.tree.column("explanation", width=600, anchor="w")

        # Đặt bằng grid để gắn scrollbar dễ hơn
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbars
        vsb = ttk.Scrollbar(tbl, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tbl, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Cho frame bảng co giãn
        tbl.rowconfigure(0, weight=1)
        tbl.columnconfigure(0, weight=1)

        # Data holder
        self._last_df = None

        for i in range(3):
            frm_top.columnconfigure(i, weight=1)

    def _browse_csv(self):
        path = filedialog.askopenfilename(title="Choose CSV", filetypes=[("CSV","*.csv"),("All files","*.*")])
        if path:
            self.var_csv.set(path)

    def _on_run_clicked(self):
        self.btn_run.config(state="disabled")
        self.var_status.set("Running...")
        threading.Thread(target=self._run_logic, daemon=True).start()

    def _run_logic(self):
        try:
            csv_path = self.var_csv.get().strip()
            if not os.path.exists(csv_path):
                raise FileNotFoundError(csv_path)

            split_text = self.var_split.get().strip()
            if split_text:
                try:
                    split_year = int(split_text)
                except ValueError:
                    raise ValueError("Split year must be an integer.")
            else:
                split_year = pick_split_year(csv_path, DEFAULT_YEAR_COL, self.var_train_frac.get())

            adj, nodes, author_journals, used_rows = build_graph_and_journals(
                csv_path,
                DEFAULT_AUTHORS_COL,
                DEFAULT_YEAR_COL,
                DEFAULT_VENUE_COL,
                split_year,
                DEFAULT_MAX_TRAIN_ROWS,
            )
            num_edges = sum(len(nei) for nei in adj.values()) // 2

            if not adj:
                raise RuntimeError("Empty graph. Check the CSV and columns.")

            target = pick_target(adj, self.var_author.get().strip())
            jj, aa, cn = self.wctrl.get_weights()

            filter_set = None
            if self.var_filter.get().strip():
                filter_set = {j.strip() for j in self.var_filter.get().split(";") if j.strip()}

            recs = recommend(
                adj, author_journals, target, int(self.var_topk.get()), self.var_include.get(),
                w_aa=aa, w_cn=cn, w_jj=jj, filter_journals=filter_set
            )

            # Update summary
            self._sum_vars["split_year"].set(str(split_year))
            self._sum_vars["rows"].set(str(used_rows))
            self._sum_vars["nodes"].set(str(len(nodes)))
            self._sum_vars["edges"].set(str(num_edges))
            self._sum_vars["target"].set(target)
            self._sum_vars["num_recs"].set(str(len(recs)))

            # Fill table
            for item in self.tree.get_children():
                self.tree.delete(item)
            rows = []
            for (v, score, aa_val, cn_val, jj_val, cj, cnbr, expl) in recs:
                rows.append((v, f"{score:.6f}", f"{aa_val:.4f}", cn_val, f"{jj_val:.4f}",
                             "; ".join(cj), "; ".join(cnbr), expl))
            for r in rows:
                self.tree.insert("", "end", values=r)

            # Keep DataFrame for saving
            self._last_df = pd.DataFrame([
                {"Candidate": v,
                "Score": float(score),
                "Adamic–Adar": float(aa_val),
                "Common Neighbors": int(cn_val),
                "Journal Jaccard": float(jj_val),
                "Common Journals": "; ".join(cj),
                "Common Neighbors (names)": "; ".join(cnbr),
                "Explanation": expl}
                for (v, score, aa_val, cn_val, jj_val, cj, cnbr, expl) in recs
            ])
            self.btn_save.config(state="normal")
            self.var_status.set("Done.")
        except Exception as e:
            self.var_status.set(f"Error: {e}")
        finally:
            self.btn_run.config(state="normal")

    def _save_csv(self):
        if self._last_df is None:
            messagebox.showinfo("Info", "No results to save.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not path:
            return
        self._last_df.to_csv(path, index=False, encoding="utf-8")
        messagebox.showinfo("Saved", f"Saved to {path}")

if __name__ == "__main__":
    App().mainloop()
