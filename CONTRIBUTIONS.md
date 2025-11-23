# Contribution Guidelines for edu-ai-product-engineer-s3

Welcome to **Season 3** of the AI Product Engineer course! This guide will help you set up your environment, complete homework assignments, and submit your work for review.

## Overview: How This Course Works

Unlike traditional courses where everyone works in one shared repository, **you'll work in your own fork** and submit homework via pull requests. This mirrors real-world software development workflows and gives you portfolio-worthy commit history.

**The Flow:**
1. Fork this repository → You get your own copy
2. Complete homework in your fork → Build in your workspace
3. Create pull requests → Submit for review
4. Get feedback → Iterate and improve
5. Merge your own PRs → Close the loop

## 1. Initial Setup (One-Time)

### Step 1: Fork the Repository

Click the **Fork** button at the top right of this repository page. This creates your personal copy at:
```
https://github.com/YOUR_USERNAME/edu-ai-product-engineer-s3
```

### Step 2: Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/edu-ai-product-engineer-s3.git
cd edu-ai-product-engineer-s3
```

### Step 3: Set Upstream Remote

This allows you to pull new lessons as they're released:

```bash
git remote add upstream https://github.com/BayramAnnakov/edu-ai-product-engineer-s3.git
```

Verify your remotes:
```bash
git remote -v
# Should show:
# origin    https://github.com/YOUR_USERNAME/edu-ai-product-engineer-s3.git (your fork)
# upstream  https://github.com/BayramAnnakov/edu-ai-product-engineer-s3.git (course repo)
```

### Step 4: Set Up Lesson Environment

```bash
cd lesson1
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Follow the detailed setup in [lesson1/SETUP_GUIDE.md](lesson1/SETUP_GUIDE.md).

## 2. Homework Submission Workflow

### For Each Lesson Assignment

#### Step 1: Sync with Upstream (Get Latest Changes)

Before starting homework, pull any updates from the main course repository:

```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main  # Update your fork
```

#### Step 2: Create a Homework Branch

Use a descriptive branch name following this format:

```bash
git checkout -b lesson1-homework
# Or for specific features:
git checkout -b lesson1-custom-agent
git checkout -b lesson2-research-tool
```

**Branch Naming Conventions:**
- `lessonN-homework` - For completing the standard assignment
- `lessonN-feature-description` - For bonus challenges or experiments
- `lessonN-bugfix-description` - For fixing issues

#### Step 3: Complete Your Homework

Work in the appropriate lesson directory:

```bash
cd lesson1
# Create your files, modify code, etc.
```

**Required Files in Your Submission:**
1. **Your Implementation** - Working code that meets homework requirements
2. **README.md** - Document your approach:
   - What you built
   - Design decisions you made
   - Challenges you encountered
   - How you solved them
3. **Test Results** - Screenshots or logs showing your code works
4. **.env.example** - Template for any required API keys (NEVER commit actual .env!)

**Example Structure:**
```
lesson1/
├── my_custom_agent.py           # Your implementation
├── README_FirstName.md          # Your documentation
├── test_results.txt             # Output logs
└── screenshots/                 # Visual proof
    ├── chained_failure.png
    └── agent_success.png
```

#### Step 4: Commit Your Work

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "Lesson 1: Implement LinkedIn outreach agent with self-correction

- Built agentic workflow using Claude Agent SDK
- Added custom URL normalization tool
- Tested with 10 messy LinkedIn URLs (90% success rate)
- Added retry logic for EnrichLayer API failures"
```

**Commit Message Best Practices:**
- First line: Brief summary (50 chars or less)
- Blank line
- Detailed explanation of what and why
- Reference any issues: "Fixes #123"

#### Step 5: Push to Your Fork

```bash
git push origin lesson1-homework
```

#### Step 6: Create Pull Request

1. Go to your fork on GitHub: `https://github.com/YOUR_USERNAME/edu-ai-product-engineer-s3`
2. Click **"Pull requests"** → **"New pull request"**
3. Set the base correctly:
   - **Base repository**: `YOUR_USERNAME/edu-ai-product-engineer-s3` (your fork)
   - **Base branch**: `main`
   - **Head branch**: `lesson1-homework`

