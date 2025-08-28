# TRD: 알림 및 리마인더 시스템

## 1. 기술 개요
**목적:** PRD 07-notification-system 요구사항을 충족하기 위한 지능형 알림 시스템의 기술적 구현 방안

**핵심 기술 스택:**
- 푸시 알림: Firebase Cloud Messaging (FCM) + Apple Push Notification Service (APNS)
- 스케줄링: Redis + Bull Queue + Cron Jobs
- 실시간 데이터: WebSocket + Server-Sent Events
- 알림 최적화: 머신러닝 기반 개인화 엔진
- 외부 데이터: Weather API + Transit API + Business Hours Scraping

---

## 2. 시스템 아키텍처

### 2-1. 전체 아키텍처
```
[Mobile Apps] ←→ [FCM/APNS]
      ↓              ↑
[Notification Gateway] ←→ [Notification Scheduler]
      ↓                        ↑
[Message Composer] ←→ [Template Engine]
      ↓                        ↑
[Context Collector] ←→ [External Data Sources]
      ↓                        ↑
[User Preferences] ←→ [Analytics & ML Engine]
      ↓
[MongoDB + Redis]
```

### 2-2. 마이크로서비스 구성
```
1. Notification Orchestrator
   - 알림 생성 및 전송 총괄
   - 사용자 설정 및 조용시간 관리
   - 중복 방지 및 우선순위 처리

2. Scheduling Service
   - 알림 스케줄링 및 큐 관리
   - 크론 작업 관리
   - 재시도 로직

3. Context Service
   - 외부 데이터 수집 (날씨, 교통, 영업시간)
   - 실시간 모니터링
   - 데이터 캐싱

4. Personalization Engine
   - 사용자 행동 분석
   - 알림 최적화
   - A/B 테스트
```

---

## 3. 알림 엔진 구현

### 3-1. 알림 오케스트레이터
```python
class NotificationOrchestrator:
    def __init__(self):
        self.fcm_client = FCMClient()
        self.apns_client = APNSClient()
        self.template_engine = NotificationTemplateEngine()
        self.context_collector = ContextCollector()
        self.scheduler = NotificationScheduler()
        self.user_preferences = UserPreferencesService()
        
    async def create_course_reminder(self, course: Course, user_id: str) -> List[ScheduledNotification]:
        """코스 기반 알림 생성"""
        
        user_settings = await self.user_preferences.get_settings(user_id)
        if not user_settings.enabled:
            return []
        
        notifications = []
        
        # 1. 사전 준비 알림 (데이트 전날)
        if user_settings.types.date_reminder:
            prep_notification = await self._create_preparation_notification(
                course, user_settings
            )
            notifications.append(prep_notification)
        
        # 2. 출발 시간 알림
        if user_settings.types.departure_time:
            departure_notification = await self._create_departure_notification(
                course, user_settings
            )
            notifications.append(departure_notification)
        
        # 3. 이동 알림들 (각 장소 간)
        for i in range(len(course.places) - 1):
            move_notification = await self._create_move_notification(
                course.places[i], course.places[i + 1], user_settings
            )
            notifications.append(move_notification)
        
        # 스케줄링
        for notification in notifications:
            await self.scheduler.schedule_notification(notification)
        
        return notifications
    
    async def _create_preparation_notification(
        self, 
        course: Course, 
        settings: NotificationSettings
    ) -> ScheduledNotification:
        """사전 준비 알림 생성"""
        
        # 컨텍스트 정보 수집
        context = await self.context_collector.collect_course_context(course)
        
        # 준비사항 분석
        preparation_items = await self._analyze_preparation_needs(course, context)
        
        # 메시지 생성
        message = await self.template_engine.render_template(
            'preparation_reminder',
            {
                'course': course,
                'context': context,
                'preparation_items': preparation_items,
                'user_preferences': settings
            }
        )
        
        # 발송 시간 계산 (데이트 전날 설정 시간)
        course_date = course.scheduled_date
        send_time = course_date.replace(
            hour=settings.timing.day_before_hour,
            minute=0,
            second=0
        ) - timedelta(days=1)
        
        return ScheduledNotification(
            user_id=course.user_id,
            type=NotificationType.PREPARATION_REMINDER,
            priority=NotificationPriority.NORMAL,
            scheduled_time=send_time,
            message=message,
            course_id=course.id,
            deep_link=f"hotly://course/{course.id}"
        )
    
    async def _create_departure_notification(
        self, 
        course: Course, 
        settings: NotificationSettings
    ) -> ScheduledNotification:
        """출발 시간 알림 생성"""
        
        first_place = course.places[0]
        
        # 현재 위치에서 첫 장소까지의 이동 시간 계산
        travel_time = await self._calculate_travel_time(
            from_location=None,  # 현재 위치는 발송 시점에 계산
            to_location=first_place.location,
            transport_method=course.transport_method,
            departure_time=first_place.arrival_time
        )
        
        # 출발 시간 계산
        departure_time = first_place.arrival_time - timedelta(minutes=travel_time)
        
        # 알림 발송 시간 (출발 시간 N분 전)
        notification_time = departure_time - timedelta(
            minutes=settings.timing.departure_minutes_before
        )
        
        # 실시간 교통 정보 수집
        traffic_context = await self.context_collector.get_traffic_info(
            destination=first_place.location,
            planned_departure=departure_time
        )
        
        message = await self.template_engine.render_template(
            'departure_reminder',
            {
                'course': course,
                'departure_time': departure_time,
                'travel_time': travel_time,
                'traffic_context': traffic_context,
                'first_place': first_place
            }
        )
        
        return ScheduledNotification(
            user_id=course.user_id,
            type=NotificationType.DEPARTURE_REMINDER,
            priority=NotificationPriority.IMPORTANT,
            scheduled_time=notification_time,
            message=message,
            course_id=course.id,
            deep_link=f"hotly://navigation/{first_place.id}",
            actions=[
                NotificationAction(
                    id="show_route",
                    title="경로 보기",
                    deep_link=f"hotly://route/{course.id}"
                ),
                NotificationAction(
                    id="snooze_10min",
                    title="10분 뒤",
                    action_type="snooze"
                )
            ]
        )
    
    async def _analyze_preparation_needs(
        self, 
        course: Course, 
        context: CourseContext
    ) -> List[PreparationItem]:
        """준비사항 분석"""
        
        items = []
        
        for place in course.places:
            # 예약 필요성 체크
            if await self._needs_reservation(place):
                items.append(PreparationItem(
                    type="reservation",
                    place_name=place.name,
                    description=f"{place.name} 예약 권장 (대기시간: {context.wait_times.get(place.id, 'N/A')}분)",
                    priority="high",
                    action_link=place.reservation_url
                ))
            
            # 특별 준비사항 체크
            special_requirements = await self._get_special_requirements(place, context)
            items.extend(special_requirements)
        
        # 날씨 관련 준비사항
        if context.weather.requires_umbrella:
            items.append(PreparationItem(
                type="weather",
                description="우천 예보, 우산 준비 필요",
                priority="medium"
            ))
        
        if context.weather.temperature < 5:
            items.append(PreparationItem(
                type="weather", 
                description="추위 주의, 따뜻한 옷 준비",
                priority="medium"
            ))
        
        return items
    
    async def send_notification(self, notification: ScheduledNotification):
        """알림 전송 실행"""
        
        # 사용자 설정 재확인
        user_settings = await self.user_preferences.get_settings(notification.user_id)
        if not user_settings.enabled:
            return
        
        # 조용시간 체크
        if notification.priority != NotificationPriority.URGENT:
            if self._is_quiet_time(user_settings.quiet_hours):
                # 다음 활성 시간으로 연기
                await self._reschedule_after_quiet_time(notification, user_settings)
                return
        
        # 중복 체크
        if await self._is_duplicate_notification(notification):
            return
        
        # 디바이스 토큰 조회
        device_tokens = await self._get_user_device_tokens(notification.user_id)
        
        # 플랫폼별 전송
        send_tasks = []
        for token in device_tokens:
            if token.platform == 'ios':
                send_tasks.append(self._send_apns(token, notification))
            else:  # android
                send_tasks.append(self._send_fcm(token, notification))
        
        results = await asyncio.gather(*send_tasks, return_exceptions=True)
        
        # 전송 결과 로깅
        await self._log_notification_results(notification, results)
        
        # 사용자 반응 추적 준비
        await self._setup_tracking(notification)
```

