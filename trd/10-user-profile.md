# TRD: 사용자 프로필 및 설정 관리 시스템

## 1. 시스템 개요

### 1-1. 아키텍처 구조
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   API Gateway   │    │ Profile Service │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Profile UI  │ │◄───┤ │ Auth        │ │◄───┤ │ Profile     │ │
│ │ Settings UI │ │    │ │ Middleware  │ │    │ │ Manager     │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Analytics   │ │    │ │ Validation  │ │    │ │ Settings    │ │
│ │ Dashboard   │ │    │ │ Middleware  │ │    │ │ Manager     │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Privacy     │ │    │ │ Rate Limit  │ │    │ │ Privacy     │ │
│ │ Controls    │ │    │ │ Middleware  │ │    │ │ Controller  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ External APIs   │    │   Data Store    │    │ Analytics       │
│                 │    │                 │    │ Service         │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Image CDN   │ │───►│ │ PostgreSQL  │ │◄───┤ │ User Stats  │ │
│ │ (Cloudinary)│ │    │ │User Profiles│ │    │ │ Aggregator  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Cloud       │ │    │ │ Redis Cache │ │    │ │ Insight     │ │
│ │ Storage     │ │    │ │Settings     │ │    │ │ Generator   │ │
│ └─────────────┘ │    │ │Preferences  │ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ └─────────────┘ │    │ ┌─────────────┐ │
│ │ Email       │ │    │ ┌─────────────┐ │    │ │ Report      │ │
│ │ Service     │ │    │ │ Analytics   │ │    │ │ Generator   │ │
│ └─────────────┘ │    │ │ DB          │ │    │ └─────────────┘ │
└─────────────────┘    │ │(ClickHouse) │ │    └─────────────────┘
                       │ └─────────────┘ │
                       └─────────────────┘
```

### 1-2. 기술 스택
```yaml
Backend:
  Runtime: Node.js 18+ (TypeScript)
  Framework: Express.js
  Validation: Joi, express-validator
  File Upload: Multer, Sharp (이미지 처리)

Database:
  Primary: PostgreSQL (user profiles, settings)
  Cache: Redis Cluster (settings, preferences)
  Analytics: ClickHouse (user activity tracking)
  Search: Elasticsearch (user search)

Storage:
  Images: Cloudinary CDN
  Backups: AWS S3
  Data Export: AWS S3 + Lambda

Security:
  Encryption: AES-256-GCM (sensitive data)
  Privacy: GDPR compliance toolkit
  Audit: Winston + PostgreSQL (audit logs)

Client:
  State Management: Redux Toolkit (profile state)
  Form Handling: React Hook Form + Yup
  Image Upload: React Native Image Picker
  Analytics: Custom tracking hooks
```

## 2. 데이터베이스 설계

### 2-1. 사용자 프로필 스키마 (PostgreSQL)
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

  -- 예시 JSONB 구조:
  -- dating_preferences: {
  --   "region": ["seoul", "busan"],
  --   "transport": ["walking", "public_transport"],
  --   "timeSlots": ["evening", "night"],
  --   "companionType": ["couple"],
  --   "budget": {"min": 30000, "max": 100000, "currency": "KRW"}
  -- }
  -- recommendation_preferences: {
  --   "categoryRatings": {"cafe": 4, "restaurant": 5, "tourist": 3},
  --   "atmospherePreference": {"quiet_lively": 2, "traditional_modern": -1},
  --   "discoveryMode": "moderate"
  -- }

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

### 2-2. 사용자 통계 스키마 (ClickHouse)
```sql
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

CREATE TABLE user_behavior_events (
    user_id String,
    event_type String,
    event_data String, -- JSON
    timestamp DateTime,
    session_id String,
    device_type String,
    app_version String
) ENGINE = MergeTree()
ORDER BY (user_id, timestamp);
```

### 2-3. 설정 변경 이력 스키마 (PostgreSQL)
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

-- 자동 삭제를 위한 파티션 테이블 (선택사항)
CREATE TABLE setting_change_logs_old (LIKE setting_change_logs);
```

## 3. API 설계

### 3-1. 프로필 관리 API
```typescript
// GET /api/profile
interface GetProfileResponse {
  profile: {
    displayName: string;
    photoURL?: string;
    bio?: string;
    location?: string;
    interests: string[];
    joinedAt: string;
    stats: {
      placesCount: number;
      coursesCount: number;
      sharesCount: number;
    };
  };
  personalInfo: {
    email: string;
    phoneNumber?: string;
    verified: {
      email: boolean;
      phone: boolean;
    };
  };
}

// PUT /api/profile
interface UpdateProfileRequest {
  displayName?: string;
  bio?: string;
  location?: string;
  interests?: string[];
  personalInfo?: {
    phoneNumber?: string;
    dateOfBirth?: string;
  };
}

// POST /api/profile/photo
interface UploadProfilePhotoRequest {
  photo: File; // multipart/form-data
  crop?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

interface UploadProfilePhotoResponse {
  photoURL: string;
  thumbnailURL: string;
}
```

### 3-2. 설정 관리 API
```typescript
// GET /api/settings
interface GetSettingsResponse {
  preferences: UserPreferences;
  notifications: NotificationSettings;
  privacy: PrivacySettings;
}

// PUT /api/settings/preferences
interface UpdatePreferencesRequest {
  dating?: Partial<DatingPreferences>;
  recommendations?: Partial<RecommendationPreferences>;
}

// PUT /api/settings/notifications
interface UpdateNotificationSettingsRequest {
  push?: Partial<PushNotificationSettings>;
  email?: Partial<EmailNotificationSettings>;
  quietHours?: QuietHoursSettings;
}

// PUT /api/settings/privacy
interface UpdatePrivacySettingsRequest {
  profileVisibility?: 'public' | 'friends' | 'private';
  activityVisibility?: 'public' | 'friends' | 'private';
  locationSharing?: boolean;
  analyticsOptIn?: boolean;
  marketingOptIn?: boolean;
}
```

### 3-3. 통계 및 분석 API
```typescript
// GET /api/profile/stats
interface GetUserStatsRequest {
  period?: 'week' | 'month' | 'quarter' | 'year';
  categories?: string[];
}

interface GetUserStatsResponse {
  summary: {
    totalPlaces: number;
    totalCourses: number;
    totalShares: number;
    activeStreak: number; // 연속 활동 일수
  };

  activity: {
    placesThisPeriod: number;
    coursesThisPeriod: number;
    avgPerWeek: number;
    trendDirection: 'up' | 'down' | 'stable';
  };

  preferences: {
    topCategories: Array<{
      category: string;
      count: number;
      percentage: number;
    }>;
    topRegions: Array<{
      region: string;
      count: number;
      percentage: number;
    }>;
    timePatterns: {
      preferredDays: string[];
      preferredHours: number[];
    };
  };

  insights: {
    personalityType: string;
    explorationScore: number; // 0-100
    socialScore: number;
    recommendations: string[];
  };
}

// GET /api/profile/activity-timeline
interface GetActivityTimelineResponse {
  events: Array<{
    date: string;
    type: 'place_saved' | 'course_created' | 'place_visited' | 'course_shared';
    title: string;
    description?: string;
    metadata?: any;
  }>;
  milestones: Array<{
    date: string;
    type: 'first_place' | 'first_course' | '10_places' | '50_places';
    title: string;
    badge?: string;
  }>;
}
```

