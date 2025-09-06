# Hotly App - Database Schema Documentation

## 1. Core Tables

### 1.1 User Profiles (사용자 프로필)
```sql
CREATE TABLE user_profiles (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(128) UNIQUE NOT NULL, -- Firebase Auth UID

  -- 공개 프로필 정보
  display_name VARCHAR(50) NOT NULL,
  photo_url TEXT,
  bio TEXT CHECK (LENGTH(bio) <= 500),
  location VARCHAR(100),
  interests TEXT[], -- PostgreSQL array type
  joined_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  last_active_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  -- 개인정보 (비공개)
  email VARCHAR(255) NOT NULL,
  phone_number VARCHAR(20),
  date_of_birth DATE,
  gender VARCHAR(20) CHECK (gender IN ('male', 'female', 'other', 'prefer_not_to_say')),
  email_verified BOOLEAN NOT NULL DEFAULT FALSE,
  phone_verified BOOLEAN NOT NULL DEFAULT FALSE,

  -- 개인화 설정 (JSONB로 저장)
  dating_preferences JSONB DEFAULT '{}',
  recommendation_preferences JSONB DEFAULT '{}',

  -- 알림 설정
  notification_settings JSONB DEFAULT '{
    "push": {
      "enabled": true,
      "dateReminders": true,
      "recommendations": true,
      "social": true,
      "system": true
    },
    "email": {
      "enabled": true,
      "weekly_summary": false,
      "monthly_report": false,
      "marketing": false
    },
    "quietHours": {
      "enabled": false,
      "start": "22:00",
      "end": "08:00",
      "timezone": "Asia/Seoul"
    }
  }',

  -- 프라이버시 설정
  privacy_settings JSONB DEFAULT '{
    "profileVisibility": "friends",
    "activityVisibility": "friends",
    "locationSharing": true,
    "analyticsOptIn": true,
    "marketingOptIn": false,
    "dataRetention": "standard"
  }',

  -- 메타데이터
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  version INTEGER NOT NULL DEFAULT 1,
  last_synced_at TIMESTAMP WITH TIME ZONE,
  device_ids TEXT[] DEFAULT '{}'
);

-- 인덱스 생성
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_last_active ON user_profiles(last_active_at DESC);
CREATE INDEX idx_user_profiles_updated_at ON user_profiles(updated_at DESC);
CREATE INDEX idx_user_profiles_display_name ON user_profiles USING gin(to_tsvector('english', display_name));
CREATE INDEX idx_user_profiles_preferences ON user_profiles USING gin(dating_preferences);
CREATE INDEX idx_user_profiles_privacy ON user_profiles((privacy_settings->>'profileVisibility'));
```

### 1.2 Places (장소)
```sql
CREATE TABLE places (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL,
  external_id VARCHAR(255), -- 외부 서비스 ID (Google Places, Kakao 등)

  -- 기본 정보
  name VARCHAR(200) NOT NULL,
  address TEXT NOT NULL,
  phone VARCHAR(50),
  website TEXT,

  -- 지리 정보 (PostGIS)
  coordinates GEOGRAPHY(POINT, 4326) NOT NULL,
  region VARCHAR(100),
  district VARCHAR(100),

  -- 분류 정보
  category VARCHAR(50) NOT NULL CHECK (category IN ('cafe', 'restaurant', 'tourist', 'shopping', 'culture', 'activity')),
  tags TEXT[] DEFAULT '{}',
  atmosphere_tags TEXT[] DEFAULT '{}',

  -- AI 분석 결과
  ai_confidence DECIMAL(3,2) CHECK (ai_confidence >= 0 AND ai_confidence <= 1),
  ai_analysis JSONB,

  -- 사용자 평가
  personal_rating INTEGER CHECK (personal_rating >= 1 AND personal_rating <= 5),
  personal_notes TEXT,
  visited_at TIMESTAMP WITH TIME ZONE,

  -- 소셜 정보
  likes_count INTEGER DEFAULT 0,
  saves_count INTEGER DEFAULT 0,
  shares_count INTEGER DEFAULT 0,

  -- 상태 관리
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deleted')),
  visibility VARCHAR(20) DEFAULT 'private' CHECK (visibility IN ('public', 'friends', 'private')),

  -- 메타데이터
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX idx_places_user_id ON places(user_id);
CREATE INDEX idx_places_category ON places(category);
CREATE INDEX idx_places_status ON places(status);
CREATE INDEX idx_places_coordinates ON places USING GIST(coordinates);
CREATE INDEX idx_places_name_search ON places USING gin(to_tsvector('korean', name));
CREATE INDEX idx_places_tags ON places USING gin(tags);
CREATE INDEX idx_places_created_at ON places(created_at DESC);
CREATE INDEX idx_places_user_category ON places(user_id, category);
CREATE INDEX idx_places_region_category ON places(region, category);
```