### 3-2. 스케줄링 서비스
```python
class NotificationScheduler:
    def __init__(self):
        self.redis = Redis.from_url(settings.REDIS_URL)
        self.queue = Queue('notifications', connection=self.redis)
    
    async def schedule_notification(self, notification: ScheduledNotification):
        """알림 스케줄링"""
        
        # 즉시 발송인 경우
        if notification.scheduled_time <= datetime.utcnow():
            await self.queue.enqueue(
                'send_notification',
                notification.dict()
            )
            return
        
        # 미래 시점 스케줄링
        delay = (notification.scheduled_time - datetime.utcnow()).total_seconds()
        
        await self.queue.enqueue_in(
            delay,
            'send_notification',
            notification.dict(),
            job_id=f"notification_{notification.id}",
            retry=Retry(max=3, interval=[60, 300, 900])  # 1분, 5분, 15분 간격 재시도
        )
        
        # 스케줄 기록
        await self._save_schedule_record(notification)
    
    async def cancel_notification(self, notification_id: str):
        """예약된 알림 취소"""
        
        job_id = f"notification_{notification_id}"
        
        # 큐에서 제거
        job = await self.queue.fetch_job(job_id)
        if job:
            await job.cancel()
        
        # 스케줄 기록 삭제
        await self.redis.delete(f"scheduled:{notification_id}")
    
    async def reschedule_notification(
        self, 
        notification_id: str, 
        new_time: datetime
    ):
        """알림 재스케줄링"""
        
        # 기존 스케줄 취소
        await self.cancel_notification(notification_id)
        
        # 새로운 시간으로 다시 스케줄링
        notification = await self._get_notification(notification_id)
        notification.scheduled_time = new_time
        
        await self.schedule_notification(notification)
    
    async def setup_recurring_jobs(self):
        """주기적 작업 설정"""
        
        # 실시간 정보 모니터링 (1시간마다)
        await self.queue.enqueue_periodic(
            crontab('0 * * * *'),  # 매시 정각
            'monitor_realtime_changes'
        )
        
        # 날씨 정보 업데이트 (6시간마다)
        await self.queue.enqueue_periodic(
            crontab('0 */6 * * *'),  # 6시간마다
            'update_weather_data'
        )
        
        # 교통 정보 업데이트 (1시간마다, 출퇴근 시간에는 30분마다)
        await self.queue.enqueue_periodic(
            crontab('*/30 7-9,17-19 * * 1-5'),  # 출퇴근 시간
            'update_traffic_data'
        )
        
        await self.queue.enqueue_periodic(
            crontab('0 * * * *'),  # 평시
            'update_traffic_data'
        )
        
        # 영업시간 정보 업데이트 (일 1회)
        await self.queue.enqueue_periodic(
            crontab('0 1 * * *'),  # 새벽 1시
            'update_business_hours'
        )
```

