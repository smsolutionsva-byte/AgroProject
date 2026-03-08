"""
Project Structure Overview

/Agro_project
│
├── README.md              - Project documentation
├── requirements.txt       - Python dependencies
├── .gitignore            - Git-ignored files
├── .gitattributes        - Git file attributes
│
├── /src                  - Main application code
├── /models               - Model training scripts
├── /data                 - All data files
│   ├── /trained_models   - Serialized .pkl models
│   ├── /datasets         - Raw & processed data
│   └── /state            - Runtime state files
├── /pages                - Streamlit multi-page app
├── /config               - Configuration files
├── /utils                - Utility functions
└── /docs                 - Documentation

Getting Started:
1. Check README.md for setup instructions
2. Install dependencies: pip install -r requirements.txt
3. Run: streamlit run src/dashboard.py

For detailed project info, see README.md
"""
