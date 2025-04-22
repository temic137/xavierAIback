# Xavier AI Backend

This is the backend server for the Xavier AI chatbot platform.

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