### 3-3. 컨텍스트 수집기
```python
class ContextCollector:
    def __init__(self):
        self.weather_service = WeatherService()
        self.traffic_service = TrafficService()
        self.business_hours_service = BusinessHoursService()
        self.cache = ContextCache()
    
    async def collect_course_context(self, course: Course) -> CourseContext:
        """코스 관련 컨텍스트 정보 수집"""
        
        # 병렬로 정보 수집
        weather_task = self.weather_service.get_forecast(
            course.places[0].location,
            course.scheduled_date
        )
        
        business_hours_tasks = [
            self.business_hours_service.get_hours(place.id, course.scheduled_date)
            for place in course.places
        ]
        
        wait_time_tasks = [
            self._get_expected_wait_time(place, course.scheduled_date)
            for place in course.places
        ]
        
        # 결과 수집
        weather = await weather_task
        business_hours_list = await asyncio.gather(*business_hours_tasks)
        wait_times_list = await asyncio.gather(*wait_time_tasks)
        
        # 정보 구조화
        business_hours = {
            place.id: hours 
            for place, hours in zip(course.places, business_hours_list)
        }
        
        wait_times = {
            place.id: wait_time
            for place, wait_time in zip(course.places, wait_times_list)
        }
        
        return CourseContext(
            weather=weather,
            business_hours=business_hours,
            wait_times=wait_times,
            collected_at=datetime.utcnow()
        )
    
    async def monitor_realtime_changes(self):
        """실시간 변동사항 모니터링"""
        
        # 오늘/내일 예정된 코스들 조회
        upcoming_courses = await self._get_upcoming_courses()
        
        for course in upcoming_courses:
            try:
                await self._check_course_changes(course)
            except Exception as e:
                logger.error(f"Failed to check course changes: {e}")
                continue
    
    async def _check_course_changes(self, course: Course):
        """개별 코스의 변동사항 체크"""
        
        # 이전 컨텍스트 조회
        previous_context = await self.cache.get_course_context(course.id)
        if not previous_context:
            return
        
        # 현재 컨텍스트 수집
        current_context = await self.collect_course_context(course)
        
        # 변동사항 감지
        changes = self._detect_changes(previous_context, current_context)
        
        if changes:
            # 긴급 알림 생성
            await self._create_change_notifications(course, changes)
            
            # 캐시 업데이트
            await self.cache.set_course_context(course.id, current_context)
    
    def _detect_changes(
        self, 
        previous: CourseContext, 
        current: CourseContext
    ) -> List[ContextChange]:
        """컨텍스트 변동사항 감지"""
        
        changes = []
        
        # 날씨 변화 체크
        if self._significant_weather_change(previous.weather, current.weather):
            changes.append(ContextChange(
                type="weather",
                severity="high" if current.weather.is_severe else "medium",
                description=f"날씨 변경: {current.weather.summary}",
                old_value=previous.weather.summary,
                new_value=current.weather.summary
            ))
        
        # 영업시간 변화 체크
        for place_id, current_hours in current.business_hours.items():
            previous_hours = previous.business_hours.get(place_id)
            
            if previous_hours and self._business_hours_changed(previous_hours, current_hours):
                changes.append(ContextChange(
                    type="business_hours",
                    severity="high",
                    place_id=place_id,
                    description=f"영업시간 변경",
                    old_value=str(previous_hours),
                    new_value=str(current_hours)
                ))
        
        # 대기시간 변화 체크 (큰 변동만)
        for place_id, current_wait in current.wait_times.items():
            previous_wait = previous.wait_times.get(place_id, 0)
            
            if abs(current_wait - previous_wait) > 30:  # 30분 이상 차이
                changes.append(ContextChange(
                    type="wait_time",
                    severity="medium",
                    place_id=place_id,
                    description=f"대기시간 변경: {previous_wait}분 → {current_wait}분"
                ))
        
        return changes
    
    async def _create_change_notifications(
        self, 
        course: Course, 
        changes: List[ContextChange]
    ):
        """변동사항 기반 긴급 알림 생성"""
        
        high_severity_changes = [c for c in changes if c.severity == "high"]
        
        if not high_severity_changes:
            return
        
        # 긴급 알림 메시지 생성
        message = await self.template_engine.render_template(
            'urgent_change_alert',
            {
                'course': course,
                'changes': high_severity_changes
            }
        )
        
        urgent_notification = ImmediateNotification(
            user_id=course.user_id,
            type=NotificationType.URGENT_CHANGE,
            priority=NotificationPriority.URGENT,
            message=message,
            course_id=course.id,
            changes=changes
        )
        
        # 즉시 발송
        await self.orchestrator.send_notification(urgent_notification)
```

---

## 4. 메시지 템플릿 엔진

### 4-1. 템플릿 시스템
```python
class NotificationTemplateEngine:
    def __init__(self):
        self.jinja_env = Environment(
            loader=FileSystemLoader('templates/notifications'),
            autoescape=True
        )
        self.personalization = PersonalizationEngine()
    
    async def render_template(
        self, 
        template_name: str, 
        context: Dict[str, Any]
    ) -> NotificationMessage:
        """템플릿 렌더링"""
        
        # 개인화 정보 추가
        personalized_context = await self._add_personalization(context)
        
        # 플랫폼별 템플릿 렌더링
        ios_template = self.jinja_env.get_template(f'{template_name}_ios.j2')
        android_template = self.jinja_env.get_template(f'{template_name}_android.j2')
        
        ios_content = ios_template.render(personalized_context)
        android_content = android_template.render(personalized_context)
        
        return NotificationMessage(
            ios=self._parse_ios_content(ios_content),
            android=self._parse_android_content(android_content),
            deep_link=personalized_context.get('deep_link'),
            actions=personalized_context.get('actions', [])
        )
    
    async def _add_personalization(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """개인화 정보 추가"""
        
        user_id = context.get('user_id')
        if not user_id:
            return context
        
        # 사용자 선호도 반영
        user_prefs = await self.personalization.get_user_preferences(user_id)
        
        # 시간대 조정
        if 'time' in context:
            context['time'] = self._adjust_timezone(context['time'], user_prefs.timezone)
        
        # 언어 설정
        context['language'] = user_prefs.language
        
        # 개인화된 인사말
        context['greeting'] = await self.personalization.get_personalized_greeting(
            user_id, datetime.now().hour
        )
        
        return context

# 템플릿 예시 (preparation_reminder_ios.j2)
"""
{% if weather.requires_umbrella %}🌧️{% elif weather.is_sunny %}☀️{% else %}☁️{% endif %} {{ greeting }}

내일 {{ course.scheduled_time.strftime('%H시') }} {{ course.places[0].address }} 데이트 준비!

{% for item in preparation_items %}
{% if item.priority == 'high' %}📍 {{ item.description }}{% else %}💡 {{ item.description }}{% endif %}
{% endfor %}

{% if weather.requires_umbrella %}☔ {{ weather.summary }}{% endif %}
"""

# 템플릿 예시 (departure_reminder_android.j2)
"""
{
  "title": "{{ departure_time.strftime('%H:%M') }}에 출발하세요! 🚇",
  "body": "📍 {{ first_place.name }}까지 {{ transport_method }} {{ travel_time }}분\n🚇 {{ traffic_context.status }}\n💡 도착 예상: {{ (departure_time + timedelta(minutes=travel_time)).strftime('%H:%M') }}",
  "icon": "departure_icon",
  "color": "#007AFF",
  "actions": [
    {
      "title": "경로보기",
      "action": "SHOW_ROUTE"
    },
    {
      "title": "10분 뒤",
      "action": "SNOOZE_10"
    }
  ]
}
"""
```

