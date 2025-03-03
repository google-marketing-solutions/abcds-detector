Copyright 2024 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

# Disclaimer

ABCDs Detector is NOT an official Google product.

# ABCDs Detector

The ABCDs Detector solution streamlines the assessment of your video ads against YouTube's ABCD framework. Powered by Google AI, this tool automates the evaluation process, providing detailed reports on how well your ads align with key attention-driving metrics. Simplify your YouTube ad analysis and gain valuable insights for optimization with the ABCDs Detector.

## The Approach

### Overview

The solution leverages:

**Video content annotation:** Google AI extracts features and identifies key moments within your video ads.

**Large Language Model (LLM) integration:** LLMs are used to assess features against YouTube's ABCD framework rubrics. This enables the detector to "ask questions" and determine if the ad adheres to each rubric.

By combining these techniques, ABCDs Detector automates the evaluation process and delivers comprehensive reports on how well your ads align with the ABCD framework. This empowers you to optimize your YouTube ad campaigns for maximum impact.

### Detailed approach

1. Video Intelligence API: To get annotations for the following features:
  - Label annotations
  - Face annotations
  - Text annotations
  - Object annotations
  - People annotations
  - Speech annotations
  - Shot annotations
  - Logo annotations


2. Gemini 1.5 Pro: To perform video Q&A about the features to evaluate if the video adheres to the ABCD rubrics. The colab will send a request to Gemini with tailored prompts to evaluate each rubric.

ABCDs Detector will perform 2 verifications, first with annotations and then with LLMs. Since the LLM approach is prone to hallucinations, False Positives or False Negatives will be expected. The solution will still require human QA if 100% accuracy is required for the evaluation.

ABCDs Detector MVP supports a single video evaluation for the following features/rubrics:
  - Quick Pacing
  - Quick Pacing (First 5 seconds)
  - Dynamic Start
  - Supers
  - Supers with Audio
  - Brand Visuals
  - Brand Visuals (First 5 seconds)
  - Brand Mention (Speech)
  - Brand Mention (Speech) (First 5 seconds)
  - Product Visuals
  - Product Visuals (First 5 seconds)
  - Product Mention (Text)
  - Product Mention (Text) (First 5 seconds)
  - Product Mention (Speech)
  - Product Mention (Speech) (First 5 seconds)
  - Visible Face (First 5 seconds)
  - Visible Face (Close Up)
  - Presence of People
  - Presence of People (First 5 seconds)
  - Overall Pacing
  - Audio Speech Early
  - Call To Action (Text)
  - Call To Action (Speech)

