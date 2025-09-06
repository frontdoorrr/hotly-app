# TRD: 검색, 필터링, 정렬 기능

## 1. 시스템 개요

### 1-1. 아키텍처 구조
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   API Gateway   │    │  Search Service │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Search UI   │ │◄───┤ │ Rate Limit  │ │◄───┤ │ Query       │ │
│ │ Filter UI   │ │    │ │ Auth Check  │ │    │ │ Parser      │ │
│ │ Sort UI     │ │    │ │ Validation  │ │    │ └─────────────┘ │
│ └─────────────┘ │    │ └─────────────┘ │    │ ┌─────────────┐ │
└─────────────────┘    └─────────────────┘    │ │ Search      │ │
                                              │ │ Engine      │ │
┌─────────────────┐    ┌─────────────────┐    │ │(Elasticsearch)│
│ External APIs   │    │   Data Store    │    │ └─────────────┘ │
│                 │    │                 │    │ ┌─────────────┐ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ │ Filter      │ │
│ │Location API │ │───►│ │ Redis Cache │ │◄───┤ │ Engine      │ │
│ │Maps API     │ │    │ │Search Cache │ │    │ └─────────────┘ │
│ │Analytics    │ │    │ └─────────────┘ │    │ ┌─────────────┐ │
│ └─────────────┘ │    │ ┌─────────────┐ │    │ │ Sort &      │ │
└─────────────────┘    │ │ PostgreSQL  │ │◄───┤ │ Pagination  │ │
                       │ │Places       │ │    │ └─────────────┘ │
                       │ │Courses      │ │    └─────────────────┘
                       │ │SearchHistory│ │
                       │ └─────────────┘ │
                       └─────────────────┘
```

### 1-2. 기술 스택
```yaml
Search Engine:
  Primary: Elasticsearch 8.x
  Analyzer: Korean (nori), English (standard)
  Features: Full-text search, geo-spatial, aggregations

Backend:
  Runtime: Node.js 18+ (TypeScript)
  Framework: Express.js + Fastify (high-performance endpoints)
  Cache: Redis Cluster
  Database: PostgreSQL (metadata), PostgreSQL (analytics)

Client:
  Debouncing: Lodash debounce (300ms)
  State: Redux Toolkit (search state)
  UI: React Query (server state)
  Virtualization: React Window (large result sets)
```

## 2. 검색 엔진 설계

### 2-1. Elasticsearch 인덱스 스키마
```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "name": {
        "type": "text",
        "analyzer": "korean_analyzer",
        "fields": {
          "raw": { "type": "keyword" },
          "suggest": { "type": "completion" }
        }
      },
      "description": {
        "type": "text",
        "analyzer": "korean_analyzer"
      },
      "address": {
        "type": "text",
        "analyzer": "korean_analyzer",
        "fields": {
          "components": {
            "type": "object",
            "properties": {
              "sido": { "type": "keyword" },
              "sigungu": { "type": "keyword" },
              "dong": { "type": "keyword" }
            }
          }
        }
      },
      "location": { "type": "geo_point" },
      "category": { "type": "keyword" },
      "tags": { "type": "keyword" },
      "user_tags": { "type": "keyword" },
      "status": { "type": "keyword" },
      "price_range": { "type": "integer_range" },
      "rating": { "type": "float" },
      "review_count": { "type": "integer" },
      "popularity_score": { "type": "float" },
      "visit_status": { "type": "keyword" },
      "created_at": { "type": "date" },
      "updated_at": { "type": "date" },
      "user_id": { "type": "keyword" }
    }
  },
  "settings": {
    "analysis": {
      "analyzer": {
        "korean_analyzer": {
          "type": "custom",
          "tokenizer": "nori_tokenizer",
          "filter": ["lowercase", "nori_part_of_speech", "synonym_filter"]
        }
      },
      "filter": {
        "synonym_filter": {
          "type": "synonym",
          "synonyms": [
            "카페,커피숍,cafe",
            "맛집,식당,레스토랑,restaurant",
            "관광지,명소,여행지,tourist"
          ]
        }
      }
    }
  }
}
```

### 2-2. 검색 쿼리 구조
```typescript
interface SearchQuery {
  query: {
    bool: {
      must: Query[];
      filter: Filter[];
      should: Query[];
      minimum_should_match?: number;
    };
  };
  sort: SortClause[];
  aggs?: Aggregations;
  from: number;
  size: number;
}

// 메인 검색 쿼리 생성
class SearchQueryBuilder {
  buildSearchQuery(params: SearchParams): SearchQuery {
    const query = {
      query: {
        bool: {
          must: this.buildMustClauses(params),
          filter: this.buildFilterClauses(params),
          should: this.buildShouldClauses(params),
        }
      },
      sort: this.buildSortClauses(params),
      from: (params.page - 1) * params.limit,
      size: params.limit,
    };

    if (params.includeFacets) {
      query.aggs = this.buildAggregations();
    }

    return query;
  }