4. Fill in the PR template:

```markdown
## Lesson 1 Homework: Chained vs Agentic Workflows

### What I Built
[Brief description of your implementation]

### Requirements Completed
- [x] Implemented chained workflow
- [x] Implemented agentic workflow
- [x] Tested with messy LinkedIn URLs
- [x] Calculated ROI for my use case
- [ ] Bonus: Added custom tool

### Challenges & Solutions
1. **Challenge**: EnrichLayer API rate limits
   **Solution**: Added exponential backoff retry logic

2. **Challenge**: Agent making too many attempts
   **Solution**: Limited max retries to 3

### Test Results
- Clean URLs: 100% success (10/10)
- Messy URLs (chained): 40% success (4/10)
- Messy URLs (agentic): 90% success (9/10)

### Questions for Review
1. Is my retry logic too aggressive?
2. Should I cache EnrichLayer responses?

### Time Spent
~4 hours (3 hours coding, 1 hour testing)

### Screenshots
[Attach or link screenshots showing your code working]
```

5. Click **"Create pull request"**

#### Step 7: Share for Review

Post your PR link in the course chat:

```
Lesson 1 homework submitted! 🚀
PR: https://github.com/YOUR_USERNAME/edu-ai-product-engineer-s3/pull/1
```

## 3. Getting Feedback

### Instructor Review

I'll review your PR and provide feedback as comments:
- ✅ **Approve** - Meets requirements, great work!
- 💬 **Comment** - Suggestions for improvement
- 🔄 **Request changes** - Needs updates before merging

### Peer Review

**Review Your Classmates' Work:**
1. Browse the course chat for PR links
2. Read their code and documentation
3. Leave constructive feedback:
   - What you liked
   - What you learned
   - Suggestions for improvement

**Example Peer Review Comment:**
```
Great implementation! I really like how you handled the rate limiting issue.

One suggestion: You could extract the retry logic into a decorator function
to make it reusable across different API calls. Something like:

@retry(max_attempts=3, backoff=exponential)
def fetch_profile(url):
    ...

This would make your code more DRY. Check out the `tenacity` library!
```

### Addressing Feedback

If changes are requested:

```bash
# Make your changes
git add .
git commit -m "Address review feedback: Add retry decorator"
git push origin lesson1-homework
# The PR updates automatically!
```

## 4. Merging Your Work

Once your PR is approved (by instructor or self-approved after incorporating feedback):

1. Click **"Merge pull request"** on GitHub
2. Choose merge strategy:
   - **"Create a merge commit"** (recommended) - Preserves full history
   - **"Squash and merge"** - Combines commits (cleaner history)
   - **"Rebase and merge"** - Linear history (advanced)

3. Delete the branch (optional but recommended):
```bash
git branch -d lesson1-homework
git push origin --delete lesson1-homework
```

## 5. Preparing for Next Lesson

### Sync with Upstream

When a new lesson is released:

```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
```

### Start Fresh

```bash
git checkout -b lesson2-homework
cd lesson2
# Begin new homework
```

## 6. Code Quality Standards

### Python Best Practices

- **Type hints**: Use them for better code clarity
  ```python
  def fetch_profile(url: str) -> dict[str, Any]:
      ...
  ```

- **Docstrings**: Document all functions
  ```python
  def normalize_url(url: str) -> str:
      """
      Normalize LinkedIn URL to standard format.

      Args:
          url: Raw LinkedIn profile URL (may be messy)

      Returns:
          Normalized URL with https://www.linkedin.com/in/ prefix

      Example:
          >>> normalize_url("linkedin.com/in/jenhsunhuang")
          'https://www.linkedin.com/in/jenhsunhuang/'
      """
  ```

- **Error handling**: Handle expected failures gracefully
  ```python
  try:
      profile = await fetch_profile(url)
  except EnrichLayerError as e:
      logger.error(f"Failed to fetch profile: {e}")
      return None
  ```

