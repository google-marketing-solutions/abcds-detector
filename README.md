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

# ABCD Detector

The ABCD Detector solution offers a streamlined solution for understanding how video ads align with key metrics within the YouTube ABCD framework. Powered by Google AI, the tool leverages a data-driven and AI analysis to automate the ABCD assessment, providing a comprehensive report of adherence across a collection of defined features.

## The Approach & Design

### Overview
ABCD Detector leverages the latest Google AI to annotate video content and to ‘ask questions’ to LLMs regarding specific ABCD rubrics or features to evaluate if the video complies with such rubrics.

### Detailed approach
ABCD Detector uses 2 approaches to evaluate ABCD rubrics:

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
ABCD Detector will perform 2 verifications, first with annotations and then with LLMs. Since the LLM approach is prone to hallucinations, False Positives or False Negatives will be expected. The solution will still require human QA if 100% accuracy is required for the evaluation.
ABCD Detector MVP supports a single video evaluation for the following features/rubrics:
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

1. Video Intelligence API: Prices are per minute. Partial minutes are rounded up to the next full minute. Volume is per month. For more details please check the official documentation: https://cloud.google.com/video-intelligence/pricing

2. Gemini Pro Vision & Gemini Pro: With the Multimodal models in Vertex AI, you can input either text or media (images, video). Text input is charged by every 1,000 characters of input (prompt) and every 1,000 characters of output (response). Characters are counted by UTF-8 code points and white space is excluded from the count. Prediction requests that lead to filtered responses are charged for the input only. At the end of each billing cycle, fractions of one cent ($0.01) are rounded to one cent. Media input is charged per image or per second (video). For more details please check the official documentation: https://cloud.google.com/vertex-ai/generative-ai/pricing

For questions, please reach out to: anaesqueda@google.com, nnajdova@google.com

## Requirements:

* Google Cloud Project with enabled APIs:
    * [Video Intelligence API](https://cloud.google.com/video-intelligence?hl=en)
    * Vertex AI
* Project Billing enabled
* Python libraries:
    * `google-cloud-videointelligence`
    * `google-cloud-aiplatform`

You can see more on the ABCD methodology [here.](https://www.thinkwithgoogle.com/intl/en-emea/future-of-marketing/creativity/youtube-video-ad-best-practices/)

## Where to start?

1. Navigate to [colab.research.google.com](http://colab.research.google.com).
2. In the dialog, open a Notebook from GitHub.
3. Enter the url from this page.


## Solution Setup

Please follow the steps below before executing the ABCD Detector solution.

1. Store your videos on Google Cloud Storage with the following folder structure: bucket_name/brand_name/videos/my_video.mp4. For example: abcd-detector/Nike/videos/my_video.mp4. The brand_name should be the same as defined in the **"Define Brand & Videos Details"** section below.
  - **Video considerations:**
    -  Due to LLM limits, the videos should be <= 7 MB.
    - Videos should be mp4 format.
    - Video annotations are stored in GCS under bucket_name/brand_name/annotations/video_name/annotation.json
    - Due to Google Colab limitations (free version) and since this is a reference implementation, consider using it for 10-15 videos max per brand.

2. Follow steps in the colab:

    2.1. Enable the Vertex AI API and make sure that your user has access to Google Cloud Storage buckets.

    2.2. Add your Google Cloud project id in the **"Perform colab authentication"** section.

    2.3. (Optional) Enable the "Verbose" option on the **"Load helper function"** section if you want to see more logs.

    2.4. Generate an API Key to connect to the Knowledge Graph API to find entities such as brands, products, etc., to match with video annotation results. To generate an API key, please follow the steps here: https://support.google.com/googleapi/answer/6158862?hl=en

    2.5. Fill out the brand and video details in the **"Define Brand & Videos Details"** section below. For brand and product details, you can be as generic or specific as possible depending on your video asset.

    2.6. Fill out the ABCD Detector thresholds in the **"ABCD Assessment Thresholds"** section below.

## Customization:

* Change the default parameters used for the ABCDs detection.
* Modify the ABCDs signals detection logic to fit yours.
* Add or remove ABCDs signals.
* Specify your own logic for calculating ABCDs score per video.

**Note:**

* This notebook is a starting point and can be further customized to fit your specific needs.

## Roadmap

1. Improvement: cut the video in shorter segments to improve LLM accuracy.
2. Improvement: leverage a consensus approach: https://arxiv.org/pdf/2310.20151.pdf to increase response confidence.

## Additional Resources:

* Google Video Intelligence API: [https://cloud.google.com/video-intelligence](https://cloud.google.com/video-intelligence?hl=en)
* Vertex AI: [https://cloud.google.com/vertex-ai](https://cloud.google.com/vertex-ai)
* ABCDs: [youtube-video-ad-best-practices](https://www.thinkwithgoogle.com/intl/en-emea/future-of-marketing/creativity/youtube-video-ad-best-practices/)