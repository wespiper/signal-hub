# MCP Tools Reference

Signal Hub provides several MCP (Model Context Protocol) tools that integrate seamlessly with Claude Code. Each tool is designed for specific use cases in code exploration and understanding.

## Available Tools

### 🔍 search_code

Search for code semantically across your indexed codebase.

#### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `query` | string | Yes | - | Natural language search query |
| `limit` | integer | No | 10 | Maximum number of results to return |
| `threshold` | float | No | 0.7 | Minimum similarity score (0.0-1.0) |
| `file_types` | array | No | [] | Filter by file extensions (e.g., ["py", "js"]) |
| `exclude_patterns` | array | No | [] | Patterns to exclude from results |

#### Request Example

```json
{
  "tool": "search_code",
  "arguments": {
    "query": "function that validates email addresses",
    "limit": 5,
    "threshold": 0.8,
    "file_types": ["py"]
  }
}
```

#### Response Example

```json
{
  "results": [
    {
      "file": "src/validators.py",
      "line_start": 42,
      "line_end": 58,
      "score": 0.89,
      "content": "def validate_email(email: str) -> bool:\n    \"\"\"Validate email format using regex.\"\"\"\n    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'\n    return bool(re.match(pattern, email))",
      "language": "python",
      "metadata": {
        "function_name": "validate_email",
        "complexity": "low",
        "imports": ["re"]
      }
    }
  ],
  "total_matches": 5,
  "search_time_ms": 127
}
```

#### Error Responses

| Error Code | Description | Solution |
|------------|-------------|----------|
| `NO_INDEX` | No index found for project | Run `signal-hub index` first |
| `INVALID_QUERY` | Query too short or invalid | Provide more descriptive query |
| `THRESHOLD_ERROR` | Invalid threshold value | Use value between 0.0 and 1.0 |

---

### 💡 explain_code

Get detailed explanations of code with relevant context automatically assembled.

#### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `query` | string | Yes | - | What you want explained |
| `context_size` | integer | No | 2000 | Maximum context tokens |
| `include_related` | boolean | No | true | Include related code |
| `detail_level` | string | No | "medium" | "brief", "medium", or "detailed" |

#### Request Example

```json
{
  "tool": "explain_code",
  "arguments": {
    "query": "How does the authentication middleware work?",
    "context_size": 3000,
    "detail_level": "detailed"
  }
}
```

#### Response Example

```json
{
  "explanation": "The authentication middleware follows a token-based approach...",
  "relevant_files": [
    {
      "file": "src/middleware/auth.py",
      "relevance": 0.95,
      "summary": "Main authentication middleware implementation"
    },
    {
      "file": "src/models/user.py",
      "relevance": 0.82,
      "summary": "User model with authentication methods"
    }
  ],
  "code_snippets": [
    {
      "file": "src/middleware/auth.py",
      "lines": "15-45",
      "content": "class AuthMiddleware:..."
    }
  ],
  "model_used": "sonnet",
  "tokens_used": 2847
}
```

---

### 🔄 find_similar

Find code similar to a given snippet or pattern.

#### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `code` | string | Yes* | - | Code snippet to find similar to |
| `file_path` | string | Yes* | - | File path to find similar to |
| `limit` | integer | No | 10 | Maximum results |
| `min_similarity` | float | No | 0.7 | Minimum similarity score |

*Note: Provide either `code` or `file_path`, not both.

#### Request Example

```json
{
  "tool": "find_similar",
  "arguments": {
    "code": "def calculate_total(items):\n    return sum(item.price * item.quantity for item in items)",
    "limit": 5,
    "min_similarity": 0.8
  }
}
```

#### Response Example

```json
{
  "similar_code": [
    {
      "file": "src/utils/billing.py",
      "similarity": 0.92,
      "line_start": 78,
      "line_end": 82,
      "content": "def compute_subtotal(line_items):\n    return sum(line.amount * line.qty for line in line_items)",
      "differences": ["Parameter name", "Property names"]
    }
  ]
}
```

---

### 📋 get_context

Get relevant context for your current task or question.

#### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `task` | string | Yes | - | Description of your current task |
| `current_file` | string | No | - | File you're currently working on |
| `max_files` | integer | No | 5 | Maximum files to include |
| `include_tests` | boolean | No | false | Include test files |
| `include_docs` | boolean | No | true | Include documentation |

#### Request Example

```json
{
  "tool": "get_context",
  "arguments": {
    "task": "Adding a new payment method to the checkout process",
    "current_file": "src/checkout/payment.py",
    "max_files": 8,
    "include_tests": true
  }
}
```

#### Response Example

```json
{
  "context": {
    "summary": "The checkout process involves several components...",
    "key_files": [
      {
        "file": "src/checkout/payment.py",
        "role": "Payment processing logic",
        "key_functions": ["process_payment", "validate_card"]
      },
      {
        "file": "src/models/payment_method.py",
        "role": "Payment method data model",
        "key_classes": ["PaymentMethod", "CreditCard"]
      }
    ],
    "related_tests": [
      "tests/test_payment.py",
      "tests/integration/test_checkout.py"
    ],
    "suggested_approach": "To add a new payment method, you'll need to..."
  }
}
```

---

### ⬆️ escalate_query

Manually escalate a query to a more powerful model.

#### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `query` | string | Yes | - | Query to process |
| `target_model` | string | Yes | - | "sonnet" or "opus" |
| `reason` | string | No | - | Why escalation is needed |
| `session_escalate` | boolean | No | false | Escalate entire session |

#### Request Example

```json
{
  "tool": "escalate_query",
  "arguments": {
    "query": "Debug this complex race condition in the async code",
    "target_model": "opus",
    "reason": "Complex concurrency issue requiring deep analysis"
  }
}
```

#### Response Example

```json
{
  "result": "After analyzing the code, the race condition occurs when...",
  "model_used": "opus",
  "escalation_reason": "Complex concurrency issue requiring deep analysis",
  "cost_increase": "5.2x",
  "tokens_used": 4521
}
```

## Common Patterns

### Combining Tools

Tools work best when used together:

```python
# 1. Search for relevant code
results = search_code("payment processing")

# 2. Get detailed explanation
explanation = explain_code("How does payment processing work?")

# 3. Find similar patterns
similar = find_similar(code=results[0].content)

# 4. Get full context
context = get_context("Refactoring payment system")
```

### Query Optimization

#### Use Specific Queries
```json
// ❌ Too vague
{"query": "database stuff"}

// ✅ Specific and clear
{"query": "database connection pooling implementation"}
```

#### Leverage Metadata
```json
{
  "query": "React components",
  "file_types": ["jsx", "tsx"],
  "exclude_patterns": ["**/node_modules/**", "**/*.test.js"]
}
```

### Cost Management

#### Check Model Routing
```python
# Simple queries route to Haiku (cheap)
search_code("list all functions")  # → Haiku

# Complex queries route to Sonnet/Opus
explain_code("analyze security vulnerabilities")  # → Opus
```

#### Use Caching
```python
# Similar queries use cache
search_code("user authentication")  # First call
search_code("user auth logic")     # Cache hit!
```

## Error Handling

### Retry Logic

```python
async def search_with_retry(query, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await search_code(query)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Graceful Degradation

```python
try:
    # Try with high threshold
    results = search_code(query, threshold=0.9)
except NoResultsError:
    # Fall back to lower threshold
    results = search_code(query, threshold=0.7)
```

## Performance Tips

1. **Batch Operations**: Process multiple queries together
2. **Use Appropriate Limits**: Don't request more results than needed
3. **Filter Early**: Use file_types and exclude_patterns
4. **Cache Warming**: Pre-search common queries
5. **Index Optimization**: Keep index up-to-date

## Rate Limits

| Tool | Rate Limit | Burst |
|------|------------|-------|
| search_code | 100/min | 20 |
| explain_code | 50/min | 10 |
| find_similar | 100/min | 20 |
| get_context | 50/min | 10 |
| escalate_query | 20/min | 5 |

## Versioning

All tools follow semantic versioning. Current version: `1.0.0`

Check version compatibility:
```bash
signal-hub tools --version
```