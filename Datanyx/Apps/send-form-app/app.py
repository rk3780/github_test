import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

# Page config
st.set_page_config(page_title="Send Forms", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for styling
st.markdown("""
<style>
    .main-title {
        font-size: 28px;
        font-weight: 600;
        margin-bottom: 20px;
    }
    .step-container {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .step-item {
        display: inline-block;
        padding: 8px 16px;
        margin-right: 10px;
        border-radius: 4px;
        font-weight: 500;
    }
    .step-active {
        background-color: #FFF4E6;
        color: #000;
        border: 2px solid #FFB84D;
    }
    .step-completed {
        background-color: #E8F5E9;
        color: #2E7D32;
    }
    .step-inactive {
        background-color: #f0f0f0;
        color: #999;
    }
    .info-banner {
        background-color: #E3F2FD;
        border-left: 4px solid #2196F3;
        padding: 12px;
        margin: 16px 0;
        border-radius: 4px;
    }
    .sidebar-panel {
        background-color: #f8f9fa;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    div.stButton > button {
        font-weight: 500;
        border-radius: 4px;
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid #dee2e6;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'selected_patients' not in st.session_state:
    st.session_state.selected_patients = []
if 'selected_forms' not in st.session_state:
    st.session_state.selected_forms = []
if 'patient_selections' not in st.session_state:
    st.session_state.patient_selections = []
if 'form_selections' not in st.session_state:
    st.session_state.form_selections = []

# Generate mock patient data
@st.cache_data
def load_patients():
    first_names = ['Justin', 'Sally', 'Sam', 'Eric', 'Barb', 'John', 'Mary', 'James', 'Patricia', 'Michael',
                   'Jennifer', 'William', 'Linda', 'David', 'Elizabeth', 'Richard', 'Susan', 'Joseph', 'Jessica', 'Thomas']
    last_names = ['Case', 'Forth', 'Miller', 'Palmer', 'Dwyer', 'Anderson', 'Brown', 'Davis', 'Garcia', 'Rodriguez',
                  'Wilson', 'Martinez', 'Taylor', 'Thomas', 'Moore', 'Jackson', 'Martin', 'Lee', 'Harris', 'Clark']
    providers = ['Seth Fillmore, MD', 'Doctor Pink, MD', 'Dr. Johnson, MD', 'Dr. Smith, MD', 'Dr. Williams, MD']
    locations = ['Fremont', 'San Francisco Medical Oncology', 'Downtown Clinic', 'Northside Hospital', 'Westside Center']
    appt_types = ['Alpha Shawn Test', 'Follow-up', 'Initial Consultation', 'Annual Physical', 'Specialist Visit']
    
    patients = []
    for i in range(100):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        dob = datetime(1940, 1, 1) + timedelta(days=random.randint(0, 25000))
        mrn = f"ju{random.randint(100000, 999999)}{random.choice('abcdefghijklmnopqrstuvwxyz')}{random.choice('abcdefghijklmnopqrstuvwxyz')}"
        next_appt = 'N/A' if random.random() > 0.7 else (datetime.now() + timedelta(days=random.randint(-30, 60))).strftime('%m/%d/%Y')
        
        patients.append({
            'patient_name': f"{lname}, {fname}",
            'mrn': mrn,
            'date_of_birth': dob.strftime('%m/%d/%Y'),
            'age': (datetime.now() - dob).days // 365,
            'provider_name': random.choice(providers),
            'location_name': random.choice(locations),
            'next_appointment': next_appt,
            'appointment_type': random.choice(appt_types)
        })
    
    return pd.DataFrame(patients).sort_values('patient_name').reset_index(drop=True)

# Generate mock forms data
@st.cache_data
def load_forms():
    forms_list = [
        'Acknowledgement of Notice of Privacy Practices',
        'AO - Assignment of Benefits',
        'AO - Financial Policy',
        'AO - HIPAA Consent to Share Information',
        'AOB Patient Info and Insurance'
    ]
    specialties = ['General Practice', 'Oncology', 'Cardiology', 'Pediatrics', 'All']
    providers = ['Seth Fillmore, MD', 'Doctor Pink, MD', 'Dr. Johnson, MD', 'All']
    locations = ['Fremont', 'San Francisco Medical Oncology', 'Downtown Clinic', 'All']
    appt_types = ['Alpha Shawn Test', 'Follow-up', 'Initial Consultation', 'All']
    
    forms = []
    for form in forms_list:
        for _ in range(20):  # Create multiple entries with different filters
            last_update = '09/19/24' if 'Acknowledgement' in form else ('11/22/24' if 'AOB' in form else '03/18/25')
            forms.append({
                'packet_form_name': form,
                'specialty': random.choice(specialties),
                'provider_name': random.choice(providers),
                'location_name': random.choice(locations),
                'appointment_type': random.choice(appt_types),
                'last_update': last_update,
                'version': 1
            })
    
    return pd.DataFrame(forms).drop_duplicates().reset_index(drop=True)

# Load data
patients_df = load_patients()
forms_df = load_forms()

# Step indicator
def show_step_indicator(current_step):
    steps = [
        (1, "Select Patients"),
        (2, "Select Packets and Forms"),
        (3, "Confirm & Send")
    ]
    
    html = '<div class="step-container">'
    for step_num, step_name in steps:
        if step_num < current_step:
            css_class = "step-item step-completed"
            icon = "✓ "
        elif step_num == current_step:
            css_class = "step-item step-active"
            icon = ""
        else:
            css_class = "step-item step-inactive"
            icon = ""
        html += f'<span class="{css_class}">{icon}{step_num}. {step_name}</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# Main title
st.markdown('<div class="main-title">Send Forms</div>', unsafe_allow_html=True)

# Show step indicator
show_step_indicator(st.session_state.step)

# ========== STEP 1: SELECT PATIENTS ==========
if st.session_state.step == 1:
    col_main, col_sidebar = st.columns([3, 1])
    
    with col_main:
        st.markdown("### Filter Patients")
        
        # Search and filters
        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input("🔍 Enter Patient Name, DOB or MRN", key="patient_search")
        with col2:
            st.write("")
            st.write("")
            if st.button("CLEAR FILTERS", key="clear_patient_filters"):
                st.rerun()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            provider_filter = st.multiselect("Provider", options=['All'] + sorted(patients_df['provider_name'].unique().tolist()))
        with col2:
            location_filter = st.multiselect("Location", options=['All'] + sorted(patients_df['location_name'].unique().tolist()))
        with col3:
            appt_type_filter = st.multiselect("Appointment Type", options=['All'] + sorted(patients_df['appointment_type'].unique().tolist()))
        with col4:
            date_range = st.date_input("Appointment Date Range", value=[], key="appt_date")
        
        # Filter data
        filtered_patients = patients_df.copy()
        
        if search_term:
            filtered_patients = filtered_patients[
                filtered_patients['patient_name'].str.contains(search_term, case=False, na=False) |
                filtered_patients['mrn'].str.contains(search_term, case=False, na=False) |
                filtered_patients['date_of_birth'].str.contains(search_term, case=False, na=False)
            ]
        
        if provider_filter and 'All' not in provider_filter:
            filtered_patients = filtered_patients[filtered_patients['provider_name'].isin(provider_filter)]
        
        if location_filter and 'All' not in location_filter:
            filtered_patients = filtered_patients[filtered_patients['location_name'].isin(location_filter)]
        
        if appt_type_filter and 'All' not in appt_type_filter:
            filtered_patients = filtered_patients[filtered_patients['appointment_type'].isin(appt_type_filter)]
        
        st.markdown(f"### Available Patients ({len(filtered_patients)} results)")
        
        # Display table with selection
        event = st.dataframe(
            filtered_patients,
            use_container_width=True,
            height=400,
            on_select="rerun",
            selection_mode="multi-row",
            key="patient_table"
        )
        
        # Store selections
        if event and hasattr(event, 'selection') and hasattr(event.selection, 'rows'):
            st.session_state.patient_selections = event.selection.rows
            st.session_state.selected_patients = filtered_patients.iloc[event.selection.rows].to_dict('records')
    
    with col_sidebar:
        st.markdown('<div class="sidebar-panel">', unsafe_allow_html=True)
        st.markdown(f"### Included Patients ({len(st.session_state.selected_patients)})")
        
        if st.session_state.selected_patients:
            for patient in st.session_state.selected_patients:
                st.markdown(f"**{patient['patient_name']}**")
                st.markdown(f"<small>{patient['mrn']}</small>", unsafe_allow_html=True)
                st.markdown("---")
        else:
            st.info("No patients selected")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("CANCEL", use_container_width=True):
            st.session_state.step = 1
            st.session_state.selected_patients = []
            st.session_state.selected_forms = []
            st.rerun()
    with col2:
        if st.button("SELECT FORMS/PACKETS →", type="primary", use_container_width=True, disabled=len(st.session_state.selected_patients) == 0):
            st.session_state.step = 2
            st.rerun()

# ========== STEP 2: SELECT FORMS ==========
elif st.session_state.step == 2:
    col_main, col_sidebar = st.columns([3, 1])
    
    with col_main:
        st.markdown("### Filter Forms and Packets")
        
        # Search and filters
        col1, col2 = st.columns([3, 1])
        with col1:
            form_search_term = st.text_input("🔍 Enter Form or Packet Name", key="form_search")
        with col2:
            st.write("")
            st.write("")
            if st.button("CLEAR FILTERS", key="clear_form_filters"):
                st.rerun()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            form_location_filter = st.multiselect("Location", options=['All'] + sorted(forms_df['location_name'].unique().tolist()))
        with col2:
            form_provider_filter = st.multiselect("Provider", options=['All'] + sorted(forms_df['provider_name'].unique().tolist()))
        with col3:
            form_appt_type_filter = st.multiselect("Appointment Type", options=['All'] + sorted(forms_df['appointment_type'].unique().tolist()))
        with col4:
            specialty_filter = st.multiselect("Specialty", options=['All'] + sorted(forms_df['specialty'].unique().tolist()))
        
        # Filter data
        filtered_forms = forms_df.copy()
        
        if form_search_term:
            filtered_forms = filtered_forms[
                filtered_forms['packet_form_name'].str.contains(form_search_term, case=False, na=False)
            ]
        
        if form_location_filter and 'All' not in form_location_filter:
            filtered_forms = filtered_forms[filtered_forms['location_name'].isin(form_location_filter)]
        
        if form_provider_filter and 'All' not in form_provider_filter:
            filtered_forms = filtered_forms[filtered_forms['provider_name'].isin(form_provider_filter)]
        
        if form_appt_type_filter and 'All' not in form_appt_type_filter:
            filtered_forms = filtered_forms[filtered_forms['appointment_type'].isin(form_appt_type_filter)]
        
        if specialty_filter and 'All' not in specialty_filter:
            filtered_forms = filtered_forms[filtered_forms['specialty'].isin(specialty_filter)]
        
        st.markdown(f"### Available Forms ({len(filtered_forms)} results)")
        
        # Display table with selection
        event = st.dataframe(
            filtered_forms,
            use_container_width=True,
            height=400,
            on_select="rerun",
            selection_mode="multi-row",
            key="form_table"
        )
        
        # Store selections
        if event and hasattr(event, 'selection') and hasattr(event.selection, 'rows'):
            st.session_state.form_selections = event.selection.rows
            st.session_state.selected_forms = filtered_forms.iloc[event.selection.rows].to_dict('records')
    
    with col_sidebar:
        st.markdown('<div class="sidebar-panel">', unsafe_allow_html=True)
        st.markdown(f"### Included Forms ({len(st.session_state.selected_forms)})")
        
        if st.session_state.selected_forms:
            for form in st.session_state.selected_forms:
                st.markdown(f"📋 **{form['packet_form_name']}**")
                st.markdown("---")
        else:
            st.info("No forms selected")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("← SELECT PATIENTS", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("CONFIRMATION →", type="primary", use_container_width=True, disabled=len(st.session_state.selected_forms) == 0):
            st.session_state.step = 3
            st.rerun()

# ========== STEP 3: CONFIRM & SEND ==========
elif st.session_state.step == 3:
    # Warning banner
    st.markdown(
        '<div class="info-banner">'
        '⚠️ <strong>Important:</strong> These forms will be sent immediately. '
        'Please confirm patient/patient group and forms before sending.'
        '</div>',
        unsafe_allow_html=True
    )
    
    # Selected Patients
    st.markdown("### Selected Patients")
    selected_patients_df = pd.DataFrame(st.session_state.selected_patients)
    if not selected_patients_df.empty:
        st.dataframe(
            selected_patients_df[['patient_name', 'mrn', 'date_of_birth', 'provider_name', 'location_name', 'next_appointment']],
            use_container_width=True,
            height=300
        )
        st.markdown(f"**{len(st.session_state.selected_patients)} results**")
    
    st.markdown("---")
    
    # Selected Forms
    st.markdown("### Selected Forms")
    selected_forms_df = pd.DataFrame(st.session_state.selected_forms)
    if not selected_forms_df.empty:
        st.dataframe(
            selected_forms_df[['packet_form_name', 'specialty', 'provider_name', 'location_name', 'last_update', 'version']],
            use_container_width=True,
            height=300
        )
        st.markdown(f"**{len(st.session_state.selected_forms)} results**")
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("← BACK TO SELECT FORMS", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("CONFIRM AND SEND", type="primary", use_container_width=True):
            # Show success message
            st.success(
                f"✅ Successfully sent {len(st.session_state.selected_forms)} form(s) "
                f"to {len(st.session_state.selected_patients)} patient(s)!"
            )
            
            # Log the submission (in a real app, this would send forms or write to a database)
            st.info(
                f"**Summary:**\n\n"
                f"- Patients: {', '.join([p['patient_name'] for p in st.session_state.selected_patients[:3]])}" +
                (f" and {len(st.session_state.selected_patients) - 3} more" if len(st.session_state.selected_patients) > 3 else "") +
                f"\n- Forms: {', '.join([f['packet_form_name'] for f in st.session_state.selected_forms])}"
            )
            
            # Reset and go back to step 1
            if st.button("Start New Submission"):
                st.session_state.step = 1
                st.session_state.selected_patients = []
                st.session_state.selected_forms = []
                st.session_state.patient_selections = []
                st.session_state.form_selections = []
                st.rerun()