### 3-4. 데이터 관리 API
```typescript
// POST /api/profile/export
interface ExportDataRequest {
  format: 'json' | 'csv';
  includePersonalInfo: boolean;
  includeActivity: boolean;
  includeAnalytics: boolean;
}

interface ExportDataResponse {
  exportId: string;
  status: 'processing' | 'ready' | 'expired';
  downloadUrl?: string;
  expiresAt: string;
}

// DELETE /api/profile/data
interface DeleteDataRequest {
  dataTypes: ('profile' | 'activity' | 'analytics' | 'all')[];
  confirmationCode: string;
}

// POST /api/profile/deactivate
interface DeactivateAccountRequest {
  reason?: string;
  feedback?: string;
  deleteAfterDays: number; // 1-30
}
```

## 4. 프로필 관리 서비스

### 4-1. 프로필 서비스 구현
```typescript
// profile-service.ts
class ProfileService {
  constructor(
    private postgresql: Pool,
    private redis: Redis,
    private imageService: ImageService,
    private auditLogger: AuditLogger
  ) {}

  async getProfile(userId: string): Promise<UserProfile> {
    // 1. 캐시 확인
    const cachedProfile = await this.redis.get(`profile:${userId}`);
    if (cachedProfile) {
      return JSON.parse(cachedProfile);
    }

    // 2. DB에서 조회
    const result = await this.postgresql.query(
      'SELECT * FROM user_profiles WHERE user_id = $1',
      [userId]
    );

    if (result.rows.length === 0) {
      throw new NotFoundError('Profile not found');
    }

    const profile = result.rows[0];

    // 3. 캐시 저장 (1시간 TTL)
    await this.redis.setex(
      `profile:${userId}`,
      3600,
      JSON.stringify(profile)
    );

    return profile;
  }

  async updateProfile(
    userId: string,
    updates: Partial<UserProfile>,
    context: RequestContext
  ): Promise<UserProfile> {
    // 1. 입력 검증
    this.validateProfileUpdates(updates);

    // 2. 기존 프로필 조회
    const currentProfile = await this.getProfile(userId);

    // 3. 변경사항 기록
    await this.logProfileChanges(userId, currentProfile, updates, context);

    // 4. 프로필 업데이트
    const updatedProfile = {
      ...currentProfile,
      ...updates,
      metadata: {
        ...currentProfile.metadata,
        updatedAt: new Date(),
        version: currentProfile.metadata.version + 1
      }
    };

    await this.postgresql.query(`
      UPDATE user_profiles
      SET
        display_name = COALESCE($2, display_name),
        bio = COALESCE($3, bio),
        location = COALESCE($4, location),
        interests = COALESCE($5, interests),
        phone_number = COALESCE($6, phone_number),
        date_of_birth = COALESCE($7, date_of_birth),
        dating_preferences = COALESCE($8, dating_preferences),
        recommendation_preferences = COALESCE($9, recommendation_preferences),
        updated_at = NOW(),
        version = version + 1
      WHERE user_id = $1
    `, [
      userId,
      updates.profile?.displayName,
      updates.profile?.bio,
      updates.profile?.location,
      updates.profile?.interests,
      updates.personalInfo?.phoneNumber,
      updates.personalInfo?.dateOfBirth,
      updates.preferences?.dating ? JSON.stringify(updates.preferences.dating) : null,
      updates.preferences?.recommendations ? JSON.stringify(updates.preferences.recommendations) : null
    ]);

    // 5. 캐시 무효화
    await this.redis.del(`profile:${userId}`);

    // 6. 실시간 알림 (다른 기기들에게)
    await this.notifyProfileUpdate(userId, updates);

    return updatedProfile;
  }

  async uploadProfilePhoto(
    userId: string,
    file: Express.Multer.File,
    cropOptions?: CropOptions
  ): Promise<{ photoURL: string; thumbnailURL: string }> {
    try {
      // 1. 이미지 검증
      this.validateImageFile(file);

      // 2. 이미지 처리
      const processedImage = await this.imageService.processProfileImage(
        file.buffer,
        {
          crop: cropOptions,
          resize: { width: 400, height: 400 },
          format: 'jpeg',
          quality: 90
        }
      );

      // 3. 썸네일 생성
      const thumbnail = await this.imageService.generateThumbnail(
        processedImage,
        { width: 100, height: 100 }
      );

      // 4. CDN 업로드
      const [photoURL, thumbnailURL] = await Promise.all([
        this.imageService.uploadToCDN(processedImage, `profiles/${userId}/photo.jpg`),
        this.imageService.uploadToCDN(thumbnail, `profiles/${userId}/thumbnail.jpg`)
      ]);

      // 5. 프로필 업데이트
      await this.updateProfile(userId, {
        profile: { photoURL }
      }, { source: 'photo_upload' });

      return { photoURL, thumbnailURL };
    } catch (error) {
      console.error('Profile photo upload failed:', error);
      throw new ProfilePhotoUploadError('Failed to upload profile photo');
    }
  }

  private validateProfileUpdates(updates: Partial<UserProfile>): void {
    const schema = Joi.object({
      profile: Joi.object({
        displayName: Joi.string().min(2).max(50),
        bio: Joi.string().max(500),
        location: Joi.string().max(100),
        interests: Joi.array().items(Joi.string()).max(20)
      }),
      personalInfo: Joi.object({
        phoneNumber: Joi.string().pattern(/^\+[1-9]\d{1,14}$/),
        dateOfBirth: Joi.date().max(new Date())
      })
    });

    const { error } = schema.validate(updates);
    if (error) {
      throw new ValidationError(error.details[0].message);
    }
  }

  private async logProfileChanges(
    userId: string,
    oldProfile: UserProfile,
    updates: Partial<UserProfile>,
    context: RequestContext
  ): Promise<void> {
    const changes = this.calculateChanges(oldProfile, updates);

    for (const change of changes) {
      await this.auditLogger.log({
        userId,
        action: 'profile_update',
        field: change.field,
        oldValue: change.oldValue,
        newValue: change.newValue,
        context
      });
    }
  }

  private async notifyProfileUpdate(
    userId: string,
    updates: Partial<UserProfile>
  ): Promise<void> {
    // WebSocket을 통해 다른 기기들에게 프로필 변경 알림
    const message = {
      type: 'profile_updated',
      userId,
      changes: Object.keys(updates),
      timestamp: new Date().toISOString()
    };

    await this.publishUpdate(`user:${userId}`, message);
  }
}
```

