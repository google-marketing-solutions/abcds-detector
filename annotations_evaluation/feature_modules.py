#!/usr/bin/env python3

###########################################################################
#
#  Copyright 2024 Google LLC
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

"""Module to import the annotations modules to evaluate ABCD features."""

from annotations_evaluation.features.a_dynamic_start import detect_dynamic_start
from annotations_evaluation.features.a_quick_pacing import (
    detect_quick_pacing,
    detect_quick_pacing_1st_5_secs,
)
from annotations_evaluation.features.a_supers import (
    detect_supers,
    detect_supers_with_audio,
)
from annotations_evaluation.features.b_brand_mention_speech import (
    detect_brand_mention_speech,
    detect_brand_mention_speech_1st_5_secs,
)
from annotations_evaluation.features.b_brand_visuals import (
    detect_brand_visuals,
    detect_brand_visuals_1st_5_secs,
)
from annotations_evaluation.features.b_product_mention_speech import (
    detect_product_mention_speech,
    detect_product_mention_speech_1st_5_secs,
)
from annotations_evaluation.features.b_product_mention_text import (
    detect_product_mention_text,
    detect_product_mention_text_1st_5_secs,
)
from annotations_evaluation.features.b_product_visuals import (
    detect_product_visuals,
    detect_product_visuals_1st_5_secs,
)
from annotations_evaluation.features.c_overall_pacing import detect_overall_pacing
from annotations_evaluation.features.c_presence_of_people import (
    detect_presence_of_people,
    detect_presence_of_people_1st_5_secs,
)
from annotations_evaluation.features.c_visible_face import (
    detect_visible_face,
    detect_visible_face_close_up,
)
from annotations_evaluation.features.d_audio_speech_early import (
    detect_audio_speech_early_1st_5_secs,
)
from annotations_evaluation.features.d_call_to_action import (
    detect_call_to_action_speech,
    detect_call_to_action_text,
)
