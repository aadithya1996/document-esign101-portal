# Document E-Sign Portal

A secure multi-tenant document portal with OTP-based authentication and PDF storage.

## Features

- 🔐 **OTP Authentication** - Email-based one-time password login
- 📁 **PDF Storage** - Upload and manage multiple PDF documents
- 👥 **Multi-Tenant** - Isolated document storage per organization
- ☁️ **Cloud-Ready** - Deployable to Streamlit Cloud

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Supabase (PostgreSQL + Auth + Storage)
- **Deployment**: Streamlit Community Cloud

## Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Copy your Project URL and anon key

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

### 3. Run Database Migrations

Execute the SQL in `database/schema.sql` in Supabase SQL Editor.

### 4. Create Storage Bucket

In Supabase Dashboard → Storage → Create bucket named `documents`.

### 5. Install & Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo and deploy
4. Add secrets in Streamlit Cloud settings:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

## Project Structure

```
├── app.py                  # Main entry point
├── pages/                  # Streamlit pages
│   ├── 1_📧_Login.py
│   ├── 2_🔐_Verify_OTP.py
│   └── 3_📁_Dashboard.py
├── utils/                  # Utility functions
│   ├── supabase_client.py
│   ├── auth_utils.py
│   └── storage_utils.py
├── database/
│   └── schema.sql          # Database schema
└── assets/
    └── styles.css          # Custom styling
```
