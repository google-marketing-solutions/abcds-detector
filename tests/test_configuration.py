"""Tests for configuration.py."""

import pytest
import models
from configuration import Configuration


class TestSetParameters:
    def test_gcs_provider_from_string(self):
        config = Configuration()
        config.set_parameters(
            project_id="p", project_zone="z", bucket_name="b",
            knowledge_graph_api_key="k", bigquery_dataset="d",
            bigquery_table="t", assessment_file="",
            extract_brand_metadata=True, use_annotations=False,
            use_llms=True, run_long_form_abcd=True, run_shorts=False,
            run_creative_intelligence=True, features_to_evaluate=[],
            creative_provider_type="GCS", verbose=False,
        )
        assert config.creative_provider_type == models.CreativeProviderType.GCS

    def test_youtube_provider_from_string(self):
        config = Configuration()
        config.set_parameters(
            project_id="p", project_zone="z", bucket_name="b",
            knowledge_graph_api_key="k", bigquery_dataset="d",
            bigquery_table="t", assessment_file="",
            extract_brand_metadata=True, use_annotations=False,
            use_llms=True, run_long_form_abcd=True, run_shorts=False,
            run_creative_intelligence=True, features_to_evaluate=[],
            creative_provider_type="YOUTUBE", verbose=False,
        )
        assert config.creative_provider_type == models.CreativeProviderType.YOUTUBE

    def test_api_key_stripped(self):
        config = Configuration()
        config.set_parameters(
            project_id="p", project_zone="z", bucket_name="b",
            knowledge_graph_api_key="  key_with_spaces  ",
            bigquery_dataset="", bigquery_table="", assessment_file="",
            extract_brand_metadata=False, use_annotations=False,
            use_llms=True, run_long_form_abcd=True, run_shorts=False,
            run_creative_intelligence=False, features_to_evaluate=[],
            creative_provider_type="GCS", verbose=False,
        )
        assert config.knowledge_graph_api_key == "key_with_spaces"

    def test_zone_defaults_to_us_central(self):
        config = Configuration()
        config.set_parameters(
            project_id="p", project_zone=None, bucket_name="b",
            knowledge_graph_api_key="", bigquery_dataset="", bigquery_table="",
            assessment_file="", extract_brand_metadata=False,
            use_annotations=False, use_llms=True, run_long_form_abcd=True,
            run_shorts=False, run_creative_intelligence=False,
            features_to_evaluate=[], creative_provider_type="GCS", verbose=False,
        )
        assert config.project_zone == "us-central1"


class TestSetVideos:
    def test_list_input(self):
        config = Configuration()
        config.set_videos(["gs://a/1.mp4", "gs://a/2.mp4"])
        assert len(config.video_uris) == 2

    def test_string_input(self):
        config = Configuration()
        config.set_videos("gs://a/1.mp4, gs://a/2.mp4")
        assert len(config.video_uris) == 2
        assert config.video_uris[0].strip() == "gs://a/1.mp4"

    def test_single_string(self):
        config = Configuration()
        config.set_videos("gs://a/video.mp4")
        assert config.video_uris == ["gs://a/video.mp4"]


class TestSetBrandDetails:
    def test_parses_csv(self):
        config = Configuration()
        config.set_brand_details(
            brand_name="Acme",
            brand_variations="Acme, ACME, acme",
            products="Widget, Gadget",
            products_categories="tools, electronics",
            call_to_actions="Buy now, Shop",
        )
        assert config.brand_name == "Acme"
        assert len(config.brand_variations) == 3
        assert len(config.branded_products) == 2
        assert len(config.branded_call_to_actions) == 2

    def test_empty_strings(self):
        config = Configuration()
        config.set_brand_details("Brand", "", "", "", "")
        assert config.brand_variations == []
        assert config.branded_products == []


class TestSetLLMParams:
    def test_sets_model_and_generation_config(self):
        config = Configuration()
        config.set_llm_params(
            llm_name="gemini-2.5-pro",
            location="us-central1",
            max_output_tokens=8192,
            temperature=0.5,
            top_p=0.9,
        )
        assert config.llm_params.model_name == "gemini-2.5-pro"
        assert config.llm_params.location == "us-central1"
        assert config.llm_params.generation_config["max_output_tokens"] == 8192
        assert config.llm_params.generation_config["temperature"] == 0.5
