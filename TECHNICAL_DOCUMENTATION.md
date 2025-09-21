# TikTok Recommendation Engine - Technical Documentation

## System Overview

The TikTok Recommendation Engine is a multi-stage pipeline system that generates personalized video recommendations by analyzing user behavior patterns, generating content taxonomies, and scoring videos across multiple dimensions. The system leverages both LLM-based content understanding and traditional information retrieval techniques.

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Main Pipeline System                      │
├───────────────────┬─────────────────┬──────────────────────────┤
│  Taxonomy Pipeline │ Profiling Pipeline │ Recommendation Pipeline│
├───────────────────┴─────────────────┴──────────────────────────┤
│                          Core Services                           │
├──────────────┬──────────────┬──────────────┬──────────────────┤
│ TikTok API   │ OpenAI LLM   │ Supabase DB  │ Cache Manager    │
│   Client     │   Service    │    Client    │                  │
└──────────────┴──────────────┴──────────────┴──────────────────┘
```

### Data Flow

```
Input Text → Taxonomy Generation → Categories with Embeddings
     ↓
User Profile → Tag Mapping → Affinity Scores
     ↓
Search Query Generation → Video Retrieval → Scoring & Ranking
     ↓
Personalized Recommendations
```

## Pipeline Processes

### 1. Taxonomy Generation Pipeline

**Purpose**: Generate content categories from unstructured TikTok text data (hashtags, captions, bios)

**Process Flow**:

1. **Text Extraction** (`TextExtractor`)
   - Reads raw text files containing TikTok trending data
   - Extracts hashtags, captions, and metadata

2. **Text Processing** (`TextProcessor`)
   - Cleans and normalizes text
   - Removes special characters while preserving hashtags
   - Extracts hashtag and mention lists
   - Truncates to manageable length (max 10,000 chars)

3. **Category Generation** (`CategoryGenerator`)
   - Uses GPT-4.1 with structured prompts
   - Generates N distinct content categories
   - Each category includes:
     - Tag name (lowercase, underscore-separated)
     - Description (1-2 sentences)
     - Keywords (5-10 related terms)

4. **Embedding Generation** (`EmbeddingGenerator`)
   - Creates vector embeddings for each category
   - Uses OpenAI's text-embedding-3-large model
   - Embeddings enable semantic similarity comparisons

5. **Storage**
   - Categories saved to Supabase database
   - JSON output for local reference

### 2. User Profiling Pipeline

**Purpose**: Analyze user activity to assign relevant category tags with affinity scores

**Process Flow**:

1. **User Data Extraction** (`APIExtractor`)
   ```python
   # Fetches comprehensive user data:
   - User profile (bio, stats, region, language)
   - Posted videos (up to 50)
   - Reposted videos (up to 30)  
   - Liked videos (up to 30)
   ```

2. **Tag Mapping** (`TagMapper`)
   - LLM-based analysis of user content against categories
   - Considers multiple signals:
     - Content themes in posts
     - Frequently used hashtags
     - Music preferences
     - Bio keywords
     - Engagement patterns
   - Assigns initial affinity scores (0.0-1.0)

3. **Affinity Scoring** (`AffinityScorer`)
   ```python
   Final Score = Base Affinity + Engagement Boost × Influence Factor
   ```
   
   **Engagement Boost Calculation**:
   - Analyzes content relevance across posts, reposts, likes
   - Weights: Posts (1.0), Reposts (0.8), Likes (0.6)
   - Considers engagement metrics (likes, comments, shares)
   
   **Influence Factor**:
   - < 1K followers: 0.8
   - 1K-10K: 0.9
   - 10K-100K: 1.0
   - 100K-1M: 1.1
   - > 1M: 1.2

4. **Profile Creation**
   - Filters tags above minimum affinity (0.3)
   - Sorts by affinity score
   - Stores in database with metadata

### 3. Recommendation Pipeline

**Purpose**: Generate personalized video recommendations based on user profile

**Process Flow**:

1. **Query Generation** (`QueryGenerator`)
   - LLM generates search queries from user tags
   - Creates diverse queries:
     - Broad category searches
     - Niche interest combinations
     - Trending format searches
   - Optimizes for TikTok's search API

2. **Video Retrieval** (`APIExtractor`)
   - Executes search queries via TikTok API
   - Fetches videos_per_query (default: 20) for each query
   - Deduplicates by video ID
   - Preserves source query and tags for scoring

3. **Multi-Dimensional Scoring**

   **a. Virality Score** (`ViralityScorer`)
   ```python
   Components:
   - Play count normalization (0-1 scale)
   - Engagement rate (likes+comments+shares/plays)
   - Share ratio (viral indicator)
   - Time decay factor (recency bonus)
   
   Virality = 0.3×plays + 0.3×engagement + 0.2×shares + 0.2×recency
   ```

   **b. Relevance Score** (`RelevanceScorer`)
   ```python
   Components:
   - Tag matching score (direct & partial matches)
   - Embedding similarity (semantic relevance)
   - Source tag boost (query-tag alignment)
   
   Relevance = 0.4×tag_match + 0.4×embedding + 0.2×source_boost
   ```

   **c. Engagement Quality**
   ```python
   Ratios:
   - Like ratio: likes/plays
   - Comment ratio: comments/plays (weighted higher)
   - Share ratio: shares/plays
   
   Quality = 0.3×likes + 0.4×comments + 0.3×shares (normalized)
   ```

4. **Final Ranking** (`FinalRanker`)
   ```python
   Final Score = virality×0.3 + relevance×0.4 + engagement×0.3
   ```
   
   **Diversity Optimization**:
   - Penalizes repeated authors (0.9× score)
   - Penalizes identical tag sets (0.85× score)
   - Ensures content variety in recommendations

5. **Output Generation**
   - Filters by minimum score threshold (0.5)
   - Returns top N recommendations
   - Includes metadata: scores, matched tags, stats

## Retrieval Components

### TikTok API Integration

**Endpoints Used**:
- `/user/info`: Basic user profile
- `/user/info-with-region`: Enhanced profile with location
- `/user/posts`: User's posted videos
- `/user/repost`: User's reposted content
- `/user/liked-posts`: User's liked videos
- `/search/video`: Video search
- `/post/trending`: Trending videos

**Rate Limiting**:
- Configurable delay between requests (1 second default)
- Exponential backoff on failures
- Response caching to minimize API calls

### Caching Strategy

**Cache Manager Features**:
- Disk-based caching with TTL
- Key generation from request parameters
- Default TTL: 1 hour
- Separate caches for API responses and computations

## Ranking Algorithm Details

### Score Normalization

**Play Count Scaling**:
```
< 10K:        0-30% of max score
10K-100K:     30-60% of max score  
100K-1M:      60-80% of max score
1M-10M:       80-95% of max score
> 10M:        95-100% of max score
```

**Engagement Rate Benchmarks**:
```
< 1%:         Poor engagement
1-5%:         Good engagement
5-10%:        Excellent engagement
> 10%:        Viral content
```

### Time Decay Function

```python
Age (days) | Weight
-----------|---------
< 1        | 1.0
1-7        | 0.9
7-30       | 0.7
30-90      | 0.5
90-180     | 0.3
> 180      | 0.1
```

## Database Schema

### Core Tables

**categories**
- `tag` (PK): Category identifier
- `description`: Category description
- `keywords`: Associated keywords (JSON)
- `embedding`: Vector embedding (JSON)

**user_profiles**
- `username` (PK): TikTok username
- `user_id`: TikTok user ID
- `sec_uid`: Secure user ID
- Profile stats and metadata

**user_tags**
- `username` (FK): Links to user_profiles
- `tag` (FK): Links to categories
- `affinity`: Score 0.0-1.0
- `reason`: Explanation for affinity

**recommendations**
- `username` (FK): Links to user_profiles
- `video_id`: TikTok video ID
- Score components and metadata

## Configuration

### Key Settings (`config.py`)

**Pipeline Settings**:
- `num_categories`: Categories to generate (100)
- `max_posts_to_analyze`: User posts to analyze (50)
- `max_liked_posts`: Liked posts to analyze (30)
- `min_tag_affinity`: Minimum affinity threshold (0.3)
- `max_search_queries`: Queries per recommendation (10)
- `videos_per_query`: Videos per search (20)

**Ranking Weights**:
- `virality_weight`: 0.3
- `engagement_weight`: 0.3
- `relevance_weight`: 0.4

**Model Configuration**:
- LLM: GPT-4.1
- Embeddings: text-embedding-3-large
- Temperature: 0.7

## Usage Examples

### Generate Taxonomy
```bash
python main.py taxonomy \
  --input data/input/trending_hashtags.txt \
  --output data/output/taxonomy.json \
  --num-categories 100
