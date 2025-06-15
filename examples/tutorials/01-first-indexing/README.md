# Tutorial 1: Index Your First Repository

**Time Required**: 15 minutes  
**Difficulty**: Beginner  
**Prerequisites**: Signal Hub installed

## Learning Objectives

By the end of this tutorial, you will:
- ✅ Set up Signal Hub for a project
- ✅ Configure indexing parameters  
- ✅ Perform your first semantic search
- ✅ Understand how Signal Hub processes code

## Setup

### 1. Get the Sample Project

We'll use a simple Python web app for this tutorial:

```bash
# Clone the sample project
git clone https://github.com/signal-hub/tutorial-webapp.git
cd tutorial-webapp

# Look at the project structure
ls -la
```

You should see:
```
tutorial-webapp/
├── app.py           # Main Flask application
├── models.py        # Database models
├── auth.py          # Authentication logic
├── utils/           # Utility functions
├── templates/       # HTML templates
├── tests/           # Test files
└── requirements.txt
```

### 2. Initialize Signal Hub

```bash
signal-hub init
```

This creates `signal-hub.yaml`. Let's examine it:

```bash
cat signal-hub.yaml
```

## Step 1: Configure Indexing (3 minutes)

Edit `signal-hub.yaml` to customize what gets indexed:

```yaml
# signal-hub.yaml
indexing:
  # Include Python files and templates
  include_patterns:
    - "**/*.py"
    - "templates/**/*.html"
    
  # Exclude test files for now
  exclude_patterns:
    - "**/__pycache__/**"
    - "**/venv/**"
    - "tests/**"  # We'll index tests separately
    
  # Chunking configuration
  chunk_size: 500
  chunk_overlap: 50
```

### Understanding the Configuration

- **include_patterns**: Uses glob patterns to select files
- **exclude_patterns**: Prevents indexing unnecessary files
- **chunk_size**: How large each searchable chunk should be
- **chunk_overlap**: Overlap between chunks for better context

## Step 2: Run Indexing (5 minutes)

Now let's index the codebase:

```bash
signal-hub index . --verbose
```

### Expected Output

```
🔍 Scanning for files...
  ✓ Found 12 Python files
  ✓ Found 5 HTML templates
  ✓ Total: 17 files to index

📝 Parsing files...
  ✓ Extracted 45 functions
  ✓ Extracted 8 classes
  ✓ Generated 127 code chunks

🧠 Creating embeddings...
  ✓ Generated 127 embeddings
  ✓ Stored in vector database

✨ Indexing complete!
  Files: 17
  Chunks: 127
  Time: 12.3 seconds
  Storage: 2.1 MB
```

### What Just Happened?

1. **Scanning**: Signal Hub found all matching files
2. **Parsing**: Extracted code structure and metadata
3. **Chunking**: Split code into semantic chunks
4. **Embedding**: Created vector representations
5. **Storage**: Saved everything for fast retrieval

## Step 3: Test Semantic Search (5 minutes)

Let's test different types of searches:

### Basic Function Search

```bash
signal-hub search "function that handles user login"
```

Expected result:
```python
# auth.py (lines 23-41)
def login_user(username: str, password: str) -> Optional[User]:
    """Authenticate user and create session."""
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        session['user_id'] = user.id
        return user
    
    return None
```

### Conceptual Search

```bash
signal-hub search "how is data validated before saving to database"
```

This finds validation logic even without exact keyword matches!

### Architecture Search

```bash
signal-hub search "what databases does this app use"
```

Signal Hub understands context and finds:
- SQLAlchemy imports
- Database models
- Configuration settings

## Step 4: Understand Search Results (2 minutes)

Let's examine a search result in detail:

```bash
signal-hub search "error handling for failed payments" --json
```

```json
{
  "results": [
    {
      "file": "app.py",
      "score": 0.87,
      "line_start": 156,
      "line_end": 172,
      "content": "try:\n    payment_result = process_payment(order)\nexcept PaymentError as e:\n    log_error(f'Payment failed: {e}')\n    return render_template('payment_failed.html')",
      "metadata": {
        "function": "checkout",
        "imports": ["PaymentError", "process_payment"],
        "complexity": "medium"
      }
    }
  ],
  "search_time_ms": 47,
  "model_used": "text-embedding-3-small"
}
```

### Key Points:
- **score**: Similarity score (0-1, higher is better)
- **metadata**: Extracted code information
- **search_time_ms**: Search completed in 47ms!

## Advanced: Index Different File Types

### Add JavaScript Files

```bash
# Update config to include JS
echo '    - "static/**/*.js"' >> signal-hub.yaml

# Update the index
signal-hub index . --update
```

### Index Test Files Separately

```bash
# Index only tests with a tag
signal-hub index tests/ --tag tests
```

## Troubleshooting

### Issue: "No results found"

Your query might be too specific. Try:
```bash
# More general query
signal-hub search "payment" --threshold 0.6
```

### Issue: "Index out of date"

Update after code changes:
```bash
signal-hub index . --update --changed-only
```

## 🎯 Challenge Tasks

Try these searches on your own:

1. Find all database models
2. Search for authentication decorators
3. Find error handling patterns
4. Look for SQL queries

## What You Learned

- ✅ How to configure Signal Hub indexing
- ✅ Understanding include/exclude patterns
- ✅ Running indexing and interpreting output
- ✅ Performing semantic searches
- ✅ Reading and understanding results

## Next Steps

- 📚 Continue to [Tutorial 2: Smart Routing](../02-smart-routing/)
- 🔧 Learn about [Configuration Options](../../docs/user-guide/configuration.md)
- 🚀 Explore [Advanced Indexing](../../docs/user-guide/indexing.md)

---

**Tip**: Keep your index updated! Run `signal-hub index . --watch` to automatically update when files change.