  private buildMustClauses(params: SearchParams): Query[] {
    const clauses: Query[] = [];

    if (params.query) {
      clauses.push({
        multi_match: {
          query: params.query,
          fields: [
            'name^3',           // 장소명 가중치 높음
            'name.raw^5',       // 정확한 매치 가중치 가장 높음
            'description^1',
            'address^2',
            'tags^2',
            'user_tags^2'
          ],
          type: 'best_fields',
          fuzziness: 'AUTO'     // 오타 허용
        }
      });
    }

    // 사용자별 필터링
    clauses.push({
      term: { user_id: params.userId }
    });

    return clauses;
  }

  private buildFilterClauses(params: SearchParams): Filter[] {
    const filters: Filter[] = [];

    // 카테고리 필터
    if (params.categories?.length) {
      filters.push({
        terms: { category: params.categories }
      });
    }

    // 지역 필터
    if (params.regions?.length) {
      filters.push({
        bool: {
          should: params.regions.map(region => ({
            match: { 'address.components.sigungu': region }
          }))
        }
      });
    }

    // 태그 필터
    if (params.tags?.length) {
      filters.push({
        bool: {
          should: [
            { terms: { tags: params.tags } },
            { terms: { user_tags: params.tags } }
          ]
        }
      });
    }

    // 상태 필터
    if (params.status?.length) {
      filters.push({
        terms: { visit_status: params.status }
      });
    }

    // 가격대 필터
    if (params.priceRange?.length) {
      const priceFilters = params.priceRange.map(range => {
        const [min, max] = this.parsePriceRange(range);
        return {
          range: {
            price_range: { gte: min, lte: max }
          }
        };
      });

      filters.push({
        bool: { should: priceFilters }
      });
    }

    // 지리적 필터
    if (params.location && params.radius) {
      filters.push({
        geo_distance: {
          distance: `${params.radius}km`,
          location: {
            lat: params.location.lat,
            lon: params.location.lng
          }
        }
      });
    }

    return filters;
  }

  private buildSortClauses(params: SearchParams): SortClause[] {
    switch (params.sortBy) {
      case 'distance':
        if (!params.location) {
          throw new Error('Location required for distance sort');
        }
        return [{
          _geo_distance: {
            location: params.location,
            order: 'asc',
            unit: 'km'
          }
        }];

      case 'rating':
        return [
          { rating: { order: 'desc' } },
          { review_count: { order: 'desc' } }
        ];

      case 'recent':
        return [{ created_at: { order: 'desc' } }];

      case 'price':
        return [{ 'price_range.gte': { order: params.sortOrder || 'asc' } }];

      case 'popular':
        return [{ popularity_score: { order: 'desc' } }];

      case 'name':
        return [{ 'name.raw': { order: 'asc' } }];

      default:
        return [
          { _score: { order: 'desc' } },
          { created_at: { order: 'desc' } }
        ];
    }
  }
}
```

## 3. API 설계

### 3-1. 검색 API
```typescript
// GET /api/search
interface SearchRequest {
  query?: string;
  categories?: string[];
  regions?: string[];
  tags?: string[];
  status?: ('wishlist' | 'favorite' | 'visited' | 'planned')[];
  priceRange?: string[];
  sortBy?: 'relevance' | 'distance' | 'rating' | 'recent' | 'price' | 'popular' | 'name';
  sortOrder?: 'asc' | 'desc';
  page?: number;
  limit?: number;
  location?: {
    lat: number;
    lng: number;
  };
  radius?: number; // km
  includeFacets?: boolean;
}

interface SearchResponse {
  results: PlaceSearchResult[];
  pagination: {
    total: number;
    page: number;
    limit: number;
    hasNext: boolean;
  };
  facets?: SearchFacets;
  query_info: {
    took: number; // ms
    total_hits: number;
    max_score: number;
  };
}

interface PlaceSearchResult {
  id: string;
  name: string;
  description?: string;
  address: string;
  location: {
    lat: number;
    lng: number;
  };
  category: string;
  tags: string[];
  user_tags: string[];
  rating?: number;
  review_count?: number;
  price_range?: {
    min: number;
    max: number;
  };
  visit_status: string;
  distance?: number; // meters
  created_at: string;
  highlights?: {
    [field: string]: string[];
  };
}

// 패싯 정보 (필터 옵션)
interface SearchFacets {
  categories: { name: string; count: number }[];
  regions: { name: string; count: number }[];
  tags: { name: string; count: number }[];
  status: { name: string; count: number }[];
  price_ranges: { range: string; count: number }[];
}
```

### 3-2. 자동완성 API
```typescript
// GET /api/search/suggest
interface SuggestRequest {
  query: string;
  limit?: number;
  types?: ('places' | 'regions' | 'categories' | 'tags')[];
}

interface SuggestResponse {
  suggestions: Suggestion[];
}

interface Suggestion {
  type: 'place' | 'region' | 'category' | 'tag';
  text: string;
  count?: number;
  metadata?: {
    id?: string;
    category?: string;
    region?: string;
  };
}