### 4-2. 개인화 엔진
```python
class PersonalizationEngine:
    def __init__(self):
        self.db = get_database()
        self.ml_model = NotificationPersonalizationModel()
    
    async def optimize_notification_timing(
        self, 
        user_id: str, 
        notification_type: str,
        default_time: datetime
    ) -> datetime:
        """개인화된 알림 시간 최적화"""
        
        # 사용자의 과거 알림 반응 패턴 분석
        user_behavior = await self._get_user_behavior_pattern(user_id)
        
        # ML 모델로 최적 시간 예측
        optimal_hour = await self.ml_model.predict_optimal_time(
            user_id=user_id,
            notification_type=notification_type,
            default_hour=default_time.hour,
            user_behavior=user_behavior
        )
        
        # 기본 시간에서 시간만 조정
        optimized_time = default_time.replace(hour=optimal_hour)
        
        return optimized_time
    
    async def get_notification_frequency_limit(self, user_id: str) -> int:
        """사용자별 알림 빈도 제한"""
        
        # 사용자의 알림 반응률 기반으로 빈도 조정
        engagement_rate = await self._calculate_engagement_rate(user_id)
        
        if engagement_rate > 0.7:
            return 10  # 고반응 사용자: 많은 알림 허용
        elif engagement_rate > 0.3:
            return 7   # 중반응 사용자: 보통 수준
        else:
            return 3   # 저반응 사용자: 필수 알림만
    
    async def should_send_notification(
        self, 
        user_id: str, 
        notification: ScheduledNotification
    ) -> bool:
        """개인화된 알림 발송 여부 결정"""
        
        # 최근 24시간 알림 발송 횟수 체크
        recent_count = await self._get_recent_notification_count(user_id, hours=24)
        frequency_limit = await self.get_notification_frequency_limit(user_id)
        
        if recent_count >= frequency_limit and notification.priority != NotificationPriority.URGENT:
            return False
        
        # 사용자 활동 패턴 기반 판단
        is_likely_to_engage = await self.ml_model.predict_engagement(
            user_id=user_id,
            notification=notification,
            current_time=datetime.utcnow()
        )
        
        return is_likely_to_engage > 0.3  # 30% 이상 반응할 것으로 예상되면 발송
    
    async def _get_user_behavior_pattern(self, user_id: str) -> Dict[str, Any]:
        """사용자 행동 패턴 분석"""
        
        # 과거 30일간의 알림 반응 데이터
        interactions = await self.db.notification_interactions.find({
            'user_id': user_id,
            'created_at': {'$gte': datetime.utcnow() - timedelta(days=30)}
        }).to_list(None)
        
        if not interactions:
            return {'pattern': 'new_user'}
        
        # 시간대별 반응률 계산
        hourly_engagement = {}
        for hour in range(24):
            hour_interactions = [
                i for i in interactions 
                if i['created_at'].hour == hour
            ]
            if hour_interactions:
                engagement_rate = sum(1 for i in hour_interactions if i['engaged']) / len(hour_interactions)
                hourly_engagement[hour] = engagement_rate
        
        # 요일별 반응률
        weekly_engagement = {}
        for weekday in range(7):
            weekday_interactions = [
                i for i in interactions
                if i['created_at'].weekday() == weekday
            ]
            if weekday_interactions:
                engagement_rate = sum(1 for i in weekday_interactions if i['engaged']) / len(weekday_interactions)
                weekly_engagement[weekday] = engagement_rate
        
        return {
            'hourly_engagement': hourly_engagement,
            'weekly_engagement': weekly_engagement,
            'total_interactions': len(interactions),
            'overall_engagement_rate': sum(1 for i in interactions if i['engaged']) / len(interactions)
        }
```

---

## 5. FCM/APNS 통합

### 5-1. FCM 클라이언트
```python
class FCMClient:
    def __init__(self):
        self.credentials = service_account.Credentials.from_service_account_file(
            settings.FCM_SERVICE_ACCOUNT_KEY
        )
        self.fcm = messaging.Client(credentials=self.credentials)
    
    async def send_notification(
        self, 
        device_token: str, 
        notification: NotificationMessage
    ) -> FCMResult:
        """FCM 알림 전송"""
        
        try:
            # FCM 메시지 구성
            message = messaging.Message(
                token=device_token,
                notification=messaging.Notification(
                    title=notification.android.title,
                    body=notification.android.body,
                    image=notification.android.image_url
                ),
                data={
                    'type': notification.type,
                    'course_id': notification.course_id,
                    'deep_link': notification.deep_link,
                    'actions': json.dumps(notification.actions)
                },
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        icon=notification.android.icon,
                        color=notification.android.color,
                        sound=notification.android.sound,
                        click_action=notification.deep_link,
                        channel_id='course_reminders'
                    ),
                    collapse_key=self._generate_collapse_key(notification)
                )
            )
            
            # 전송
            response = await self.fcm.send_async(message)
            
            return FCMResult(
                success=True,
                message_id=response,
                token=device_token
            )
            
        except messaging.UnregisteredError:
            # 토큰 무효화 - DB에서 제거
            await self._invalidate_token(device_token)
            return FCMResult(
                success=False,
                error='unregistered_token',
                token=device_token
            )
            
        except messaging.SenderIdMismatchError:
            await self._invalidate_token(device_token)
            return FCMResult(
                success=False,
                error='sender_id_mismatch',
                token=device_token
            )
            
        except Exception as e:
            logger.error(f"FCM send error: {e}")
            return FCMResult(
                success=False,
                error=str(e),
                token=device_token
            )
    
    async def send_batch_notifications(
        self, 
        notifications: List[Tuple[str, NotificationMessage]]
    ) -> List[FCMResult]:
        """배치 알림 전송 (최대 500개)"""
        
        if len(notifications) > 500:
            raise ValueError("FCM batch limit is 500 messages")
        
        messages = []
        for token, notification in notifications:
            message = messaging.Message(
                token=token,
                notification=messaging.Notification(
                    title=notification.android.title,
                    body=notification.android.body
                ),
                data={
                    'deep_link': notification.deep_link,
                    'type': notification.type
                }
            )
            messages.append(message)
        
        try:
            response = await self.fcm.send_multicast_async(
                messaging.MulticastMessage(messages=messages)
            )
            
            results = []
            for i, result in enumerate(response.responses):
                token = notifications[i][0]
                
                if result.success:
                    results.append(FCMResult(
                        success=True,
                        message_id=result.message_id,
                        token=token
                    ))
                else:
                    results.append(FCMResult(
                        success=False,
                        error=result.exception.code if result.exception else 'unknown',
                        token=token
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"FCM batch send error: {e}")
            return [
                FCMResult(success=False, error=str(e), token=token) 
                for token, _ in notifications
            ]
    
    def _generate_collapse_key(self, notification: NotificationMessage) -> str:
        """동일한 유형의 알림을 그룹화하는 키"""
        
        if notification.course_id:
            return f"{notification.type}_{notification.course_id}"
        else:
            return notification.type
```

