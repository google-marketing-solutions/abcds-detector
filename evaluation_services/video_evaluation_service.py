"""Service that handles video evaluations using AI (LLMs + Annotations)"""

import logging
import functools
from features_repository.feature_configs_handler import features_configs_handler
from llms_evaluation.llms_detector import llm_detector
from custom_evaluation.custom_detector import custom_detector
from configuration import Configuration
from helpers.generic_helpers import execute_tasks_in_parallel
from gcp_api_services.gcs_api_service import gcs_api_service
from models import VideoFeature, FeatureEvaluation, VideoFeatureCategory


class VideoEvaluationService:
    """Service that handles video evaluations using AI (LLMs + Annotations)"""

    def __init__(self):
        pass

    def evaluate_features(
        self,
        config: Configuration,
        video_uri: str,
        features_category: VideoFeatureCategory
    ):
        """Run ABCD evaluation on videos"""

        feature_evaluations = []

        # Full ABCD features or shorts
        feature_configs: list[VideoFeature] = (
            features_configs_handler.get_feature_configs_by_category(features_category)
        )

        for feature_config in feature_configs:
            logging.info("Starting evaluation for feature %s...", feature_config.name)

            if self.is_custom_evaluation(feature_config.evaluation_function):
                evaluation = custom_detector.evaluate_feature(
                    config, feature_config, video_uri
                )
                feature_evaluations.append(evaluation)
            else:
                # If custom detector was not defined, default to LLMs
                tasks = []
                feature_groups = features_configs_handler.get_groups_of_features(
                    features_category
                )
                uri = video_uri  # use full video uri by default

                for group_key in feature_groups:
                    feature_configs: list[VideoFeature] = feature_groups.get(group_key)
                    # Process the features that are not grouped individually
                    # meaning, each will be a separate request to the LLM
                    if group_key == "no_grouping":
                        for f_confing in feature_configs:
                            if f_confing.get("type") == "first_5_secs_video":
                                uri = gcs_api_service.get_reduced_uri(config, video_uri)
                            else:
                                uri = video_uri
                            # Build function to execute in parallel
                            func = functools.partial(
                                llm_detector.evaluate_features,
                                config,
                                {
                                    "group_by": f"{group_key}-{f_confing.get('id')}",
                                    "video_uri": uri,
                                    "feature_configs": [
                                        f_confing
                                    ],  # process feature individually
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
                                "group_by": group_key,
                                "video_uri": uri,
                                "feature_configs": feature_configs,  # process each group
                            },
                        )
                        # Add task to be process
                        tasks.append(func)

                logging.info("Starting ABCD evaluation using LLMs... \n")

                llm_evals = execute_tasks_in_parallel(tasks)

                # Process LLM results and create feature objs in the required format
                for evals in llm_evals:
                    for evaluated_feature in evals:
                        feature = self.get_feature_by_id(
                            evaluated_feature.get("id"), feature_configs
                        )
                        # Warning: This could be a hallucination - False Positive answer
                        detected = (
                            evaluated_feature.get("detected")
                            or evaluated_feature.get("detected") == "True"
                            or evaluated_feature.get("detected") == "true"
                        )
                        feature_evaluations.append(
                            FeatureEvaluation(
                                feature=feature,
                                detected=detected,
                                confidence_score=evaluated_feature.get(
                                    "confidence_score"
                                ),
                                evaluation_details=evaluated_feature.get(
                                    "evaluated_feature"
                                ),
                            )
                        )

                # Sort features for presentation
                feature_evaluations = sorted(
                    feature_evaluations,
                    key=lambda feature: feature.id,
                    reverse=False,
                )

    def get_feature_by_id(self, feature_id: str, feature_configs: list[VideoFeature]):
        """Gets a feature by id"""
        feature = [feature for feature in feature_configs if feature.id == feature_id]

        return feature

    def is_custom_evaluation(self, function_name):
        return function_name is not ''


video_evaluation_service = VideoEvaluationService()
