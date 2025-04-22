# Xavier AI Backend

This is the backend server for the Xavier AI chatbot platform.

## Important Note

This repository has been cleaned to remove sensitive information. The `clean-branch` should be set as the default branch on GitHub. If you're working with the old `main` branch, please switch to this branch instead.

## Setup Instructions

### Environment Variables

1. Copy the `.env.example` file to a new file named `.env`:
   ```
   cp .env.example .env
   ```

2. Edit the `.env` file and add your actual API keys and credentials.

### Installation

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running the Server

```
python app.py
```

## Security Notes

- Never commit sensitive information like API keys or credentials to the repository
- Always use environment variables for sensitive information
- Make sure `.env` is in your `.gitignore` file
- If you need to remove sensitive information from Git history, consider using tools like BFG Repo-Cleaner or git-filter-repo