class SuggestService {
  async getSuggestions(params: SuggestRequest): Promise<SuggestResponse> {
    const query = {
      suggest: {
        place_suggest: {
          prefix: params.query,
          completion: {
            field: 'name.suggest',
            size: params.limit || 10,
            skip_duplicates: true
          }
        },
        region_suggest: {
          prefix: params.query,
          completion: {
            field: 'address.suggest',
            size: 5
          }
        }
      }
    };

    const response = await this.elasticsearch.search({
      index: 'places',
      body: query
    });

    return this.formatSuggestions(response);
  }

  private formatSuggestions(response: any): SuggestResponse {
    const suggestions: Suggestion[] = [];

    // 장소명 제안
    response.suggest.place_suggest[0]?.options.forEach((option: any) => {
      suggestions.push({
        type: 'place',
        text: option.text,
        metadata: {
          id: option._source.id,
          category: option._source.category
        }
      });
    });

    // 지역 제안
    response.suggest.region_suggest[0]?.options.forEach((option: any) => {
      suggestions.push({
        type: 'region',
        text: option.text
      });
    });

    return { suggestions };
  }
}
```

### 3-3. 검색 기록 API
```typescript
// GET /api/search/history
interface SearchHistoryResponse {
  history: SearchHistoryItem[];
}

interface SearchHistoryItem {
  id: string;
  query: string;
  filters: SearchFilters;
  results_count: number;
  searched_at: string;
}

// POST /api/search/history
interface SaveSearchRequest {
  query?: string;
  filters: SearchFilters;
  results_count: number;
}

// 저장된 검색 조건
// GET /api/search/saved
interface SavedSearchResponse {
  saved_searches: SavedSearch[];
}

interface SavedSearch {
  id: string;
  name: string;
  query?: string;
  filters: SearchFilters;
  created_at: string;
  last_used: string;
}
```

## 4. 필터링 시스템

### 4-1. 필터 상태 관리
```typescript
interface FilterState {
  categories: Set<string>;
  regions: Set<string>;
  tags: Set<string>;
  status: Set<string>;
  priceRanges: Set<string>;
  location?: {
    lat: number;
    lng: number;
    radius: number;
  };
}

class FilterManager {
  private state: FilterState;
  private listeners: ((state: FilterState) => void)[] = [];

  constructor() {
    this.state = {
      categories: new Set(),
      regions: new Set(),
      tags: new Set(),
      status: new Set(),
      priceRanges: new Set(),
    };
  }

  addFilter(type: keyof FilterState, value: string): void {
    if (this.state[type] instanceof Set) {
      (this.state[type] as Set<string>).add(value);
      this.notifyListeners();
    }
  }

  removeFilter(type: keyof FilterState, value: string): void {
    if (this.state[type] instanceof Set) {
      (this.state[type] as Set<string>).delete(value);
      this.notifyListeners();
    }
  }

  clearAllFilters(): void {
    this.state = {
      categories: new Set(),
      regions: new Set(),
      tags: new Set(),
      status: new Set(),
      priceRanges: new Set(),
    };
    this.notifyListeners();
  }

  getActiveFilters(): { [key: string]: string[] } {
    return {
      categories: Array.from(this.state.categories),
      regions: Array.from(this.state.regions),
      tags: Array.from(this.state.tags),
      status: Array.from(this.state.status),
      priceRanges: Array.from(this.state.priceRanges),
    };
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.state));
  }

  subscribe(listener: (state: FilterState) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }
}
```

### 4-2. 동적 필터 옵션
```typescript
class FilterOptionsService {
  async getFilterOptions(userId: string): Promise<FilterOptions> {
    // 사용자의 장소들을 기반으로 필터 옵션 생성
    const aggregationQuery = {
      query: {
        term: { user_id: userId }
      },
      aggs: {
        categories: {
          terms: { field: 'category', size: 20 }
        },
        regions: {
          terms: { field: 'address.components.sigungu', size: 50 }
        },
        user_tags: {
          terms: { field: 'user_tags', size: 100 }
        },
        status: {
          terms: { field: 'visit_status', size: 10 }
        },
        price_ranges: {
          range: {
            field: 'price_range.gte',
            ranges: [
              { key: '~10000', to: 10000 },
              { key: '10000-20000', from: 10000, to: 20000 },
              { key: '20000-30000', from: 20000, to: 30000 },
              { key: '30000-50000', from: 30000, to: 50000 },
              { key: '50000+', from: 50000 }
            ]
          }
        }
      },
      size: 0
    };

    const response = await this.elasticsearch.search({
      index: 'places',
      body: aggregationQuery
    });

    return this.formatFilterOptions(response.aggregations);
  }

