import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
import webbrowser
import json
import os

class ReviewScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SaaS Review Scraper")

        self._build_gui()

    def _build_gui(self):
        padding = {"padx": 10, "pady": 5}

        # Company Input
        ttk.Label(self.root, text="Company / Capterra Slug:").grid(row=0, column=0, sticky="w", **padding)
        self.company_entry = ttk.Entry(self.root, width=30)
        self.company_entry.grid(row=0, column=1, **padding)

        # Search Button
        self.search_btn = ttk.Button(self.root, text="🔍 Search Capterra", command=self.open_capterra_search)
        self.search_btn.grid(row=0, column=2, **padding)

        # Date Inputs
        ttk.Label(self.root, text="Start Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="w", **padding)
        self.start_entry = ttk.Entry(self.root)
        self.start_entry.grid(row=1, column=1, **padding)

        ttk.Label(self.root, text="End Date (YYYY-MM-DD):").grid(row=2, column=0, sticky="w", **padding)
        self.end_entry = ttk.Entry(self.root)
        self.end_entry.grid(row=2, column=1, **padding)

        # Source Dropdown
        ttk.Label(self.root, text="Source:").grid(row=3, column=0, sticky="w", **padding)
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(self.root, textvariable=self.source_var, values=["g2", "capterra"])
        self.source_combo.grid(row=3, column=1, **padding)
        self.source_combo.set("")  # force user to choose

        # Scrape Button
        self.scrape_button = ttk.Button(self.root, text="Scrape Reviews", command=self.start_scraping)
        self.scrape_button.grid(row=4, columnspan=3, pady=10)

        # Status
        self.status_label = ttk.Label(self.root, text="", foreground="blue")
        self.status_label.grid(row=5, columnspan=3, pady=(5, 10))

    def open_capterra_search(self):
        query = self.company_entry.get().strip()
        if query:
            url = f"https://www.capterra.in/search/product?q={query}"
            webbrowser.open(url)

    def start_scraping(self):
        company = self.company_entry.get().strip().lower()
        start_date = self.start_entry.get().strip()
        end_date = self.end_entry.get().strip()
        source = self.source_var.get().strip().lower()

        # Validate
        if not company or not start_date or not end_date or not source:
            messagebox.showerror("Missing Info", "All fields are required.")
            return

        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Dates must be in YYYY-MM-DD format.")
            return

        self.status_label.config(text="⏳ Scraping in progress...", foreground="orange")

        threading.Thread(
            target=self.run_scraper,
            args=(company, start_date, end_date, source),
            daemon=True
        ).start()

    def run_scraper(self, company, start_date, end_date, source):
        try:
            # start = datetime.strptime(start_date, "%Y-%m-%d").date()
            # end = datetime.strptime(end_date, "%Y-%m-%d").date()
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            if source == "g2":
                from scrapers.g2 import scrape_g2
                reviews = scrape_g2(company, start, end)
            elif source == "capterra":
                from scrapers.capterra import scrape_capterra
                reviews = scrape_capterra(company, start, end)
            else:
                raise Exception("Unknown source selected.")

            os.makedirs("output", exist_ok=True)
            filename = f"output/{company}_{source}_reviews.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(reviews, f, indent=2, ensure_ascii=False)

            self.status_label.config(
                text=f"✅ Saved {len(reviews)} reviews to {filename}", foreground="green"
            )
        except Exception as e:
            self.status_label.config(text="❌ Failed: " + str(e), foreground="red")
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = ReviewScraperApp(root)
    root.mainloop()