### 5-2. APNS 클라이언트
```python
class APNSClient:
    def __init__(self):
        self.client = aioapns.APNs(
            key=settings.APNS_KEY,
            key_id=settings.APNS_KEY_ID,
            team_id=settings.APNS_TEAM_ID,
            topic=settings.APNS_TOPIC,
            use_sandbox=settings.DEBUG
        )
    
    async def send_notification(
        self, 
        device_token: str, 
        notification: NotificationMessage
    ) -> APNSResult:
        """APNS 알림 전송"""
        
        try:
            # APNS 페이로드 구성
            payload = aioapns.Payload(
                alert=aioapns.Alert(
                    title=notification.ios.title,
                    body=notification.ios.body,
                    subtitle=notification.ios.subtitle
                ),
                badge=await self._get_badge_count(device_token),
                sound=notification.ios.sound,
                content_available=True,
                mutable_content=True,
                custom={
                    'type': notification.type,
                    'course_id': notification.course_id,
                    'deep_link': notification.deep_link,
                    'actions': notification.actions
                }
            )
            
            # Rich Notification 이미지 추가
            if notification.ios.image_url:
                payload.custom['media_url'] = notification.ios.image_url
            
            # 액션 버튼 추가
            if notification.actions:
                payload.category = self._get_notification_category(notification.type)
            
            request = aioapns.NotificationRequest(
                device_token=device_token,
                message=payload,
                priority=aioapns.NotificationPriority.Immediate if notification.priority == NotificationPriority.URGENT else aioapns.NotificationPriority.Normal,
                collapse_id=self._generate_collapse_id(notification)
            )
            
            response = await self.client.send_notification(request)
            
            if response.is_successful:
                return APNSResult(
                    success=True,
                    message_id=response.notification_id,
                    token=device_token
                )
            else:
                # 토큰 무효화 체크
                if response.description in ['BadDeviceToken', 'Unregistered']:
                    await self._invalidate_token(device_token)
                
                return APNSResult(
                    success=False,
                    error=response.description,
                    token=device_token
                )
                
        except Exception as e:
            logger.error(f"APNS send error: {e}")
            return APNSResult(
                success=False,
                error=str(e),
                token=device_token
            )
    
    async def _get_badge_count(self, device_token: str) -> int:
        """사용자의 읽지 않은 알림 수"""
        
        user_id = await self._get_user_id_from_token(device_token)
        if not user_id:
            return 0
        
        unread_count = await self.db.notifications.count_documents({
            'user_id': user_id,
            'read': False,
            'created_at': {'$gte': datetime.utcnow() - timedelta(days=7)}
        })
        
        return min(unread_count, 99)  # iOS 배지 최대값
    
    def _get_notification_category(self, notification_type: str) -> str:
        """알림 타입별 카테고리 (액션 버튼 정의)"""
        
        category_mapping = {
            'departure_reminder': 'DEPARTURE_CATEGORY',
            'preparation_reminder': 'PREPARATION_CATEGORY',
            'urgent_change': 'URGENT_CATEGORY',
            'move_reminder': 'MOVE_CATEGORY'
        }
        
        return category_mapping.get(notification_type, 'DEFAULT_CATEGORY')
```

---

## 6. 실시간 모니터링

### 6-1. 변동 사항 감지
```python
class RealTimeMonitor:
    def __init__(self):
        self.weather_monitor = WeatherMonitor()
        self.business_monitor = BusinessHoursMonitor()
        self.traffic_monitor = TrafficMonitor()
        self.websocket_manager = WebSocketManager()
    
    async def start_monitoring(self):
        """실시간 모니터링 시작"""
        
        # 각 모니터를 별도 태스크로 실행
        tasks = [
            asyncio.create_task(self.weather_monitor.start()),
            asyncio.create_task(self.business_monitor.start()),
            asyncio.create_task(self.traffic_monitor.start()),
            asyncio.create_task(self._process_change_events())
        ]
        
        await asyncio.gather(*tasks)
    
    async def _process_change_events(self):
        """변동 이벤트 처리"""
        
        async for event in self._get_change_events():
            try:
                await self._handle_change_event(event)
            except Exception as e:
                logger.error(f"Failed to handle change event: {e}")
    
    async def _handle_change_event(self, event: ChangeEvent):
        """변동 이벤트 처리"""
        
        # 영향받는 코스들 조회
        affected_courses = await self._find_affected_courses(event)
        
        if not affected_courses:
            return
        
        # 각 코스에 대해 알림 생성
        for course in affected_courses:
            # 사용자 설정 확인
            user_settings = await self.user_preferences.get_settings(course.user_id)
            
            if not self._should_notify_change(event, user_settings):
                continue
            
            # 변동 알림 생성
            change_notification = await self._create_change_notification(
                course, event
            )
            
            # 즉시 발송
            await self.orchestrator.send_notification(change_notification)
            
            # 웹소켓으로 실시간 알림
            await self.websocket_manager.send_to_user(
                course.user_id,
                {
                    'type': 'course_change',
                    'course_id': course.id,
                    'change': event.dict(),
                    'notification': change_notification.dict()
                }
            )
    
    def _should_notify_change(
        self, 
        event: ChangeEvent, 
        user_settings: NotificationSettings
    ) -> bool:
        """변동 알림 발송 여부 판단"""
        
        if not user_settings.enabled:
            return False
        
        # 알림 유형별 설정 확인
        type_enabled = {
            'weather': user_settings.types.weather,
            'business_hours': user_settings.types.business_hours,
            'traffic': user_settings.types.traffic
        }
        
        if not type_enabled.get(event.type, False):
            return False
        
        # 심각도 기반 판단
        if event.severity == 'urgent':
            return True  # 긴급은 항상 알림
        
        if event.severity == 'high':
            return True  # 높음도 알림
        
        if event.severity == 'medium':
            # 중간은 조용시간이 아닐 때만
            return not self._is_quiet_time(user_settings.quiet_hours)
        
        return False  # 낮음은 알림 안함

class WeatherMonitor:
    def __init__(self):
        self.weather_api = WeatherAPI()
        self.change_publisher = ChangeEventPublisher()
    
    async def start(self):
        """날씨 모니터링 시작"""
        
        while True:
            try:
                await self._check_weather_changes()
                await asyncio.sleep(1800)  # 30분마다 체크
            except Exception as e:
                logger.error(f"Weather monitoring error: {e}")
                await asyncio.sleep(300)  # 5분 후 재시도
    
    async def _check_weather_changes(self):
        """날씨 변화 체크"""
        
        # 오늘/내일 코스가 있는 지역들 조회
        active_regions = await self._get_active_regions()
        
        for region in active_regions:
            # 현재 예보 조회
            current_forecast = await self.weather_api.get_forecast(
                region.coordinates,
                hours=48
            )
            
            # 이전 예보와 비교
            previous_forecast = await self._get_previous_forecast(region.id)
            
            if not previous_forecast:
                await self._save_forecast(region.id, current_forecast)
                continue
            
            # 유의미한 변화 감지
            changes = self._detect_weather_changes(previous_forecast, current_forecast)
            
            for change in changes:
                await self.change_publisher.publish(ChangeEvent(
                    type='weather',
                    region_id=region.id,
                    severity=self._assess_weather_severity(change),
                    description=change.description,
                    old_value=change.old_value,
                    new_value=change.new_value,
                    timestamp=datetime.utcnow()
                ))
            
            # 예보 업데이트
            await self._save_forecast(region.id, current_forecast)
    
    def _assess_weather_severity(self, change: WeatherChange) -> str:
        """날씨 변화 심각도 평가"""
        
        # 극한 날씨는 긴급
        if any(keyword in change.description.lower() for keyword in ['태풍', '폭우', '폭설', '한파']):
            return 'urgent'
        
        # 비/눈 시작/중단은 높음
        if any(keyword in change.description.lower() for keyword in ['비', '눈', '소나기']):
            return 'high'
        
        # 온도 10도 이상 변화는 높음
        if hasattr(change, 'temperature_diff') and abs(change.temperature_diff) >= 10:
            return 'high'
        
        # 나머지는 중간
        return 'medium'
```

