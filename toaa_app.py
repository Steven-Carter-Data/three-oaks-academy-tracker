import streamlit as st
import pandas as pd
import json
from datetime import datetime, date, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from supabase import create_client, Client

# Configure page
st.set_page_config(
    page_title="Three Oaks Academy Tracker",
    page_icon="🏫",
    layout="wide"
)

# School year dates
SCHOOL_START = date(2025, 7, 21)
SCHOOL_END = date(2026, 5, 31)

# Student class hierarchies
STUDENT_CLASSES = {
    "Killian": {
        "Three Oaks Academy": ["PE", "Math", "Reading", "Cursive", "Typing", "History", "News review", "Logic", "Other"],
        "UHC Coop": ["Ecology", "Lego Stem", "Literature Discussion", "IEW"],
        "Velos Coop": ["Drama", "Archery", "Woodworking"]
    },
    "Lucy": {
        "Three Oaks Academy": ["PE", "Math", "Reading", "Cursive", "Typing", "News review", "Logic", "Other"],
        "UHC Coop": ["Science", "IEW", "Art", "History"],
        "Velos Coop": ["Drama", "Archery", "Dance"]
    },
    "Vann": {
        "Three Oaks Academy": ["PE", "Math", "Reading", "Cursive", "Typing", "News review", "Logic", "Other"],
        "UHC Coop": ["Science", "IEW", "Art", "History"],
        "Velos Coop": ["Drama", "Archery"]
    }
}

STUDENTS = list(STUDENT_CLASSES.keys())
ACADEMIC_SUBJECTS = ["Reading", "Writing", "Math", "Science", "Social Studies"]
PROGRESS_OPTIONS = ["Satisfactory", "Needs Improvement", "Unsatisfactory"]

