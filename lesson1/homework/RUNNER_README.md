# Evening Agent Runner Scripts

Easy-to-use command scripts for running the evening agent with different publishers.

## 🚀 Quick Start

### macOS/Linux

```bash
# Run with default publisher (kurier)
./homework/run_evening_agent.sh

# Run with specific publisher
./homework/run_evening_agent.sh tagesspiegel

# Or make it executable and run from homework directory
cd homework
./run_evening_agent.sh tagesspiegel
```

## 📋 Available Publishers

The scripts accept any publisher name that has snapshots in the `snapshots/` directory:

- `kurier` - Kurier.de
- `tagesspiegel` - Tagesspiegel.de

## ⚙️ What the Scripts Do

1. **Check environment setup**
   - Verifies `.env` file exists
   - Warns if API keys are missing

2. **Activate virtual environment**
   - Auto-activates `venv` if not already active
   - Shows error if venv not found

3. **Run the agent**
   - Executes `python -m homework.evening_agent --publisher <name>`
   - Passes through all agent output
   - Shows completion status

## 🔧 Configuration

The scripts automatically:
- Load environment variables from `.env`
- Activate the Python virtual environment
- Set the working directory correctly

### Required Environment Variables

Create a `.env` file in the project root:

```bash
ANTHROPIC_API_KEY=sk-ant-...
FIRECRAWL_API_KEY=fc-...
```

## 💡 Examples

### Basic Usage
```bash
# Analyze Tagesspiegel last 24h
./homework/run_evening_agent.sh tagesspiegel
```

### From Different Directories
```bash
# Works from project root
./homework/run_evening_agent.sh kurier

# Works from homework directory
cd homework
./run_evening_agent.sh tagesspiegel
```

## 🐛 Troubleshooting

### "Permission denied" (macOS/Linux)
Make the script executable:
```bash
chmod +x homework/run_evening_agent.sh
```

### "Virtual environment not found"
Create and set up the virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### "ANTHROPIC_API_KEY not found"
Create `.env` file in project root:
```bash
echo "ANTHROPIC_API_KEY=your-key-here" > .env
echo "FIRECRAWL_API_KEY=your-key-here" >> .env
```

## 📊 Output

The scripts provide colored output showing:
- ✅ Configuration status
- 🤖 Agent progress (tool calls, reasoning)
- 💰 Cost and usage statistics
- ⏱️ Execution time

Example output:
```
═══════════════════════════════════════════════════════════
🤖 Evening Agent Runner
═══════════════════════════════════════════════════════════
Publisher: tagesspiegel
═══════════════════════════════════════════════════════════

✓ Virtual environment activated

Starting analysis...

🤖 Agent: Retrieving data...
🔧 Agent using tool: get_top_articles_for_period
🤖 Agent: Found 47 articles. Analyzing clusters...

💰 Cost: $0.2341
⏱ Duration: 67.23s (API: 34.12s)

✓ Analysis complete!
```

## 🔗 Related Files

- `evening_agent.py` - Main agent implementation
- `config.py` - Publisher configuration
- `snapshots/` - Time-series data storage
- `utils.py` - Shared utilities

## 📝 Notes

- Scripts automatically handle virtual environment activation
- Working directory is set to project root
- All Python module imports work correctly
- Environment variables loaded from `.env`

## 🎯 Advanced Usage

### Testing Firecrawl Connection
Edit `evening_agent.py` line 343 to test:
```python
prompt = "Check that FireCrawl MCP is accessible to you."
```

Then run:
```bash
./homework/run_evening_agent.sh tagesspiegel
```

### Full Analysis
Uncomment line 341 in `evening_agent.py`:
```python
prompt = f"Analyze the homepage for {publisher} over the last 24 hours..."
```

### Multiple Publishers in Sequence
```bash
#!/bin/bash
for publisher in kurier tagesspiegel; do
    echo "Analyzing $publisher..."
    ./homework/run_evening_agent.sh "$publisher"
    echo "---"
done
```