### 1.3 Courses (코스)
```sql
CREATE TABLE courses (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL,

  -- 기본 정보
  title VARCHAR(200) NOT NULL,
  description TEXT,
  course_type VARCHAR(50) NOT NULL CHECK (course_type IN ('romantic', 'activity', 'food', 'culture', 'shopping', 'nature')),

  -- 코스 설정
  duration_hours DECIMAL(3,1), -- 예상 소요시간
  difficulty_level INTEGER CHECK (difficulty_level >= 1 AND difficulty_level <= 5),
  budget_min INTEGER,
  budget_max INTEGER,

  -- 참가자 정보
  companion_type VARCHAR(20) CHECK (companion_type IN ('couple', 'friend', 'solo', 'family')),
  group_size_min INTEGER DEFAULT 1,
  group_size_max INTEGER DEFAULT 2,

  -- 시간 정보
  preferred_time_slots TEXT[] DEFAULT '{}', -- ['morning', 'afternoon', 'evening', 'night']
  seasonal_availability TEXT[] DEFAULT '{}', -- ['spring', 'summer', 'autumn', 'winter']

  -- AI 추천 정보
  recommendation_score DECIMAL(3,2),
  recommendation_reasons TEXT[],

  -- 소셜 정보
  likes_count INTEGER DEFAULT 0,
  saves_count INTEGER DEFAULT 0,
  shares_count INTEGER DEFAULT 0,
  views_count INTEGER DEFAULT 0,

  -- 상태 관리
  status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived', 'deleted')),
  visibility VARCHAR(20) DEFAULT 'private' CHECK (visibility IN ('public', 'friends', 'private')),

  -- 메타데이터
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX idx_courses_user_id ON courses(user_id);
CREATE INDEX idx_courses_type ON courses(course_type);
CREATE INDEX idx_courses_status ON courses(status);
CREATE INDEX idx_courses_visibility ON courses(visibility);
CREATE INDEX idx_courses_created_at ON courses(created_at DESC);
CREATE INDEX idx_courses_recommendation_score ON courses(recommendation_score DESC);
CREATE INDEX idx_courses_title_search ON courses USING gin(to_tsvector('korean', title));
```

### 1.4 Course Places (코스-장소 연결)
```sql
CREATE TABLE course_places (
  id SERIAL PRIMARY KEY,
  course_id INTEGER NOT NULL,
  place_id INTEGER NOT NULL,

  -- 순서 정보
  sequence_order INTEGER NOT NULL,

  -- 이동 정보
  travel_time_minutes INTEGER,
  travel_distance_km DECIMAL(5,2),
  travel_method VARCHAR(20) CHECK (travel_method IN ('walking', 'driving', 'public_transport', 'bicycle')),

  -- 장소별 계획
  planned_duration_minutes INTEGER,
  planned_budget INTEGER,
  visit_notes TEXT,

  -- 메타데이터
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
  FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE,
  UNIQUE(course_id, sequence_order)
);

-- 인덱스 생성
CREATE INDEX idx_course_places_course_id ON course_places(course_id);
CREATE INDEX idx_course_places_place_id ON course_places(place_id);
CREATE INDEX idx_course_places_sequence ON course_places(course_id, sequence_order);
```

## 2. SNS Link Analysis Tables