  private formatFilterOptions(aggs: any): FilterOptions {
    return {
      categories: aggs.categories.buckets.map((bucket: any) => ({
        name: bucket.key,
        count: bucket.doc_count,
        label: this.getCategoryLabel(bucket.key)
      })),
      regions: aggs.regions.buckets.map((bucket: any) => ({
        name: bucket.key,
        count: bucket.doc_count
      })),
      tags: aggs.user_tags.buckets.map((bucket: any) => ({
        name: bucket.key,
        count: bucket.doc_count
      })),
      status: aggs.status.buckets.map((bucket: any) => ({
        name: bucket.key,
        count: bucket.doc_count,
        label: this.getStatusLabel(bucket.key)
      })),
      priceRanges: aggs.price_ranges.buckets.map((bucket: any) => ({
        name: bucket.key,
        count: bucket.doc_count,
        label: this.getPriceRangeLabel(bucket.key)
      }))
    };
  }
}
```

## 5. 정렬 및 페이징

### 5-1. 정렬 시스템
```typescript
type SortField = 'relevance' | 'distance' | 'rating' | 'recent' | 'price' | 'popular' | 'name';
type SortOrder = 'asc' | 'desc';

interface SortOptions {
  field: SortField;
  order: SortOrder;
  location?: { lat: number; lng: number };
}

class SortManager {
  private defaultSort: SortOptions = {
    field: 'relevance',
    order: 'desc'
  };

  getSortClause(options: SortOptions): any[] {
    switch (options.field) {
      case 'distance':
        if (!options.location) {
          throw new Error('Location required for distance sorting');
        }
        return [{
          _geo_distance: {
            location: {
              lat: options.location.lat,
              lon: options.location.lng
            },
            order: options.order,
            unit: 'km',
            mode: 'min',
            distance_type: 'arc'
          }
        }];

      case 'rating':
        return [
          { rating: { order: options.order, missing: '_last' } },
          { review_count: { order: 'desc' } }, // 동점 시 리뷰 수 순
          { _score: { order: 'desc' } }
        ];

      case 'recent':
        return [
          { created_at: { order: options.order } },
          { _score: { order: 'desc' } }
        ];

      case 'price':
        return [
          { 'price_range.gte': { order: options.order, missing: '_last' } },
          { rating: { order: 'desc' } }
        ];

      case 'popular':
        return [
          { popularity_score: { order: options.order } },
          { rating: { order: 'desc' } },
          { review_count: { order: 'desc' } }
        ];

      case 'name':
        return [
          { 'name.raw': { order: options.order } }
        ];

      case 'relevance':
      default:
        return [
          { _score: { order: 'desc' } },
          { created_at: { order: 'desc' } }
        ];
    }
  }

  getAvailableSortOptions(hasLocation: boolean): SortOption[] {
    const options: SortOption[] = [
      { field: 'relevance', label: '관련성순', order: 'desc' },
      { field: 'recent', label: '최근순', order: 'desc' },
      { field: 'rating', label: '평점순', order: 'desc' },
      { field: 'popular', label: '인기순', order: 'desc' },
      { field: 'name', label: '이름순', order: 'asc' }
    ];

    if (hasLocation) {
      options.splice(1, 0, {
        field: 'distance',
        label: '거리순',
        order: 'asc'
      });
    }

    return options;
  }
}
```

### 5-2. 커서 기반 페이징
```typescript
interface CursorPagination {
  limit: number;
  cursor?: string;
}

interface CursorResponse<T> {
  data: T[];
  pagination: {
    hasNext: boolean;
    nextCursor?: string;
    total?: number;
  };
}

class CursorPaginator {
  encodeCursor(lastItem: any, sortField: string): string {
    const cursorData = {
      value: lastItem[sortField] || lastItem._score,
      id: lastItem.id,
      timestamp: Date.now()
    };

    return Buffer.from(JSON.stringify(cursorData)).toString('base64');
  }

  decodeCursor(cursor: string): { value: any; id: string } {
    try {
      const decoded = Buffer.from(cursor, 'base64').toString();
      return JSON.parse(decoded);
    } catch {
      throw new Error('Invalid cursor format');
    }
  }

  buildSearchAfter(cursor: string, sortField: string): any[] {
    const { value, id } = this.decodeCursor(cursor);

    // 정렬 필드에 따라 search_after 구성
    switch (sortField) {
      case 'distance':
        return [value, id];
      case 'rating':
        return [value, id];
      case 'recent':
        return [value, id];
      default:
        return [value, id];
    }
  }
}
```

## 6. 캐싱 시스템

### 6-1. 다층 캐싱 구조
```typescript
interface CacheLayer {
  get(key: string): Promise<any>;
  set(key: string, value: any, ttl?: number): Promise<void>;
  delete(key: string): Promise<void>;
}

class SearchCacheManager {
  private l1Cache: Map<string, { value: any; expires: number }> = new Map();
  private l2Cache: Redis;

  constructor(redisClient: Redis) {
    this.l2Cache = redisClient;
  }

  async get(key: string): Promise<any> {
    // L1 캐시 (메모리)
    const l1Result = this.l1Cache.get(key);
    if (l1Result && l1Result.expires > Date.now()) {
      return l1Result.value;
    }

    // L2 캐시 (Redis)
    const l2Result = await this.l2Cache.get(`search:${key}`);
    if (l2Result) {
      const parsed = JSON.parse(l2Result);
      // L1 캐시에도 저장 (짧은 TTL)
      this.l1Cache.set(key, {
        value: parsed,
        expires: Date.now() + 30000 // 30초
      });
      return parsed;
    }

    return null;
  }