- **Code formatting**: Use `black` for consistent style
  ```bash
  pip install black
  black lesson1/
  ```

- **Linting**: Use `ruff` to catch issues
  ```bash
  pip install ruff
  ruff check lesson1/
  ```

### Project Documentation

Every homework submission should include a README with:

1. **Overview** - What problem does this solve?
2. **Architecture** - High-level design decisions
3. **Setup** - How to run your code
4. **Results** - Performance metrics, screenshots
5. **Learnings** - What you discovered
6. **Future Work** - What you'd improve with more time

**Example README Template:**
```markdown
# Lesson 1: LinkedIn Outreach Agent

## Overview
Built an agentic workflow that self-corrects messy LinkedIn URLs,
achieving 90% success vs 40% for traditional chained approach.

## Architecture
- **Agent**: Claude Sonnet 4.5 with ReAct pattern
- **Tools**: fetch_linkedin_profile, normalize_url
- **Self-correction**: 4-step URL fixing strategy

## Setup
\`\`\`bash
source venv/bin/activate
python my_custom_agent.py
\`\`\`

## Results
Tested with 20 LinkedIn URLs (10 clean, 10 messy):
- Chained: 14/20 success (70%)
- Agentic: 19/20 success (95%)

See [test_results.txt](test_results.txt) for full logs.

## Key Learnings
1. Agents excel when input quality is unpredictable
2. Proper prompt engineering is crucial for self-correction
3. Tool design impacts agent reasoning quality

## Future Improvements
- [ ] Add caching for repeated URLs
- [ ] Implement parallel URL processing
- [ ] Build evaluation framework for systematic testing
```

## 7. Common Pitfalls to Avoid

### ❌ Don't: Commit Secrets
```bash
# NEVER commit these:
.env
*_api_key.txt
credentials.json
```

Always use `.env.example` templates:
```bash
# .env.example (SAFE to commit)
ANTHROPIC_API_KEY=your_key_here
ENRICHLAYER_API_KEY=your_key_here

# .env (in .gitignore, NOT committed)
ANTHROPIC_API_KEY=sk-ant-actual-secret-key
```

### ❌ Don't: Create PR to Main Course Repo

**Wrong:**
```
Base: BayramAnnakov/edu-ai-product-engineer-s3 (main)
Head: YOUR_USERNAME/edu-ai-product-engineer-s3 (lesson1-homework)
```

**Right:**
```
Base: YOUR_USERNAME/edu-ai-product-engineer-s3 (main)
Head: YOUR_USERNAME/edu-ai-product-engineer-s3 (lesson1-homework)
```

### ❌ Don't: Work Directly on Main Branch

Always create a feature branch:
```bash
# Bad
git checkout main
# make changes
git commit -m "homework"

# Good
git checkout -b lesson1-homework
# make changes
git commit -m "homework"
```

### ❌ Don't: Forget to Sync Before Starting

Always pull latest changes first:
```bash
git fetch upstream
git merge upstream/main
```

## 8. Getting Help

### Before Asking for Help

1. **Check Documentation**
   - Lesson README
   - SETUP_GUIDE.md
   - TROUBLESHOOTING.md

2. **Run Verification Script**
   ```bash
   python verify_setup.py
   ```

3. **Search Existing Issues**
   - Check course chat history
   - Look at other students' PRs

### How to Ask for Help

**Good Question:**
```
I'm getting a 404 error from EnrichLayer API even with correct URL format.

What I tried:
1. Verified API key is valid (tested with curl)
2. Checked URL format matches docs
3. Added logging to see exact request

Error message:
```
EnrichLayerError: 404 - Profile not found
```

Code snippet:
[paste minimal reproducible example]

Any ideas what might be wrong?
```

**Not Helpful:**
```
My code doesn't work. Help!
```

### Support Channels

- **Course Chat** - Quick questions, discussion
- **GitHub Issues** - Bug reports, feature requests
- **Office Hours** - Live troubleshooting, code review
- **Peer Review** - Learning from classmates

## 9. Bonus Challenges & Extra Credit

Want to go beyond the standard homework?

