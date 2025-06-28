# 🚀 SaaS Review Scraper

A powerful and flexible Python-based tool to **scrape SaaS product reviews** from G2 and Capterra.  
Easily extract structured data like reviewer name, review content, rating, and date — filtered by date range.  

Supports:
- ✅ **G2.com** (via dynamic browser scraping)
- ✅ **Capterra.com** (via direct HTML scraping)
- ✅ **CLI** and **GUI (Tkinter)** interfaces
- ✅ Output as JSON files

---

## 📸 Preview

**GUI:**  
Easily enter your product name, date range, and source. Click to scrape and export!
---

## 📦 Features

- 🔍 Scrape **G2** or **Capterra** reviews using company name
- ⏱️ **Date filtering**: Filter reviews by start and end date
- 📁 Exports structured data as `JSON`
- 🧭 User-friendly **GUI** to run without terminal
- 🧪 Built with **Tkinter**, **Selenium**, and **BeautifulSoup**

---

## 🛠️ Installation

Make sure you have **Python 3.9+** installed.

```bash
git clone https://github.com/Yogeshlodhi/pulse_assignment
cd pulse_assignment

# (Optional) Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Usage

### CLI Mode

```bash
python main.py --company slack --start_date 2025-06-01 --end_date 2025-06-24 --source g2
python main.py --company slack --start_date 2025-06-01 --end_date 2025-06-24 --source capterra
```

### GUI Mode

```bash
python app_gui.py