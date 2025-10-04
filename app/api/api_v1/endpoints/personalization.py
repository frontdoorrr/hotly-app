"""Personalization and A/B testing API endpoints."""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ab_testing.framework import ABTestOrchestrator, ExperimentManager
from app.analytics.onboarding import OnboardingAnalytics
from app.api.deps import get_db
from app.services.content.dynamic_content_service import DynamicContentGenerator
from app.services.ml.personalization_service import (
    OnboardingPersonalizationEngine,
    PersonalizationOptimizer,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/onboarding/personalized", response_model=dict)
async def get_personalized_onboarding(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    device_info: Optional[dict] = None,
    referral_source: Optional[str] = None,
    user_segment: Optional[str] = None,
) -> dict:
    """
    Get personalized onboarding flow for user.

    - **user_id**: User identifier
    - **device_info**: Device and platform information (optional)
    - **referral_source**: How user discovered the app (optional)
    - **user_segment**: Predetermined user segment (optional)

    Returns personalized onboarding configuration.
    """
    try:
        # Build user context
        user_context = {
            "device_info": device_info or {},
            "referral_source": referral_source or "unknown",
            "user_segment": user_segment,
        }

        # Generate personalized onboarding
        personalization_engine = OnboardingPersonalizationEngine(db)
        personalized_flow = personalization_engine.get_personalized_onboarding_flow(
            user_id, user_context
        )

        # Run A/B test experiments
        ab_orchestrator = ABTestOrchestrator(db)
        experiment_result = ab_orchestrator.run_onboarding_experiment(
            user_id, personalized_flow, user_context
        )

        # Generate dynamic content
        content_generator = DynamicContentGenerator(db)
        welcome_content = content_generator.generate_personalized_content(
            "welcome_message", personalized_flow["user_segment"], user_context
        )

        response = {
            "user_id": user_id,
            "personalized_flow": personalized_flow,
            "experiment_assignments": experiment_result.get("applied_experiments", []),
            "dynamic_content": {
                "welcome_message": welcome_content.get("generated_content", {}),
            },
            "personalization_metadata": {
                "personalization_confidence": personalized_flow.get(
                    "personalization_confidence", 0
                ),
                "experiment_count": len(
                    experiment_result.get("applied_experiments", [])
                ),
                "generated_at": datetime.utcnow().isoformat(),
            },
        }

        logger.info(f"Personalized onboarding generated for user {user_id}")
        return response

    except Exception as e:
        logger.error(f"Failed to get personalized onboarding: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate personalized onboarding"
        )


@router.post("/ab-test/track", response_model=dict)
async def track_ab_test_event(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    event_name: str,
    event_data: dict,
    experiment_assignments: Optional[List[dict]] = None,
) -> dict:
    """
    Track A/B test event for analysis.

    - **user_id**: User identifier
    - **event_name**: Name of the event to track
    - **event_data**: Event data and context
    - **experiment_assignments**: Current experiment assignments (optional)

    Returns event tracking confirmation.
    """
    try:
        experiment_manager = ExperimentManager(db)

        # Track the event
        experiment_manager.track_event(
            user_id, event_name, event_data, experiment_assignments
        )

        # If this is a completion event, track it specifically
        if event_name == "onboarding_completed":
            ab_orchestrator = ABTestOrchestrator(db)
            ab_orchestrator.track_onboarding_completion(
                user_id, event_data, experiment_assignments
            )

        tracking_result = {
            "user_id": user_id,
            "event_name": event_name,
            "tracked_successfully": True,
            "experiment_count": len(experiment_assignments or []),
            "tracked_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"A/B test event '{event_name}' tracked for user {user_id}")
        return tracking_result

    except Exception as e:
        logger.error(f"Failed to track A/B test event: {e}")
        raise HTTPException(status_code=500, detail="Failed to track A/B test event")


@router.get("/analytics/onboarding", response_model=dict)
async def get_onboarding_analytics(
    *,
    db: Session = Depends(get_db),
    time_period_days: int = 30,
    user_segment: Optional[str] = None,
    analysis_type: str = "cohort",
) -> dict:
    """
    Get onboarding analytics and insights.

    - **time_period_days**: Analysis time period in days
    - **user_segment**: Specific user segment to analyze (optional)
    - **analysis_type**: Type of analysis (cohort, behavior, optimization)

    Returns comprehensive onboarding analytics.
    """
    try:
        analytics = OnboardingAnalytics(db)

        if analysis_type == "cohort":
            analysis_result = analytics.generate_cohort_analysis(
                time_period_days, user_segment
            )
        elif analysis_type == "optimization":
            optimizer = PersonalizationOptimizer(db)
            analysis_result = optimizer.analyze_personalization_performance(
                time_period_days
            )
        else:
            raise HTTPException(
                status_code=422, detail=f"Unsupported analysis type: {analysis_type}"
            )

        response = {
            "analysis_type": analysis_type,
            "time_period_days": time_period_days,
            "user_segment": user_segment,
            "results": analysis_result,
            "generated_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Onboarding analytics generated: {analysis_type}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get onboarding analytics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate onboarding analytics"
        )


@router.post("/personalization/analyze-behavior", response_model=dict)
async def analyze_user_behavior(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    session_data: dict,
) -> dict:
    """
    Analyze user behavior patterns during onboarding.

    - **user_id**: User identifier
    - **session_data**: Onboarding session interaction data

    Returns behavior analysis and personalization insights.
    """
    try:
        analytics = OnboardingAnalytics(db)
        behavior_analysis = analytics.analyze_user_behavior_patterns(
            user_id, session_data
        )

        # Extract actionable insights
        behavior_analysis.get("personalization_insights", {})
        recommendations = []

        # Generate recommendations based on analysis
        if behavior_analysis.get("struggle_indicators", {}).get("risk_level") == "high":
            recommendations.append(
                {
                    "type": "intervention",
                    "priority": "high",
                    "action": "Provide additional guidance and support",
                }
            )

        if (
            behavior_analysis.get("efficiency_metrics", {}).get("overall_efficiency", 0)
            < 0.5
        ):
            recommendations.append(
                {
                    "type": "optimization",
                    "priority": "medium",
                    "action": "Simplify onboarding flow for this user type",
                }
            )

        response = {
            "user_id": user_id,
            "behavior_analysis": behavior_analysis,
            "recommendations": recommendations,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"User behavior analyzed for {user_id}")
        return response

    except Exception as e:
        logger.error(f"Failed to analyze user behavior: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze user behavior")


@router.get("/personalization/content", response_model=dict)
async def get_dynamic_content(
    *,
    db: Session = Depends(get_db),
    content_type: str,
    user_segment: str,
    context: Optional[dict] = None,
) -> dict:
    """
    Get dynamically generated personalized content.

    - **content_type**: Type of content to generate (welcome_message, step_description, etc.)
    - **user_segment**: User segment for personalization
    - **context**: Additional context for content generation

    Returns personalized content.
    """
    try:
        content_generator = DynamicContentGenerator(db)
        content_result = content_generator.generate_personalized_content(
            content_type, user_segment, context or {}
        )

        logger.info(f"Dynamic content generated: {content_type} for {user_segment}")
        return content_result

    except Exception as e:
        logger.error(f"Failed to generate dynamic content: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate dynamic content"
        )


@router.post("/experiments/create", response_model=dict)
async def create_ab_experiment(
    *,
    db: Session = Depends(get_db),
    experiment_config: dict,
) -> dict:
    """
    Create new A/B test experiment.

    - **experiment_config**: Experiment configuration including variants, metrics, and targeting

    Returns created experiment details.
    """
    try:
        experiment_manager = ExperimentManager(db)
        experiment = experiment_manager.create_experiment(experiment_config)

        logger.info(f"A/B test experiment created: {experiment['id']}")
        return experiment

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create A/B experiment: {e}")
        raise HTTPException(status_code=500, detail="Failed to create A/B experiment")


@router.get("/experiments/{experiment_id}/results", response_model=dict)
async def get_experiment_results(
    *,
    db: Session = Depends(get_db),
    experiment_id: str,
    analysis_period_days: Optional[int] = None,
) -> dict:
    """
    Get A/B test experiment results and analysis.

    - **experiment_id**: Experiment identifier
    - **analysis_period_days**: Analysis period in days (optional)

    Returns experiment results and statistical analysis.
    """
    try:
        from app.ab_testing.framework import ABTestAnalyzer

        analyzer = ABTestAnalyzer(db)
        results = analyzer.analyze_experiment_results(
            experiment_id, analysis_period_days
        )

        if not results:
            raise HTTPException(
                status_code=404, detail=f"Experiment {experiment_id} not found"
            )

        # Generate comprehensive report
        report = analyzer.generate_experiment_report(experiment_id, results)

        response = {
            "experiment_id": experiment_id,
            "results": results,
            "report": report,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Experiment results generated for {experiment_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get experiment results: {e}")
        raise HTTPException(status_code=500, detail="Failed to get experiment results")


@router.post("/personalization/track-effectiveness", response_model=dict)
async def track_personalization_effectiveness(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    onboarding_session: dict,
    completion_metrics: dict,
) -> dict:
    """
    Track effectiveness of personalization decisions.

    - **user_id**: User identifier
    - **onboarding_session**: Onboarding session data with personalization applied
    - **completion_metrics**: Completion metrics and user feedback

    Returns effectiveness tracking results.
    """
    try:
        personalization_engine = OnboardingPersonalizationEngine(db)
        effectiveness_data = personalization_engine.track_personalization_effectiveness(
            user_id, onboarding_session, completion_metrics
        )

        logger.info(f"Personalization effectiveness tracked for user {user_id}")
        return effectiveness_data

    except Exception as e:
        logger.error(f"Failed to track personalization effectiveness: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to track personalization effectiveness"
        )


@router.get("/personalization/optimization-recommendations", response_model=dict)
async def get_optimization_recommendations(
    *,
    db: Session = Depends(get_db),
    time_period_days: int = 30,
) -> dict:
    """
    Get optimization recommendations based on performance analysis.

    - **time_period_days**: Analysis time period in days

    Returns optimization recommendations and priorities.
    """
    try:
        optimizer = PersonalizationOptimizer(db)

        # Get performance analysis
        performance_analysis = optimizer.analyze_personalization_performance(
            time_period_days
        )

        # Generate recommendations
        recommendations = optimizer.generate_optimization_recommendations(
            performance_analysis
        )

        response = {
            "time_period_days": time_period_days,
            "performance_analysis": performance_analysis,
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "high_priority_count": len(
                [r for r in recommendations if r.get("priority") == "high"]
            ),
            "generated_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Optimization recommendations generated for {time_period_days} days"
        )
        return response

    except Exception as e:
        logger.error(f"Failed to get optimization recommendations: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get optimization recommendations"
        )


@router.post("/personalization/track-optimization-impact", response_model=dict)
async def track_optimization_impact(
    *,
    db: Session = Depends(get_db),
    optimization_id: str,
    before_metrics: dict,
    after_metrics: dict,
    time_period_days: int = 30,
) -> dict:
    """
    Track impact of optimization changes.

    - **optimization_id**: Optimization identifier
    - **before_metrics**: Metrics before optimization
    - **after_metrics**: Metrics after optimization
    - **time_period_days**: Analysis time period in days

    Returns impact analysis and statistical significance.
    """
    try:
        analytics = OnboardingAnalytics(db)
        impact_analysis = analytics.track_optimization_impact(
            optimization_id, before_metrics, after_metrics, time_period_days
        )

        logger.info(f"Optimization impact tracked for {optimization_id}")
        return impact_analysis

    except Exception as e:
        logger.error(f"Failed to track optimization impact: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to track optimization impact"
        )