---

## 7. 성능 최적화

### 7-1. 배치 처리 시스템
```python
class NotificationBatchProcessor:
    def __init__(self):
        self.batch_size = 500  # FCM 배치 제한
        self.processing_queue = asyncio.Queue(maxsize=10000)
        self.fcm_client = FCMClient()
        self.apns_client = APNSClient()
    
    async def start_batch_processor(self):
        """배치 프로세서 시작"""
        
        # 여러 워커를 병렬로 실행
        workers = [
            asyncio.create_task(self._batch_worker(f"worker_{i}"))
            for i in range(5)  # 5개 워커
        ]
        
        await asyncio.gather(*workers)
    
    async def _batch_worker(self, worker_id: str):
        """배치 워커"""
        
        while True:
            try:
                # 배치 수집
                batch = []
                
                # 최대 배치 크기까지 또는 1초까지 대기
                end_time = time.time() + 1.0
                
                while len(batch) < self.batch_size and time.time() < end_time:
                    try:
                        notification = await asyncio.wait_for(
                            self.processing_queue.get(),
                            timeout=max(0.1, end_time - time.time())
                        )
                        batch.append(notification)
                    except asyncio.TimeoutError:
                        break
                
                if batch:
                    await self._process_batch(batch, worker_id)
                
            except Exception as e:
                logger.error(f"Batch worker {worker_id} error: {e}")
                await asyncio.sleep(1)
    
    async def _process_batch(self, batch: List[ScheduledNotification], worker_id: str):
        """배치 처리"""
        
        # 플랫폼별로 분리
        fcm_notifications = []
        apns_notifications = []
        
        for notification in batch:
            device_tokens = await self._get_user_device_tokens(notification.user_id)
            
            for token in device_tokens:
                if token.platform == 'android':
                    fcm_notifications.append((token.token, notification.message))
                else:
                    apns_notifications.append((token.token, notification.message))
        
        # 병렬 전송
        tasks = []
        
        if fcm_notifications:
            # FCM 배치를 500개씩 나누어 전송
            for i in range(0, len(fcm_notifications), 500):
                chunk = fcm_notifications[i:i+500]
                tasks.append(self.fcm_client.send_batch_notifications(chunk))
        
        if apns_notifications:
            # APNS는 개별 전송 (배치 API 없음)
            for token, message in apns_notifications:
                tasks.append(self.apns_client.send_notification(token, message))
        
        # 전송 결과 수집
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 로깅
        await self._log_batch_results(batch, results, worker_id)
```

### 7-2. 캐싱 전략
```python
class NotificationCache:
    def __init__(self):
        self.redis = Redis.from_url(settings.REDIS_URL)
        self.local_cache = TTLCache(maxsize=1000, ttl=300)
    
    async def get_user_notification_settings(self, user_id: str) -> Optional[NotificationSettings]:
        """사용자 알림 설정 캐시 조회"""
        
        # L1: 로컬 캐시
        cache_key = f"settings:{user_id}"
        settings = self.local_cache.get(cache_key)
        if settings:
            return NotificationSettings.parse_obj(settings)
        
        # L2: Redis 캐시
        cached_data = await self.redis.get(f"notification_settings:{user_id}")
        if cached_data:
            settings_data = json.loads(cached_data)
            self.local_cache[cache_key] = settings_data
            return NotificationSettings.parse_obj(settings_data)
        
        return None
    
    async def set_user_notification_settings(
        self, 
        user_id: str, 
        settings: NotificationSettings
    ):
        """사용자 알림 설정 캐시 저장"""
        
        settings_data = settings.dict()
        
        # L1 + L2 동시 저장
        self.local_cache[f"settings:{user_id}"] = settings_data
        await self.redis.setex(
            f"notification_settings:{user_id}",
            3600,  # 1시간
            json.dumps(settings_data, default=str)
        )
    
    async def cache_context_data(self, context_key: str, data: Any, ttl: int = 1800):
        """컨텍스트 데이터 캐싱 (날씨, 교통 등)"""
        
        await self.redis.setex(
            f"context:{context_key}",
            ttl,
            json.dumps(data, default=str)
        )
    
    async def get_context_data(self, context_key: str) -> Optional[Any]:
        """컨텍스트 데이터 조회"""
        
        cached = await self.redis.get(f"context:{context_key}")
        if cached:
            return json.loads(cached)
        return None
    
    async def invalidate_user_cache(self, user_id: str):
        """사용자 관련 캐시 무효화"""
        
        # 로컬 캐시 제거
        keys_to_remove = [key for key in self.local_cache.keys() if user_id in key]
        for key in keys_to_remove:
            del self.local_cache[key]
        
        # Redis 캐시 제거
        pattern = f"*{user_id}*"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
```