### Bonus Ideas for Lesson 1

1. **Advanced Self-Correction** (+10 pts)
   - Implement fuzzy matching for LinkedIn usernames
   - Add company domain lookup fallback

2. **Observability** (+15 pts)
   - Add structured logging
   - Track metrics (success rate, avg attempts, cost)
   - Create dashboard with plots

3. **Production Hardening** (+20 pts)
   - Add rate limiting
   - Implement caching layer
   - Handle edge cases (private profiles, deleted accounts)

4. **Testing** (+15 pts)
   - Unit tests for URL normalization
   - Integration tests with mocked API
   - Property-based testing with Hypothesis

5. **Your Own Use Case** (+25 pts)
   - Apply agent pattern to different domain
   - Document why it's better than chained approach
   - Include real business metrics

**How to Submit Bonus Work:**
1. Create separate branch: `lesson1-bonus-observability`
2. Complete the challenge
3. Create separate PR with clear documentation
4. Reference bonus challenge in PR description

## 10. Academic Integrity

### What's Allowed ✅

- Discussing concepts and approaches with classmates
- Sharing debugging strategies
- Reviewing each other's code via PRs
- Using AI assistants (Claude, ChatGPT) for learning
- Referencing official documentation
- Building on course examples

### What's Not Allowed ❌

- Copying code directly from classmates without attribution
- Submitting someone else's work as your own
- Sharing complete solutions before the deadline
- Using unauthorized external services during assessments

### Using AI Assistants

AI assistants are **encouraged** for learning, but:

1. **Understand what you submit** - Don't copy-paste without comprehension
2. **Document AI usage** - Mention in README if Claude/ChatGPT helped significantly
3. **Explain your reasoning** - PRs should show YOUR thought process

**Example Attribution:**
```markdown
## AI Assistant Usage

Used Claude Code to help debug the retry logic after getting stuck
on asyncio event loop issues. Claude suggested using `asyncio.create_task()`
instead of `await` for parallel execution, which I researched and adapted
for my use case.
```

## 11. Portfolio Tips

This course is designed to build your portfolio. Make it count!

### Maximize Portfolio Value

1. **Write for Future Employers**
   - Clear README that explains business value
   - Professional code with proper documentation
   - Metrics showing real impact

2. **Pin Your Best Work**
   - After lesson 5, pin the repo to your GitHub profile
   - Add topics: `ai`, `agents`, `llm`, `product-engineering`

3. **Share Your Journey**
   - Blog about what you learned
   - Post milestones on LinkedIn
   - Give a talk at a meetup

4. **Keep Building**
   - Don't stop at homework - extend the project
   - Deploy to production
   - Get real users

### Example Portfolio Project

**Before Course:**
Empty GitHub profile

**After Lesson 1:**
Working agent with test results

**After Lesson 5:**
Production AI system with:
- Multi-agent orchestration
- Evaluation framework
- REST API
- Docker deployment
- Monitoring dashboard
- Real business metrics ($X saved/month)

**Result:**
Portfolio project that proves you can ship AI products!

---

## Quick Reference

### Common Commands

```bash
# Sync with course repo
git fetch upstream && git merge upstream/main

# Start new homework
git checkout -b lessonN-homework

# Save your work
git add . && git commit -m "Description"

# Submit for review
git push origin lessonN-homework
# Then create PR on GitHub

# Update PR after feedback
git add . && git commit -m "Address feedback"
git push origin lessonN-homework
```

### Need Help?

- 📖 Documentation: Check lesson README first
- 🔧 Setup Issues: Run `python verify_setup.py`
- 💬 Questions: Ask in course chat
- 🐛 Bugs: Create GitHub issue
- 👥 Live Help: Join office hours

---

## Let's Build! 🚀

You're now ready to start contributing. Head to [lesson1/](lesson1/) and begin your journey to becoming an AI Product Engineer!

**Remember:** The goal isn't just to complete homework—it's to build production-grade AI systems that solve real problems. Focus on understanding WHY, not just HOW.

Good luck, and happy coding! 🎉