class SupabaseDataManager:
    def __init__(self):
        self.supabase = None
        self.connected = False
        self.setup_connection()
    
    def setup_connection(self):
        """Setup Supabase connection"""
        try:
            # Get Supabase credentials from Streamlit secrets
            if "supabase" in st.secrets:
                url = st.secrets["supabase"]["url"]
                key = st.secrets["supabase"]["anon_key"]
                
                self.supabase = create_client(url, key)
                
                # Test connection by trying to read from attendance table
                self.supabase.table("attendance").select("*").limit(1).execute()
                
                self.connected = True
                st.success("✅ Connected to Supabase - Data will be safely stored in the cloud")
                
            else:
                raise Exception("No Supabase credentials found in secrets")
                
        except Exception as e:
            st.error(f"⚠️ Database connection failed: {str(e)}")
            st.info("🔄 Running in local mode - data will not be saved permanently")
            self.connected = False
    
    def save_attendance(self, date_str, student, present):
        """Save attendance data to Supabase"""
        if not self.connected:
            return False
        
        try:
            # Check if record exists
            existing = self.supabase.table("attendance").select("*").eq("date", date_str).eq("student", student).execute()
            
            data = {
                "date": date_str,
                "student": student,
                "present": present,
                "updated_at": datetime.now().isoformat()
            }
            
            if existing.data:
                # Update existing record
                result = self.supabase.table("attendance").update(data).eq("date", date_str).eq("student", student).execute()
            else:
                # Insert new record
                result = self.supabase.table("attendance").insert(data).execute()
            
            return True
            
        except Exception as e:
            st.error(f"Error saving attendance: {str(e)}")
            return False
    
    def save_assignment(self, date_str, student, category, subject, completed):
        """Save assignment data to Supabase"""
        if not self.connected:
            return False
        
        try:
            # Check if record exists
            existing = self.supabase.table("assignments").select("*").eq("date", date_str).eq("student", student).eq("category", category).eq("subject", subject).execute()
            
            data = {
                "date": date_str,
                "student": student,
                "category": category,
                "subject": subject,
                "completed": completed,
                "updated_at": datetime.now().isoformat()
            }
            
            if existing.data:
                # Update existing record
                result = self.supabase.table("assignments").update(data).eq("date", date_str).eq("student", student).eq("category", category).eq("subject", subject).execute()
            else:
                # Insert new record
                result = self.supabase.table("assignments").insert(data).execute()
            
            return True
            
        except Exception as e:
            st.error(f"Error saving assignment: {str(e)}")
            return False
    
    def delete_assignment(self, date_str, student, category, subject):
        """Delete an assignment record from Supabase"""
        if not self.connected:
            return False
        
        try:
            result = self.supabase.table("assignments").delete().eq("date", date_str).eq("student", student).eq("category", category).eq("subject", subject).execute()
            return True
            
        except Exception as e:
            st.error(f"Error deleting assignment: {str(e)}")
            return False
    
    def save_progress(self, period, student, subject, rating):
        """Save progress rating to Supabase"""
        if not self.connected:
            return False
        
        try:
            table_name = f"progress_{period}"
            
            # Check if record exists
            existing = self.supabase.table(table_name).select("*").eq("student", student).eq("subject", subject).execute()
            
            data = {
                "student": student,
                "subject": subject,
                "rating": rating,
                "updated_at": datetime.now().isoformat()
            }
            
            if existing.data:
                # Update existing record
                result = self.supabase.table(table_name).update(data).eq("student", student).eq("subject", subject).execute()
            else:
                # Insert new record
                result = self.supabase.table(table_name).insert(data).execute()
            
            return True
            
        except Exception as e:
            st.error(f"Error saving progress: {str(e)}")
            return False
    
    def load_attendance(self):
        """Load all attendance data from Supabase"""
        if not self.connected:
            return {}
        
        try:
            result = self.supabase.table("attendance").select("*").execute()
            
            attendance_data = {}
            for record in result.data:
                date_str = record["date"]
                student = record["student"]
                present = record["present"]
                
                if date_str not in attendance_data:
                    attendance_data[date_str] = {}
                attendance_data[date_str][student] = present
            
            return attendance_data
            
        except Exception as e:
            st.error(f"Error loading attendance: {str(e)}")
            return {}
    
    def load_assignments(self):
        """Load all assignment data from Supabase"""
        if not self.connected:
            return {}
        
        try:
            result = self.supabase.table("assignments").select("*").execute()
            
            assignments_data = {}
            for record in result.data:
                date_str = record["date"]
                student = record["student"]
                category = record["category"]
                subject = record["subject"]
                completed = record["completed"]
                
                if date_str not in assignments_data:
                    assignments_data[date_str] = {}
                if student not in assignments_data[date_str]:
                    assignments_data[date_str][student] = {}
                if category not in assignments_data[date_str][student]:
                    assignments_data[date_str][student][category] = {}
                
                assignments_data[date_str][student][category][subject] = completed
            
            return assignments_data
            
        except Exception as e:
            st.error(f"Error loading assignments: {str(e)}")
            return {}
    
    def load_progress(self, period):
        """Load progress data from Supabase"""
        if not self.connected:
            return {}
        
        try:
            table_name = f"progress_{period}"
            result = self.supabase.table(table_name).select("*").execute()
            
            progress_data = {}
            for record in result.data:
                student = record["student"]
                subject = record["subject"]
                rating = record["rating"]
                
                if student not in progress_data:
                    progress_data[student] = {}
                progress_data[student][subject] = rating
            
            return progress_data
            
        except Exception as e:
            st.error(f"Error loading progress: {str(e)}")
            return {}

def load_local_data():
    """Load data from local JSON file as backup"""
    try:
        with open("toaa_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "attendance": {},
            "assignments": {},
            "progress_90": {},
            "progress_180": {}
        }

def save_local_data(data):
    """Save data to local JSON file as backup"""
    try:
        with open("toaa_data.json", "w") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        st.error(f"Error saving local data: {str(e)}")