### 2.1 Link Analysis Results (링크 분석 결과)
```sql
CREATE TABLE link_analysis_results (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL,

  -- 링크 정보
  original_url TEXT NOT NULL,
  url_hash VARCHAR(64) UNIQUE NOT NULL, -- SHA-256 해시
  platform VARCHAR(50) NOT NULL, -- 'instagram', 'youtube', 'blog', etc.

  -- 추출된 컨텐츠
  title TEXT,
  description TEXT,
  images TEXT[], -- 이미지 URL 배열
  extracted_text TEXT,

  -- AI 분석 결과
  analysis_status VARCHAR(20) DEFAULT 'pending' CHECK (analysis_status IN ('pending', 'processing', 'completed', 'failed')),
  ai_confidence DECIMAL(3,2),
  detected_places JSONB, -- AI가 감지한 장소들

  -- 메타데이터
  processing_time_ms INTEGER,
  error_message TEXT,
  retry_count INTEGER DEFAULT 0,
  expires_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX idx_link_analysis_user_id ON link_analysis_results(user_id);
CREATE INDEX idx_link_analysis_url_hash ON link_analysis_results(url_hash);
CREATE INDEX idx_link_analysis_status ON link_analysis_results(analysis_status);
CREATE INDEX idx_link_analysis_platform ON link_analysis_results(platform);
CREATE INDEX idx_link_analysis_created_at ON link_analysis_results(created_at DESC);
```

## 3. Social Features Tables

### 3.1 Shares (공유)
```sql
CREATE TABLE shares (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL, -- 공유한 사용자
  content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('place', 'course')),
  content_id INTEGER NOT NULL, -- places.id 또는 courses.id

  -- 공유 정보
  share_type VARCHAR(20) NOT NULL CHECK (share_type IN ('link', 'direct', 'social')),
  share_token VARCHAR(64) UNIQUE, -- 공유 링크용 토큰
  recipient_user_ids TEXT[], -- 직접 공유 시 수신자 ID들

  -- 공유 설정
  expires_at TIMESTAMP WITH TIME ZONE,
  requires_auth BOOLEAN DEFAULT FALSE,
  view_count INTEGER DEFAULT 0,

  -- 메타데이터
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX idx_shares_user_id ON shares(user_id);
CREATE INDEX idx_shares_content ON shares(content_type, content_id);
CREATE INDEX idx_shares_token ON shares(share_token);
CREATE INDEX idx_shares_created_at ON shares(created_at DESC);
```

### 3.2 Likes (좋아요)
```sql
CREATE TABLE likes (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL,
  content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('place', 'course')),
  content_id INTEGER NOT NULL,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE,
  UNIQUE(user_id, content_type, content_id)
);

-- 인덱스 생성
CREATE INDEX idx_likes_user_id ON likes(user_id);
CREATE INDEX idx_likes_content ON likes(content_type, content_id);
CREATE INDEX idx_likes_created_at ON likes(created_at DESC);
```

### 3.3 Comments (댓글)
```sql
CREATE TABLE comments (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL,
  content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('place', 'course')),
  content_id INTEGER NOT NULL,
  parent_comment_id INTEGER, -- 대댓글용

  -- 댓글 내용
  content TEXT NOT NULL CHECK (LENGTH(content) <= 1000),

  -- 상태 관리
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'deleted', 'reported')),

  -- 메타데이터
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE,
  FOREIGN KEY (parent_comment_id) REFERENCES comments(id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX idx_comments_content ON comments(content_type, content_id);
CREATE INDEX idx_comments_user_id ON comments(user_id);
CREATE INDEX idx_comments_parent ON comments(parent_comment_id);
CREATE INDEX idx_comments_created_at ON comments(created_at DESC);
```

## 4. Search and Filter Tables

### 4.1 Search Logs (검색 로그)
```sql
CREATE TABLE search_logs (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(128),

  -- 검색 정보
  query TEXT NOT NULL,
  search_type VARCHAR(20) CHECK (search_type IN ('place', 'course', 'user', 'tag')),
  filters_applied JSONB,

  -- 결과 정보
  results_count INTEGER,
  selected_result_id INTEGER,
  selected_result_position INTEGER,

  -- 세션 정보
  session_id VARCHAR(64),
  device_type VARCHAR(20),

  -- 메타데이터
  search_duration_ms INTEGER,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE SET NULL
);

-- 인덱스 생성
CREATE INDEX idx_search_logs_user_id ON search_logs(user_id);
CREATE INDEX idx_search_logs_query ON search_logs USING gin(to_tsvector('korean', query));
CREATE INDEX idx_search_logs_created_at ON search_logs(created_at DESC);
```

