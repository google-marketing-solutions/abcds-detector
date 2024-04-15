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

"""Module to load helper functions"""

import json
import time
import urllib
from google.cloud import storage
import vertexai
import vertexai.preview.generative_models as generative_models
from vertexai.preview.generative_models import GenerativeModel, Part
from googleapiclient.errors import HttpError

### REMOVE FOR COLAB - START
from input_parameters import (
    PROJECT_ID,
    GEMINI_PRO,
    VERBOSE,
    KNOWLEDGE_GRAPH_API_KEY,
    BUCKET_NAME,
    STORE_TEST_RESULTS,
    TEST_RESULTS,
    early_time_seconds,
    confidence_threshold,
    brand_name,
)

### REMOVE FOR COLAB - END

# Init cloud storage bucket
storage_client = storage.Client()
bucket = storage_client.get_bucket(BUCKET_NAME)

# Knowledge Graph module


def get_knowledge_graph_entities(queries: list[str]) -> dict[str, dict]:
    """Get the knowledge Graph Entities for a list of queries
    Args:
        queries: a list of entities to find in KG
    Returns:
        kg_entities: entities found in KG
        Format example: entity id is the key and entity details the value
        kg_entities = {
            "mcy/12": {} TODO (ae) add here
        }
    """
    kg_entities = {}
    for query in queries:
        service_url = "https://kgsearch.googleapis.com/v1/entities:search"
        params = {
            "query": query,
            "limit": 10,
            "indent": True,
            "key": KNOWLEDGE_GRAPH_API_KEY,
        }
        url = f"{service_url}?{urllib.parse.urlencode(params)}"
        response = json.loads(urllib.request.urlopen(url).read())
        for element in response["itemListElement"]:
            kg_entity_name = element["result"]["name"]
            # To only add the exact KG entity
            if query.lower() == kg_entity_name.lower():
                kg_entities[element["result"]["@id"][3:]] = element["result"]
    return kg_entities


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


def get_file_name_from_gcs_url(gcs_url: str) -> tuple[str]:
    """Get file name from GCS url
    Args:
        gcs_url: the gcs url with the file name
    Returns:
        file_name_with_format: the file name with its format
        file_name: the file name
    """
    url_parts = gcs_url.split("/")
    if len(url_parts) == 3:
        file_name = url_parts[2].split(".")[0]
        file_name_with_format = url_parts[2]
        return file_name, file_name_with_format
    return ""


def get_existing_annotations_from_gcs(brand_name: str) -> list[str]:
    """Get existing annotations from Cloud Storage
    Args:
        brand_name: the parent folder in Cloud Storage
    Returns:
        video_annotations: array of annotation url/names
    """
    blobs = bucket.list_blobs(prefix=f"{brand_name}/annotations/")
    video_annotations = []
    for blob in blobs:
        video_annotations.append(f"gs://{BUCKET_NAME}/{blob.name}")
    return video_annotations


class LLMParameters:
    """Class that represents the required params to make a prediction to the LLM"""

    model_name: str
    location: str
    modality: dict
    generation_config: dict = {  # Default model config
        "max_output_tokens": 2048,
        "temperature": 0.5,
        "top_p": 1,
        "top_k": 40,
    }

    def __init__(
        self,
        model_name: str,
        location: str,
        generation_config: dict,
        modality: dict = None,
    ):
        self.model_name = model_name
        self.location = location
        self.generation_config = generation_config
        self.modality = modality

    def set_modality(self, modality: dict) -> None:
        """Sets the modal to use in the LLM
        The modality object changes depending on the type.
        For video:
        {
            "type": "video", # prompt is handled separately
            "video_uri": ""
        }
        For text:
        {
            "type": "text" # prompt is handled separately
        }
        """
        self.modality = modality


def get_video_format(video_location: str):
    """Gets video format from gcs url
    Args:
        video_location: gcs video location
    Returns:
        video_format: video format
    """
    gcs_parts = video_location.split(".")
    if len(gcs_parts) == 2:
        video_format = gcs_parts[1]
        return video_format
    return ""