---

## 8. 분석 및 모니터링

### 8-1. 알림 성과 분석
```python
class NotificationAnalytics:
    def __init__(self):
        self.db = get_database()
        self.metrics_collector = PrometheusMetrics()
    
    async def track_notification_sent(self, notification: ScheduledNotification, result: SendResult):
        """알림 전송 추적"""
        
        # DB에 전송 기록
        await self.db.notification_logs.insert_one({
            'notification_id': notification.id,
            'user_id': notification.user_id,
            'type': notification.type,
            'priority': notification.priority,
            'sent_at': datetime.utcnow(),
            'success': result.success,
            'platform': result.platform,
            'error': result.error if not result.success else None,
            'message_id': result.message_id
        })
        
        # Prometheus 메트릭
        self.metrics_collector.notification_sent.labels(
            type=notification.type,
            priority=notification.priority,
            platform=result.platform,
            success=result.success
        ).inc()
        
        if result.success:
            self.metrics_collector.notification_delivery_time.labels(
                type=notification.type
            ).observe(
                (datetime.utcnow() - notification.scheduled_time).total_seconds()
            )
    
    async def track_notification_interaction(
        self, 
        notification_id: str,
        user_id: str,
        interaction_type: str,
        timestamp: datetime = None
    ):
        """알림 상호작용 추적"""
        
        timestamp = timestamp or datetime.utcnow()
        
        # DB에 상호작용 기록
        await self.db.notification_interactions.insert_one({
            'notification_id': notification_id,
            'user_id': user_id,
            'interaction_type': interaction_type,  # opened, clicked, dismissed
            'timestamp': timestamp
        })
        
        # 메트릭 업데이트
        self.metrics_collector.notification_interactions.labels(
            interaction=interaction_type
        ).inc()
    
    async def generate_daily_report(self, date: datetime.date) -> NotificationReport:
        """일일 알림 성과 리포트 생성"""
        
        start_time = datetime.combine(date, time.min)
        end_time = datetime.combine(date, time.max)
        
        # 전송 통계
        sent_stats = await self.db.notification_logs.aggregate([
            {'$match': {
                'sent_at': {'$gte': start_time, '$lte': end_time}
            }},
            {'$group': {
                '_id': '$type',
                'total_sent': {'$sum': 1},
                'successful': {'$sum': {'$cond': ['$success', 1, 0]}},
                'failed': {'$sum': {'$cond': ['$success', 0, 1]}}
            }}
        ]).to_list(None)
        
        # 상호작용 통계
        interaction_stats = await self.db.notification_interactions.aggregate([
            {'$match': {
                'timestamp': {'$gte': start_time, '$lte': end_time}
            }},
            {'$group': {
                '_id': '$interaction_type',
                'count': {'$sum': 1}
            }}
        ]).to_list(None)
        
        # 성과 계산
        total_sent = sum(stat['total_sent'] for stat in sent_stats)
        total_opened = next(
            (stat['count'] for stat in interaction_stats if stat['_id'] == 'opened'),
            0
        )
        total_clicked = next(
            (stat['count'] for stat in interaction_stats if stat['_id'] == 'clicked'),
            0
        )
        
        return NotificationReport(
            date=date,
            total_sent=total_sent,
            success_rate=sum(stat['successful'] for stat in sent_stats) / total_sent if total_sent > 0 else 0,
            open_rate=total_opened / total_sent if total_sent > 0 else 0,
            click_rate=total_clicked / total_sent if total_sent > 0 else 0,
            type_breakdown=sent_stats,
            interaction_breakdown=interaction_stats
        )
    
    async def analyze_user_engagement(self, user_id: str, days: int = 30) -> UserEngagementAnalysis:
        """사용자 알림 참여도 분석"""
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # 사용자 알림 로그
        user_notifications = await self.db.notification_logs.find({
            'user_id': user_id,
            'sent_at': {'$gte': since_date},
            'success': True
        }).to_list(None)
        
        if not user_notifications:
            return UserEngagementAnalysis(
                user_id=user_id,
                period_days=days,
                total_received=0,
                engagement_rate=0,
                preferred_times=[],
                most_engaged_types=[]
            )
        
        # 상호작용 데이터
        interactions = await self.db.notification_interactions.find({
            'user_id': user_id,
            'timestamp': {'$gte': since_date}
        }).to_list(None)
        
        notification_ids = [notif['notification_id'] for notif in user_notifications]
        engaged_notifications = [
            inter for inter in interactions 
            if inter['notification_id'] in notification_ids and inter['interaction_type'] in ['opened', 'clicked']
        ]
        
        # 참여율 계산
        engagement_rate = len(engaged_notifications) / len(user_notifications)
        
        # 선호 시간대 분석
        hour_engagement = {}
        for notif in user_notifications:
            hour = notif['sent_at'].hour
            hour_engagement[hour] = hour_engagement.get(hour, {'total': 0, 'engaged': 0})
            hour_engagement[hour]['total'] += 1
            
            if any(inter['notification_id'] == notif['notification_id'] for inter in engaged_notifications):
                hour_engagement[hour]['engaged'] += 1
        
        # 최고 참여 시간대 (상위 3개)
        preferred_times = sorted(
            [(hour, data['engaged'] / data['total']) for hour, data in hour_engagement.items() if data['total'] >= 3],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return UserEngagementAnalysis(
            user_id=user_id,
            period_days=days,
            total_received=len(user_notifications),
            total_engaged=len(engaged_notifications),
            engagement_rate=engagement_rate,
            preferred_times=[hour for hour, _ in preferred_times],
            avg_response_time=self._calculate_avg_response_time(user_notifications, interactions)
        )
```

---

## 9. 테스트 전략

