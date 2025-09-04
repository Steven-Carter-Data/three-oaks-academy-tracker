# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Three Oaks Academy Tracker is a Streamlit-based homeschool management application that tracks attendance, assignments, and academic progress for multiple students. The application integrates with Supabase for cloud data storage with local JSON fallback.

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit application
streamlit run toaa_app.py
```

## Architecture

### Core Components

- **`toaa_app.py`**: Main Streamlit application containing all functionality
- **`toaa_data.json`**: Local data backup file (JSON format)
- **`.streamlit/secrets.toml`**: Supabase connection credentials
- **`requirements.txt`**: Python dependencies

### Data Architecture

The application manages four types of data:
1. **Attendance**: Daily attendance records by student and date
2. **Assignments**: Subject completion tracking by student, date, category, and subject
3. **Progress (90-day)**: Academic assessments at 90-day milestone
4. **Progress (180-day)**: Academic assessments at 180-day milestone

### Data Storage Strategy

- **Primary**: Supabase cloud database with real-time sync
- **Backup**: Local JSON file (`toaa_data.json`) for offline mode
- **Connection**: Automatic fallback to local mode if Supabase unavailable

### Student Structure

Students are configured in `STUDENT_CLASSES` dictionary with three-tier hierarchy:
- Student → Category (Three Oaks Academy, UHC Coop, Velos Coop) → Subjects

Special handling for "Other" subjects allows custom subject entry with dynamic text input.

## Database Schema (Supabase)

The application expects these Supabase tables:
- `attendance`: date, student, present, updated_at
- `assignments`: date, student, category, subject, completed, updated_at  
- `progress_90`: student, subject, rating, updated_at
- `progress_180`: student, subject, rating, updated_at

## Key Constants

- **School year**: July 21, 2025 to May 31, 2026
- **Students**: Killian, Lucy, Vann
- **Academic subjects**: Reading, Writing, Math, Science, Social Studies
- **Progress ratings**: Satisfactory, Needs Improvement, Unsatisfactory

## Report Generation

The application generates two report types:
- **CSV**: Tabular data export with attendance and assignment completion
- **PDF**: Comprehensive formatted report with attendance analysis, subject completion rates, and progress assessments using ReportLab

## Development Notes

- All data operations include both Supabase and local JSON updates for consistency
- Custom subjects in "Other" category require special handling with text input and cleanup of old entries
- School day calculations exclude weekends for milestone tracking
- Error handling includes graceful degradation to local mode when database unavailable