  async set(key: string, value: any, ttl: number = 300): Promise<void> {
    // L1 캐시
    this.l1Cache.set(key, {
      value,
      expires: Date.now() + Math.min(ttl * 1000, 60000) // 최대 1분
    });

    // L2 캐시
    await this.l2Cache.setex(`search:${key}`, ttl, JSON.stringify(value));
  }

  generateCacheKey(params: SearchParams): string {
    const keyData = {
      query: params.query,
      filters: params.filters,
      sort: params.sort,
      page: params.page,
      userId: params.userId
    };

    return `search:${Buffer.from(JSON.stringify(keyData)).toString('base64')}`;
  }

  // 지능형 캐싱: 자주 사용되는 쿼리는 더 오래 캐싱
  async smartCache(key: string, value: any, frequency: number): Promise<void> {
    let ttl = 300; // 기본 5분

    if (frequency > 100) ttl = 3600;      // 1시간
    else if (frequency > 50) ttl = 1800;  // 30분
    else if (frequency > 10) ttl = 900;   // 15분

    await this.set(key, value, ttl);
  }
}
```

### 6-2. 캐시 무효화 전략
```typescript
class CacheInvalidationManager {
  private patterns: Map<string, string[]> = new Map([
    ['place:create', ['search:*', 'filter:*']],
    ['place:update', ['search:*:{{placeId}}', 'filter:categories']],
    ['place:delete', ['search:*', 'filter:*']],
    ['user:settings', ['search:*:{{userId}}']],
  ]);

  async invalidateByEvent(event: string, data: any): Promise<void> {
    const patterns = this.patterns.get(event);
    if (!patterns) return;

    for (const pattern of patterns) {
      const resolvedPattern = this.resolvePattern(pattern, data);
      await this.invalidatePattern(resolvedPattern);
    }
  }

  private resolvePattern(pattern: string, data: any): string {
    return pattern.replace(/\{\{(\w+)\}\}/g, (match, key) => {
      return data[key] || '*';
    });
  }

  private async invalidatePattern(pattern: string): Promise<void> {
    if (pattern.includes('*')) {
      // 패턴 매칭으로 키 삭제
      const keys = await this.l2Cache.keys(pattern);
      if (keys.length > 0) {
        await this.l2Cache.del(...keys);
      }
    } else {
      await this.l2Cache.del(pattern);
    }
  }

  // 프로액티브 캐시 워밍
  async warmupCache(userId: string): Promise<void> {
    const popularQueries = await this.getPopularQueries(userId);

    for (const query of popularQueries) {
      try {
        await this.searchService.search(query);
      } catch (error) {
        console.warn(`Cache warmup failed for query:`, query, error);
      }
    }
  }
}
```

## 7. 성능 최적화

### 7-1. 쿼리 최적화
```typescript
class QueryOptimizer {
  optimizeQuery(query: SearchQuery): SearchQuery {
    // 1. 불필요한 필드 제거
    if (!query.query?.bool?.must?.length) {
      delete query.query.bool.must;
    }

    // 2. 지리적 검색 최적화
    if (query.query.bool.filter?.some((f: any) => f.geo_distance)) {
      // 거리 기반 정렬 시 정확도 조절
      const geoFilter = query.query.bool.filter.find((f: any) => f.geo_distance);
      if (geoFilter) {
        geoFilter.geo_distance.distance_type = 'arc'; // 더 정확하지만 느림
      }
    }

    // 3. 불필요한 집계 제거
    if (query.aggs && Object.keys(query.aggs).length === 0) {
      delete query.aggs;
    }

    // 4. 페이징 최적화
    if (query.from > 10000) {
      // 깊은 페이징 시 search_after 사용 권장
      console.warn('Deep pagination detected, consider using search_after');
    }

    return query;
  }

  addPerformanceBoosts(query: SearchQuery): SearchQuery {
    // 1. 결과 크기 제한
    if (!query.size || query.size > 100) {
      query.size = 50;
    }

    // 2. 필요한 필드만 반환
    query._source = [
      'id', 'name', 'description', 'address', 'location',
      'category', 'tags', 'user_tags', 'rating', 'price_range',
      'visit_status', 'created_at'
    ];

    // 3. 하이라이트 최적화
    if (query.highlight) {
      query.highlight.fragment_size = 100;
      query.highlight.number_of_fragments = 1;
    }

    return query;
  }
}
```

### 7-2. 인덱스 최적화
```typescript
class IndexManager {
  async optimizeIndex(): Promise<void> {
    // 1. 인덱스 병합
    await this.elasticsearch.indices.forcemerge({
      index: 'places',
      max_num_segments: 1
    });

    // 2. 캐시 정리
    await this.elasticsearch.indices.clearCache({
      index: 'places',
      query: true,
      fielddata: true,
      request: true
    });

    // 3. 리프레시
    await this.elasticsearch.indices.refresh({
      index: 'places'
    });
  }

