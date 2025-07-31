#!/bin/bash
pip install -r requirements.txt
streamlit run streamlit_chat_server.py --server.port 8501 --server.address 0.0.0.0