For a definition for each of these signals please take a look at the [features.py](https://github.com/google-marketing-solutions/abcds-detector/blob/main/feature_configs/features.py) file.

The final result of the assessment (Excellent, Might Improve or Needs Review) is defined in the [generics_helpers.py](https://github.com/google-marketing-solutions/abcds-detector/blob/main/helpers/generic_helpers.py?plain=1#L186) and can be customized based on preferences.

### Google Cloud Cost breakdown

1. Video Intelligence API: Prices are per minute. Partial minutes are rounded up to the next full minute. Volume is per month. For more details please check the official [documentation](https://cloud.google.com/video-intelligence/pricing).

2. Gemini 1.5 Pro: With the Multimodal models in Vertex AI, you can input either text or media (images, video). Text input is charged by every 1,000 characters of input (prompt) and every 1,000 characters of output (response). Characters are counted by UTF-8 code points and white space is excluded from the count. Prediction requests that lead to filtered responses are charged for the input only. At the end of each billing cycle, fractions of one cent ($0.01) are rounded to one cent. Media input is charged per image or per second (video). For more details please check the official documentation: https://cloud.google.com/vertex-ai/generative-ai/pricing

For questions, please reach out to: abcds-detector@google.com

## Requirements
Please esure you have access to all of the following before starting:
* [Google Cloud Project](https://cloud.google.com) with enabled APIs:
    * [Video Intelligence API](https://console.cloud.google.com/marketplace/product/google/videointelligence.googleapis.com) - Optional if you are only using LLMs.
    * [Vertex AI API](https://console.cloud.google.com/marketplace/product/google/aiplatform.googleapis.com) - Optional if you are only using Annotations.
    * [Knowledge Graph API](https://console.cloud.google.com/marketplace/product/google/kgsearch.googleapis.com) - Optional if you are only using LLMs.
    * [Cloud Storage API](https://console.cloud.google.com/marketplace/product/google/storage.googleapis.com)
    * [BigQuery](https://cloud.google.com/bigquery/docs/reference/rest) - Optional if you don't want to store the results in BQ.
* [API Key](https://cloud.google.com/docs/authentication/api-keys) provisioned. - Optional if you are only using LLMs.
* [Project Billing](https://cloud.google.google.com/billing/) enabled.
* Python libraries:
    * `google-cloud-videointelligence`
    * `google-cloud-aiplatform`
* FFMPEG (not needed for colab)
  * Save the platform specific [FFMPEG Binary](https://evermeet.cx/ffmpeg/) locally.
  * Set the **IMAGEIO_FFMPEG_EXE** variable to the FFMPEG binary path.

You can see more on the ABCD methodology [here.](https://www.thinkwithgoogle.com/intl/en-emea/future-of-marketing/creativity/youtube-video-ad-best-practices/)

## Where to start?

1. Navigate to [colab.research.google.com](http://colab.research.google.com).
2. In the dialog, open a Notebook from GitHub.
3. Enter the url from this page.

**Note:** This repository provides python modules that can be executed on local machines for easier debugging and troubleshooting.

## Instructions
Please follow the steps below before executing the ABCDs Detector solution. Every **[VARIABLE]** is a parameter you can configure in the **Define ABCDs Detector Parameters** section.

1. Store your videos on [Google Cloud Storage](https://console.cloud.google.com/storage/browser) with the following folder structure:
  * **[BUCKET_NAME]** - name of bucket, ensure you have write permission. Same as paramter below.
    * **[brand_name]** - a folder, must be same as parameter below.
      * **videos** - a folder called videos, hard coded. Consider only **10-15 videos max** due to processing time limitations.
        * **some_video.mp4** - upload video to analyze, must be **mp4** and must be **[<= 50 MB](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models)**.
      * **annotations** - a folder created by this tool to store AI data. No need to create this.

1. Make sure the requirements are met:
  * Enable APIs:
    * [Video Intelligence API](https://console.cloud.google.com/marketplace/product/google/videointelligence.googleapis.com)
    * [Vertex AI API](https://console.cloud.google.com/marketplace/product/google/aiplatform.googleapis.com)
    * [Knowledge Graph API](https://console.cloud.google.com/marketplace/product/google/kgsearch.googleapis.com)
    * [Cloud Storage API](https://console.cloud.google.com/marketplace/product/google/storage.googleapis.com)
    * [BigQuery](https://console.cloud.google.com/marketplace/product/google/bigquery.googleapis.com)
  * Provision [An API Key](https://cloud.google.com/docs/authentication/api-keys):
    1. Visit [Credentials Page](https://cloud.console.google.com/apis/credentials).
    1. Create a **New API Key** and copy it into **[KNOWLEDGE_GRAPH_API_KEY]** below.
    1. We recommend editing and restricting the key to the above APIs.

1. Define all the parameters.
  * Required:
    * Google Cloud Project Details
    * Brand And Product Details
  * Optional
    * Solution Setup
    * ABCD Framework Details
    * LLM Configuration

1. Run all of the steps in sequence.
  * Some steps do not produce output, they only define functions.
  * If a step asks you to **Restart Runtime**, do so.
  * If a step displays an error, stop and debug it. Debug the following:
    * APIs are enabled.
    * Storage bucket is correctly configured.
    * The video is the correct size.
    * API Key has correct restrictions.
    * Previous colab sections completed.
    * Select _Runtime > Reset Session and Run All_ as a last resort.
  * The **Execute Bulk ABCD Assessment** produces the video analysis.

1. For questions, please reach out to: abcds-detector@google.com

**Note:** Please check the official [Gemini API documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini) to learn more about the LLM parameters (temperature, top_k, top_p, etc) that are used in this colab.

## Customization:

* Change the default parameters used for the ABCDs detection.
* Modify the ABCDs signals detection logic to fit yours.
* Add or remove ABCDs signals.
* Specify your own logic for calculating ABCDs score per video.
* ABCD features are dynamically added to a JSON list. If you want to add/remove features, please do that directly in the features_config/features.py file.
* To optimize LLM execution, features support grouping by 'full_video' and 'first_5_secs_video'. If you want to execute the features separately, please specify 'no_grouping' in the "group_by" field. 

**Note:**

* This notebook is a starting point and can be further customized to fit your specific needs.

## Roadmap

1. Improvement: cut the video in shorter segments to improve LLM accuracy.
2. Improvement: leverage a [consensus approach](https://arxiv.org/pdf/2310.20151.pdf) to increase response confidence.

## Additional Resources:

* [Google Video Intelligence API](https://cloud.google.com/video-intelligence?hl=en)
* [Vertex AI](https://cloud.google.com/vertex-ai)
* [ABCD Framework best practices](https://www.thinkwithgoogle.com/intl/en-emea/future-of-marketing/creativity/youtube-video-ad-best-practices/)
