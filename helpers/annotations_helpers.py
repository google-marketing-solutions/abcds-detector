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

"""Module to load helper functions to process annotations"""

import json


### REMOVE FOR COLAB - START
from input_parameters import (
    VERBOSE,
    early_time_seconds,
    confidence_threshold,
)

from helpers.generic_helpers import get_blob, get_annotation_uri
from helpers.face_detection import detect_faces
from helpers.label_detection import detect_labels
from helpers.logo_detection import detect_logos
from helpers.object_detection import detect_objects
from helpers.people_detection import detect_people
from helpers.shot_detection import detect_shots
from helpers.speech_detection import detect_speech
from helpers.text_detection import detect_text


### REMOVE FOR COLAB - END

def calculate_time_seconds(part_obj: dict, part: str) -> float:
    """Calculate time of the provided part of the video
    Args:
        part_obj: part of the video to calculate the time
        part: either start_time_offset or end_time_offset
    Returns:
        time_seconds: the time in seconds
    """
    if part not in part_obj:
        if VERBOSE:
            print(f"There is no part time {part} in {part_obj}")
            # TODO (ae) check this later
            return 0
    time_seconds = (
        (part_obj.get(part).get("seconds") or 0)
        + ((part_obj.get(part).get("microseconds") or 0) / 1e6)
        + ((part_obj.get(part).get("nanos") or 0) / 1e9)
    )
    return time_seconds


def detected_text_in_first_5_seconds(annotation: dict) -> tuple[bool, any]:
    """Detect if the text feature appears in the first 5 seconds
    Args:
        annotation: the text annotation
    Returns:
        True if the text is found in the 1st 5 secs, False otherwise
        frame: the frame where the feature was found
    """
    for segment in annotation.get("segments"):
        start_time_secs = calculate_time_seconds(
            segment.get("segment"), "start_time_offset"
        )
        if start_time_secs > early_time_seconds:
            continue  # Ignore a segment > 5 secs
        frames = segment.get("frames")
        for frame in frames:
            start_time_seconds = calculate_time_seconds(frame, "time_offset")
            if start_time_seconds <= early_time_seconds:
                return True, frame
    return False, None


def find_elements_in_transcript(
    speech_transcriptions: list[dict],
    elements: list[str],
    elements_categories: list[str],
    apply_condition: bool,
) -> tuple[bool, bool]:
    """Finds a list of elements in the video transcript
    Args:
        speech_transcriptions: the speech annotations
        elements: list of elements to find in the transcript
        elements_categories: list of element categories to find in the transcript
        apply_condition: flag to filter out text with less than x chars. This is
        only needed when elements come from text annotations since words are
        sometimes 1 character only.
    Returns:
        True if the elements are found, False otherwise
    """
    words_1st_5_secs = []
    element_mention_speech = False
    element_mention_speech_1st_5_secs = False
    for speech_transcription in speech_transcriptions:
        # The number of alternatives for each transcription is limited by
        # SpeechTranscriptionConfig.max_alternatives.
        # Each alternative is a different possible transcription
        # and has its own confidence score.
        for alternative in speech_transcription.get("alternatives"):
            # Check confidence against user defined threshold
            if alternative and alternative.get("confidence") >= confidence_threshold:
                transcript = alternative.get("transcript")
                # Check if elements or elements categories are found in transcript
                # TODO (ae) filter out words with less than x chars? - DONE
                if apply_condition:
                    found_elements = find_text_annotation_elements_in_transcript(
                        elements, transcript
                    )
                else:
                    found_elements = [
                        element
                        for element in elements
                        if element.lower() in transcript.lower()
                    ]
                found_elements_categories = [
                    elements_category
                    for elements_category in elements_categories
                    if elements_category.lower() in transcript.lower()
                ]
                if len(found_elements) > 0 or len(found_elements_categories) > 0:
                    element_mention_speech = True
                # For 1st 5 secs, check elements and elements_categories in words
                # since only the words[] contain times
                words = alternative.get("words") if "words" in alternative else []
                # Sort words by time to construct correct transcript later
                sorted_words = sorted(
                    words,
                    key=lambda x: calculate_time_seconds(x, "start_time"),
                    reverse=False,
                )
                for word_info in sorted_words:
                    start_time_secs = calculate_time_seconds(word_info, "start_time")
                    # Consider only words in the 1st 5 secs
                    if start_time_secs <= early_time_seconds:
                        words_1st_5_secs.append(word_info.get("word"))

    # Evaluate 1st 5 secs - Construct transcript from words
    transcript_1st_5_secs = " ".join(words_1st_5_secs)
    if apply_condition:
        found_elements_1st_5_seconds = find_text_annotation_elements_in_transcript(
            elements, transcript_1st_5_secs
        )
    else:
        found_elements_1st_5_seconds = [
            element
            for element in elements
            if element.lower() in transcript_1st_5_secs.lower()
        ]
    found_elements_categories_1st_5_seconds = [
        elements_category
        for elements_category in elements_categories
        if elements_category.lower() in transcript_1st_5_secs.lower()
    ]
    if (
        len(found_elements_1st_5_seconds) > 0
        or len(found_elements_categories_1st_5_seconds) > 0
    ):
        element_mention_speech_1st_5_secs = True

    return element_mention_speech, element_mention_speech_1st_5_secs


