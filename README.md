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


2. Gemini Pro Vision & Gemini Pro: To perform video Q&A about the features to evaluate if the video adheres to the ABCD rubrics. The colab will send a request to Gemini with tailored prompts to evaluate each rubric.

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

### Google Cloud Cost breakdown

1. Video Intelligence API: Prices are per minute. Partial minutes are rounded up to the next full minute. Volume is per month. For more details please check the official [documentation](https://cloud.google.com/video-intelligence/pricing).

2. Gemini Pro Vision & Gemini Pro: With the Multimodal models in Vertex AI, you can input either text or media (images, video). Text input is charged by every 1,000 characters of input (prompt) and every 1,000 characters of output (response). Characters are counted by UTF-8 code points and white space is excluded from the count. Prediction requests that lead to filtered responses are charged for the input only. At the end of each billing cycle, fractions of one cent ($0.01) are rounded to one cent. Media input is charged per image or per second (video). For more details please check the official documentation: https://cloud.google.com/vertex-ai/generative-ai/pricing

For questions, please reach out to: abcds-detector@google.com

## Requirements:

* Google Cloud Project with enabled APIs:
    * [Video Intelligence API](https://cloud.google.com/video-intelligence?hl=en)
    * [Vertex AI API](https://cloud.google.com/vertex-ai/docs/reference)
    * [Knowledge Graph API](https://developers.google.com/knowledge-graph)
* Project Billing enabled
* Python libraries:
    * `google-cloud-videointelligence`
    * `google-cloud-aiplatform`

You can see more on the ABCD methodology [here.](https://www.thinkwithgoogle.com/intl/en-emea/future-of-marketing/creativity/youtube-video-ad-best-practices/)

## Where to start?

1. Navigate to [colab.research.google.com](http://colab.research.google.com).
2. In the dialog, open a Notebook from GitHub.
3. Enter the url from this page.

**Note:** This repository provides python modules that can be executed on local machines for easier debugging and troubleshooting.
If you make any changes to the modules and plan to update your colab, please make sure to remove the sections that are marked
as ### REMOVE FOR COLAB - START and ### REMOVE FOR COLAB - END, since those are ONLY required when running the code locally.


## Solution Setup

Please follow the steps below before executing the ABCDs Detector solution.

1. Store your videos on Google Cloud Storage with the following folder structure: bucket_name/brand_name/videos/my_video.mp4. For example: abcd-detector/Nike/videos/my_video.mp4. The brand_name should be the same as defined in the **"Define Brand & Videos Details"** section below.
  - **Video considerations:**
    - Due to LLM limits, the videos should be <= 7 MB. Please see more information [here](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models).
    - Videos should be mp4 format.
    - Video annotations are stored in GCS under bucket_name/brand_name/annotations/video_name/annotation.json
    - Due to Google Colab limitations (free version) and since this is a reference implementation, consider using it for 10-15 videos max per brand.

2. Follow steps in the colab:

    2.1. Enable the Video Intelligence API, Vertex AI API, Knowledge Graph API and make sure that your user has access to Google Cloud Storage buckets.

    2.2. Generate an API Key to connect to the Knowledge Graph API to find entities such as brands, products, etc., to match with video annotation results. To generate an API key, please follow the steps [here.](https://support.google.com/googleapi/answer/6158862?hl=en)

    2.5. Fill out the project details, brand/video details and ABCD Assessment thresholds in the **"Define ABCDs Detector parameters"** section below. For brand and product details, you can be as generic or specific as possible depending on your video asset.

    **Note:** Please check the official [Gemini API documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini) to learn more about the LLM parameters (temperature, top_k, top_p, etc) that are used in this colab.

## Customization:

* Change the default parameters used for the ABCDs detection.
* Modify the ABCDs signals detection logic to fit yours.
* Add or remove ABCDs signals.
* Specify your own logic for calculating ABCDs score per video.

**Note:**

* This notebook is a starting point and can be further customized to fit your specific needs.

## Roadmap

1. Improvement: cut the video in shorter segments to improve LLM accuracy.
2. Improvement: leverage a [consensus approach](https://arxiv.org/pdf/2310.20151.pdf) to increase response confidence.

## Additional Resources:

* [Google Video Intelligence API](https://cloud.google.com/video-intelligence?hl=en)
* [Vertex AI](https://cloud.google.com/vertex-ai)
* [ABCD Framework best practices](https://www.thinkwithgoogle.com/intl/en-emea/future-of-marketing/creativity/youtube-video-ad-best-practices/)