### 4.2 Popular Tags (인기 태그)
```sql
CREATE TABLE popular_tags (
  id SERIAL PRIMARY KEY,
  tag_name VARCHAR(50) UNIQUE NOT NULL,
  category VARCHAR(50),

  -- 통계 정보
  usage_count INTEGER DEFAULT 1,
  last_used_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  trending_score DECIMAL(5,2) DEFAULT 0,

  -- 메타데이터
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_popular_tags_name ON popular_tags(tag_name);
CREATE INDEX idx_popular_tags_category ON popular_tags(category);
CREATE INDEX idx_popular_tags_usage_count ON popular_tags(usage_count DESC);
CREATE INDEX idx_popular_tags_trending ON popular_tags(trending_score DESC);
```

## 5. Recommendation System Tables

### 5.1 User Preferences History (사용자 선호도 이력)
```sql
CREATE TABLE user_preference_history (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL,

  -- 선호도 정보
  content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('place', 'course')),
  content_id INTEGER NOT NULL,
  interaction_type VARCHAR(20) NOT NULL CHECK (interaction_type IN ('like', 'save', 'share', 'visit', 'skip')),

  -- 컨텍스트 정보
  context JSONB, -- 시간대, 날씨, 동반자 등

  -- 가중치
  preference_weight DECIMAL(3,2) DEFAULT 1.0,

  -- 메타데이터
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX idx_preference_history_user_id ON user_preference_history(user_id);
CREATE INDEX idx_preference_history_content ON user_preference_history(content_type, content_id);
CREATE INDEX idx_preference_history_interaction ON user_preference_history(interaction_type);
CREATE INDEX idx_preference_history_created_at ON user_preference_history(created_at DESC);
```

### 5.2 Recommendation Results (추천 결과)
```sql
CREATE TABLE recommendation_results (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL,

  -- 추천 정보
  recommendation_type VARCHAR(20) NOT NULL CHECK (recommendation_type IN ('place', 'course', 'hybrid')),
  context JSONB, -- 추천 요청 시 컨텍스트

  -- 추천 결과
  recommended_items JSONB NOT NULL, -- 추천된 아이템들과 점수
  algorithm_version VARCHAR(20),
  confidence_score DECIMAL(3,2),

  -- 사용자 반응
  user_feedback VARCHAR(20) CHECK (user_feedback IN ('accepted', 'rejected', 'ignored')),
  feedback_reason TEXT,

  -- 메타데이터
  expires_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX idx_recommendation_results_user_id ON recommendation_results(user_id);
CREATE INDEX idx_recommendation_results_type ON recommendation_results(recommendation_type);
CREATE INDEX idx_recommendation_results_created_at ON recommendation_results(created_at DESC);
```

## 6. Notification System Tables

### 6.1 Notifications (알림)
```sql
CREATE TABLE notifications (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL,

  -- 알림 정보
  notification_type VARCHAR(50) NOT NULL,
  title VARCHAR(200) NOT NULL,
  message TEXT NOT NULL,

  -- 액션 정보
  action_type VARCHAR(20), -- 'open_place', 'open_course', 'open_url'
  action_data JSONB,

  -- 발송 정보
  delivery_method VARCHAR(20) NOT NULL CHECK (delivery_method IN ('push', 'email', 'in_app')),
  delivery_status VARCHAR(20) DEFAULT 'pending' CHECK (delivery_status IN ('pending', 'sent', 'delivered', 'failed')),
  delivery_attempts INTEGER DEFAULT 0,

  -- 사용자 상호작용
  read_at TIMESTAMP WITH TIME ZONE,
  clicked_at TIMESTAMP WITH TIME ZONE,

  -- 스케줄링
  scheduled_for TIMESTAMP WITH TIME ZONE,
  expires_at TIMESTAMP WITH TIME ZONE,

  -- 메타데이터
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_type ON notifications(notification_type);
CREATE INDEX idx_notifications_delivery_status ON notifications(delivery_status);
CREATE INDEX idx_notifications_scheduled_for ON notifications(scheduled_for);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
```

### 6.2 Notification Templates (알림 템플릿)
```sql
CREATE TABLE notification_templates (
  id SERIAL PRIMARY KEY,

  -- 템플릿 정보
  template_key VARCHAR(100) UNIQUE NOT NULL,
  template_name VARCHAR(200) NOT NULL,

  -- 다국어 지원
  title_template JSONB NOT NULL, -- {"ko": "제목", "en": "Title"}
  message_template JSONB NOT NULL,

  -- 설정
  default_delivery_method VARCHAR(20) DEFAULT 'push',
  priority_level INTEGER DEFAULT 3 CHECK (priority_level >= 1 AND priority_level <= 5),

  -- 상태
  is_active BOOLEAN DEFAULT TRUE,

  -- 메타데이터
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_notification_templates_key ON notification_templates(template_key);
CREATE INDEX idx_notification_templates_active ON notification_templates(is_active);
```