def get_n_secs_video_uri_from_uri(video_uri: str, new_name_part: str):
    """Get uri for the n seconds video
    Args:
        video_uri: str
    Return:
        video_name_n_secs
    """
    gcs_parts = video_uri.split(".")
    if len(gcs_parts) == 2:
        video_format = gcs_parts[1]
        long_video_name_parts = gcs_parts[0].split("/")
        if len(long_video_name_parts) == 6:
            gcs = long_video_name_parts[0]
            bucket_name = long_video_name_parts[2]
            brand = long_video_name_parts[3]
            videos_folder = long_video_name_parts[4]
            # Last element is the video name
            video_name = f"{long_video_name_parts[-1]}_{new_name_part}.{video_format}"
            n_secs_video_uri = (
                f"{gcs}//{bucket_name}/{brand}/{videos_folder}/{video_name}"
            )
        return n_secs_video_uri
    return ""


class VertexAIService:
    """Vertex AI Service to leverage the Vertex APIs for inference"""

    def __init__(self, project_id: str):
        self.project_id = project_id

    def execute_gemini_pro(self, prompt: str, params: LLMParameters) -> str:
        """Makes a request to Gemini to get a prediction based on the provided prompt
        and multi-modal params
        Args:
            prompt: a string with the prompt for LLM
            params: llm params model_name, location, modality and generation_config
        Returns:
            response.text: a string with the generated response
        """
        retries = 4
        for this_retry in range(retries):
            try:
                vertexai.init(project=self.project_id, location=params.location)
                model = GenerativeModel(params.model_name)
                modality_params = self._get_modality_params(prompt, params)
                response = model.generate_content(
                    modality_params,
                    generation_config=params.generation_config,
                    safety_settings={
                        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    },
                    stream=False,
                )
                return response.text if response else ""
            except AttributeError as ex:
                error_message = str(ex)
                if "Content has no parts" in error_message:
                    print(
                        f"Error: {ex} Gemini might be blocking the response due to safety issues.\n"
                    )
            except HttpError as ex:
                print("HTTP EXCEPTION...\n")
                if VERBOSE:
                    print(f"HttpError: {ex}\n")
                if this_retry == retries - 1 or ex.resp.status not in [
                    403,
                    429,
                    500,
                    503,
                ]:
                    raise
                if VERBOSE and ex.resp.status == 429:
                    print(
                        f"Quota issue. Retrying {retries - 1} times using exponential backoff. Retry number {this_retry}...\n"
                    )
                wait = 10 * 2**this_retry
                time.sleep(wait)
            except Exception as ex:
                print("GENERAL EXCEPTION...\n")
                error_message = str(ex)
                # Check quota issues for now
                if (
                    this_retry == retries - 1
                    or "429 Quota exceeded" not in error_message
                ):
                    if VERBOSE:
                        print(f"{error_message}\n")
                    raise
                if VERBOSE and "429 Quota exceeded" in error_message:
                    print(
                        f"Quota issue. Retrying {retries - 1} times using exponential backoff. Retry number {this_retry}...\n"
                    )
                wait = 10 * 2**this_retry
                time.sleep(wait)
        return ""

    def _get_modality_params(self, prompt: str, params: LLMParameters) -> list[any]:
        """Build the modality params based on the type of llm capability to use
        Args:
            prompt: a string with the prompt for LLM
            model_params: the model params for inference, see defaults above
        Returns:
            modality_params: list of modality params based on the model capability to use
        """
        if params.modality["type"] == "video":
            mime_type = f"video/{get_video_format(params.modality['video_uri'])}"
            video = Part.from_uri(uri=params.modality["video_uri"], mime_type=mime_type)
            return [video, prompt]
        elif params.modality["type"] == "text":
            return [prompt]
        return []


vertex_ai_service = VertexAIService(PROJECT_ID)


def detect_feature_with_llm(
    feature: str, prompt: str, llm_params: LLMParameters
) -> bool:
    """Detect feature using LLM
    Args:
        feature: the feature to evaluate
        prompt: prompt for the llm
        llm_params: object with llm params
    Returns:
        feature_detected: True if the feature is detected, False otherwise
    """
    if llm_params.model_name == GEMINI_PRO:
        # Gemini 1.5 does not support top_k param
        if "top_k" in llm_params.generation_config:
            del llm_params.generation_config["top_k"]
        llm_response = vertex_ai_service.execute_gemini_pro(
            prompt=prompt, params=llm_params
        )
    else:
        print(f"LLM {llm_params.model_name} not supported.")
        return False
    try:
        llm_response_json = json.loads(clean_llm_response(llm_response))
        if STORE_TEST_RESULTS:
            store_test_results(feature, prompt, llm_params, llm_response)
        if VERBOSE:
            print("***Powered by LLMs***")
            print(
                f"Feature detected: {feature}: {llm_response_json['feature_detected']}"
            )
            print(f"Explanation: {llm_response_json['explanation']}\n")
        return llm_response_json["feature_detected"] == "True"
    except json.JSONDecodeError as ex:
        if STORE_TEST_RESULTS:
            store_test_results(feature, prompt, llm_params, llm_response)
        if VERBOSE:
            print(f"LLM response could not be parsed: {ex}\n")
            print("Using string version...\n")
            if llm_response:
                print("***Powered by LLMs***")
                print(f"{feature}: {llm_response}")
    except Exception as ex:
        print(ex)
        raise

    return llm_response and '"feature_detected": "True"' in llm_response