```

### Profile User
```bash
python main.py profile \
  --username taylorswift \
  --taxonomy data/output/taxonomy.json \
  --output data/output/profile.json
```

### Get Recommendations
```bash
python main.py recommend \
  --username taylorswift \
  --profile data/output/profile.json \
  --count 20
```

### Full Pipeline
```bash
python main.py pipeline \
  --username taylorswift \
  --taxonomy data/output/taxonomy.json \
  --count 20
```

## Performance Considerations

### Optimization Strategies

1. **Batch Processing**: 
   - Embedding generation supports batch requests
   - Database operations use upsert for efficiency

2. **Caching**:
   - API responses cached for 1 hour
   - Pipeline results stored for reuse

3. **Parallel Processing**:
   - Multiple search queries can be executed concurrently
   - Score calculations are vectorized where possible

4. **Resource Management**:
   - Text truncation prevents LLM token limits
   - Pagination for large result sets
   - Configurable limits on data fetching

## Error Handling

### Fallback Mechanisms

1. **LLM Failures**: 
   - Default categories provided
   - Keyword-based tag mapping fallback

2. **API Failures**:
   - Exponential backoff with retry
   - Cached responses used when available

3. **Database Failures**:
   - Operations continue without persistence
   - Warning messages logged

## Future Enhancements

### Planned Improvements

1. **Advanced Scoring**:
   - Temporal trend analysis
   - Creator authority scoring
   - Cross-platform signal integration

2. **Personalization**:
   - User feedback loop
   - A/B testing framework
   - Real-time preference updates

3. **Scale Optimization**:
   - Redis for caching
   - Async API calls
   - Distributed processing

4. **Analytics**:
   - Recommendation performance tracking
   - User engagement metrics
   - Category effectiveness analysis