"""Service that handles video evaluations using AI (LLMs and/or Annotations)"""

import logging
import functools
from features_repository.feature_configs_handler import features_configs_handler
from llms_evaluation.llms_detector import llm_detector
from custom_evaluation.custom_detector import custom_detector
from configuration import Configuration
from helpers.generic_helpers import execute_tasks_in_parallel
from gcp_api_services.gcs_api_service import gcs_api_service
from models import VideoFeature, FeatureEvaluation, VideoFeatureCategory, VideoSegment


class VideoEvaluationService:
    """Service that handles video evaluations using AI (LLMs and/or Annotations)"""

    def __init__(self):
        pass

    def evaluate_features(
        self,
        config: Configuration,
        video_uri: str,
        features_category: VideoFeatureCategory,
    ):
        """Run ABCD evaluation on videos for Full ABCD features or Shorts"""

        feature_evaluations: list[FeatureEvaluation] = []
        tasks = []
        feature_groups = (
            features_configs_handler.get_features_by_category_by_group_config(
                features_category
            )
        )
        uri = video_uri  # use full video uri by default

        for group_key in feature_groups:
            feature_configs: list[VideoFeature] = feature_groups.get(group_key)
            # Process the features that are not grouped individually
            # meaning, each will be a separate request to the LLM
            if group_key == "NO_GROUPING":
                for f_config in feature_configs:
                    if (
                        f_config.video_segment.value
                        == VideoSegment.FIRST_5_SECS_VIDEO.value
                    ):
                        uri = gcs_api_service.get_reduced_uri(config, video_uri)
                    else:
                        uri = video_uri

                    # Build function to execute in parallel
                    # If custom detector was not defined, default to LLMs
                    if self.is_custom_evaluation(f_config.evaluation_function):
                        func = functools.partial(
                            custom_detector.evaluate_features, config, f_config, uri
                        )
                    else:
                        func = functools.partial(
                            llm_detector.evaluate_features,
                            config,
                            {
                                "group_by": f"{group_key}-{f_config.id}",
                                "video_uri": uri,
                                "feature_configs": feature_configs,  # process feature individually
                            },
                        )
                    # Add task to be process
                    tasks.append(func)
            else:
                if group_key == "first_5_secs_video":
                    uri = gcs_api_service.get_reduced_uri(config, video_uri)
                else:
                    uri = video_uri

                # Build function to execute in parallel
                func = functools.partial(
                    llm_detector.evaluate_features,
                    config,
                    {
                        "group_by": f"{group_key}",
                        "video_uri": uri,
                        "feature_configs": feature_configs,  # process feature individually
                    },
                )
                # Add task to be process
                tasks.append(func)

            logging.info("Starting ABCD evaluation using LLMs... \n")

            llm_evals = execute_tasks_in_parallel(tasks)

            # Process LLM results and create feature objs in the required format
            for evals in llm_evals:
                for evaluated_feature in evals:
                    feature: VideoFeature = self.get_feature_by_id(
                        evaluated_feature.get("id"), feature_configs
                    )
                    feature_evaluations.append(
                        FeatureEvaluation(
                            feature=feature,
                            detected=evaluated_feature.get("detected"),
                            confidence_score=evaluated_feature.get("confidence_score"),
                            rationale=evaluated_feature.get("rationale"),
                            evidence=evaluated_feature.get("evidence"),
                            strengths=evaluated_feature.get("strengths"),
                            weaknesses=evaluated_feature.get("weaknesses"),
                        )
                    )

        # Sort features by category and id for presentation
        """feature_evaluations = sorted(
            feature_evaluations,
            key=lambda feature_eval: (feature_eval.feature.category.value, feature_eval.feature.id),
            reverse=False,
        )"""

        return feature_evaluations

    def get_feature_by_id(self, feature_id: str, feature_configs: list[VideoFeature]):
        """Gets a feature by id"""
        feature = [feature for feature in feature_configs if feature.id == feature_id]
        if len(feature) > 0:
            return feature[0]

        return None

    def is_custom_evaluation(self, function_name):
        return function_name is not ""


video_evaluation_service = VideoEvaluationService()