### 4-2. 설정 관리 서비스
```typescript
// settings-service.ts
class SettingsService {
  constructor(
    private postgresql: Pool,
    private redis: Redis,
    private eventBus: EventBus
  ) {}

  async getSettings(userId: string): Promise<UserSettings> {
    const cacheKey = `settings:${userId}`;

    // Redis에서 설정 조회
    const cachedSettings = await this.redis.hgetall(cacheKey);

    if (Object.keys(cachedSettings).length > 0) {
      return this.deserializeSettings(cachedSettings);
    }

    // DB에서 조회
    const result = await this.postgresql.query(`
      SELECT
        dating_preferences,
        recommendation_preferences,
        notification_settings,
        privacy_settings
      FROM user_profiles
      WHERE user_id = $1
    `, [userId]);

    if (result.rows.length === 0) {
      throw new NotFoundError('User settings not found');
    }

    const profile = result.rows[0];

    const settings = {
      preferences: {
        dating: profile.dating_preferences,
        recommendations: profile.recommendation_preferences
      },
      notifications: profile.notification_settings,
      privacy: profile.privacy_settings
    };

    // Redis에 캐시 (설정은 자주 변경되므로 짧은 TTL)
    await this.cacheSettings(userId, settings);

    return settings;
  }

  async updateSettings(
    userId: string,
    settingType: 'preferences' | 'notifications' | 'privacy',
    updates: any,
    context: RequestContext
  ): Promise<void> {
    // 1. 설정 검증
    this.validateSettings(settingType, updates);

    // 2. DB 업데이트
    let updateQuery: string;
    let queryParams: any[];

    switch (settingType) {
      case 'preferences':
        updateQuery = `
          UPDATE user_profiles
          SET dating_preferences = COALESCE($2, dating_preferences),
              recommendation_preferences = COALESCE($3, recommendation_preferences),
              updated_at = NOW(),
              version = version + 1
          WHERE user_id = $1
        `;
        queryParams = [
          userId,
          updates.dating ? JSON.stringify(updates.dating) : null,
          updates.recommendations ? JSON.stringify(updates.recommendations) : null
        ];
        break;
      case 'notifications':
        updateQuery = `
          UPDATE user_profiles
          SET notification_settings = $2,
              updated_at = NOW(),
              version = version + 1
          WHERE user_id = $1
        `;
        queryParams = [userId, JSON.stringify(updates)];
        break;
      case 'privacy':
        updateQuery = `
          UPDATE user_profiles
          SET privacy_settings = $2,
              updated_at = NOW(),
              version = version + 1
          WHERE user_id = $1
        `;
        queryParams = [userId, JSON.stringify(updates)];
        break;
    }

    await this.postgresql.query(updateQuery, queryParams);

    // 3. 캐시 업데이트
    await this.updateSettingsCache(userId, settingType, updates);

    // 4. 변경 이력 기록
    await this.logSettingChange(userId, settingType, updates, context);

    // 5. 설정 변경 이벤트 발송
    await this.eventBus.publish('settings_updated', {
      userId,
      settingType,
      updates,
      timestamp: new Date()
    });

    // 6. 즉시 적용이 필요한 설정 처리
    await this.applyImmediateSettings(userId, settingType, updates);
  }

  private async applyImmediateSettings(
    userId: string,
    settingType: string,
    updates: any
  ): Promise<void> {
    switch (settingType) {
      case 'notifications':
        // 알림 서비스에 즉시 설정 반영
        await this.updateNotificationPreferences(userId, updates);
        break;

      case 'privacy':
        // 프라이버시 설정 즉시 적용
        if (updates.profileVisibility) {
          await this.updateProfileVisibility(userId, updates.profileVisibility);
        }
        break;

      case 'preferences':
        // 추천 엔진에 새로운 선호도 반영
        await this.updateRecommendationPreferences(userId, updates);
        break;
    }
  }

  async resetSettings(
    userId: string,
    settingType: 'all' | 'preferences' | 'notifications' | 'privacy'
  ): Promise<void> {
    const defaultSettings = this.getDefaultSettings();

    let updateQuery: any = {
      'metadata.updatedAt': new Date(),
      $inc: { 'metadata.version': 1 }
    };

    if (settingType === 'all') {
      updateQuery = `
        UPDATE user_profiles
        SET dating_preferences = $2,
            recommendation_preferences = $3,
            notification_settings = $4,
            privacy_settings = $5,
            updated_at = NOW(),
            version = version + 1
        WHERE user_id = $1
      `;
      queryParams = [
        userId,
        JSON.stringify(defaultSettings.preferences.dating),
        JSON.stringify(defaultSettings.preferences.recommendations),
        JSON.stringify(defaultSettings.notifications),
        JSON.stringify(defaultSettings.privacy)
      ];
    } else {
      switch (settingType) {
        case 'preferences':
          updateQuery = `
            UPDATE user_profiles
            SET dating_preferences = $2,
                recommendation_preferences = $3,
                updated_at = NOW(),
                version = version + 1
            WHERE user_id = $1
          `;
          queryParams = [
            userId,
            JSON.stringify(defaultSettings.preferences.dating),
            JSON.stringify(defaultSettings.preferences.recommendations)
          ];
          break;
        case 'notifications':
          updateQuery = `
            UPDATE user_profiles
            SET notification_settings = $2,
                updated_at = NOW(),
                version = version + 1
            WHERE user_id = $1
          `;
          queryParams = [userId, JSON.stringify(defaultSettings.notifications)];
          break;
        case 'privacy':
          updateQuery = `
            UPDATE user_profiles
            SET privacy_settings = $2,
                updated_at = NOW(),
                version = version + 1
            WHERE user_id = $1
          `;
          queryParams = [userId, JSON.stringify(defaultSettings.privacy)];
          break;
      }
    }

    await this.postgresql.query(updateQuery, queryParams);

    // 캐시 초기화
    await this.redis.del(`settings:${userId}`);
  }

  private validateSettings(settingType: string, updates: any): void {
    const schemas = {
      preferences: Joi.object({
        dating: Joi.object({
          region: Joi.array().items(Joi.string()),
          transport: Joi.array().items(Joi.string().valid('walking', 'public_transport', 'car', 'bicycle')),
          budget: Joi.object({
            min: Joi.number().min(0),
            max: Joi.number().min(Joi.ref('min')),
            currency: Joi.string().valid('KRW', 'USD', 'EUR', 'JPY')
          })
        }),
        recommendations: Joi.object({
          categoryRatings: Joi.object().pattern(
            Joi.string(),
            Joi.number().min(1).max(5)
          ),
          discoveryMode: Joi.string().valid('conservative', 'moderate', 'adventurous')
        })
      }),

      notifications: Joi.object({
        push: Joi.object({
          enabled: Joi.boolean(),
          dateReminders: Joi.boolean(),
          recommendations: Joi.boolean(),
          social: Joi.boolean()
        }),
        email: Joi.object({
          enabled: Joi.boolean(),
          weekly_summary: Joi.boolean(),
          marketing: Joi.boolean()
        }),
        quietHours: Joi.object({
          enabled: Joi.boolean(),
          start: Joi.string().pattern(/^([01]?[0-9]|2[0-3]):[0-5][0-9]$/),
          end: Joi.string().pattern(/^([01]?[0-9]|2[0-3]):[0-5][0-9]$/)
        })
      }),

      privacy: Joi.object({
        profileVisibility: Joi.string().valid('public', 'friends', 'private'),
        activityVisibility: Joi.string().valid('public', 'friends', 'private'),
        locationSharing: Joi.boolean(),
        analyticsOptIn: Joi.boolean()
      })
    };

    const schema = schemas[settingType];
    if (!schema) {
      throw new ValidationError('Invalid setting type');
    }

    const { error } = schema.validate(updates);
    if (error) {
      throw new ValidationError(error.details[0].message);
    }
  }
}
```

## 5. 사용자 통계 및 분석

