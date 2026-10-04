###########################################################################
#
#  Copyright 2025 Google LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
###########################################################################

"""Module to evaluate features for ABCDs using custom functions / registry."""

import importlib
import logging
import pathlib
import sys
from typing import Any, Callable

import configuration
import models

logger = logging.getLogger("abcd_detector")

# Registry for custom feature evaluation functions
CUSTOM_EVALUATORS: dict[str, Callable[..., Any]] = {}


def register_evaluator(
    name: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
  """Decorator to register a custom evaluation function.

  Args:
    name: Identifier name for the custom evaluator.

  Returns:
    Decorator function registering the callable under the given name.
  """

  def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    """Registers the decorated function in CUSTOM_EVALUATORS."""
    CUSTOM_EVALUATORS[name] = func
    return func

  return decorator


def load_custom_evaluators() -> None:
  """Imports all evaluator modules from custom_evaluation/evaluations/."""
  evaluations_dir = pathlib.Path(__file__).parent / "evaluations"
  if evaluations_dir.exists() and evaluations_dir.is_dir():
    for file_path in sorted(evaluations_dir.glob("*.py")):
      if file_path.name.startswith("__"):
        continue
      module_name = f"custom_evaluation.evaluations.{file_path.stem}"
      if module_name not in sys.modules:
        try:
          importlib.import_module(module_name)
          logger.debug("Imported custom evaluator module: %s", module_name)
        except Exception as err:
          logger.warning(
              "Failed to auto-import custom evaluator '%s': %s",
              module_name,
              err,
          )


class CustomDetector:
  """Evaluates ABCD features using registered custom evaluation functions."""

  def __init__(self) -> None:
    """Initializes CustomDetector and auto-discovers custom evaluators."""
    load_custom_evaluators()

  def evaluate_feature(
      self,
      gemini_config: configuration.GeminiConfig,
      feature_config: models.VideoFeature,
      video_uri: str,
      brand_context: configuration.BrandContext | None = None,
  ) -> models.FeatureEvaluation:
    """Evaluates a single ABCD feature using its registered custom function.

    Args:
      gemini_config: Gemini API configuration parameters.
      feature_config: Definition of the feature to evaluate.
      video_uri: Cloud Storage URI of the video.
      brand_context: Optional brand metadata for augmented prompts.

    Returns:
      Evaluation result for the feature.
    """
    func_name = feature_config.evaluation_function
    logger.info(
        "Executing custom evaluator '%s' for feature '%s'...",
        func_name,
        feature_config.name,
    )

    if not func_name:
      raise ValueError(
          f"Feature '{feature_config.id}' does not have an evaluation_function"
          " defined."
      )

    if func_name not in CUSTOM_EVALUATORS:
      load_custom_evaluators()

    if func_name not in CUSTOM_EVALUATORS:
      raise ValueError(
          f"Custom evaluation function '{func_name}' is not registered. "
          f"Available evaluators: {list(CUSTOM_EVALUATORS.keys())}"
      )

    evaluator_func = CUSTOM_EVALUATORS[func_name]
    result = evaluator_func(
        gemini_config=gemini_config,
        feature_config=feature_config,
        video_uri=video_uri,
        brand_context=brand_context,
    )

    if not isinstance(result, models.FeatureEvaluation):
      raise TypeError(
          f"Custom evaluator '{func_name}' must return a FeatureEvaluation"
          f" instance, got '{type(result).__name__}'."
      )

    return result
