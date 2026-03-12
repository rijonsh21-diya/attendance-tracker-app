import sqlite3
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

# Theme Config
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def init_db():
    conn = sqlite3.connect('attendance_pro.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS student 
                      (name TEXT, reg_no TEXT, total_daily_hours INTEGER, min_pct REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS subjects 
                      (id INTEGER PRIMARY KEY, name TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS timetable 
                      (day TEXT, hour INTEGER, subject_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs 
                      (date TEXT, subject_id INTEGER, status TEXT)''')
    conn.commit()
    return conn

class AttendanceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Attendance Tracker Pro v3.5")
        self.geometry("1150x800")
        self.conn = init_db()
        
        # Define days
        self.work_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        self.sub_map = {}

        self.check_setup()

    def check_setup(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM student")
        if not cursor.fetchone():
            self.setup_registration_ui()
        else:
            self.build_main_interface()

    # --- UI UTILS ---
    def clear_screen(self):
        for w in self.winfo_children():
            w.destroy()

    def clear_workspace(self):
        if hasattr(self, 'workspace') and self.workspace.winfo_exists():
            for w in self.workspace.winfo_children():
                w.destroy()

    # --- REGISTRATION FLOW ---
    def setup_registration_ui(self):
        self.clear_screen()
        self.reg_frame = ctk.CTkFrame(self, corner_radius=25, border_width=2, border_color="#3B8ED0")
        self.reg_frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self.reg_frame, text="STUDENT REGISTRATION", font=("Inter", 28, "bold")).pack(pady=25, padx=50)
        
        self.ent_name = self.create_input(self.reg_frame, "Full Name")
        self.ent_reg = self.create_input(self.reg_frame, "Register Number")
        self.ent_hours = self.create_input(self.reg_frame, "Total Hours Per Day (e.g. 7)")
        self.ent_min = self.create_input(self.reg_frame, "Min Attendance % (e.g. 75)")
        self.ent_sub_count = self.create_input(self.reg_frame, "How many subjects?")

        btn = ctk.CTkButton(self.reg_frame, text="Next Step →", height=45, corner_radius=10,
                            font=("Inter", 16, "bold"), command=self.save_student_info)
        btn.pack(pady=30, padx=50, fill="x")

    def create_input(self, parent, placeholder):
        en = ctk.CTkEntry(parent, placeholder_text=placeholder, width=350, height=45, corner_radius=10)
        en.pack(pady=10, padx=50)
        return en

    def save_student_info(self):
        try:
            name, reg = self.ent_name.get(), self.ent_reg.get()
            hours, min_p = int(self.ent_hours.get()), float(self.ent_min.get())
            sub_count = int(self.ent_sub_count.get())
            
            if not name or not reg: raise ValueError
            
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM student") # Clear old data if any
            cursor.execute("INSERT INTO student VALUES (?, ?, ?, ?)", (name, reg, hours, min_p))
            self.conn.commit()
            self.subject_setup_ui(sub_count)
        except ValueError:
            messagebox.showerror("Error", "Please fill all fields with valid numbers/text.")

    def subject_setup_ui(self, count):
        self.clear_screen()
        frame = ctk.CTkFrame(self, corner_radius=20)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        scroll = ctk.CTkScrollableFrame(frame, width=450, height=400, label_text="Step 2: Subject Names")
        scroll.pack(pady=20, padx=20)

        self.sub_entries = []
        for i in range(count):
            en = ctk.CTkEntry(scroll, placeholder_text=f"Subject {i+1}", width=300)
            en.pack(pady=8, padx=20)
            self.sub_entries.append(en)

        ctk.CTkButton(frame, text="Next: Timetable →", command=self.save_subjects).pack(pady=20)

    def save_subjects(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM subjects")
        added = 0
        for en in self.sub_entries:
            val = en.get().strip()
            if val:
                cursor.execute("INSERT INTO subjects (name) VALUES (?)", (val,))
                added += 1
        
        if added == 0:
            messagebox.showwarning("Warning", "Please enter at least one subject.")
            return

        self.conn.commit()
        self.show_edit_timetable(is_setup=True)

    # --- MAIN INTERFACE ---
    def build_main_interface(self):
        self.clear_screen()
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="RIJO'S TRACKER", font=("Inter", 24, "bold"), text_color="#3B8ED0").pack(pady=40)
        
        self.nav_btn(self.sidebar, "🏠   Dashboard", self.show_dashboard)
        self.nav_btn(self.sidebar, "✅   Mark Attendance", self.show_marking)
        self.nav_btn(self.sidebar, "📅   My Timetable", self.show_timetable_view)
        self.nav_btn(self.sidebar, "✏️   Edit Timetable", lambda: self.show_edit_timetable(is_setup=False))
        
        self.btn_reset = ctk.CTkButton(self.sidebar, text="Logout / Reset", fg_color="transparent", 
                                       text_color="#E74C3C", hover_color="#321414", command=self.reset_db)
        self.btn_reset.pack(fill="x", padx=20, pady=10, side="bottom")

        self.workspace = ctk.CTkFrame(self, corner_radius=25, fg_color="#121212")
        self.workspace.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.show_dashboard()

    def nav_btn(self, parent, text, cmd):
        btn = ctk.CTkButton(parent, text=text, fg_color="transparent", height=45,
                            anchor="w", font=("Inter", 14), hover_color="#2A2A2A", command=cmd)
        btn.pack(fill="x", padx=15, pady=5)

    def show_dashboard(self):
        self.clear_workspace()
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, min_pct FROM student")
        res = cursor.fetchone()
        if not res: return
        user_name, min_p = res

        header = ctk.CTkLabel(self.workspace, text=f"Welcome, {user_name}", font=("Inter", 28, "bold"))
        header.pack(pady=(30, 10), padx=40, anchor="w")
        
        container = ctk.CTkScrollableFrame(self.workspace, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=10)

        cursor.execute("SELECT id, name FROM subjects")
        for sid, sname in cursor.fetchall():
            self.create_subject_card(container, sid, sname, min_p)

    def create_subject_card(self, parent, sid, sname, min_p):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM logs WHERE subject_id=? AND status='P'", (sid,))
        att = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM logs WHERE subject_id=? AND status IN ('P', 'A')", (sid,))
        total = cursor.fetchone()[0]
        
        perc = (att / total) if total > 0 else 0
        color = "#2ECC71" if (perc*100) >= min_p else "#E74C3C"

        card = ctk.CTkFrame(parent, height=120, corner_radius=20, border_width=1, border_color="#2A2A2A")
        card.pack(fill="x", pady=10, padx=15)
        card.pack_propagate(False) 

        ctk.CTkLabel(card, text=sname, font=("Inter", 20, "bold")).place(x=25, y=20)
        ctk.CTkLabel(card, text=f"Stats: {att} attended / {total} total", 
                     font=("Inter", 13), text_color="gray").place(x=25, y=52)
        
        prog = ctk.CTkProgressBar(card, width=600, height=12, progress_color=color)
        prog.place(x=25, y=85)
        prog.set(perc)

        ctk.CTkLabel(card, text=f"{perc*100:.1f}%", 
                     font=("Inter", 22, "bold"), text_color=color).place(relx=0.9, rely=0.5, anchor="center")

    def show_marking(self):
        self.clear_workspace()
        date_str = datetime.now().strftime("%Y-%m-%d")
        day = datetime.now().strftime("%A")
        
        ctk.CTkLabel(self.workspace, text=f"Attendance: {date_str} ({day})", font=("Inter", 26, "bold")).pack(pady=30, padx=40, anchor="w")

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM logs WHERE date=? AND status='H'", (date_str,))
        if cursor.fetchone():
            ctk.CTkLabel(self.workspace, text="Today is marked as a Holiday! 🌴", font=("Inter", 18), text_color="#E67E22").pack(pady=40)
            ctk.CTkButton(self.workspace, text="Undo Holiday", command=self.undo_holiday).pack()
            return

        cursor.execute("""SELECT t.hour, s.name, s.id FROM timetable t 
                          JOIN subjects s ON t.subject_id = s.id 
                          WHERE t.day = ? ORDER BY t.hour""", (day,))
        classes = cursor.fetchall()

        if not classes:
            ctk.CTkLabel(self.workspace, text="No classes scheduled for today.", font=("Inter", 18)).pack(pady=50)
            return

        self.att_vars = []
        for hr, sname, sid in classes:
            f = ctk.CTkFrame(self.workspace, corner_radius=15)
            f.pack(fill="x", padx=40, pady=8)
            ctk.CTkLabel(f, text=f"Hour {hr}: {sname}", font=("Inter", 15), width=300, anchor="w").pack(side="left", padx=20, pady=15)
            
            var = ctk.StringVar(value="P")
            ctk.CTkRadioButton(f, text="Present", variable=var, value="P", text_color="#2ECC71").pack(side="left", padx=10)
            ctk.CTkRadioButton(f, text="Absent", variable=var, value="A", text_color="#E74C3C").pack(side="left", padx=10)
            self.att_vars.append((sid, var))

        btn_row = ctk.CTkFrame(self.workspace, fg_color="transparent")
        btn_row.pack(pady=40)

        ctk.CTkButton(btn_row, text="Save Records", command=self.save_attendance, height=45, width=180).pack(side="left", padx=10)
        ctk.CTkButton(btn_row, text="Mark as Holiday", command=self.mark_holiday, height=45, width=180, 
                      fg_color="#E67E22", hover_color="#D35400").pack(side="left", padx=10)

    def mark_holiday(self):
        if messagebox.askyesno("Holiday", "Mark today as a holiday?"):
            date = datetime.now().strftime("%Y-%m-%d")
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM logs WHERE date=?", (date,))
            cursor.execute("INSERT INTO logs (date, status) VALUES (?, 'H')", (date,))
            self.conn.commit()
            self.show_dashboard()

    def undo_holiday(self):
        date = datetime.now().strftime("%Y-%m-%d")
        self.conn.cursor().execute("DELETE FROM logs WHERE date=? AND status='H'", (date,))
        self.conn.commit()
        self.show_marking()

    def save_attendance(self):
        date = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM logs WHERE date=? AND status != 'H'", (date,))
        for sid, var in self.att_vars:
            cursor.execute("INSERT INTO logs VALUES (?, ?, ?)", (date, sid, var.get()))
        self.conn.commit()
        messagebox.showinfo("Saved", "Attendance updated!")
        self.show_dashboard()

    def show_timetable_view(self):
        self.clear_workspace()
        ctk.CTkLabel(self.workspace, text="Weekly Schedule", font=("Inter", 26, "bold")).pack(pady=30, padx=40, anchor="w")
        scroll = ctk.CTkScrollableFrame(self.workspace, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20)

        cursor = self.conn.cursor()
        for day in self.work_days:
            f = ctk.CTkFrame(scroll, corner_radius=15)
            f.pack(fill="x", pady=10, padx=10)
            ctk.CTkLabel(f, text=day, font=("Inter", 16, "bold"), text_color="#3B8ED0", width=100).pack(side="left", padx=20, pady=20)
            
            cursor.execute("SELECT t.hour, s.name FROM timetable t JOIN subjects s ON t.subject_id=s.id WHERE day=? ORDER BY t.hour", (day,))
            day_classes = [f"H{h}: {n}" for h, n in cursor.fetchall()]
            ctk.CTkLabel(f, text=" | ".join(day_classes) if day_classes else "No Classes", font=("Inter", 13)).pack(side="left", padx=10)

    def show_edit_timetable(self, is_setup=False):
        # Determine where to draw
        if is_setup:
            self.clear_screen()
            parent = ctk.CTkFrame(self)
            parent.pack(fill="both", expand=True, padx=20, pady=20)
        else:
            self.clear_workspace()
            parent = self.workspace

        ctk.CTkLabel(parent, text="Edit Schedule (Includes Saturday)", font=("Inter", 26, "bold")).pack(pady=20, padx=40, anchor="w")
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT total_daily_hours FROM student")
        row = cursor.fetchone()
        if not row: return
        hours_limit = row[0]
        
        cursor.execute("SELECT id, name FROM subjects")
        subs = cursor.fetchall()
        sub_list = ["None"] + [f"{s[1]} (ID:{s[0]})" for s in subs]
        self.sub_map = {f"{s[1]} (ID:{s[0]})": s[0] for s in subs}

        cursor.execute("SELECT day, hour, subject_id FROM timetable")
        current_data = {(d, h): sid for d, h, sid in cursor.fetchall()}

        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20)

        self.tt_entries = {}
        for day in self.work_days:
            ctk.CTkLabel(scroll, text=day.upper(), font=("Inter", 16, "bold"), text_color="#3B8ED0").pack(pady=(15, 5))
            for h in range(1, hours_limit + 1):
                f = ctk.CTkFrame(scroll, fg_color="transparent")
                f.pack(fill="x", padx=100)
                ctk.CTkLabel(f, text=f"Hour {h}:", width=80).pack(side="left")
                cb = ctk.CTkComboBox(f, values=sub_list, width=250)
                cb.pack(side="left", pady=2)
                
                current_sid = current_data.get((day, h))
                if current_sid:
                    for sname in sub_list:
                        if f"(ID:{current_sid})" in sname: cb.set(sname)
                else:
                    cb.set("None")
                self.tt_entries[(day, h)] = cb

        ctk.CTkButton(parent, text="Save & Continue", command=self.save_timetable, height=45, width=250).pack(pady=20)

    def save_timetable(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM timetable")
        for (day, h), cb in self.tt_entries.items():
            val = cb.get()
            if val in self.sub_map:
                cursor.execute("INSERT INTO timetable VALUES (?, ?, ?)", (day, h, self.sub_map[val]))
        self.conn.commit()
        messagebox.showinfo("Success", "Timetable Updated!")
        self.build_main_interface()

    def reset_db(self):
        if messagebox.askyesno("Reset App", "Delete all data and logout?"):
            c = self.conn.cursor()
            c.execute("DROP TABLE IF EXISTS student")
            c.execute("DROP TABLE IF EXISTS subjects")
            c.execute("DROP TABLE IF EXISTS timetable")
            c.execute("DROP TABLE IF EXISTS logs")
            self.conn.commit()
            self.setup_registration_ui()

if __name__ == "__main__":
    app = AttendanceApp()
    app.mainloop()