# Supabase Setup Guide

Complete guide to set up Supabase for the Document E-Sign Portal.

---

## Step 1: Create Supabase Account

1. Go to [supabase.com](https://supabase.com)
2. Click **"Start your project"**
3. Sign up using GitHub (recommended) or Email.

---

## Step 2: Create New Project

1. Click **"New Project"** in the dashboard.
2. Select your Organization.
3. Fill in details:
   - **Name**: `document-esign-portal`
   - **Database Password**: Generate a strong password.
   - **Region**: Choose closest to your users.
4. Click **"Create new project"**.
5. Wait ~2 minutes for it to be ready.

---

## Step 3: Get API Credentials

1. In your project, go to **Settings** (gear icon) → **API**.
2. Find `Project URL` and `anon` `public` key.
3. Update your `.env` file locally:

   ```bash
   SUPABASE_URL="https://your-project-id.supabase.co"
   SUPABASE_KEY="your-anon-key"
   ```

---

## Step 4: Run the "One-Click" Setup Script

This script sets up **Database Tables**, **Security Policies (RLS)**, and **Storage Buckets** automatically.

1. Go to **SQL Editor** in the Supabase sidebar.
2. Click **"New query"**.
3. Copy the **entire** contents of the file `database/schema.sql` from this project.
4. Paste it into the SQL Editor.
5. Click **"Run"** (bottom right).

> **Success?** You should see "Success" in the results pane.

### Verify Installation:
- **Table Editor**: You should see tables: `profiles`, `tenants`, `tenant_members`, `documents`.
- **Storage**: You should see a bucket named `documents`.

---

## Step 5: Configure Auth (Optional)

1. **Email Templates**: Go to **Authentication** → **Email Templates**. Customize the "Magic Link" template if you wish.
2. **SMTP**: For production, configure **Settings** → **Authentication** → **SMTP Settings** with SendGrid or similar.

---

## Step 6: Test It

1. Restart your Streamlit app:
   ```bash
   python3 -m streamlit run app.py
   ```
2. Open the app in your browser.
3. Enter your email to login (Magic Link).
4. Verify OTP from your email.
5. Upload a PDF to the Dashboard.

---

## Troubleshooting

- **Storage Bucket Missing?** If the SQL script failed to create the bucket (sometimes permissions vary), go to **Storage** → **New Bucket** → Name it `documents` → Keep it Private. The policies from the SQL script will still work.
- **"Policy already exists"**: If you run the script twice, you might get errors. This is fine, the script is designed to be safe but policies might conflict if changed manually.