### 5-1. 통계 수집 서비스
```typescript
// analytics-service.ts
class UserAnalyticsService {
  constructor(
    private clickhouse: ClickHouseClient,
    private postgresql: Pool,
    private redis: Redis
  ) {}

  async trackUserActivity(
    userId: string,
    activity: UserActivity
  ): Promise<void> {
    try {
      // 1. ClickHouse에 실시간 이벤트 저장
      await this.clickhouse.insert('user_behavior_events', {
        user_id: userId,
        event_type: activity.type,
        event_data: JSON.stringify(activity.data),
        timestamp: new Date(),
        session_id: activity.sessionId,
        device_type: activity.deviceType,
        app_version: activity.appVersion
      });

      // 2. Redis에서 일일 통계 증분 업데이트
      const today = new Date().toISOString().split('T')[0];
      const key = `user_stats:${userId}:${today}`;

      await this.redis.hincrby(key, activity.type, 1);
      await this.redis.expire(key, 86400 * 7); // 7일 보관

      // 3. 실시간 스트리크 업데이트
      await this.updateActivityStreak(userId);

    } catch (error) {
      console.error('Failed to track user activity:', error);
      // 통계 수집 실패는 사용자 경험에 영향을 주면 안됨
    }
  }

  async getUserStats(
    userId: string,
    period: 'week' | 'month' | 'quarter' | 'year' = 'month'
  ): Promise<UserStats> {
    const cacheKey = `user_stats:${userId}:${period}`;

    // 캐시 확인
    const cachedStats = await this.redis.get(cacheKey);
    if (cachedStats) {
      return JSON.parse(cachedStats);
    }

    // ClickHouse에서 통계 계산
    const stats = await this.calculateUserStats(userId, period);

    // 캐시 저장 (1시간 TTL)
    await this.redis.setex(cacheKey, 3600, JSON.stringify(stats));

    return stats;
  }

  private async calculateUserStats(
    userId: string,
    period: string
  ): Promise<UserStats> {
    const dateRange = this.getDateRange(period);

    // 병렬로 여러 통계 쿼리 실행
    const [
      activitySummary,
      categoryDistribution,
      timePatterns,
      explorationMetrics
    ] = await Promise.all([
      this.getActivitySummary(userId, dateRange),
      this.getCategoryDistribution(userId, dateRange),
      this.getTimePatterns(userId, dateRange),
      this.getExplorationMetrics(userId, dateRange)
    ]);

    return {
      summary: activitySummary,
      preferences: {
        topCategories: categoryDistribution,
        timePatterns
      },
      exploration: explorationMetrics,
      insights: await this.generateInsights(userId, {
        activitySummary,
        categoryDistribution,
        timePatterns,
        explorationMetrics
      })
    };
  }

  private async getActivitySummary(
    userId: string,
    dateRange: { start: Date; end: Date }
  ): Promise<ActivitySummary> {
    const query = `
      SELECT
        countIf(event_type = 'place_saved') as places_saved,
        countIf(event_type = 'course_created') as courses_created,
        countIf(event_type = 'place_visited') as places_visited,
        countIf(event_type = 'course_shared') as courses_shared,
        uniq(toDate(timestamp)) as active_days
      FROM user_behavior_events
      WHERE user_id = ? AND timestamp BETWEEN ? AND ?
    `;

    const result = await this.clickhouse.query(query, [
      userId,
      dateRange.start,
      dateRange.end
    ]);

    return result.rows[0];
  }

  private async getCategoryDistribution(
    userId: string,
    dateRange: { start: Date; end: Date }
  ): Promise<CategoryDistribution[]> {
    const query = `
      SELECT
        JSONExtractString(event_data, 'category') as category,
        count(*) as count,
        count(*) * 100.0 / sum(count(*)) OVER() as percentage
      FROM user_behavior_events
      WHERE user_id = ?
        AND event_type = 'place_saved'
        AND timestamp BETWEEN ? AND ?
      GROUP BY category
      ORDER BY count DESC
      LIMIT 10
    `;

    const result = await this.clickhouse.query(query, [
      userId,
      dateRange.start,
      dateRange.end
    ]);

    return result.rows;
  }

  private async generateInsights(
    userId: string,
    stats: any
  ): Promise<UserInsights> {
    const insights: UserInsights = {
      personalityType: this.determinePersonalityType(stats),
      explorationScore: this.calculateExplorationScore(stats.explorationMetrics),
      socialScore: this.calculateSocialScore(stats.activitySummary),
      recommendations: []
    };

    // AI 기반 개인화 추천 생성
    insights.recommendations = await this.generatePersonalizedRecommendations(
      userId,
      insights,
      stats
    );

    return insights;
  }

  private determinePersonalityType(stats: any): string {
    const { categoryDistribution, explorationMetrics, timePatterns } = stats;

    // 카테고리 다양성 지수
    const diversityScore = this.calculateDiversityScore(categoryDistribution);

    // 탐험성 지수
    const explorationScore = explorationMetrics.newPlacesRatio;

    // 시간 패턴 분석
    const isEveningPerson = timePatterns.preferredHours.some(h => h >= 18);
    const isWeekendPerson = timePatterns.preferredDays.includes('weekend');

    // 성향 분류 로직
    if (diversityScore > 0.7 && explorationScore > 0.6) {
      return isEveningPerson ? '모험가형 탐험가' : '활발한 탐험가';
    } else if (diversityScore < 0.4 && explorationScore < 0.3) {
      return isWeekendPerson ? '안정 추구형' : '루틴 선호형';
    } else {
      return '균형잡힌 탐험가';
    }
  }

  async generateMonthlyReport(userId: string): Promise<MonthlyReport> {
    const lastMonth = new Date();
    lastMonth.setMonth(lastMonth.getMonth() - 1);

    const stats = await this.getUserStats(userId, 'month');
    const profile = await this.getProfile(userId);

    return {
      userId,
      period: {
        start: new Date(lastMonth.getFullYear(), lastMonth.getMonth(), 1),
        end: new Date(lastMonth.getFullYear(), lastMonth.getMonth() + 1, 0)
      },
      highlights: this.generateHighlights(stats),
      achievements: await this.checkAchievements(userId, stats),
      recommendations: await this.generateMonthlyRecommendations(userId, stats),
      trends: this.analyzeMonthlyTrends(userId, stats),
      generatedAt: new Date()
    };
  }
}
```