  async updateIndexSettings(settings: any): Promise<void> {
    // 인덱스 설정 업데이트 (리플리카, 리프레시 간격 등)
    await this.elasticsearch.indices.putSettings({
      index: 'places',
      body: {
        index: settings
      }
    });
  }

  // 인덱스 상태 모니터링
  async getIndexStats(): Promise<any> {
    return await this.elasticsearch.indices.stats({
      index: 'places',
      metric: ['docs', 'store', 'search', 'indexing']
    });
  }
}
```

## 8. 검색 분석 및 개선

### 8-1. 검색 로그 분석
```typescript
interface SearchLog {
  id: string;
  userId: string;
  query: string;
  filters: any;
  results_count: number;
  clicked_results: string[];
  search_time: number; // ms
  timestamp: Date;
  session_id: string;
}

class SearchAnalytics {
  async logSearch(log: SearchLog): Promise<void> {
    // 검색 로그 저장
    await this.db.execute(
      `INSERT INTO search_logs (id, user_id, query, filters, results_count, clicked_results, search_time, timestamp, session_id)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
      log.id, log.userId, log.query, JSON.stringify(log.filters), log.results_count,
      JSON.stringify(log.clicked_results), log.search_time, log.timestamp, log.session_id
    );

    // 실시간 메트릭 업데이트
    await this.updateSearchMetrics(log);
  }

  async getSearchInsights(period: 'day' | 'week' | 'month'): Promise<SearchInsights> {
    const startDate = this.getStartDate(period);

    const pipeline = [
      { $match: { timestamp: { $gte: startDate } } },
      { $group: {
        _id: null,
        total_searches: { $sum: 1 },
        avg_response_time: { $avg: '$search_time' },
        zero_result_rate: {
          $avg: { $cond: [{ $eq: ['$results_count', 0] }, 1, 0] }
        },
        popular_queries: { $push: '$query' },
        avg_results_per_search: { $avg: '$results_count' }
      }},
      { $project: {
        total_searches: 1,
        avg_response_time: { $round: ['$avg_response_time', 2] },
        zero_result_rate: { $multiply: ['$zero_result_rate', 100] },
        avg_results_per_search: { $round: ['$avg_results_per_search', 1] }
      }}
    ];

    const result = await this.db.fetch(
      `SELECT
         COUNT(*) as total_searches,
         AVG(search_time) as avg_response_time,
         AVG(CASE WHEN results_count = 0 THEN 1 ELSE 0 END) * 100 as zero_result_rate,
         AVG(results_count) as avg_results_per_search
       FROM search_logs
       WHERE timestamp >= $1`,
      startDate
    );

    return result[0] || this.getDefaultInsights();
  }

  async getPopularQueries(limit: number = 20): Promise<QueryPopularity[]> {
    const pipeline = [
      { $match: { timestamp: { $gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) } } },
      { $group: {
        _id: '$query',
        count: { $sum: 1 },
        avg_results: { $avg: '$results_count' },
        click_through_rate: {
          $avg: { $cond: [{ $gt: [{ $size: '$clicked_results' }, 0] }, 1, 0] }
        }
      }},
      { $sort: { count: -1 } },
      { $limit: limit },
      { $project: {
        query: '$_id',
        count: 1,
        avg_results: { $round: ['$avg_results', 1] },
        click_through_rate: { $multiply: ['$click_through_rate', 100] }
      }}
    ];

    return await this.db.fetch(
      `SELECT query,
              COUNT(*) as count,
              AVG(results_count) as avg_results,
              AVG(CASE WHEN array_length(clicked_results, 1) > 0 THEN 1 ELSE 0 END) * 100 as click_through_rate
       FROM search_logs
       WHERE timestamp >= $1
       GROUP BY query
       ORDER BY count DESC
       LIMIT $2`,
      new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), limit
    );
  }

  // 검색 개선 제안
  async getSearchImprovements(): Promise<SearchImprovement[]> {
    const improvements: SearchImprovement[] = [];

    // 1. 결과 없는 검색어 분석
    const zeroResultQueries = await this.getZeroResultQueries();
    for (const query of zeroResultQueries) {
      improvements.push({
        type: 'add_synonym',
        query: query.query,
        suggestion: `"${query.query}"에 대한 동의어 추가 검토`,
        impact: 'medium'
      });
    }

    // 2. 느린 검색 분석
    const slowQueries = await this.getSlowQueries();
    for (const query of slowQueries) {
      improvements.push({
        type: 'optimize_query',
        query: query.query,
        suggestion: '쿼리 최적화 필요 (인덱스 추가 고려)',
        impact: 'high'
      });
    }

    return improvements;
  }
}
```

### 8-2. A/B 테스트 프레임워크
```typescript
interface SearchExperiment {
  id: string;
  name: string;
  variants: SearchVariant[];
  traffic_split: number[]; // [50, 50] for 50/50 split
  status: 'active' | 'paused' | 'completed';
  metrics: ExperimentMetrics;
}

interface SearchVariant {
  name: string;
  config: {
    query_boost?: Record<string, number>;
    sort_default?: string;
    result_limit?: number;
    filter_defaults?: any;
  };
}

class SearchExperimentManager {
  async assignVariant(userId: string, experimentId: string): Promise<string> {
    // 사용자 ID 해싱을 통한 일관된 변형 할당
    const hash = this.hashUserId(userId + experimentId);
    const experiment = await this.getExperiment(experimentId);

    if (!experiment || experiment.status !== 'active') {
      return 'control';
    }

    const bucket = hash % 100;
    let cumulative = 0;

    for (let i = 0; i < experiment.variants.length; i++) {
      cumulative += experiment.traffic_split[i];
      if (bucket < cumulative) {
        return experiment.variants[i].name;
      }
    }

    return 'control';
  }

  async trackExperimentEvent(
    userId: string,
    experimentId: string,
    variant: string,
    event: string,
    metadata?: any
  ): Promise<void> {
    await this.db.execute(
      `INSERT INTO experiment_events (user_id, experiment_id, variant, event, metadata, timestamp)
       VALUES ($1, $2, $3, $4, $5, $6)`,
      userId, experimentId, variant, event, JSON.stringify(metadata), new Date()
    );
  }

  async getExperimentResults(experimentId: string): Promise<ExperimentResults> {
    const pipeline = [
      { $match: { experimentId } },
      { $group: {
        _id: { variant: '$variant', event: '$event' },
        count: { $sum: 1 }
      }},
      { $group: {
        _id: '$_id.variant',
        events: { $push: { event: '$_id.event', count: '$count' } }
      }}
    ];

    const results = await this.db.fetch(
      `SELECT variant, event, COUNT(*) as count
       FROM experiment_events
       WHERE experiment_id = $1
       GROUP BY variant, event`,
      experimentId
    );

    return this.calculateStatisticalSignificance(results);
  }
}
```

## 9. 보안 및 권한 관리

### 9-1. 검색 권한 제어
```typescript
interface SearchPermission {
  userId: string;
  allowedFields: string[];
  rateLimits: {
    requests_per_minute: number;
    requests_per_hour: number;
  };
  restrictions: {
    max_results_per_query: number;
    allowed_sort_fields: string[];
    geo_restrictions?: {
      allowed_regions: string[];
      max_radius: number; // km
    };
  };
}

class SearchSecurityManager {
  async validateSearchRequest(
    userId: string,
    request: SearchRequest
  ): Promise<{ valid: boolean; error?: string }> {
    const permissions = await this.getUserPermissions(userId);

    // 1. Rate limiting 체크
    const rateLimitResult = await this.checkRateLimit(userId);
    if (!rateLimitResult.allowed) {
      return { valid: false, error: 'Rate limit exceeded' };
    }

    // 2. 결과 수 제한
    if (request.limit && request.limit > permissions.restrictions.max_results_per_query) {
      return { valid: false, error: 'Result limit exceeded' };
    }

    // 3. 정렬 필드 검증
    if (request.sortBy && !permissions.restrictions.allowed_sort_fields.includes(request.sortBy)) {
      return { valid: false, error: 'Sort field not allowed' };
    }

    // 4. 지리적 제한
    if (request.location && permissions.restrictions.geo_restrictions) {
      const geoCheck = this.validateGeoRestrictions(request, permissions.restrictions.geo_restrictions);
      if (!geoCheck.valid) {
        return { valid: false, error: geoCheck.error };
      }
    }

    return { valid: true };
  }

  async sanitizeQuery(query: string): Promise<string> {
    // 1. 특수 문자 이스케이핑
    let sanitized = query.replace(/[<>\"']/g, '');

    // 2. Elasticsearch 특수 구문 제거
    sanitized = sanitized.replace(/[\[\]{}()~^]/g, '');

    // 3. 길이 제한
    if (sanitized.length > 200) {
      sanitized = sanitized.substring(0, 200);
    }

    return sanitized.trim();
  }

  async auditSearchAccess(userId: string, request: SearchRequest): Promise<void> {
    await this.db.execute(
      `INSERT INTO search_audit_logs (user_id, query, filters, timestamp, ip_address, user_agent)
       VALUES ($1, $2, $3, $4, $5, $6)`,
      userId, request.query, JSON.stringify(request.filters), new Date(),
      request.ip_address, request.user_agent
    );
  }
}
```

## 10. 모니터링 및 알림

### 10-1. 검색 시스템 모니터링
```typescript
interface SearchMetrics {
  total_searches: number;
  avg_response_time: number;
  error_rate: number;
  zero_result_rate: number;
  cache_hit_rate: number;
  elasticsearch_health: 'green' | 'yellow' | 'red';
}

class SearchMonitoring {
  private metrics: SearchMetrics = {
    total_searches: 0,
    avg_response_time: 0,
    error_rate: 0,
    zero_result_rate: 0,
    cache_hit_rate: 0,
    elasticsearch_health: 'green'
  };

  async collectMetrics(): Promise<void> {
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);

    // Elasticsearch 건강도 확인
    const clusterHealth = await this.elasticsearch.cluster.health();
    this.metrics.elasticsearch_health = clusterHealth.status;

    // 검색 메트릭 수집
    const searchStats = await this.getSearchStats(oneHourAgo, now);
    this.metrics = { ...this.metrics, ...searchStats };

    // 알림 체크
    await this.checkAlerts();
  }

  private async checkAlerts(): Promise<void> {
    const alerts = [];

    // 1. 응답 시간 알림
    if (this.metrics.avg_response_time > 3000) {
      alerts.push({
        type: 'performance',
        message: `검색 응답 시간이 ${this.metrics.avg_response_time}ms로 높습니다`,
        severity: 'warning'
      });
    }

    // 2. 에러율 알림
    if (this.metrics.error_rate > 5) {
      alerts.push({
        type: 'error',
        message: `검색 에러율이 ${this.metrics.error_rate}%입니다`,
        severity: 'critical'
      });
    }

    // 3. Elasticsearch 건강도 알림
    if (this.metrics.elasticsearch_health !== 'green') {
      alerts.push({
        type: 'infrastructure',
        message: `Elasticsearch 상태: ${this.metrics.elasticsearch_health}`,
        severity: this.metrics.elasticsearch_health === 'red' ? 'critical' : 'warning'
      });
    }

    // 4. 캐시 성능 알림
    if (this.metrics.cache_hit_rate < 50) {
      alerts.push({
        type: 'cache',
        message: `캐시 적중률이 ${this.metrics.cache_hit_rate}%로 낮습니다`,
        severity: 'warning'
      });
    }

    // 알림 발송
    for (const alert of alerts) {
      await this.sendAlert(alert);
    }
  }

  async sendAlert(alert: any): Promise<void> {
    // Slack, 이메일, PagerDuty 등으로 알림 발송
    console.error(`ALERT [${alert.severity}] ${alert.type}: ${alert.message}`);
  }

  // 대시보드용 메트릭 반환
  getMetrics(): SearchMetrics {
    return { ...this.metrics };
  }
}
```

## 11. 배포 및 확장성

### 11-1. 수평 확장 설계
```yaml
# Elasticsearch 클러스터 설정
elasticsearch:
  cluster_name: "hotly-search"
  nodes:
    - name: "es-master-1"
      roles: ["master"]
      heap_size: "2g"
    - name: "es-data-1"
      roles: ["data", "ingest"]
      heap_size: "8g"
    - name: "es-data-2"
      roles: ["data", "ingest"]
      heap_size: "8g"

# 검색 서비스 스케일링
search_service:
  replicas: 3
  resources:
    cpu: "500m"
    memory: "1Gi"
  autoscaling:
    min_replicas: 2
    max_replicas: 10
    target_cpu: 70
    target_memory: 80

# Redis 클러스터
redis:
  mode: "cluster"
  nodes: 6
  memory_per_node: "2GB"
```

### 11-2. 성능 벤치마킹
```typescript
class SearchBenchmark {
  async runBenchmark(scenarios: BenchmarkScenario[]): Promise<BenchmarkResults> {
    const results: BenchmarkResults = {
      scenarios: [],
      summary: {
        total_requests: 0,
        avg_response_time: 0,
        p95_response_time: 0,
        p99_response_time: 0,
        error_rate: 0
      }
    };

    for (const scenario of scenarios) {
      const scenarioResult = await this.runScenario(scenario);
      results.scenarios.push(scenarioResult);
    }

    results.summary = this.calculateSummary(results.scenarios);
    return results;
  }

  private async runScenario(scenario: BenchmarkScenario): Promise<ScenarioResult> {
    const startTime = Date.now();
    const responses: ResponseTime[] = [];
    let errorCount = 0;

    for (let i = 0; i < scenario.request_count; i++) {
      try {
        const requestStart = Date.now();
        await this.searchService.search(scenario.request);
        const responseTime = Date.now() - requestStart;
        responses.push({ time: responseTime });
      } catch (error) {
        errorCount++;
      }
    }

    const totalTime = Date.now() - startTime;
    const avgResponseTime = responses.reduce((sum, r) => sum + r.time, 0) / responses.length;

    responses.sort((a, b) => a.time - b.time);
    const p95Index = Math.floor(responses.length * 0.95);
    const p99Index = Math.floor(responses.length * 0.99);

    return {
      scenario_name: scenario.name,
      request_count: scenario.request_count,
      total_time: totalTime,
      avg_response_time: avgResponseTime,
      p95_response_time: responses[p95Index]?.time || 0,
      p99_response_time: responses[p99Index]?.time || 0,
      error_rate: (errorCount / scenario.request_count) * 100,
      throughput: scenario.request_count / (totalTime / 1000) // requests per second
    };
  }
}
```

이제 검색, 필터링, 정렬 기능의 TRD 작성이 완료되었습니다. 다음 태스크로 넘어가겠습니다.