def find_text_annotation_elements_in_transcript(elements: list[str], transcript: str):
    """Checks if text annotation elements in an array are found in transcript
    Args:
        elements: list of elements to find in the transcript
        transcript: the transcript to find the elements in
        This is only needed when elements come from text annotations since
        words are sometimes 1 character only.
    """
    found_elements = [
        element
        for element in elements
        # filter out words with less than 3 chars? - DONE
        if len(element) > 3 and element.lower() in transcript.lower()
    ]
    return found_elements


def get_speech_transcript(speech_transcriptions: list[dict]) -> str:
    """Get transcript built from transcript alternatives
    Args:
        speech_transcriptions: the speech annotations
    Returns
        final_transcript: the constructured transcript
    """
    transcript_alternatives = []
    transcript_alt_confidence = []
    for speech_transcription in speech_transcriptions:
        # The number of alternatives for each transcription is limited by
        # SpeechTranscriptionConfig.max_alternatives.
        # Each alternative is a different possible transcription
        # and has its own confidence score.
        for alternative in speech_transcription.get("alternatives"):
            # Check confidence against user defined threshold
            transcript = alternative.get("transcript")
            if alternative and alternative.get("confidence") >= confidence_threshold:
                transcript_alternatives.append(transcript)
                transcript_alt_confidence.append(alternative)

    sorted_transcript_by_confidence = sorted(
        transcript_alt_confidence,
        key=lambda x: x.get("confidence"),
        reverse=True,
    )  # don't use this for now
    highest_confidence_trascript = (
        sorted_transcript_by_confidence[0].get("transcript")
        if len(sorted_transcript_by_confidence) > 0
        else ""
    )  # don't use this for now
    final_transcript = " ".join(transcript_alternatives)
    return final_transcript


def get_speech_transcript_1st_5_secs(speech_transcriptions: list[dict]):
    """Get transcript with highest confidence
    Args:
        speech_transcriptions: the speech annotations
    Returns
        transcript_1st_5_secs: the transcript in the 1st 5 secs
    """
    words_1st_5_secs = []
    for speech_transcription in speech_transcriptions:
        # The number of alternatives for each transcription is limited by
        # SpeechTranscriptionConfig.max_alternatives.
        # Each alternative is a different possible transcription
        # and has its own confidence score.
        for alternative in speech_transcription.get("alternatives"):
            # Check confidence against user defined threshold
            if alternative and alternative.get("confidence") >= confidence_threshold:
                # For 1st 5 secs get transcript from words
                # since only the words[] contain times
                words = alternative.get("words") if "words" in alternative else []
                # Sort words by time to construct correct transcript later
                sorted_words = sorted(
                    words,
                    key=lambda x: calculate_time_seconds(x, "start_time"),
                    reverse=False,
                )
                for word_info in sorted_words:
                    start_time_secs = calculate_time_seconds(word_info, "start_time")
                    # Consider only words in the 1st 5 secs
                    if start_time_secs <= early_time_seconds:
                        words_1st_5_secs.append(word_info.get("word"))
    # Construct transcript from words
    transcript_1st_5_secs = " ".join(words_1st_5_secs)
    return transcript_1st_5_secs


def download_video_annotations(
    video_uri: str
) -> tuple[dict, dict, dict, dict, dict, dict, dict]:
    """Download video annotations from Google Cloud Storage
    Args:
        video_uri: Full video uri
    Returns:
        text_annotation_results (list): Text annotations tuple
    """

    results = []
    annotation_location = get_annotation_uri(video_uri)

    for annotation_name, annotation_function in {
      'face-detection':detect_faces,
      'label-detection':detect_labels,
      'logo-detection':detect_logos,
      'object-detection':detect_objects,
      'people-detection':detect_people,
      'shot-detection':detect_shots,
      'speech-detection':detect_speech,
      'text-detection':detect_text,
    }.items():
      annotation_uri = f"{get_annotation_uri(video_uri)}{annotation_name}.json"
      annotataion_blob = get_blob(annotation_uri)
      if annotataion_blob is None:
        annotation_function(video_uri, annotation_uri)
        annotataion_blob = get_blob(annotation_uri)
      else:
        print(f"Annotation {annotation_uri} exists.")
      data = json.loads(annotataion_blob.download_as_string(client=None))
      results.append(data.get("annotation_results")[0]) # The first result is retrieved because a single video was processed.

    return results
