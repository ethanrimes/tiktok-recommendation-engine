# TikTok Recommendation Engine

A proof-of-concept recommendation system that uses AI to generate content categories, profile users, and recommend TikTok videos based on their interests.

## Features

- **Category Discovery**: Generate content categories from unstructured TikTok text data
- **User Profiling**: Analyze user activity to assign relevant category tags
- **Content Recommendation**: Generate personalized video recommendations with ranking

## Setup

### Prerequisites

- Python 3.9+
- Supabase account
- RapidAPI account with TikTok API access
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd tiktok-recommendation-engine
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Supabase:
   - Create a new Supabase project at https://supabase.com
   - Run the SQL migrations in `database/migrations/` in your Supabase SQL editor
   - Copy your project URL and anon key

5. Configure environment variables:
   - Copy `.env.local` to `.env`
   - Fill in your API keys and Supabase credentials

6. Initialize the database:
```bash
python scripts/init_db.py
```

## Usage

### Main CLI

```bash
# Generate taxonomy from text files
python main.py taxonomy --input data/input/trending_hashtags.txt --output data/output/taxonomy.json -n 100

# Profile a user
python main.py profile --username taylorswift --output data/output/taylorswift_profile.json --taxonomy data/output/taxonomy.json

# Get recommendations for a user
python main.py recommend --username taylorswift --count 5

# Run full pipeline
python main.py pipeline --username taylorswift --taxonomy data/output/taxonomy.json
```

### Standalone Scripts

```bash
# Generate taxonomy
python scripts/run_taxonomy.py --input data/input/sample.txt

# Profile user
python scripts/run_profile.py --username username123

# Get recommendations
python scripts/run_recommend.py --username username123 --tags "music,dance"
```

## Project Structure

```
tiktok-recommendation-engine/
├── main.py                 # CLI entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── .env.local            # Environment template
├── README.md             # This file
│
├── data/
│   ├── input/           # Raw text files
│   ├── output/          # Generated files
│   └── cache/           # API response cache
│
├── core/                # Core functionality
│   ├── models.py        # Data models
│   └── api_client.py    # TikTok API wrapper
│
├── pipelines/           # Pipeline implementations
│   ├── base.py          # Base pipeline class
│   ├── taxonomy_pipeline.py
│   ├── profiling_pipeline.py
│   └── recommendation_pipeline.py
│
├── stages/              # Pipeline stages
│   ├── extraction/      # Data extraction
│   ├── transformation/  # Data transformation
│   └── scoring/         # Scoring and ranking
│
├── prompts/             # LLM prompt templates
│   ├── category_generation.txt
│   ├── tag_mapping.txt
│   └── query_generation.txt
│
├── database/            # Database setup
│   ├── migrations/      # SQL migrations
│   └── models.py        # Supabase models
│
├── utils/               # Utility functions
│   ├── embeddings.py    # Text embeddings
│   ├── cache.py         # Caching utilities
│   └── io.py            # File I/O
│
├── scripts/             # Standalone scripts
│   ├── init_db.py       # Initialize database
│   ├── run_taxonomy.py  # Generate taxonomy
│   ├── run_profile.py   # Profile user
│   └── run_recommend.py # Get recommendations
│
└── tests/               # Test suite
    ├── test_api.py      # API schema tests
    ├── test_db.py       # Database tests
    └── test_tags.py     # Tag generation tests
```

## Configuration

Edit `config.py` to adjust:
- Number of categories to generate
- API rate limits
- Ranking algorithm weights
- Cache expiration times

## Testing

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/test_api.py
pytest tests/test_db.py
pytest tests/test_tags.py
```

## Database Schema

The system uses Supabase with the following tables:
- `categories`: Stores generated content categories
- `user_profiles`: Stores user profile information
- `user_tags`: Maps users to category tags with affinity scores
- `recommendations`: Stores generated recommendations
- `api_cache`: Caches API responses

## API Rate Limits

The TikTok API has rate limits. The system implements:
- Response caching to minimize API calls
- Exponential backoff for rate limit errors
- Request queuing to stay within limits

## License

MIT