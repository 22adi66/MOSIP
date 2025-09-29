import streamlit as st
import requests
import json
from PIL import Image

# This single file contains everything you need, fully updated to the new guides.

st.set_page_config(page_title="MOSIP OCR", page_icon="📄", layout="wide")

st.title("📄 MOSIP OCR - Text Extraction & Verification")
st.markdown("Upload document images to extract and validate text content using the live API.")

# --- API Configuration ---
# The new, live API URL provided by your friend [cite]
API_BASE = "https://deandra-creamiest-unpenetratingly.ngrok-free.dev"

# IMPORTANT: This header is required to bypass the ngrok browser warning page [cite]
HEADERS = {"ngrok-skip-browser-warning": "true"}

# --- Helper Function for API Connection Check ---
def check_api_status():
    try:
        response = requests.get(f"{API_BASE}/health", headers=HEADERS)
        if response.status_code == 200:
            st.sidebar.success("✅ API Connected")
            return True
        else:
            st.sidebar.error(f"API Status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        st.sidebar.error("❌ API Connection Failed")
        return False

# --- Sidebar for Configuration ---
st.sidebar.header("⚙️ Configuration")
check_api_status() # Check API status on load
confidence_threshold = st.sidebar.slider("Confidence Threshold", 0.0, 1.0, 0.7, 0.1)
preprocess = st.sidebar.checkbox("Image Preprocessing", value=True)

# --- Dynamic Language Selection ---
try:
    languages_response = requests.get(f"{API_BASE}/api/v1/languages", headers=HEADERS)
    if languages_response.status_code == 200:
        lang_data = languages_response.json()
        available_languages = list(lang_data['supported_languages'].keys())
        selected_languages = st.sidebar.multiselect("Languages", available_languages, default=["en"])
    else:
        st.sidebar.warning("Could not load languages. Using defaults.")
        selected_languages = ["en"]
except requests.exceptions.RequestException:
    st.sidebar.warning("API not ready. Using default languages.")
    selected_languages = ["en"]


# --- Main Interface ---
uploaded_file = st.file_uploader(
    "Upload Document Image",
    type=['jpg', 'jpeg', 'png', 'tiff'],
    help="Upload an image file containing text to extract"
)

if uploaded_file is not None:
    col1, col2 = st.columns([1, 2])

    with col1:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", width='stretch')
        document_type = st.selectbox(
            "Document Type (for validation)",
            ["", "aadhaar", "pan", "passport", "driving_license", "voter_id"]
        )

    with col2:
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 Extract Text", "✅ Validate Text", "🔄 Full Process", "📝 Smart Fields"])

        # Tab 1: Simple Extraction
        with tab1:
            if st.button("Extract Text", key="extract", width='stretch'):
                with st.spinner("Extracting text..."):
                    # Fixed file upload format for API compatibility
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    data = {
                        "confidence_threshold": confidence_threshold,
                        "preprocess": preprocess,
                        "languages": ",".join(selected_languages)
                    }
                    try:
                        response = requests.post(f"{API_BASE}/api/v1/ocr/extract", files=files, data=data, headers=HEADERS)
                        if response.status_code == 200:
                            result = response.json()
                            st.metric("Text Blocks Found", result.get('text_blocks_found', 0))
                            st.text_area("📝 Extracted Text", result.get('combined_text', ''), height=150)
                        else:
                            st.error(f"Error: {response.status_code} - {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Connection Error: Could not connect to the API at {API_BASE}.")

        # Tab 2: Manual Text Validation
        with tab2:
            text_input = st.text_area("Enter text to validate:", height=100)
            if st.button("Validate Text", key="validate", width='stretch') and text_input:
                with st.spinner("Validating..."):
                    payload = {"text": text_input, "document_type": document_type if document_type else None}
                    try:
                        response = requests.post(f"{API_BASE}/api/v1/ocr/validate", json=payload, headers=HEADERS)
                        if response.status_code == 200:
                            result = response.json()
                            st.success(result.get('validation_message', 'Validation complete!'))
                        else:
                            st.error(f"Error: {response.status_code} - {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Connection Error: Could not connect to the API at {API_BASE}.")

        # Tab 3: Combined Document Processing
        with tab3:
            validate_fields = st.checkbox("Validate extracted fields", value=True)
            if st.button("Process Complete Document", key="process", width='stretch', type="primary"):
                with st.spinner("Processing document..."):
                    # Fixed file upload format for API compatibility
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    data = {
                        "confidence_threshold": confidence_threshold,
                        "document_type": document_type if document_type else None,
                        "validate_fields": validate_fields
                    }
                    try:
                        response = requests.post(f"{API_BASE}/api/v1/document/process", files=files, data=data, headers=HEADERS)
                        if response.status_code == 200:
                            result = response.json()
                            summary = result.get('summary', {})
                            st.success("Processing complete!")
                            st.text_area("📝 Validated Text", summary.get('combined_text', ''), height=120)
                        else:
                            st.error(f"Error: {response.status_code} - {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Connection Error: Could not connect to the API at {API_BASE}.")

        # Tab 4: Smart Field Extraction
        with tab4:
            st.markdown("### 📝 Smart Field Extraction")
            st.info("Define custom fields to extract specific information from your document")
            
            # Initialize session state for fields
            if 'custom_fields' not in st.session_state:
                st.session_state.custom_fields = []
            
            # Load available predefined fields
            try:
                fields_response = requests.get(f"{API_BASE}/api/v1/fields/available", headers=HEADERS)
                if fields_response.status_code == 200:
                    available_fields = fields_response.json()['available_fields']
                    predefined_options = {f["name"]: f for f in available_fields}
                else:
                    predefined_options = {}
            except:
                predefined_options = {}
            
            # Field management section
            col_a, col_b = st.columns([3, 1])
            
            with col_a:
                # Quick add predefined fields
                if predefined_options:
                    st.markdown("**Quick Add Predefined Fields:**")
                    selected_predefined = st.multiselect(
                        "Select from common fields:",
                        options=list(predefined_options.keys()),
                        key="predefined_select"
                    )
                    
                    if st.button("Add Selected Fields", key="add_predefined"):
                        for field_name in selected_predefined:
                            field_def = predefined_options[field_name]
                            new_field = {
                                "name": field_def["name"],
                                "keywords": field_def["keywords"],
                                "data_type": field_def["data_type"],
                                "required": False
                            }
                            if new_field not in st.session_state.custom_fields:
                                st.session_state.custom_fields.append(new_field)
                        st.rerun()
                
                # Custom field input
                st.markdown("**Add Custom Field:**")
                with st.form("add_field_form"):
                    new_field_name = st.text_input("Field Name", placeholder="e.g., Patient ID")
                    new_field_keywords = st.text_input("Keywords (comma-separated)", 
                                                     placeholder="e.g., patient id, id number, रोगी आईडी")
                    new_field_type = st.selectbox("Data Type", ["text", "number", "email", "phone", "date"])
                    new_field_required = st.checkbox("Required Field")
                    
                    if st.form_submit_button("Add Field"):
                        if new_field_name and new_field_keywords:
                            keywords_list = [kw.strip() for kw in new_field_keywords.split(",")]
                            new_field = {
                                "name": new_field_name,
                                "keywords": keywords_list,
                                "data_type": new_field_type,
                                "required": new_field_required
                            }
                            st.session_state.custom_fields.append(new_field)
                            st.success(f"Added field: {new_field_name}")
                            st.rerun()
            
            with col_b:
                st.markdown("**Actions:**")
                if st.button("Clear All Fields", key="clear_fields"):
                    st.session_state.custom_fields = []
                    st.rerun()
            
            # Display current fields
            if st.session_state.custom_fields:
                st.markdown("**Current Fields to Extract:**")
                for i, field in enumerate(st.session_state.custom_fields):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{field['name']}** ({field['data_type']})")
                        st.caption(f"Keywords: {', '.join(field['keywords'])}")
                    with col2:
                        required_text = "✅ Required" if field['required'] else "Optional"
                        st.write(required_text)
                    with col3:
                        if st.button("Remove", key=f"remove_{i}"):
                            st.session_state.custom_fields.pop(i)
                            st.rerun()
                
                # Extract fields button
                if st.button("🎯 Extract Fields from Document", key="extract_fields", width='stretch', type="primary"):
                    with st.spinner("Extracting custom fields..."):
                        # Fixed file upload format for API compatibility
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        data = {
                            "confidence_threshold": confidence_threshold,
                            "fields": json.dumps(st.session_state.custom_fields)
                        }
                        try:
                            response = requests.post(f"{API_BASE}/api/v1/fields/extract", files=files, data=data, headers=HEADERS)
                            if response.status_code == 200:
                                result = response.json()
                                st.success(f"Extracted {result['fields_extracted']}/{result['total_fields_requested']} fields!")
                                
                                # Display extracted fields in an editable form
                                st.markdown("### 📋 Extracted Information")
                                
                                # Create form for editing extracted values
                                with st.form("extracted_fields_form"):
                                    extracted_values = {}
                                    
                                    for field_def in st.session_state.custom_fields:
                                        field_name = field_def['name']
                                        
                                        # Find extracted value for this field
                                        extracted_value = ""
                                        confidence = 0.0
                                        for extracted in result['extracted_fields']:
                                            if extracted['field_name'] == field_name:
                                                extracted_value = extracted['value']
                                                confidence = extracted['confidence']
                                                break
                                        
                                        # Create input field with pre-filled value
                                        if field_def['data_type'] == 'number':
                                            value = st.number_input(
                                                f"{field_name} {'*' if field_def['required'] else ''}",
                                                value=float(extracted_value) if extracted_value.isdigit() else 0.0,
                                                key=f"field_{field_name}"
                                            )
                                        else:
                                            value = st.text_input(
                                                f"{field_name} {'*' if field_def['required'] else ''}",
                                                value=extracted_value,
                                                key=f"field_{field_name}"
                                            )
                                        
                                        extracted_values[field_name] = value
                                        
                                        # Show confidence if field was auto-extracted
                                        if extracted_value:
                                            st.caption(f"Auto-extracted with {confidence:.1%} confidence")
                                    
                                    # Form submission buttons
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        if st.form_submit_button("💾 Save as JSON"):
                                            import json
                                            json_data = json.dumps(extracted_values, indent=2)
                                            st.download_button(
                                                "Download JSON",
                                                json_data,
                                                file_name=f"extracted_fields_{uploaded_file.name}.json",
                                                mime="application/json"
                                            )
                                    
                                    with col2:
                                        if st.form_submit_button("📋 Copy to Clipboard"):
                                            clipboard_text = "\n".join([f"{k}: {v}" for k, v in extracted_values.items()])
                                            st.code(clipboard_text)
                                    
                                    with col3:
                                        if st.form_submit_button("✅ Validate Fields"):
                                            # Validate required fields
                                            missing_fields = []
                                            for field_def in st.session_state.custom_fields:
                                                if field_def['required'] and not extracted_values.get(field_def['name']):
                                                    missing_fields.append(field_def['name'])
                                            
                                            if missing_fields:
                                                st.error(f"Missing required fields: {', '.join(missing_fields)}")
                                            else:
                                                st.success("All required fields are filled!")
                                
                            else:
                                st.error(f"Error: {response.status_code} - {response.text}")
                        except requests.exceptions.RequestException as e:
                            st.error(f"Connection Error: Could not connect to the API at {API_BASE}.")
            else:
                st.info("Add fields above to extract specific information from your document")

# --- Sidebar Footer ---
st.sidebar.markdown("---")
st.sidebar.info("**MOSIP OCR API v1**")