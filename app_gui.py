import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# Your scraping imports
from scrapers.g2 import scrape_g2  # Or restructure to import scrape_g2, scrape_capterra

import threading
import webbrowser



class ReviewScraperApp:
    def __init__(self, root):
        self.root = root
        root.title("SaaS Review Scraper")

        # Company
        # ttk.Label(root, text="Company Name:").grid(row=0, column=0, sticky="w")
        # self.company_entry = ttk.Entry(root, width=30)
        # self.company_entry.grid(row=0, column=1)
        
        # Company or Capterra Slug
        ttk.Label(root, text="Company / Capterra Slug:").grid(row=0, column=0, sticky="w")
        self.company_entry = ttk.Entry(root, width=30)
        self.company_entry.grid(row=0, column=1)

        # Search button
        self.search_btn = ttk.Button(root, text="🔍 Search Capterra", command=self.open_capterra_search)
        self.search_btn.grid(row=0, column=2, padx=5)


        # Start Date
        ttk.Label(root, text="Start Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="w")
        self.start_entry = ttk.Entry(root)
        self.start_entry.grid(row=1, column=1)

        # End Date
        ttk.Label(root, text="End Date (YYYY-MM-DD):").grid(row=2, column=0, sticky="w")
        self.end_entry = ttk.Entry(root)
        self.end_entry.grid(row=2, column=1)

        # Source Dropdown
        ttk.Label(root, text="Source:").grid(row=3, column=0, sticky="w")
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(root, textvariable=self.source_var, values=["g2", "capterra"])
        self.source_combo.grid(row=3, column=1)
        self.source_combo.current(0)

        # Submit Button
        self.scrape_button = ttk.Button(root, text="Scrape Reviews", command=self.start_scraping)
        self.scrape_button.grid(row=4, columnspan=2, pady=10)

        # Status
        self.status_label = ttk.Label(root, text="")
        self.status_label.grid(row=5, columnspan=2)

    def open_capterra_search(self):
        query = self.company_entry.get().strip()
        if query:
            # url = f"https://www.capterra.in/search?search={query}"
            url = f"https://www.capterra.com/search?search={query}"
            webbrowser.open(url)

    def start_scraping(self):
        company = self.company_entry.get().strip().lower()
        start_date = self.start_entry.get().strip()
        end_date = self.end_entry.get().strip()
        source = self.source_var.get()

        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid date", "Please enter dates in YYYY-MM-DD format.")
            return

        self.status_label.config(text="Scraping in progress...")

        # Run in background thread
        threading.Thread(target=self.run_scraper, args=(company, start_date, end_date, source)).start()

    
    # def start_scraping(self):
    #     company = self.company_entry.get().strip().lower()
    #     start_date = self.start_entry.get().strip()
    #     end_date = self.end_entry.get().strip()
    #     source = self.source_var.get()

    #     try:
    #         datetime.strptime(start_date, "%Y-%m-%d")
    #         datetime.strptime(end_date, "%Y-%m-%d")
    #     except ValueError:
    #         messagebox.showerror("Invalid date", "Please enter dates in YYYY-MM-DD format.")
    #         return

    #     self.status_label.config(text="Scraping in progress...")

    #     self.root.after(100, lambda: self.run_scraper(company, start_date, end_date, source))

    def run_scraper(self, company, start_date, end_date, source):
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            if source == "g2":
                reviews = scrape_g2(company, start_date, end_date)
            elif source == "capterra":
                from scrapers.capterra import scrape_capterra
                reviews = scrape_capterra(company, start_date, end_date)

            # elif source == "capterra":
            #     from scrapers.capterra import scrape_capterra
            #     reviews = scrape_capterra(company, start_date, end_date)
            else:
                raise Exception("Unsupported source")

            # Save to file
            import json, os
            os.makedirs("output", exist_ok=True)
            filename = f"output/{company}_{source}_reviews.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(reviews, f, indent=2, ensure_ascii=False)

            self.status_label.config(text=f"✅ Saved {len(reviews)} reviews to {filename}")
        except Exception as e:
            self.status_label.config(text="❌ Failed: " + str(e))
            messagebox.showerror("Error", str(e))



if __name__ == "__main__":
    root = tk.Tk()
    app = ReviewScraperApp(root)
    root.mainloop()
