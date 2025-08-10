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
            st.error(f"❌ Could not connect to Supabase: {str(e)}")
            st.error("Please check your Supabase configuration in secrets.toml")
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
    
    def save_progress(self, period, student, subject, rating):
        """Save progress data to Supabase"""
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
    
    def load_all_data(self):
        """Load all data from Supabase"""
        return {
            "attendance": self.load_attendance(),
            "assignments": self.load_assignments(),
            "progress_90": self.load_progress("90"),
            "progress_180": self.load_progress("180")
        }
    
    def create_backup(self):
        """Create a downloadable backup of all data"""
        try:
            data = self.load_all_data()
            backup_data = {
                "backup_timestamp": datetime.now().isoformat(),
                "school_year": f"{SCHOOL_START.strftime('%Y-%m-%d')} to {SCHOOL_END.strftime('%Y-%m-%d')}",
                "app_version": "3.0_supabase",
                "data": data
            }
            return json.dumps(backup_data, indent=2)
        except Exception as e:
            st.error(f"Error creating backup: {e}")
            return None

# Initialize data manager
@st.cache_resource
def get_data_manager():
    return SupabaseDataManager()

def get_school_days():
    """Calculate school days and milestone dates"""
    current_date = SCHOOL_START
    school_days = []
    
    while current_date <= SCHOOL_END:
        # Skip weekends (optional - remove if you want 7-day weeks)
        if current_date.weekday() < 5:  # Monday = 0, Friday = 4
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
                    row[f"{category} - {subject}"] = completed
            
            report_data.append(row)
    
    # Progress data
    progress_data = []
    for milestone in ["90", "180"]:
        progress_key = f"progress_{milestone}"
        if progress_key in data:
            for student, subjects in data[progress_key].items():
                for subject, rating in subjects.items():
                    if rating:  # Only include if rating is set
                        progress_data.append({
                            "Milestone": f"{milestone}-Day",
                            "Student": student,
                            "Subject": subject,
                            "Rating": rating
                        })
    
    # Create Excel file with multiple sheets
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if report_data:
            df_attendance = pd.DataFrame(report_data)
            df_attendance.to_excel(writer, sheet_name='Daily Tracking', index=False)
        
        if progress_data:
            df_progress = pd.DataFrame(progress_data)
            df_progress.to_excel(writer, sheet_name='Progress Tracking', index=False)
    
    return output.getvalue()