### 5-2. 개인화 추천 엔진
```typescript
// personalization-engine.ts
class PersonalizationEngine {
  constructor(
    private analyticsService: UserAnalyticsService,
    private mlService: MachineLearningService
  ) {}

  async generatePersonalizedRecommendations(
    userId: string,
    userProfile: UserProfile,
    userStats: UserStats
  ): Promise<PersonalizedRecommendations> {
    // 1. 사용자 벡터 생성
    const userVector = await this.createUserVector(userProfile, userStats);

    // 2. 유사한 사용자 찾기
    const similarUsers = await this.findSimilarUsers(userId, userVector);

    // 3. 카테고리별 선호도 예측
    const categoryPreferences = await this.predictCategoryPreferences(
      userVector,
      similarUsers
    );

    // 4. 시간/지역 패턴 기반 추천
    const contextualRecommendations = await this.generateContextualRecommendations(
      userId,
      userStats.preferences.timePatterns
    );

    // 5. 최종 추천 생성
    return {
      places: await this.recommendPlaces(userId, categoryPreferences),
      courses: await this.recommendCourses(userId, contextualRecommendations),
      explorationGoals: this.generateExplorationGoals(userStats),
      personalizedTips: this.generatePersonalizedTips(userProfile, userStats)
    };
  }

  private async createUserVector(
    profile: UserProfile,
    stats: UserStats
  ): Promise<UserVector> {
    return {
      // 카테고리 선호도 (정규화)
      categoryPreferences: this.normalizePreferences(
        profile.preferences.recommendations.categoryRatings
      ),

      // 행동 패턴
      behaviorPattern: {
        explorationRate: stats.exploration.explorationScore / 100,
        socialActivity: stats.insights.socialScore / 100,
        activityLevel: Math.min(stats.summary.totalPlaces / 100, 1),
        consistency: this.calculateConsistencyScore(stats)
      },

      // 상황적 선호도
      contextualPreferences: {
        timeSlots: profile.preferences.dating.timeSlots,
        regions: profile.preferences.dating.region,
        budget: profile.preferences.dating.budget,
        transport: profile.preferences.dating.transport
      }
    };
  }

  private async findSimilarUsers(
    userId: string,
    userVector: UserVector
  ): Promise<string[]> {
    // 코사인 유사도 계산을 위한 벡터 DB 쿼리
    // 실제 구현에서는 벡터 데이터베이스(Pinecone, Weaviate 등) 사용 고려
    const query = `
      SELECT user_id, similarity_score
      FROM user_similarity_matrix
      WHERE target_user_id = ?
      ORDER BY similarity_score DESC
      LIMIT 20
    `;

    const results = await this.clickhouse.query(query, [userId]);
    return results.rows.map(row => row.user_id);
  }

  async updateUserPreferences(
    userId: string,
    feedback: UserFeedback
  ): Promise<void> {
    // 명시적 피드백 (좋아요/싫어요)
    if (feedback.type === 'explicit') {
      await this.updateExplicitPreferences(userId, feedback);
    }

    // 암묵적 피드백 (클릭, 체류시간 등)
    if (feedback.type === 'implicit') {
      await this.updateImplicitPreferences(userId, feedback);
    }

    // 선호도 모델 재학습 큐에 추가
    await this.scheduleModelRetraining(userId);
  }

  private generatePersonalizedTips(
    profile: UserProfile,
    stats: UserStats
  ): string[] {
    const tips: string[] = [];

    // 탐험성 기반 팁
    if (stats.insights.explorationScore < 30) {
      tips.push('새로운 지역도 탐험해보세요! 평소와 다른 분위기를 경험할 수 있어요.');
    }

    // 카테고리 편중 분석
    const topCategory = stats.preferences.topCategories[0];
    if (topCategory.percentage > 60) {
      tips.push(`${topCategory.category} 외에도 다양한 카테고리를 시도해보세요.`);
    }

    // 시간 패턴 분석
    if (stats.preferences.timePatterns.preferredDays.length <= 1) {
      tips.push('평일 데이트도 시도해보세요. 사람이 적어서 더 특별할 수 있어요.');
    }

    // 소셜 활동 분석
    if (stats.insights.socialScore < 20) {
      tips.push('코스를 친구들과 공유해보세요. 새로운 아이디어를 얻을 수 있어요.');
    }

    return tips.slice(0, 3); // 최대 3개 팁 반환
  }
}
```

## 6. 프라이버시 및 데이터 관리