def get_school_days():
    """Calculate all school days and milestone dates"""
    school_days = []
    current_date = SCHOOL_START
    
    while current_date <= SCHOOL_END:
        # Skip weekends (Monday = 0, Sunday = 6)
        if current_date.weekday() < 5:
            school_days.append(current_date)
        current_date += timedelta(days=1)
    
    milestone_90 = school_days[89] if len(school_days) > 89 else None
    milestone_180 = school_days[179] if len(school_days) > 179 else None
    
    return school_days, milestone_90, milestone_180

def daily_tracking_interface(selected_date, data, data_manager):
    """Interface for daily attendance and assignment tracking"""
    date_str = selected_date.strftime("%Y-%m-%d")
    
    st.subheader(f"Daily Tracking - {selected_date.strftime('%A, %B %d, %Y')}")
    
    # Student filter
    selected_students = st.multiselect(
        "Select Students to Track:",
        STUDENTS,
        default=STUDENTS,
        key="student_filter"
    )
    
    for student in selected_students:
        st.markdown(f"### {student}")
        
        # Attendance
        attendance_key = f"attendance_{student}_{date_str}"
        current_attendance = data["attendance"].get(date_str, {}).get(student, False)
        
        new_attendance = st.checkbox(
            f"Present", 
            value=current_attendance,
            key=attendance_key
        )
        
        if new_attendance != current_attendance:
            if data_manager.save_attendance(date_str, student, new_attendance):
                st.success(f"✅ Attendance saved for {student}")
                # Update local cache
                if date_str not in data["attendance"]:
                    data["attendance"][date_str] = {}
                data["attendance"][date_str][student] = new_attendance
            else:
                st.error(f"❌ Failed to save attendance for {student}")
        
        # Assignments by category
        for category, subjects in STUDENT_CLASSES[student].items():
            st.markdown(f"**{category}**")
            
            cols = st.columns(3)
            for i, subject in enumerate(subjects):
                col_idx = i % 3
                with cols[col_idx]:
                    # Handle "Other" subject specially
                    if subject == "Other":
                        # Check if there's a custom subject already saved for this date
                        current_assignment_data = (data["assignments"]
                                                 .get(date_str, {})
                                                 .get(student, {})
                                                 .get(category, {}))
                        
                        # Look for any custom subjects (keys that aren't in the predefined subjects list)
                        predefined_subjects = set(STUDENT_CLASSES[student][category])
                        custom_subjects = [k for k in current_assignment_data.keys() 
                                         if k not in predefined_subjects and k != "Other"]
                        
                        # Text input for custom subject
                        custom_subject_key = f"custom_{student}_{category}_{date_str}"
                        
                        # If there's already a custom subject saved, use it as default
                        default_custom = custom_subjects[0] if custom_subjects else ""
                        
                        custom_subject = st.text_input(
                            "Other (specify):",
                            value=default_custom,
                            placeholder="e.g., field trip, pottery...",
                            key=custom_subject_key
                        )
                        
                        if custom_subject.strip():
                            # Use the custom subject name
                            actual_subject = custom_subject.strip()
                            
                            assignment_key = f"assignment_{student}_{category}_{actual_subject}_{date_str}"
                            current_assignment = current_assignment_data.get(actual_subject, False)
                            
                            new_assignment = st.checkbox(
                                f"Completed: {actual_subject}",
                                value=current_assignment,
                                key=assignment_key
                            )
                            
                            if new_assignment != current_assignment:
                                # Remove old custom subjects if this is a new one
                                if custom_subjects and actual_subject not in custom_subjects:
                                    for old_custom in custom_subjects:
                                        if data_manager.delete_assignment(date_str, student, category, old_custom):
                                            # Remove from local cache too
                                            if (date_str in data["assignments"] and 
                                                student in data["assignments"][date_str] and
                                                category in data["assignments"][date_str][student]):
                                                data["assignments"][date_str][student][category].pop(old_custom, None)
                                
                                if data_manager.save_assignment(date_str, student, category, actual_subject, new_assignment):
                                    st.success(f"✅ {actual_subject} saved for {student}")
                                    # Update local cache
                                    if date_str not in data["assignments"]:
                                        data["assignments"][date_str] = {}
                                    if student not in data["assignments"][date_str]:
                                        data["assignments"][date_str][student] = {}
                                    if category not in data["assignments"][date_str][student]:
                                        data["assignments"][date_str][student][category] = {}
                                    data["assignments"][date_str][student][category][actual_subject] = new_assignment
                                else:
                                    st.error(f"❌ Failed to save {actual_subject} for {student}")
                        else:
                            # Show placeholder when no custom subject is entered
                            st.write("Enter a custom subject above")
                    
                    else:
                        # Handle regular predefined subjects
                        assignment_key = f"assignment_{student}_{category}_{subject}_{date_str}"
                        current_assignment = (data["assignments"]
                                            .get(date_str, {})
                                            .get(student, {})
                                            .get(category, {})
                                            .get(subject, False))
                        
                        new_assignment = st.checkbox(
                            subject,
                            value=current_assignment,
                            key=assignment_key
                        )
                        
                        if new_assignment != current_assignment:
                            if data_manager.save_assignment(date_str, student, category, subject, new_assignment):
                                st.success(f"✅ {subject} saved for {student}")
                                # Update local cache
                                if date_str not in data["assignments"]:
                                    data["assignments"][date_str] = {}
                                if student not in data["assignments"][date_str]:
                                    data["assignments"][date_str][student] = {}
                                if category not in data["assignments"][date_str][student]:
                                    data["assignments"][date_str][student][category] = {}
                                data["assignments"][date_str][student][category][subject] = new_assignment
                            else:
                                st.error(f"❌ Failed to save {subject} for {student}")
        
        st.markdown("---")
    
    # Connection status
    if data_manager.connected:
        st.success("🔗 Connected to Supabase - All data automatically saved to secure cloud database")
    else:
        st.error("❌ Database connection failed - Please check configuration")

