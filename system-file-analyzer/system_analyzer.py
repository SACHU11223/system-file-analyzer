import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
from collections import defaultdict
import threading
import queue
import time
import string
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class SystemFileAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("📊 System File Analyzer - Real Time Dashboard")
        self.root.geometry("1200x800")
        self.root.state('zoomed')  # full screen feel
        
        # Colors & Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", font=("Helvetica", 12, "bold"), padding=8)
        style.configure("TLabel", font=("Helvetica", 11))
        
        self.scanning = False
        self.stop_flag = False
        self.queue = queue.Queue()
        
        # Data storage
        self.ext_count = defaultdict(int)
        self.ext_size = defaultdict(int)
        self.folder_sizes = defaultdict(int)
        self.total_files = 0
        self.total_size = 0
        
        # Header
        header = tk.Label(root, text="📊 SYSTEM FILE ANALYZER DASHBOARD", 
                         font=("Helvetica", 20, "bold"), fg="#1E88E5", bg="#f0f0f0")
        header.pack(pady=15, fill="x")
        
        # Drive / Folder Selection
        select_frame = tk.Frame(root, bg="#f0f0f0")
        select_frame.pack(pady=10, padx=30, fill="x")
        
        ttk.Label(select_frame, text="Select Drive or Folder:").pack(anchor="w")
        self.drive_var = tk.StringVar()
        
        self.drive_combo = ttk.Combobox(select_frame, textvariable=self.drive_var, width=25, state="readonly")
        self.drive_combo.pack(side="left", padx=5)
        self.load_drives()
        
        ttk.Button(select_frame, text="📁 Custom Folder", command=self.browse_custom).pack(side="left", padx=5)
        ttk.Button(select_frame, text="🔄 Refresh Drives", command=self.load_drives).pack(side="left", padx=5)
        
        # Control Buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)
        
        self.start_btn = ttk.Button(btn_frame, text="🚀 START FULL SCAN", command=self.start_scan, style="TButton")
        self.start_btn.pack(side="left", padx=10)
        
        self.stop_btn = ttk.Button(btn_frame, text="⛔ STOP SCAN", command=self.stop_scan, state="disabled")
        self.stop_btn.pack(side="left", padx=10)
        
        self.refresh_chart_btn = ttk.Button(btn_frame, text="📈 Refresh Charts Now", command=self.refresh_charts)
        self.refresh_chart_btn.pack(side="left", padx=10)
        
        # Progress & Live Stats
        self.progress = ttk.Progressbar(root, mode="indeterminate", length=800)
        self.progress.pack(pady=8, padx=30)
        
        self.stats_label = ttk.Label(root, text="Ready | Select a drive to begin", 
                                    font=("Helvetica", 12, "bold"), foreground="#333")
        self.stats_label.pack(pady=5)
        
        # Tabs for Dashboard
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=10, padx=30, fill="both", expand=True)
        
        # Tab 1: Overview
        self.overview_tab = tk.Frame(self.notebook)
        self.notebook.add(self.overview_tab, text="📌 Overview")
        self.create_overview_tab()
        
        # Tab 2: Extensions
        self.ext_tab = tk.Frame(self.notebook)
        self.notebook.add(self.ext_tab, text="📑 Extensions")
        self.create_extensions_tab()
        
        # Tab 3: Folders
        self.folder_tab = tk.Frame(self.notebook)
        self.notebook.add(self.folder_tab, text="📁 Folders")
        self.create_folders_tab()
        
        # Tab 4: Live Log
        self.log_tab = tk.Frame(self.notebook)
        self.notebook.add(self.log_tab, text="📋 Live Log")
        self.create_log_tab()
        
        # Footer
        footer = tk.Label(root, text="Real-time scanning • Graphical Dashboard • Extension & Folder wise depth analysis", 
                         font=("Helvetica", 9), fg="gray")
        footer.pack(side="bottom", pady=8)

    def load_drives(self):
        drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
        self.drive_combo['values'] = drives
        if drives:
            self.drive_combo.current(0)

    def browse_custom(self):
        folder = filedialog.askdirectory(title="Select Folder to Analyze")
        if folder:
            self.drive_var.set(folder)
            messagebox.showinfo("Selected", f"Custom folder selected: {folder}")

    def create_overview_tab(self):
        frame = tk.Frame(self.overview_tab)
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        self.total_files_label = ttk.Label(frame, text="Total Files Scanned: 0", font=("Helvetica", 14, "bold"))
        self.total_files_label.pack(pady=10)
        
        self.total_size_label = ttk.Label(frame, text="Total Space Used: 0 GB", font=("Helvetica", 14, "bold"))
        self.total_size_label.pack(pady=10)
        
        self.time_label = ttk.Label(frame, text="Scan Time: 0 sec", font=("Helvetica", 12))
        self.time_label.pack(pady=10)

    def create_extensions_tab(self):
        frame = tk.Frame(self.ext_tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Treeview Table
        cols = ("Extension", "Count", "Size", "Percentage")
        self.ext_tree = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        self.ext_tree.heading("Extension", text="Extension")
        self.ext_tree.heading("Count", text="Files")
        self.ext_tree.heading("Size", text="Space")
        self.ext_tree.heading("Percentage", text="% of Total")
        self.ext_tree.column("Extension", width=120)
        self.ext_tree.column("Count", width=100)
        self.ext_tree.column("Size", width=150)
        self.ext_tree.column("Percentage", width=100)
        self.ext_tree.pack(side="left", fill="both", expand=True, padx=5)
        
        # Pie Chart
        self.ext_fig = Figure(figsize=(5, 4), dpi=100)
        self.ext_ax = self.ext_fig.add_subplot(111)
        self.ext_canvas = FigureCanvasTkAgg(self.ext_fig, frame)
        self.ext_canvas.get_tk_widget().pack(side="right", fill="both", expand=True)

    def create_folders_tab(self):
        frame = tk.Frame(self.folder_tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Treeview Table
        cols = ("Folder Path", "Size", "Percentage")
        self.folder_tree = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        self.folder_tree.heading("Folder Path", text="Folder")
        self.folder_tree.heading("Size", text="Space Used")
        self.folder_tree.heading("Percentage", text="% of Total")
        self.folder_tree.column("Folder Path", width=500)
        self.folder_tree.column("Size", width=150)
        self.folder_tree.column("Percentage", width=100)
        self.folder_tree.pack(side="left", fill="both", expand=True, padx=5)
        
        # Bar Chart
        self.folder_fig = Figure(figsize=(5, 4), dpi=100)
        self.folder_ax = self.folder_fig.add_subplot(111)
        self.folder_canvas = FigureCanvasTkAgg(self.folder_fig, frame)
        self.folder_canvas.get_tk_widget().pack(side="right", fill="both", expand=True)

    def create_log_tab(self):
        self.log_text = scrolledtext.ScrolledText(self.log_tab, height=25, font=("Consolas", 10), 
                                                 bg="#f8f9fa", fg="#212121")
        self.log_text.pack(pady=10, padx=10, fill="both", expand=True)

    def format_size(self, bytes_val):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.2f} TB"

    def log(self, msg):
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} | {msg}\n")
        self.log_text.see(tk.END)

    def start_scan(self):
        path = self.drive_var.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "Please select a valid Drive or Folder!")
            return
        
        if self.scanning:
            return
        
        self.scanning = True
        self.stop_flag = False
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.progress.start()
        
        # Reset data
        self.ext_count.clear()
        self.ext_size.clear()
        self.folder_sizes.clear()
        self.total_files = 0
        self.total_size = 0
        
        self.log_text.delete(1.0, tk.END)
        self.log(f"🚀 Starting real-time scan of: {path}")
        self.log("⏳ This may take 10-60 minutes for full drive (C:) - Permission errors will be skipped")
        
        threading.Thread(target=self.scan_files, args=(path,), daemon=True).start()
        self.root.after(100, self.process_queue)

    def stop_scan(self):
        self.stop_flag = True
        self.log("⛔ Stop requested... Finishing current batch")

    def scan_files(self, start_path):
        start_time = time.time()
        try:
            for root, dirs, files in os.walk(start_path):
                if self.stop_flag:
                    break
                
                for file in files:
                    if self.stop_flag:
                        break
                    
                    file_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(file_path)
                        ext = os.path.splitext(file)[1].lower() or ".no_ext"
                        
                        self.ext_count[ext] += 1
                        self.ext_size[ext] += size
                        
                        # Add size to folder and all parent folders (cumulative)
                        current = root
                        while True:
                            self.folder_sizes[current] += size
                            if current == start_path or current == os.path.dirname(current):
                                break
                            current = os.path.dirname(current)
                        
                        self.total_files += 1
                        self.total_size += size
                        
                        # Real-time update every 500 files
                        if self.total_files % 500 == 0:
                            self.queue.put(("update_live", self.total_files, self.total_size))
                            self.queue.put(("log", f"Processed {self.total_files:,} files | {self.format_size(self.total_size)}"))
                    
                    except (PermissionError, OSError, FileNotFoundError):
                        continue  # skip system protected files
                
                # Folder name log every few folders
                if len(files) > 0 and self.total_files % 1000 == 0:
                    self.queue.put(("log", f"📁 Scanned folder: {root}"))
        
        except Exception as e:
            self.queue.put(("log", f"💥 Error: {str(e)}"))
        
        finally:
            scan_time = int(time.time() - start_time)
            self.queue.put(("done", self.total_files, self.total_size, scan_time))
            self.queue.put(("log", f"🎉 Scan completed! Total files: {self.total_files:,} | Time: {scan_time} seconds"))

    def process_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                if isinstance(item, tuple):
                    msg_type = item[0]
                    
                    if msg_type == "update_live":
                        files, size = item[1], item[2]
                        self.total_files = files
                        self.total_size = size
                        self.update_live_stats()
                    
                    elif msg_type == "log":
                        self.log(item[1])
                    
                    elif msg_type == "done":
                        self.total_files = item[1]
                        self.total_size = item[2]
                        self.update_live_stats()
                        self.refresh_charts()  # Auto refresh at end
                        self.scanning = False
                        self.start_btn.config(state="normal")
                        self.stop_btn.config(state="disabled")
                        self.progress.stop()
                        return  # stop checking queue
        
        except queue.Empty:
            pass
        
        self.root.after(200, self.process_queue)  # real-time sync every 200ms

    def update_live_stats(self):
        self.total_files_label.config(text=f"Total Files Scanned: {self.total_files:,}")
        self.total_size_label.config(text=f"Total Space Used: {self.format_size(self.total_size)}")
        self.stats_label.config(text=f"Scanning in progress... {self.total_files:,} files | {self.format_size(self.total_size)}")

    def refresh_charts(self):
        if self.total_size == 0:
            return
        
        # === EXTENSIONS CHART (Pie) ===
        self.ext_ax.clear()
        total_ext_size = sum(self.ext_size.values())
        
        # Top 8 + Others
        sorted_ext = sorted(self.ext_size.items(), key=lambda x: x[1], reverse=True)
        top_ext = sorted_ext[:8]
        others = sum(size for _, size in sorted_ext[8:])
        
        labels = [ext.upper() for ext, _ in top_ext] + (["OTHERS"] if others > 0 else [])
        sizes = [size for _, size in top_ext] + ([others] if others > 0 else [])
        
        self.ext_ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, 
                       colors=plt.cm.Pastel1.colors)
        self.ext_ax.set_title("Space Distribution by Extension")
        self.ext_canvas.draw()
        
        # === EXTENSIONS TABLE ===
        for item in self.ext_tree.get_children():
            self.ext_tree.delete(item)
        
        for ext, size in sorted_ext:
            count = self.ext_count[ext]
            percent = (size / total_ext_size * 100) if total_ext_size > 0 else 0
            self.ext_tree.insert("", "end", values=(ext, f"{count:,}", self.format_size(size), f"{percent:.1f}%"))
        
        # === FOLDERS CHART (Bar) ===
        self.folder_ax.clear()
        sorted_folders = sorted(self.folder_sizes.items(), key=lambda x: x[1], reverse=True)[:12]
        
        folders = [os.path.basename(p) or p for p, _ in sorted_folders]
        folder_sizes = [size for _, size in sorted_folders]
        
        self.folder_ax.barh(folders, folder_sizes, color="#1E88E5")
        self.folder_ax.set_title("Top 12 Largest Folders (with subfolders)")
        self.folder_ax.set_xlabel("Size (bytes)")
        self.folder_ax.invert_yaxis()
        self.folder_canvas.draw()
        
        # === FOLDERS TABLE ===
        for item in self.folder_tree.get_children():
            self.folder_tree.delete(item)
        
        for path, size in sorted_folders[:25]:  # top 25 in table
            percent = (size / self.total_size * 100) if self.total_size > 0 else 0
            self.folder_tree.insert("", "end", values=(path, self.format_size(size), f"{percent:.1f}%"))

if __name__ == "__main__":
    root = tk.Tk()
    app = SystemFileAnalyzer(root)
    root.mainloop()