### 6-1. 데이터 관리 서비스
```typescript
// data-management-service.ts
class DataManagementService {
  constructor(
    private postgresql: Pool,
    private clickhouse: ClickHouseClient,
    private s3Client: S3Client,
    private encryptionService: EncryptionService
  ) {}

  async exportUserData(
    userId: string,
    options: ExportOptions
  ): Promise<ExportResult> {
    const exportId = this.generateExportId();

    try {
      // 1. 내보낼 데이터 수집
      const userData = await this.collectUserData(userId, options);

      // 2. 데이터 포맷팅
      const formattedData = await this.formatExportData(userData, options.format);

      // 3. 암호화 (옵션)
      const encryptedData = options.encrypt
        ? await this.encryptionService.encrypt(formattedData)
        : formattedData;

      // 4. S3에 업로드
      const fileName = `user-data-export-${userId}-${Date.now()}.${options.format}`;
      const uploadResult = await this.s3Client.upload({
        Bucket: process.env.DATA_EXPORT_BUCKET,
        Key: fileName,
        Body: encryptedData,
        ServerSideEncryption: 'AES256',
        Metadata: {
          userId,
          exportId,
          createdAt: new Date().toISOString()
        }
      }).promise();

      // 5. 다운로드 링크 생성 (24시간 유효)
      const downloadUrl = await this.s3Client.getSignedUrl('getObject', {
        Bucket: process.env.DATA_EXPORT_BUCKET,
        Key: fileName,
        Expires: 24 * 60 * 60 // 24시간
      });

      // 6. 내보내기 기록 저장
      await this.postgresql.query(`
        INSERT INTO data_exports (
          export_id, user_id, status, download_url,
          file_size, format, expires_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
      `, [
        exportId,
        userId,
        'completed',
        downloadUrl,
        Buffer.byteLength(encryptedData),
        options.format,
        new Date(Date.now() + 24 * 60 * 60 * 1000)
      ]);

      // 7. 사용자에게 이메일 알림
      await this.sendExportNotification(userId, {
        exportId,
        downloadUrl,
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000)
      });

      return {
        exportId,
        status: 'completed',
        downloadUrl,
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000)
      };

    } catch (error) {
      console.error('Data export failed:', error);

      // 실패 기록
      await this.postgresql.query(`
        INSERT INTO data_exports (export_id, user_id, status, error)
        VALUES ($1, $2, $3, $4)
      `, [exportId, userId, 'failed', error.message]);

      throw new DataExportError('Failed to export user data');
    }
  }

  async deleteUserData(
    userId: string,
    dataTypes: string[],
    confirmationCode: string
  ): Promise<DeletionResult> {
    // 1. 확인 코드 검증
    await this.verifyConfirmationCode(userId, confirmationCode);

    const deletionResults: DeletionResult = {
      success: true,
      deletedItems: [],
      errors: []
    };

    try {
      for (const dataType of dataTypes) {
        switch (dataType) {
          case 'profile':
            await this.deleteProfileData(userId);
            deletionResults.deletedItems.push('profile');
            break;

          case 'activity':
            await this.deleteActivityData(userId);
            deletionResults.deletedItems.push('activity');
            break;

          case 'analytics':
            await this.deleteAnalyticsData(userId);
            deletionResults.deletedItems.push('analytics');
            break;

          case 'all':
            await this.deleteAllUserData(userId);
            deletionResults.deletedItems.push('all');
            break;
        }
      }

      // 삭제 기록
      await this.logDataDeletion(userId, dataTypes);

    } catch (error) {
      deletionResults.success = false;
      deletionResults.errors.push(error.message);
    }

    return deletionResults;
  }

  async scheduleAccountDeletion(
    userId: string,
    deleteAfterDays: number,
    reason?: string
  ): Promise<void> {
    const deletionDate = new Date();
    deletionDate.setDate(deletionDate.getDate() + deleteAfterDays);

    // 삭제 스케줄 저장
    await this.postgresql.query(`
      INSERT INTO scheduled_deletions (
        user_id, scheduled_at, execution_date, reason, status
      ) VALUES ($1, NOW(), $2, $3, 'scheduled')
    `, [userId, deletionDate, reason]);

    // 계정 일시 비활성화
    await this.deactivateAccount(userId);

    // 복구 기간 동안의 알림 스케줄링
    await this.scheduleReminderNotifications(userId, deleteAfterDays);
  }

  async restoreAccount(userId: string): Promise<void> {
    // 1. 스케줄된 삭제 취소
    await this.postgresql.query(`
      UPDATE scheduled_deletions
      SET status = 'cancelled', cancelled_at = NOW()
      WHERE user_id = $1 AND status = 'scheduled'
    `, [userId]);

    // 2. 계정 재활성화
    await this.reactivateAccount(userId);

    // 3. 알림 스케줄 취소
    await this.cancelReminderNotifications(userId);
  }

  private async collectUserData(
    userId: string,
    options: ExportOptions
  ): Promise<UserExportData> {
    const data: UserExportData = {};

    if (options.includeProfile) {
      const profileResult = await this.postgresql.query(
        'SELECT * FROM user_profiles WHERE user_id = $1',
        [userId]
      );
      data.profile = profileResult.rows[0];
    }

    if (options.includeActivity) {
      const [placesResult, coursesResult] = await Promise.all([
        this.postgresql.query('SELECT * FROM places WHERE user_id = $1', [userId]),
        this.postgresql.query('SELECT * FROM courses WHERE user_id = $1', [userId])
      ]);
      data.places = placesResult.rows;
      data.courses = coursesResult.rows;
    }

    if (options.includeAnalytics) {
      const analyticsQuery = `
        SELECT *
        FROM user_behavior_events
        WHERE user_id = ?
        ORDER BY timestamp DESC
      `;

      const analyticsResult = await this.clickhouse.query(analyticsQuery, [userId]);
      data.analytics = analyticsResult.rows;
    }

    return data;
  }

  private async deleteAllUserData(userId: string): Promise<void> {
    await Promise.all([
      // PostgreSQL 데이터 삭제
      this.postgresql.query('DELETE FROM user_profiles WHERE user_id = $1', [userId]),
      this.postgresql.query('DELETE FROM places WHERE user_id = $1', [userId]),
      this.postgresql.query('DELETE FROM courses WHERE user_id = $1', [userId]),
      this.postgresql.query('DELETE FROM user_sessions WHERE user_id = $1', [userId]),

      // ClickHouse 데이터 삭제
      this.clickhouse.query('DELETE FROM user_behavior_events WHERE user_id = ?', [userId]),
      this.clickhouse.query('DELETE FROM user_activity_stats WHERE user_id = ?', [userId]),

      // Redis 캐시 삭제
      this.redis.del(`profile:${userId}`),
      this.redis.del(`settings:${userId}`),
      this.redis.keys(`user_stats:${userId}:*`).then(keys => {
        if (keys.length > 0) return this.redis.del(...keys);
      }),

      // S3 파일 삭제 (프로필 이미지 등)
      this.deleteUserFiles(userId)
    ]);
  }
}
```

### 6-2. GDPR 준수 관리
```typescript
// gdpr-compliance-service.ts
class GDPRComplianceService {
  constructor(
    private dataManagement: DataManagementService,
    private auditLogger: AuditLogger,
    private notificationService: NotificationService
  ) {}

  async handleDataSubjectRequest(
    userId: string,
    requestType: 'access' | 'rectification' | 'erasure' | 'portability',
    details?: any
  ): Promise<DSRResult> {
    // 요청 기록
    await this.auditLogger.log({
      type: 'gdpr_request',
      userId,
      requestType,
      details,
      timestamp: new Date()
    });

    switch (requestType) {
      case 'access':
        return await this.handleAccessRequest(userId);

      case 'rectification':
        return await this.handleRectificationRequest(userId, details);

      case 'erasure':
        return await this.handleErasureRequest(userId);

      case 'portability':
        return await this.handlePortabilityRequest(userId, details);

      default:
        throw new Error('Unsupported request type');
    }
  }

  private async handleAccessRequest(userId: string): Promise<DSRResult> {
    // 사용자가 접근할 수 있는 모든 개인 데이터 수집
    const personalData = await this.collectAllPersonalData(userId);

    // 데이터 처리 목적과 법적 근거 포함
    const dataReport = {
      personalData,
      processingPurposes: await this.getProcessingPurposes(userId),
      legalBasis: await this.getLegalBasis(userId),
      dataRetentionPeriods: await this.getRetentionPeriods(),
      thirdPartySharing: await this.getThirdPartySharing(userId)
    };

    // 사용자에게 보고서 전송
    await this.sendDataAccessReport(userId, dataReport);

    return {
      status: 'completed',
      message: 'Personal data access report has been sent to your email',
      completedAt: new Date()
    };
  }

  private async handleErasureRequest(userId: string): Promise<DSRResult> {
    // 삭제 권리 적용 가능성 검토
    const erasureCheck = await this.checkErasureEligibility(userId);

    if (!erasureCheck.eligible) {
      return {
        status: 'rejected',
        message: erasureCheck.reason,
        completedAt: new Date()
      };
    }

    // 30일 유예 기간 설정
    await this.dataManagement.scheduleAccountDeletion(userId, 30, 'gdpr_erasure');

    // 사용자에게 확인 알림
    await this.notificationService.send(userId, {
      type: 'gdpr_erasure_scheduled',
      message: 'Your account will be deleted in 30 days. You can restore it anytime during this period.',
      actions: [{
        label: 'Restore Account',
        url: `/account/restore?token=${await this.generateRestoreToken(userId)}`
      }]
    });

    return {
      status: 'scheduled',
      message: 'Account deletion scheduled for 30 days. You can restore it anytime during this period.',
      completedAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
    };
  }

  async checkConsentStatus(userId: string): Promise<ConsentStatus> {
    const result = await this.postgresql.query(`
      SELECT privacy_settings, dating_preferences, updated_at
      FROM user_profiles
      WHERE user_id = $1
    `, [userId]);

    if (result.rows.length === 0) {
      throw new Error('User profile not found');
    }

    const profile = result.rows[0];

    return {
      essential: true, // 서비스 운영에 필수
      analytics: profile.privacy_settings.analyticsOptIn,
      marketing: profile.privacy_settings.marketingOptIn,
      personalization: profile.dating_preferences !== null,
      lastUpdated: profile.updated_at
    };
  }

  async updateConsent(
    userId: string,
    consentType: string,
    granted: boolean
  ): Promise<void> {
    const updateField = this.getConsentField(consentType);

    const updateQuery = `
      UPDATE user_profiles
      SET privacy_settings = privacy_settings || $2,
          updated_at = NOW()
      WHERE user_id = $1
    `;

    await this.postgresql.query(updateQuery, [
      userId,
      JSON.stringify({ [this.getConsentField(consentType)]: granted })
    ]);

    // 동의 철회 시 관련 데이터 처리 중단
    if (!granted) {
      await this.handleConsentWithdrawal(userId, consentType);
    }

    // 동의 이력 기록
    await this.auditLogger.log({
      type: 'consent_update',
      userId,
      consentType,
      granted,
      timestamp: new Date()
    });
  }

  private async handleConsentWithdrawal(
    userId: string,
    consentType: string
  ): Promise<void> {
    switch (consentType) {
      case 'analytics':
        // 분석 데이터 수집 중단
        await this.stopAnalyticsCollection(userId);
        break;

      case 'marketing':
        // 마케팅 커뮤니케이션 중단
        await this.unsubscribeFromMarketing(userId);
        break;

      case 'personalization':
        // 개인화 데이터 삭제
        await this.clearPersonalizationData(userId);
        break;
    }
  }

  // 정기적인 컴플라이언스 감사
  async runComplianceAudit(): Promise<ComplianceReport> {
    const report: ComplianceReport = {
      auditDate: new Date(),
      findings: [],
      recommendations: []
    };

    // 1. 데이터 보존 정책 준수 확인
    const retentionViolations = await this.checkRetentionCompliance();
    if (retentionViolations.length > 0) {
      report.findings.push({
        type: 'data_retention',
        severity: 'high',
        count: retentionViolations.length,
        description: 'Data retention period exceeded'
      });
    }

    // 2. 동의 기록 완정성 확인
    const consentGaps = await this.checkConsentRecords();
    if (consentGaps.length > 0) {
      report.findings.push({
        type: 'consent_records',
        severity: 'medium',
        count: consentGaps.length,
        description: 'Missing or incomplete consent records'
      });
    }

    // 3. 데이터 주체 요청 처리 현황
    const pendingRequests = await this.getPendingDSRs();
    if (pendingRequests.length > 0) {
      report.findings.push({
        type: 'pending_dsr',
        severity: 'high',
        count: pendingRequests.length,
        description: 'Pending data subject requests'
      });
    }

    return report;
  }
}
```

## 7. 성능 최적화

### 7-1. 캐싱 전략
```typescript
// profile-cache-manager.ts
class ProfileCacheManager {
  constructor(
    private redis: Redis,
    private eventBus: EventBus
  ) {
    this.setupCacheInvalidation();
  }

  async getProfile(userId: string): Promise<UserProfile | null> {
    // L1: Redis 캐시
    const cached = await this.redis.get(`profile:${userId}`);
    if (cached) {
      return JSON.parse(cached);
    }

    return null;
  }

  async setProfile(userId: string, profile: UserProfile): Promise<void> {
    const ttl = this.calculateTTL(profile);

    await Promise.all([
      // 전체 프로필 캐시
      this.redis.setex(
        `profile:${userId}`,
        ttl,
        JSON.stringify(profile)
      ),

      // 자주 접근하는 필드들 별도 캐시
      this.redis.hset(`profile_quick:${userId}`, {
        displayName: profile.profile.displayName,
        photoURL: profile.profile.photoURL || '',
        lastActiveAt: profile.profile.lastActiveAt.toISOString()
      }),

      // 설정만 별도 캐시 (더 자주 변경됨)
      this.redis.setex(
        `settings:${userId}`,
        1800, // 30분
        JSON.stringify({
          preferences: profile.preferences,
          notifications: profile.notificationSettings,
          privacy: profile.privacySettings
        })
      )
    ]);
  }

  async invalidateProfile(userId: string): Promise<void> {
    const keys = [
      `profile:${userId}`,
      `profile_quick:${userId}`,
      `settings:${userId}`,
      `user_stats:${userId}:*`
    ];

    // 패턴 매칭 키들 찾기
    const patternKeys = await this.redis.keys(`user_stats:${userId}:*`);
    keys.push(...patternKeys);

    if (keys.length > 0) {
      await this.redis.del(...keys);
    }

    // 다른 서비스에 무효화 알림
    await this.eventBus.publish('profile_cache_invalidated', { userId });
  }

  private calculateTTL(profile: UserProfile): number {
    // 최근 활동 기반 TTL 계산
    const lastActive = new Date(profile.profile.lastActiveAt);
    const daysSinceActive = (Date.now() - lastActive.getTime()) / (1000 * 60 * 60 * 24);

    if (daysSinceActive < 1) return 3600;      // 1시간 (활성 사용자)
    if (daysSinceActive < 7) return 7200;      // 2시간 (최근 활성)
    if (daysSinceActive < 30) return 14400;    // 4시간 (보통)
    return 86400;                              // 24시간 (비활성)
  }

  private setupCacheInvalidation(): void {
    this.eventBus.subscribe('profile_updated', async (data) => {
      await this.invalidateProfile(data.userId);
    });

    this.eventBus.subscribe('settings_updated', async (data) => {
      await this.redis.del(`settings:${data.userId}`);
    });
  }

  // 배치로 여러 프로필 조회 (N+1 문제 해결)
  async getMultipleProfiles(userIds: string[]): Promise<Map<string, UserProfile>> {
    const pipeline = this.redis.pipeline();

    userIds.forEach(userId => {
      pipeline.get(`profile:${userId}`);
    });

    const results = await pipeline.exec();
    const profiles = new Map<string, UserProfile>();

    results?.forEach((result, index) => {
      if (result[1]) { // result[0]은 에러, result[1]은 값
        const profile = JSON.parse(result[1] as string);
        profiles.set(userIds[index], profile);
      }
    });

    return profiles;
  }
}
```

### 7-2. 데이터베이스 최적화
```typescript
// database-optimization.ts
class DatabaseOptimizer {
  async createIndexes(): Promise<void> {
    // 복합 인덱스는 이미 테이블 생성 시 정의됨

    // 추가 최적화 인덱스들
    const additionalIndexes = [
      `CREATE INDEX CONCURRENTLY idx_user_profiles_region_activity
       ON user_profiles USING gin((dating_preferences->'region'), last_active_at DESC);`,

      `CREATE INDEX CONCURRENTLY idx_user_profiles_visibility_activity
       ON user_profiles((privacy_settings->>'profileVisibility'), last_active_at DESC);`,

      `CREATE INDEX CONCURRENTLY idx_setting_logs_user_timestamp
       ON setting_change_logs(user_id, timestamp DESC);`
    ];

    for (const indexQuery of additionalIndexes) {
      try {
        await this.postgresql.query(indexQuery);
      } catch (error) {
        console.warn('Index creation failed (may already exist):', error.message);
      }
    }

    // 자동 삭제를 위한 파티션 설정 (PostgreSQL 11+)
    await this.postgresql.query(`
      SELECT cron.schedule('cleanup-old-logs', '0 2 * * *',
        'DELETE FROM setting_change_logs WHERE timestamp < NOW() - INTERVAL ''90 days'''
      );
    `);
  }

  async optimizeQueries(): Promise<void> {
    // 자주 사용되는 쿼리들을 위한 Aggregation Pipeline 최적화

    // 사용자 통계 집계를 위한 최적화된 뷰
    const createUserStatsView = `
      CREATE MATERIALIZED VIEW user_stats_view AS
      SELECT
        up.user_id,
        up.display_name,
        up.last_active_at,
        COUNT(DISTINCT p.id) as places_count,
        COUNT(DISTINCT c.id) as courses_count,
        COUNT(DISTINCT s.id) as shares_count
      FROM user_profiles up
      LEFT JOIN places p ON up.user_id = p.user_id
      LEFT JOIN courses c ON up.user_id = c.user_id
      LEFT JOIN shares s ON up.user_id = s.user_id
      GROUP BY up.user_id, up.display_name, up.last_active_at;
    `;

    // 인덱스와 함께 뷰 생성
    await this.postgresql.query(createUserStatsView);
    await this.postgresql.query('CREATE INDEX idx_user_stats_view_user_id ON user_stats_view(user_id);');
  }

  // 파티셔닝 전략 (시간별 데이터 분할)
  async implementPartitioning(): Promise<void> {
    // ClickHouse에서 월별 파티셔닝
    const partitionQuery = `
      CREATE TABLE user_behavior_events_partitioned (
        user_id String,
        event_type String,
        event_data String,
        timestamp DateTime,
        session_id String
      ) ENGINE = MergeTree()
      PARTITION BY toYYYYMM(timestamp)
      ORDER BY (user_id, timestamp)
      SETTINGS index_granularity = 8192
    `;

    await this.clickhouse.query(partitionQuery);
  }

  // 읽기 전용 복제본 사용
  setupReadReplicas(): void {
    // 읽기 전용 쿼리는 복제본으로 라우팅
    const readOnlyQueries = [
      'getUserStats',
      'getProfile',
      'getActivityTimeline'
    ];

    readOnlyQueries.forEach(queryName => {
      this.routeToReadReplica(queryName);
    });
  }
}
```

## 8. 모니터링 및 알림

### 8-1. 성능 모니터링
```typescript
// monitoring-service.ts
class ProfileMonitoringService {
  private metrics = {
    profileUpdates: 0,
    cacheHits: 0,
    cacheMisses: 0,
    dbQueries: 0,
    avgResponseTime: 0
  };

  constructor(
    private prometheus: PrometheusService,
    private alertManager: AlertManager
  ) {
    this.setupMetrics();
  }

  private setupMetrics(): void {
    // Prometheus 메트릭 정의
    const profileUpdateCounter = new this.prometheus.Counter({
      name: 'profile_updates_total',
      help: 'Total number of profile updates',
      labelNames: ['user_id', 'field_type']
    });

    const cacheHitRatio = new this.prometheus.Histogram({
      name: 'profile_cache_hit_ratio',
      help: 'Cache hit ratio for profile requests',
      buckets: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    });

    const responseTimeHistogram = new this.prometheus.Histogram({
      name: 'profile_request_duration_seconds',
      help: 'Duration of profile requests in seconds',
      labelNames: ['method', 'status_code'],
      buckets: [0.1, 0.5, 1, 2, 5, 10]
    });
  }

  async recordMetric(
    metricName: string,
    value: number,
    labels?: Record<string, string>
  ): Promise<void> {
    switch (metricName) {
      case 'profile_update':
        this.metrics.profileUpdates++;
        break;
      case 'cache_hit':
        this.metrics.cacheHits++;
        break;
      case 'cache_miss':
        this.metrics.cacheMisses++;
        break;
    }

    // 알람 규칙 확인
    await this.checkAlarmRules(metricName, value);
  }

  private async checkAlarmRules(metric: string, value: number): Promise<void> {
    const rules = {
      cache_hit_ratio: { threshold: 0.8, operator: 'lt' },
      response_time: { threshold: 2000, operator: 'gt' },
      error_rate: { threshold: 0.05, operator: 'gt' }
    };

    const rule = rules[metric];
    if (!rule) return;

    const shouldAlert = rule.operator === 'gt'
      ? value > rule.threshold
      : value < rule.threshold;

    if (shouldAlert) {
      await this.sendAlert({
        metric,
        value,
        threshold: rule.threshold,
        severity: 'warning',
        message: `${metric} threshold exceeded: ${value}`
      });
    }
  }

  async generateHealthReport(): Promise<HealthReport> {
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);

    return {
      timestamp: now,
      services: {
        database: await this.checkDatabaseHealth(),
        cache: await this.checkCacheHealth(),
        storage: await this.checkStorageHealth()
      },
      metrics: {
        ...this.metrics,
        cacheHitRatio: this.metrics.cacheHits / (this.metrics.cacheHits + this.metrics.cacheMisses)
      },
      alerts: await this.getActiveAlerts()
    };
  }

  private async checkDatabaseHealth(): Promise<ServiceHealth> {
    try {
      const start = Date.now();
      await this.postgresql.query('SELECT 1');
      const responseTime = Date.now() - start;

      return {
        status: responseTime < 100 ? 'healthy' : 'degraded',
        responseTime,
        lastCheck: new Date()
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error.message,
        lastCheck: new Date()
      };
    }
  }
}
```

## 9. 배포 및 확장성

### 9-1. 마이크로서비스 분할
```yaml
# docker-compose.yml
version: '3.8'

services:
  profile-service:
    build: ./services/profile
    environment:
      - NODE_ENV=production
      - POSTGRESQL_URI=${POSTGRESQL_URI}
      - REDIS_URI=${REDIS_URI}
    ports:
      - "3001:3000"
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

  settings-service:
    build: ./services/settings
    environment:
      - NODE_ENV=production
      - POSTGRESQL_URI=${POSTGRESQL_URI}
      - REDIS_URI=${REDIS_URI}
    ports:
      - "3002:3000"
    deploy:
      replicas: 2

  analytics-service:
    build: ./services/analytics
    environment:
      - NODE_ENV=production
      - CLICKHOUSE_URI=${CLICKHOUSE_URI}
      - REDIS_URI=${REDIS_URI}
    ports:
      - "3003:3000"
    deploy:
      replicas: 2

  nginx-gateway:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - profile-service
      - settings-service
      - analytics-service
```

### 9-2. Kubernetes 배포
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: profile-service
  labels:
    app: profile-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: profile-service
  template:
    metadata:
      labels:
        app: profile-service
    spec:
      containers:
      - name: profile-service
        image: hotly/profile-service:latest
        ports:
        - containerPort: 3000
        env:
        - name: POSTGRESQL_URI
          valueFrom:
            secretKeyRef:
              name: database-secrets
              key: postgresql-uri
        - name: REDIS_URI
          valueFrom:
            secretKeyRef:
              name: cache-secrets
              key: redis-uri
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: profile-service
spec:
  selector:
    app: profile-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: profile-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: profile-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

이제 사용자 프로필 및 설정 관리 시스템의 TRD 작성이 완료되었습니다. 마지막 TRD 문서인 캐시 및 성능 최적화를 작성하겠습니다.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Create 01-sns-link-analysis.md TRD", "status": "completed", "priority": "high", "id": "1"}, {"content": "Create 02-place-management.md TRD", "status": "completed", "priority": "high", "id": "2"}, {"content": "Create 03-course-recommendation.md TRD", "status": "completed", "priority": "high", "id": "3"}, {"content": "Create 04-map-visualization.md TRD", "status": "completed", "priority": "high", "id": "4"}, {"content": "Create 05-sharing-system.md TRD", "status": "completed", "priority": "high", "id": "5"}, {"content": "Create 06-onboarding-flow.md TRD", "status": "completed", "priority": "medium", "id": "6"}, {"content": "Create 07-notification-system.md TRD", "status": "completed", "priority": "medium", "id": "7"}, {"content": "Create 08-search-filter.md TRD", "status": "completed", "priority": "medium", "id": "8"}, {"content": "Create 09-authentication.md TRD", "status": "completed", "priority": "medium", "id": "9"}, {"content": "Create 10-user-profile.md TRD", "status": "completed", "priority": "medium", "id": "10"}, {"content": "Create 11-cache-performance.md TRD", "status": "in_progress", "priority": "medium", "id": "11"}]