def progress_tracking_interface(data, data_manager):
    """Interface for 90-day and 180-day progress tracking"""
    st.subheader("Academic Progress Tracking")
    
    school_days, milestone_90, milestone_180 = get_school_days()
    
    if milestone_90:
        st.info(f"90-day milestone: {milestone_90.strftime('%B %d, %Y')}")
    if milestone_180:
        st.info(f"180-day milestone: {milestone_180.strftime('%B %d, %Y')}")
    
    tab1, tab2 = st.tabs(["90-Day Progress", "180-Day Progress"])
    
    with tab1:
        st.markdown("### 90-Day Academic Progress")
        for student in STUDENTS:
            st.markdown(f"**{student}**")
            cols = st.columns(len(ACADEMIC_SUBJECTS))
            
            for i, subject in enumerate(ACADEMIC_SUBJECTS):
                with cols[i]:
                    current_progress = data["progress_90"].get(student, {}).get(subject, "")
                    
                    new_progress = st.selectbox(
                        subject,
                        [""] + PROGRESS_OPTIONS,
                        index=PROGRESS_OPTIONS.index(current_progress) + 1 if current_progress else 0,
                        key=f"progress_90_{student}_{subject}"
                    )
                    
                    if new_progress != current_progress:
                        if data_manager.save_progress("90", student, subject, new_progress):
                            st.success(f"✅ 90-day {subject} saved for {student}")
                            # Update local cache
                            if student not in data["progress_90"]:
                                data["progress_90"][student] = {}
                            data["progress_90"][student][subject] = new_progress
                        else:
                            st.error(f"❌ Failed to save 90-day {subject} for {student}")
    
    with tab2:
        st.markdown("### 180-Day Academic Progress")
        for student in STUDENTS:
            st.markdown(f"**{student}**")
            cols = st.columns(len(ACADEMIC_SUBJECTS))
            
            for i, subject in enumerate(ACADEMIC_SUBJECTS):
                with cols[i]:
                    current_progress = data["progress_180"].get(student, {}).get(subject, "")
                    
                    new_progress = st.selectbox(
                        subject,
                        [""] + PROGRESS_OPTIONS,
                        index=PROGRESS_OPTIONS.index(current_progress) + 1 if current_progress else 0,
                        key=f"progress_180_{student}_{subject}"
                    )
                    
                    if new_progress != current_progress:
                        if data_manager.save_progress("180", student, subject, new_progress):
                            st.success(f"✅ 180-day {subject} saved for {student}")
                            # Update local cache
                            if student not in data["progress_180"]:
                                data["progress_180"][student] = {}
                            data["progress_180"][student][subject] = new_progress
                        else:
                            st.error(f"❌ Failed to save 180-day {subject} for {student}")
    
    if data_manager.connected:
        st.success("🔗 All progress data automatically saved to secure cloud database")