### 9-1. 단위 테스트 (TDD)
```python
class TestNotificationOrchestrator:
    @pytest.fixture
    def orchestrator(self):
        return NotificationOrchestrator()
    
    @pytest.fixture
    def sample_course(self):
        return Course(
            id="test_course_123",
            user_id="user_123",
            places=[
                Place(id="place_1", name="카페 A", arrival_time=time(14, 0)),
                Place(id="place_2", name="맛집 B", arrival_time=time(16, 0))
            ],
            scheduled_date=datetime.now().replace(hour=14, minute=0) + timedelta(days=1),
            transport_method=TransportMethod.WALKING
        )
    
    async def test_create_preparation_notification(self, orchestrator, sample_course):
        # Given
        user_settings = NotificationSettings(
            enabled=True,
            types=NotificationTypes(date_reminder=True),
            timing=NotificationTiming(day_before_hour=18)
        )
        
        # When
        notification = await orchestrator._create_preparation_notification(
            sample_course, user_settings
        )
        
        # Then
        assert notification.type == NotificationType.PREPARATION_REMINDER
        assert notification.priority == NotificationPriority.NORMAL
        assert notification.user_id == sample_course.user_id
        
        # 전날 18시에 스케줄링되었는지 확인
        expected_time = sample_course.scheduled_date.replace(hour=18, minute=0) - timedelta(days=1)
        assert notification.scheduled_time == expected_time
    
    async def test_departure_notification_timing(self, orchestrator, sample_course):
        # Given
        user_settings = NotificationSettings(
            enabled=True,
            types=NotificationTypes(departure_time=True),
            timing=NotificationTiming(departure_minutes_before=30)
        )
        
        # Mock travel time calculation
        orchestrator._calculate_travel_time = AsyncMock(return_value=45)  # 45분 소요
        
        # When
        notification = await orchestrator._create_departure_notification(
            sample_course, user_settings
        )
        
        # Then
        first_place = sample_course.places[0]
        departure_time = first_place.arrival_time.replace(hour=13, minute=15)  # 14:00 - 45분
        expected_notification_time = departure_time.replace(hour=12, minute=45)  # 13:15 - 30분
        
        assert notification.scheduled_time.time() == expected_notification_time.time()
    
    async def test_quiet_hours_handling(self, orchestrator):
        # Given
        notification = ScheduledNotification(
            user_id="user_123",
            type=NotificationType.PREPARATION_REMINDER,
            priority=NotificationPriority.NORMAL,
            scheduled_time=datetime.now().replace(hour=23, minute=0)  # 조용시간
        )
        
        user_settings = NotificationSettings(
            enabled=True,
            quiet_hours=QuietHours(start=time(22, 0), end=time(8, 0))
        )
        
        orchestrator.user_preferences.get_settings = AsyncMock(return_value=user_settings)
        orchestrator._reschedule_after_quiet_time = AsyncMock()
        
        # When
        await orchestrator.send_notification(notification)
        
        # Then
        orchestrator._reschedule_after_quiet_time.assert_called_once()
    
    async def test_urgent_notification_bypasses_quiet_hours(self, orchestrator):
        # Given
        urgent_notification = ScheduledNotification(
            user_id="user_123",
            type=NotificationType.URGENT_CHANGE,
            priority=NotificationPriority.URGENT,
            scheduled_time=datetime.now().replace(hour=23, minute=0)
        )
        
        user_settings = NotificationSettings(
            enabled=True,
            quiet_hours=QuietHours(start=time(22, 0), end=time(8, 0))
        )
        
        orchestrator.user_preferences.get_settings = AsyncMock(return_value=user_settings)
        orchestrator._get_user_device_tokens = AsyncMock(return_value=[])
        
        # When
        await orchestrator.send_notification(urgent_notification)
        
        # Then
        orchestrator._get_user_device_tokens.assert_called_once()  # 실제 전송 시도
```

### 9-2. 통합 테스트
```python
class TestNotificationSystemIntegration:
    @pytest.mark.integration
    async def test_end_to_end_course_notification_flow(self, test_db, redis_client):
        # Given
        user_id = "integration_test_user"
        course = await create_test_course(user_id)
        
        # 알림 설정
        settings = NotificationSettings(
            enabled=True,
            types=NotificationTypes(
                date_reminder=True,
                departure_time=True
            ),
            timing=NotificationTiming(
                day_before_hour=18,
                departure_minutes_before=30
            )
        )
        
        await save_user_notification_settings(user_id, settings)
        
        # When
        orchestrator = NotificationOrchestrator()
        notifications = await orchestrator.create_course_reminder(course, user_id)
        
        # Then
        assert len(notifications) >= 2  # 준비 + 출발 알림 최소
        
        # 데이터베이스에 스케줄 저장 확인
        scheduled_count = await test_db.scheduled_notifications.count_documents({
            'user_id': user_id,
            'course_id': course.id
        })
        
        assert scheduled_count == len(notifications)
        
        # Redis 큐에 작업 등록 확인
        queue_size = await redis_client.llen('notifications')
        assert queue_size >= len(notifications)
    
    @pytest.mark.integration 
    async def test_real_time_change_detection_and_notification(self, test_db):
        # Given
        course = await create_test_course_for_tomorrow()
        
        # 초기 컨텍스트 저장
        initial_context = CourseContext(
            weather=WeatherInfo(temperature=20, summary="맑음"),
            business_hours={course.places[0].id: BusinessHours(open=time(9,0), close=time(21,0))},
            wait_times={}
        )
        
        await save_course_context(course.id, initial_context)
        
        # When - 날씨 급변 시뮬레이션
        monitor = RealTimeMonitor()
        
        # Mock 외부 API 응답 (비 예보로 변경)
        mock_weather = WeatherInfo(
            temperature=15,
            summary="비",
            requires_umbrella=True,
            is_severe=False
        )
        
        monitor.weather_monitor.weather_api.get_forecast = AsyncMock(return_value=mock_weather)
        
        # 변경 감지 실행
        await monitor._check_weather_changes()
        
        # Then
        # 변경 알림이 생성되었는지 확인
        change_notifications = await test_db.notification_logs.find({
            'type': 'urgent_change',
            'user_id': course.user_id
        }).to_list(None)
        
        assert len(change_notifications) > 0
        
        # 알림 내용에 날씨 변화가 포함되어 있는지 확인
        notification = change_notifications[0]
        assert "비" in notification['message']['android']['body']
```

---

## 10. 용어 사전 (Technical)
- **FCM (Firebase Cloud Messaging):** Google의 푸시 알림 서비스
- **APNS (Apple Push Notification Service):** Apple의 푸시 알림 서비스
- **Batch Processing:** 여러 알림을 한 번에 묶어서 처리하는 방식
- **Quiet Hours:** 사용자가 알림을 받지 않으려는 시간대
- **Deep Link:** 알림을 통해 앱의 특정 화면으로 바로 이동하는 링크
- **Context Collector:** 날씨, 교통 등 외부 정보를 수집하는 컴포넌트
- **Collapse Key:** 같은 종류의 알림이 겹칠 때 최신 것만 보여주는 키

---

## Changelog
- 2025-01-XX: 초기 TRD 문서 작성 (작성자: Claude)
- PRD 07-notification-system 버전과 연동