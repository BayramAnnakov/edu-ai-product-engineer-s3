"""
Test cases for LinkedIn Cold Outreach demo
Demonstrates difference between chained and agentic workflows
"""

# Clean test cases - well-formatted, complete data
CLEAN_URLS = [
    "https://www.linkedin.com/in/jenhsunhuang/",  # Jensen Huang, NVIDIA CEO
    "https://www.linkedin.com/in/satyanadella/",  # Satya Nadella, Microsoft CEO
    "https://www.linkedin.com/in/demishassabis/",  # Demis Hassabis, Google DeepMind
    "https://www.linkedin.com/in/sam-altman/",  # Sam Altman, OpenAI
    "https://www.linkedin.com/in/dariomojdehbakhsh/",  # Dario Amodei, Anthropic CEO
]

# Messy test cases - typos, variations, edge cases
MESSY_URLS = [
    "linkedin.com/in/jenhsunhuang",  # Missing https://www.
    "https://linkedin.com/in/satya-nadella",  # Missing www., hyphen variation
    "https://www.linkedin.com/in/demis-hassabis",  # Hyphen variation (correct is no hyphen)
    "https://www.linkedin.com/in/sama/",  # Shortened username (Sam Altman's actual profile)
    "https://linkedin.com/in/dario",  # Missing www., incomplete username
]

# Expected behaviors:
# CHAINED WORKFLOW:
# - Clean URLs: ✅ Should work (5/5 success)
# - Messy URLs: ❌ Will likely fail on most (1-2/5 success)
#   - Missing protocol/www: EnrichLayer may reject
#   - Username variations: Won't find profile
#   - Incomplete data: Will crash on missing fields

# AGENTIC WORKFLOW:
# - Clean URLs: ✅ Should work (5/5 success)
# - Messy URLs: ✅ Agent can self-correct (4-5/5 success)
#   - Agent will try URL variations
#   - Can handle missing data gracefully
#   - Can reason about likely corrections

ALL_TEST_CASES = CLEAN_URLS + MESSY_URLS

# For quick testing during workshop
# NOTE: EnrichLayer API is forgiving - missing protocol/www doesn't break it!
# To demonstrate chained workflow failure, we need actual DATA errors (typos, wrong username)
DEMO_PAIR = [
    ("Clean", "https://www.linkedin.com/in/jenhsunhuang/"),
    ("Messy - Username Typo", "https://www.linkedin.com/in/jenhsun-huang"),  # Hyphen typo - will fail!
]

# Alternative demo pairs showing different self-correction scenarios
DEMO_PAIR_ALT1 = [
    ("Clean", "https://www.linkedin.com/in/satyanadella/"),
    ("Messy - Missing www", "https://linkedin.com/in/satyanadella"),  # Missing www. (fixable!)
]

DEMO_PAIR_ALT2 = [
    ("Clean", "https://www.linkedin.com/in/jenhsunhuang/"),
    ("Messy - Typo (Unfixable)", "linkedin.com/in/jenhsun-huang"),  # Shows reasoning when unfixable
]

DEMO_PAIR_ALT3 = [
    ("Clean", "https://www.linkedin.com/in/gaiar/"),
    ("Non-existent profile", "linkedin.com/in/gaiar-baimuratov"),  # Shows reasoning when unfixable
]