def generate_csv_report(data):
    """Generate CSV report"""
    report_data = []
    
    # Attendance and assignments data
    for date_str, date_data in data.get("attendance", {}).items():
        for student in STUDENTS:
            attendance = date_data.get(student, False)
            assignments = data.get("assignments", {}).get(date_str, {}).get(student, {})
            
            row = {
                "Date": date_str,
                "Student": student,
                "Present": attendance
            }
            
            # Add assignment completion for each class
            for category, subjects in STUDENT_CLASSES[student].items():
                for subject in subjects:
                    completed = assignments.get(category, {}).get(subject, False)
                    row[f"{category}_{subject}"] = completed
            
            # Add any custom subjects not in the predefined list
            for category, category_data in assignments.items():
                if category in STUDENT_CLASSES[student]:
                    predefined_subjects = set(STUDENT_CLASSES[student][category])
                    for subject, completed in category_data.items():
                        if subject not in predefined_subjects:
                            row[f"{category}_{subject}"] = completed
            
            report_data.append(row)
    
    df = pd.DataFrame(report_data)
    return df

def generate_pdf_report(data):
    """Generate comprehensive PDF report"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=0.75*inch, rightMargin=0.75*inch, topMargin=1*inch, bottomMargin=1*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    story.append(Paragraph("Three Oaks Academy Homeschool Report", title_style))
    story.append(Spacer(1, 20))
    
    # Report metadata
    report_date = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(f"Report Generated: {report_date}", styles['Normal']))
    story.append(Paragraph(f"School Year: {SCHOOL_START.strftime('%B %d, %Y')} - {SCHOOL_END.strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", styles['Heading2']))
    
    # Calculate summary statistics
    all_dates = set()
    for date_str in data.get("attendance", {}):
        all_dates.add(date_str)
    for date_str in data.get("assignments", {}):
        all_dates.add(date_str)
    
    total_tracked_days = len(all_dates) if all_dates else 0
    school_days, milestone_90, milestone_180 = get_school_days()
    school_year_progress = (total_tracked_days / len(school_days)) * 100 if school_days else 0
    
    story.append(Paragraph(f"• Total School Days Tracked: {total_tracked_days} out of {len(school_days)} possible ({school_year_progress:.1f}% of school year)", styles['Normal']))
    
    if milestone_90:
        story.append(Paragraph(f"• 90-Day Milestone Date: {milestone_90.strftime('%B %d, %Y')}", styles['Normal']))
    if milestone_180:
        story.append(Paragraph(f"• 180-Day Milestone Date: {milestone_180.strftime('%B %d, %Y')}", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Student-by-Student Detailed Reports
    for student in STUDENTS:
        story.append(Paragraph(f"Detailed Report: {student}", styles['Heading2']))
        
        # Attendance Analysis
        story.append(Paragraph("Attendance Record", styles['Heading3']))
        total_days = 0
        present_days = 0
        
        for date_str, date_data in data.get("attendance", {}).items():
            if student in date_data:
                total_days += 1
                if date_data[student]:
                    present_days += 1
        
        if total_days > 0:
            attendance_rate = (present_days / total_days) * 100
            story.append(Paragraph(f"Days Present: {present_days} out of {total_days} tracked days ({attendance_rate:.1f}%)", styles['Normal']))
        else:
            story.append(Paragraph("No attendance data recorded", styles['Normal']))
        
        story.append(Spacer(1, 10))
        
        # Subject Completion Analysis by Category
        story.append(Paragraph("Subject Completion Analysis", styles['Heading3']))
        
        for category, subjects in STUDENT_CLASSES[student].items():
            story.append(Paragraph(f"{category}:", styles['Heading4']))
            
            completion_data = []
            completion_data.append(['Subject', 'Completed Days', 'Total Days', 'Completion Rate'])
            
            # Get all subjects including custom ones for this student/category
            all_subjects = set(subjects)
            for date_str, assignments in data.get("assignments", {}).items():
                if student in assignments and category in assignments[student]:
                    all_subjects.update(assignments[student][category].keys())
            
            for subject in all_subjects:
                completed_count = 0
                total_tracked = 0
                
                for date_str, assignments in data.get("assignments", {}).items():
                    if student in assignments and category in assignments[student] and subject in assignments[student][category]:
                        total_tracked += 1
                        if assignments[student][category][subject]:
                            completed_count += 1
                
                if total_tracked > 0:
                    completion_rate = (completed_count / total_tracked) * 100
                    completion_data.append([
                        subject,
                        str(completed_count),
                        str(total_tracked),
                        f"{completion_rate:.1f}%"
                    ])
            
            if len(completion_data) > 1:
                table = Table(completion_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
            else:
                story.append(Paragraph("No assignment data recorded for this category", styles['Normal']))
            
            story.append(Spacer(1, 10))
        
        story.append(Spacer(1, 20))
    
    # Academic Progress Assessment Section
    story.append(Paragraph("Academic Progress Assessments", styles['Heading2']))
    
    # 90-day progress
    story.append(Paragraph("90-Day Academic Progress", styles['Heading3']))
    if data.get("progress_90"):
        progress_data = []
        progress_data.append(['Student', 'Reading', 'Writing', 'Math', 'Science', 'Social Studies'])
        
        for student in STUDENTS:
            student_progress = data["progress_90"].get(student, {})
            row = [student]
            for subject in ACADEMIC_SUBJECTS:
                rating = student_progress.get(subject, "Not Assessed")
                row.append(rating)
            progress_data.append(row)
        
        table = Table(progress_data, colWidths=[1.2*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No 90-day assessments completed yet", styles['Normal']))
    
    story.append(Spacer(1, 15))
    
    # 180-day progress
    story.append(Paragraph("180-Day Academic Progress", styles['Heading3']))
    if data.get("progress_180"):
        progress_data = []
        progress_data.append(['Student', 'Reading', 'Writing', 'Math', 'Science', 'Social Studies'])
        
        for student in STUDENTS:
            student_progress = data["progress_180"].get(student, {})
            row = [student]
            for subject in ACADEMIC_SUBJECTS:
                rating = student_progress.get(subject, "Not Assessed")
                row.append(rating)
            progress_data.append(row)
        
        table = Table(progress_data, colWidths=[1.2*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No 180-day assessments completed yet", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Overall Program Summary
    story.append(Paragraph("Overall Program Analysis", styles['Heading2']))
    
    # Category completion summary across all students
    story.append(Paragraph("Subject Category Performance", styles['Heading3']))
    
    category_summary = {}
    for student in STUDENTS:
        for category, subjects in STUDENT_CLASSES[student].items():
            if category not in category_summary:
                category_summary[category] = {'total_possible': 0, 'total_completed': 0}
            
            # Get all subjects including custom ones
            all_subjects = set(subjects)
            for date_str, assignments in data.get("assignments", {}).items():
                if student in assignments and category in assignments[student]:
                    all_subjects.update(assignments[student][category].keys())
            
            for subject in all_subjects:
                for date_str, assignments in data.get("assignments", {}).items():
                    if student in assignments and category in assignments[student] and subject in assignments[student][category]:
                        category_summary[category]['total_possible'] += 1
                        if assignments[student][category][subject]:
                            category_summary[category]['total_completed'] += 1
    
    category_data = []
    category_data.append(['Category', 'Total Assignments', 'Completed', 'Completion Rate'])
    
    for category, stats in category_summary.items():
        if stats['total_possible'] > 0:
            completion_rate = (stats['total_completed'] / stats['total_possible']) * 100
            category_data.append([
                category,
                str(stats['total_possible']),
                str(stats['total_completed']),
                f"{completion_rate:.1f}%"
            ])
    
    if len(category_data) > 1:
        table = Table(category_data, colWidths=[2*inch, 1.2*inch, 1*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    
    story.append(Spacer(1, 20))
    
    # Footer
    story.append(Paragraph("This report contains comprehensive homeschool documentation for regulatory compliance and academic record-keeping.", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def main():
    st.title("🏫 Three Oaks Academy Tracker")
    st.markdown("Comprehensive homeschool tracking system for attendance, assignments, and academic progress")
    
    # Initialize data manager
    data_manager = SupabaseDataManager()
    
    # Load data
    if data_manager.connected:
        # Load from Supabase
        data = {
            "attendance": data_manager.load_attendance(),
            "assignments": data_manager.load_assignments(),
            "progress_90": data_manager.load_progress("90"),
            "progress_180": data_manager.load_progress("180")
        }
    else:
        # Load from local file as backup
        data = load_local_data()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Select Page", ["Daily Tracking", "Progress Tracking", "Reports"])
    
    if page == "Daily Tracking":
        # Date selector
        selected_date = st.date_input(
            "Select Date",
            value=date.today(),
            min_value=SCHOOL_START,
            max_value=SCHOOL_END
        )
        
        daily_tracking_interface(selected_date, data, data_manager)
    
    elif page == "Progress Tracking":
        progress_tracking_interface(data, data_manager)
    
    elif page == "Reports":
        st.subheader("📊 Generate Reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Generate CSV Report"):
                csv_data = generate_csv_report(data)
                csv_string = csv_data.to_csv(index=False)
                st.download_button(
                    label="Download CSV Report",
                    data=csv_string,
                    file_name=f"toaa_report_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
                st.success("CSV report generated!")
        
        with col2:
            if st.button("📄 Generate PDF Report"):
                pdf_buffer = generate_pdf_report(data)
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_buffer,
                    file_name=f"toaa_comprehensive_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
                st.success("PDF report generated!")
        
        # Data summary
        st.markdown("### 📈 Data Summary by Student")
        
        # Create columns for each student (stack on mobile)
        cols = st.columns(len(STUDENTS), gap="medium")
        
        for i, student in enumerate(STUDENTS):
            with cols[i]:
                # Professional styled header with gradient background
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 12px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 15px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                ">
                    <h4 style="
                        color: white;
                        margin: 0;
                        font-weight: 600;
                        font-size: 1.1em;
                        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                    ">{student}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Attendance records for this student
                attendance_count = 0
                for day_data in data.get("attendance", {}).values():
                    if student in day_data:
                        attendance_count += 1
                st.metric("Attendance Records", attendance_count)
                
                # Assignment records for this student
                assignment_count = 0
                for date_data in data.get("assignments", {}).values():
                    if student in date_data:
                        for category_data in date_data[student].values():
                            assignment_count += len(category_data)
                st.metric("Assignment Records", assignment_count)
                
                # Progress records for this student
                progress_90_count = len(data.get("progress_90", {}).get(student, {}))
                progress_180_count = len(data.get("progress_180", {}).get(student, {}))
                st.metric("90-Day Progress", progress_90_count)
                st.metric("180-Day Progress", progress_180_count)
    
    # Save local backup regardless of connection status
    save_local_data(data)

if __name__ == "__main__":
    main()