## 7. System and Audit Tables

### 7.1 Setting Change Logs (설정 변경 이력)
```sql
CREATE TABLE setting_change_logs (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL,
  change_type VARCHAR(20) CHECK (change_type IN ('profile', 'preferences', 'notifications', 'privacy')),
  field_name VARCHAR(100) NOT NULL,
  old_value JSONB,
  new_value JSONB,
  source VARCHAR(20) CHECK (source IN ('user', 'system', 'migration')),
  device_info JSONB,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_setting_logs_user_id ON setting_change_logs(user_id);
CREATE INDEX idx_setting_logs_timestamp ON setting_change_logs(timestamp DESC);
CREATE INDEX idx_setting_logs_change_type ON setting_change_logs(change_type);
```

### 7.2 Data Exports (데이터 내보내기)
```sql
CREATE TABLE data_exports (
  id SERIAL PRIMARY KEY,
  export_id VARCHAR(64) UNIQUE NOT NULL,
  user_id VARCHAR(128) NOT NULL,

  -- 내보내기 정보
  export_type VARCHAR(20) NOT NULL CHECK (export_type IN ('full', 'profile', 'activity')),
  format VARCHAR(10) NOT NULL CHECK (format IN ('json', 'csv')),

  -- 상태 정보
  status VARCHAR(20) DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed', 'expired')),
  download_url TEXT,
  file_size BIGINT,

  -- 에러 정보
  error TEXT,

  -- 메타데이터
  expires_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

  FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX idx_data_exports_user_id ON data_exports(user_id);
CREATE INDEX idx_data_exports_export_id ON data_exports(export_id);
CREATE INDEX idx_data_exports_status ON data_exports(status);
```

### 7.3 Scheduled Deletions (예약된 삭제)
```sql
CREATE TABLE scheduled_deletions (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(128) NOT NULL,

  -- 삭제 정보
  scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  execution_date TIMESTAMP WITH TIME ZONE NOT NULL,
  reason TEXT,

  -- 상태 관리
  status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'executed', 'cancelled')),
  cancelled_at TIMESTAMP WITH TIME ZONE,
  executed_at TIMESTAMP WITH TIME ZONE,

  FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX idx_scheduled_deletions_user_id ON scheduled_deletions(user_id);
CREATE INDEX idx_scheduled_deletions_execution_date ON scheduled_deletions(execution_date);
CREATE INDEX idx_scheduled_deletions_status ON scheduled_deletions(status);
```

## 8. Cache and Performance Tables

### 8.1 Cache Statistics (캐시 통계)
```sql
CREATE TABLE cache_statistics (
  id SERIAL PRIMARY KEY,

  -- 캐시 정보
  cache_key_pattern VARCHAR(100) NOT NULL,
  cache_type VARCHAR(20) NOT NULL CHECK (cache_type IN ('redis', 'local', 'cdn')),

  -- 통계 정보
  hit_count INTEGER DEFAULT 0,
  miss_count INTEGER DEFAULT 0,
  eviction_count INTEGER DEFAULT 0,

  -- 성능 메트릭
  avg_response_time_ms DECIMAL(8,2),
  total_size_bytes BIGINT,

  -- 시간 윈도우
  window_start TIMESTAMP WITH TIME ZONE NOT NULL,
  window_end TIMESTAMP WITH TIME ZONE NOT NULL,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_cache_stats_pattern ON cache_statistics(cache_key_pattern);
CREATE INDEX idx_cache_stats_type ON cache_statistics(cache_type);
CREATE INDEX idx_cache_stats_window ON cache_statistics(window_start, window_end);
```

## 9. Analytics Tables (ClickHouse)

### 9.1 User Behavior Events
```sql
-- ClickHouse 테이블
CREATE TABLE user_behavior_events (
    user_id String,
    event_type String,
    event_data String, -- JSON
    timestamp DateTime,
    session_id String,
    device_type String,
    app_version String,
    ip_address String,
    user_agent String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (user_id, timestamp)
SETTINGS index_granularity = 8192;
```

