# Document E-Sign Portal

A secure multi-tenant document portal with OTP-based authentication, PDF storage, and document sharing capabilities.

## Features

- **OTP Authentication** - Email-based one-time password login
- **PDF Storage** - Upload and manage multiple PDF documents
- **Document Sharing** - Share documents via email with OTP-protected access
- **Multi-Tenant** - Isolated document storage per organization
- **Cloud-Ready** - Deployable to Streamlit Cloud

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Supabase (PostgreSQL + Auth + Storage)
- **Email**: Resend (for share notifications)
- **Deployment**: Streamlit Community Cloud

## Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Copy your Project URL and anon key

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
RESEND_API_KEY=your_resend_api_key  # Optional: for email notifications
```

### 3. Run Database Migrations

Execute the following SQL files in Supabase SQL Editor (in order):

1. `database/schema.sql` - Base schema
2. `database/share_schema.sql` - Document sharing tables
3. `database/fix_rls.sql` - Row-level security policies

### 4. Create Storage Bucket

In Supabase Dashboard → Storage → Create bucket named `documents`.

### 5. Install & Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Usage

### Logging In
1. Enter your email on the Login page
2. Check your email for the OTP code
3. Enter the OTP to access your dashboard

### Managing Documents
- **Upload**: Click "Upload Document" to add PDF files
- **View**: Click on any document to preview it
- **Delete**: Remove documents you no longer need

### Sharing Documents
1. Click the share button on any document
2. Enter the recipient's email address
3. The recipient receives an email with a secure link
4. They verify with OTP to access the shared document

## Deployment

### Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo and deploy
4. Add secrets in Streamlit Cloud settings:
   ```toml
   SUPABASE_URL = "your_supabase_url"
   SUPABASE_KEY = "your_supabase_anon_key"
   RESEND_API_KEY = "your_resend_api_key"
   ```

## Project Structure

```
├── app.py                      # Main entry point
├── pages/
│   ├── 1_📧_Login.py           # Email login page
│   ├── 2_🔐_Verify_OTP.py      # OTP verification
│   ├── 3_📁_Dashboard.py       # Document management
│   └── 4_🔗_View_Document.py   # Shared document viewer
├── utils/
│   ├── __init__.py
│   ├── supabase_client.py      # Supabase connection
│   ├── auth_utils.py           # Authentication helpers
│   ├── storage_utils.py        # File upload/download
│   ├── email_utils.py          # Email notifications
│   └── share_utils.py          # Document sharing logic
├── database/
│   ├── schema.sql              # Base database schema
│   ├── share_schema.sql        # Sharing tables
│   └── fix_rls.sql             # Security policies
├── assets/
│   └── styles.css              # Custom styling
├── requirements.txt
└── .env.example
```

## License

MIT