def clean_llm_response(response: str) -> str:
    """Cleans LLM response
    Args:
        response: llm response to clean
    """
    return response.replace("```", "").replace("json", "")


def store_test_results(
    feature: str, prompt: str, llm_params: LLMParameters, llm_response: any
) -> None:
    """Store test results
    Args:
        feature: the feature being processed
        llm_params: model name, location, model params, modality params (video, text, etc)
        prompt: the prompt being processed,
        llm_response: the response from the LLM
    """
    results = {
        "brand_name": brand_name,
        "feature": feature,
        "llm_params": llm_params.__dict__,
        "prompt": prompt,
        "llm_response": llm_response,
    }
    TEST_RESULTS.append(results)


def store_test_results_local_file():
    """Store test results in a file"""
    with open(
        f"test_results/{brand_name}_test_results.json", "w", encoding="utf-8"
    ) as f:
        json.dump(TEST_RESULTS, f, ensure_ascii=False, indent=4)


def download_video_annotations(
    brand_name: str, video_name: str
) -> tuple[dict, dict, dict, dict, dict, dict, dict]:
    """Download video annotations from Google Cloud Storage
    Args:
        brand_name: the brand to generate the video annotations for
        video_name: Full video name
    Returns:
        text_annotation_results (tuple): Text annotations tuple
    """
    annotation_location = f"{brand_name}/annotations/{video_name}"

    # Label Annotations
    blob_label = bucket.blob(f"{annotation_location}/label-detection.json")
    data_label = json.loads(blob_label.download_as_string(client=None))
    # Get label annotations. The first result is retrieved because a single video was processed.
    label_annotation_results = data_label.get("annotation_results")[0]

    # Face Annotations
    blob_face = bucket.blob(f"{annotation_location}/face-detection.json")
    data_face = json.loads(blob_face.download_as_string(client=None))
    # Get face annotations. The first result is retrieved because a single video was processed.
    face_annotation_results = data_face.get("annotation_results")[0]

    # People Annotations
    blob_people = bucket.blob(f"{annotation_location}/people-detection.json")
    data_people = json.loads(blob_people.download_as_string(client=None))
    # Get people annotations. The first result is retrieved because a single video was processed.
    people_annotation_results = data_people.get("annotation_results")[0]

    # Shot Annotations
    blob_shot = bucket.blob(f"{annotation_location}/shot-detection.json")
    data_shot = json.loads(blob_shot.download_as_string(client=None))
    # Get logo annotations. The first result is retrieved because a single video was processed.
    shot_annotation_results = data_shot.get("annotation_results")[0]

    # Text Annotations
    blob_text = bucket.blob(f"{annotation_location}/text-detection.json")
    data_text = json.loads(blob_text.download_as_string(client=None))
    # Get text annotations. The first result is retrieved because a single video was processed.
    text_annotation_results = data_text.get("annotation_results")[0]

    # Logo Annotations
    blob_logo = bucket.blob(f"{annotation_location}/logo-detection.json")
    data_logo = json.loads(blob_logo.download_as_string(client=None))
    # Get logo annotations. The first result is retrieved because a single video was processed.
    logo_annotation_results = data_logo.get("annotation_results")[0]

    # Speech Annotations
    blob_speech = bucket.blob(f"{annotation_location}/speech-detection.json")
    data_speech = json.loads(blob_speech.download_as_string(client=None))
    # Get speech annotations. The first result is retrieved because a single video was processed.
    speech_annotation_results = data_speech.get("annotation_results")[0]

    return (
        label_annotation_results,
        face_annotation_results,
        people_annotation_results,
        shot_annotation_results,
        text_annotation_results,
        logo_annotation_results,
        speech_annotation_results,
    )