### 9.2 User Activity Stats
```sql
-- ClickHouse 테이블
CREATE TABLE user_activity_stats (
    user_id String,
    date Date,
    places_saved UInt32,
    places_visited UInt32,
    courses_created UInt32,
    courses_completed UInt32,
    shares_sent UInt32,
    shares_received UInt32,
    time_spent_minutes UInt32,
    categories_explored Array(String),
    regions_visited Array(String),
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (user_id, date);
```

## 10. Materialized Views

### 10.1 User Stats View
```sql
CREATE MATERIALIZED VIEW user_stats_view AS
SELECT
  up.user_id,
  up.display_name,
  up.last_active_at,
  COUNT(DISTINCT p.id) as places_count,
  COUNT(DISTINCT c.id) as courses_count,
  COUNT(DISTINCT s.id) as shares_count
FROM user_profiles up
LEFT JOIN places p ON up.user_id = p.user_id AND p.status = 'active'
LEFT JOIN courses c ON up.user_id = c.user_id AND c.status != 'deleted'
LEFT JOIN shares s ON up.user_id = s.user_id
GROUP BY up.user_id, up.display_name, up.last_active_at;

CREATE INDEX idx_user_stats_view_user_id ON user_stats_view(user_id);
```

### 10.2 Popular Places View
```sql
CREATE MATERIALIZED VIEW popular_places_view AS
SELECT
  p.id,
  p.name,
  p.category,
  p.region,
  p.coordinates,
  COUNT(DISTINCT l.user_id) as likes_count,
  COUNT(DISTINCT cp.course_id) as courses_count,
  AVG(p.personal_rating) as avg_rating,
  p.created_at
FROM places p
LEFT JOIN likes l ON l.content_type = 'place' AND l.content_id = p.id
LEFT JOIN course_places cp ON cp.place_id = p.id
WHERE p.status = 'active' AND p.visibility IN ('public', 'friends')
GROUP BY p.id, p.name, p.category, p.region, p.coordinates, p.created_at
HAVING COUNT(DISTINCT l.user_id) >= 5; -- 최소 5명 이상 좋아요

CREATE INDEX idx_popular_places_category ON popular_places_view(category);
CREATE INDEX idx_popular_places_region ON popular_places_view(region);
CREATE INDEX idx_popular_places_likes ON popular_places_view(likes_count DESC);
```

## 11. Database Triggers and Functions

### 11.1 Update Timestamps Trigger
```sql
-- updated_at 자동 업데이트 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 적용
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_places_updated_at BEFORE UPDATE ON places
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_courses_updated_at BEFORE UPDATE ON courses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 11.2 Search Vector Update Trigger
```sql
-- 검색 벡터 자동 업데이트
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector = to_tsvector('korean',
        COALESCE(NEW.name, '') || ' ' ||
        COALESCE(NEW.address, '') || ' ' ||
        COALESCE(array_to_string(NEW.tags, ' '), '')
    );
    RETURN NEW;
END;
$$ language 'plpgsql';

-- places 테이블에 검색 벡터 컬럼 추가
ALTER TABLE places ADD COLUMN search_vector tsvector;
CREATE INDEX idx_places_search_vector ON places USING gin(search_vector);

CREATE TRIGGER update_places_search_vector
    BEFORE INSERT OR UPDATE ON places
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();
```

## 12. Extensions and Setup

### 12.1 Required PostgreSQL Extensions
```sql
-- PostGIS for geographical data
CREATE EXTENSION IF NOT EXISTS postgis;

-- Full-text search with Korean support
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- JSONB operations
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Cron jobs (PostgreSQL 11+)
CREATE EXTENSION IF NOT EXISTS pg_cron;
```

### 12.2 Cleanup Jobs
```sql
-- 만료된 링크 분석 결과 정리 (매일 새벽 2시)
SELECT cron.schedule('cleanup-expired-analysis', '0 2 * * *',
  'DELETE FROM link_analysis_results WHERE expires_at < NOW()'
);

-- 오래된 설정 변경 로그 정리 (매일 새벽 3시)
SELECT cron.schedule('cleanup-old-logs', '0 3 * * *',
  'DELETE FROM setting_change_logs WHERE timestamp < NOW() - INTERVAL ''90 days'''
);

-- 만료된 알림 정리 (매시간)
SELECT cron.schedule('cleanup-expired-notifications', '0 * * * *',
  'DELETE FROM notifications WHERE expires_at < NOW()'
);
```

---

*작성일: 2025-01-XX*
*작성자: Claude*
*버전: 1.0*
