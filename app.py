import streamlit.web.cli as stcli
import sys
import os

if __name__ == '__main__':
    sys.argv = ['streamlit', 'run', 'streamlit_app/app.py']
    sys.exit(stcli.main())