def generate_pdf_report(data):
    """Generate comprehensive PDF report"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.darkblue,
        alignment=1
    )
    story.append(Paragraph("Three Oaks Academy Comprehensive Progress Report", title_style))
    story.append(Spacer(1, 20))
    
    # Report generation info
    story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    story.append(Paragraph(f"School Year: {SCHOOL_START.strftime('%B %d, %Y')} - {SCHOOL_END.strftime('%B %d, %Y')}", styles['Normal']))
    
    # Calculate report date range
    all_dates = set()
    all_dates.update(data.get("attendance", {}).keys())
    all_dates.update(data.get("assignments", {}).keys())
    
    if all_dates:
        sorted_dates = sorted(all_dates)
        story.append(Paragraph(f"Data Range: {sorted_dates[0]} to {sorted_dates[-1]} ({len(all_dates)} days tracked)", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", styles['Heading2']))
    
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
            
            for subject in subjects:
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
                else:
                    completion_data.append([subject, "0", "0", "No data"])
            
            if len(completion_data) > 1:
                table = Table(completion_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                story.append(table)
                story.append(Spacer(1, 10))
        
        # Academic Progress Milestones
        story.append(Paragraph("Academic Progress Milestones", styles['Heading3']))
        
        milestone_data = []
        milestone_data.append(['Milestone', 'Subject', 'Rating'])
        
        for milestone in ["90", "180"]:
            progress_key = f"progress_{milestone}"
            if progress_key in data and student in data[progress_key]:
                for subject, rating in data[progress_key][student].items():
                    if rating:
                        milestone_data.append([f"{milestone}-Day", subject, rating])
        
        if len(milestone_data) > 1:
            table = Table(milestone_data, colWidths=[1*inch, 2*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
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
            story.append(Paragraph("No milestone assessments completed yet", styles['Normal']))
        
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
            
            for subject in subjects:
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
    story.append(Paragraph("This report contains comprehensive homeschool documentation for regulatory compliance and academic record-keeping.", styles['Italic']))
    
    doc.build(story)
    return buffer.getvalue()

def reports_interface(data, data_manager):
    """Interface for generating reports"""
    st.subheader("Generate Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Download CSV/Excel Report", use_container_width=True):
            csv_data = generate_csv_report(data)
            st.download_button(
                label="📥 Download Excel Report",
                data=csv_data,
                file_name=f"TOAA_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col2:
        if st.button("📄 Download PDF Report", use_container_width=True):
            pdf_data = generate_pdf_report(data)
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_data,
                file_name=f"TOAA_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
    
    # Data backup section
    st.markdown("---")
    st.subheader("🔐 Data Backup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Download Complete Backup**")
        backup_data = data_manager.create_backup()
        if backup_data:
            st.download_button(
                "💾 Download Database Backup",
                backup_data,
                f"toaa_supabase_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                "application/json",
                help="Complete backup of all data from Supabase database"
            )
    
    with col2:
        st.markdown("**Data Summary**")
        attendance_days = len(data.get("attendance", {}))
        assignment_days = len(data.get("assignments", {}))
        progress_90_count = sum(1 for student in data.get("progress_90", {}).values() 
                               for rating in student.values() if rating)
        progress_180_count = sum(1 for student in data.get("progress_180", {}).values() 
                                for rating in student.values() if rating)
        
        st.metric("Attendance Days", attendance_days)
        st.metric("Assignment Days", assignment_days)
        st.metric("90-Day Assessments", progress_90_count)
        st.metric("180-Day Assessments", progress_180_count)
    
    if data_manager.connected:
        st.success("🔗 All data is securely stored in Supabase cloud database with automatic backups")
    else:
        st.error("❌ Database connection failed - Please check your Supabase configuration")

def main():
    st.title("🏫 Three Oaks Academy Tracker")
    st.markdown("Track daily attendance, assignments, and academic progress")
    
    # Initialize data manager and load data
    data_manager = get_data_manager()
    
    # Load data from Supabase (cached for performance)
    @st.cache_data(ttl=30)  # Cache for 30 seconds
    def load_data():
        return data_manager.load_all_data()
    
    # Load data
    if data_manager.connected:
        data = load_data()
    else:
        data = {"attendance": {}, "assignments": {}, "progress_90": {}, "progress_180": {}}
    
    # Initialize session state for date selection
    if 'selected_tracking_date' not in st.session_state:
        st.session_state.selected_tracking_date = date.today()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Choose a page:",
        ["Daily Tracking", "Progress Tracking", "Reports"]
    )
    
    # Display school year info
    st.sidebar.markdown("---")
    st.sidebar.markdown("**School Year:**")
    st.sidebar.markdown(f"{SCHOOL_START.strftime('%B %d, %Y')}")
    st.sidebar.markdown(f"to {SCHOOL_END.strftime('%B %d, %Y')}")
    
    school_days, milestone_90, milestone_180 = get_school_days()
    today = date.today()
    days_completed = len([d for d in school_days if d <= today])
    
    st.sidebar.markdown(f"**Days Completed:** {days_completed}/{len(school_days)}")
    
    if milestone_90:
        st.sidebar.markdown(f"**90-day milestone:** {milestone_90.strftime('%m/%d/%Y')}")
    if milestone_180:
        st.sidebar.markdown(f"**180-day milestone:** {milestone_180.strftime('%m/%d/%Y')}")
    
    # Database status in sidebar
    st.sidebar.markdown("---")
    if data_manager.connected:
        st.sidebar.success("🔗 Supabase Connected")
        total_records = (len(data.get("attendance", {})) + len(data.get("assignments", {})))
        st.sidebar.metric("Records in Database", total_records)
    else:
        st.sidebar.error("❌ Database Offline")
        st.sidebar.markdown("Check configuration")
    
    # Main content based on selected page
    if page == "Daily Tracking":
        selected_date = st.date_input(
            "Select Date:",
            value=st.session_state.selected_tracking_date,
            min_value=SCHOOL_START,
            max_value=SCHOOL_END,
            key="tracking_date_input"
        )
        
        if selected_date != st.session_state.selected_tracking_date:
            st.session_state.selected_tracking_date = selected_date
            st.rerun()
        
        daily_tracking_interface(selected_date, data, data_manager)
    
    elif page == "Progress Tracking":
        progress_tracking_interface(data, data_manager)
    
    elif page == "Reports":
        reports_interface(data, data_manager)
    
    # Refresh data button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("*Powered by Basecamp Data Analytics*", unsafe_allow_html=True)

if __name__ == "__main__":
    main()