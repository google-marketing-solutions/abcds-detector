# Disclaimer

FAVA is NOT an official Google product.

# Freeform AI Video Analysis (FAVA)

This project provides a framework for analyzing video content using Google's Gemini Flash Model, designed to be scalable and user-friendly for marketing teams.

It also incorporates a dashboard that helps evaluate the prompts against manually tagged (requires user tagging) videos.

## The Challenge

Marketing teams often need to analyze videos for various qualitative criteria, both generic and advertiser-specific. This process can be time-consuming and inefficient when done manually.
This code shows how to both prompt and evaluate the prompts.  We recommend having a subset of manually reviewed videos to test the prompts against.

1. Create feature prompts, run the tool, get scores against the manual tests, and improve.
2. Run the feature prompts against a new group of videos to get insights.
3. Consult with advertiser brand managers on features to include.
4. Connect KPIs with the features to determine importance in future creatives.

## The Solution

FAVA leverages the power of Google's Gemini Model to automate video analysis. It focuses on:

* **Advertiser Specificity:**  Uses JSON configuration files to store prompts and video assets, allowing customization for advertisers.
* **Video Scale:**  Enforces deterministic answers (labels) in prompts to enable processing of multiple videos with consistent criteria.
* **Exporting AI Results:**  Integrates with BQFlow for streamlined data export and flexibility in output destinations.
* **Ease of Use:**  Provides a single Python script for easy implementation and understanding.

## How It Works

1. **Videos** - Upload videos to Google Cloud Storage and copy their URIs.
1. **Prompts** - Create prompt file like [google_pixel.json](google_pixel.json). 
   1. Add video URIs.
   1. Add features.
      1. option - will generate a prompt asking for one answer from the list.
      1. options - will generate a prompt asking for possibly multiple answer.
   1. Test entry will associate a manually reviewed answer for each video that the AI can be compared against.
1. Run main.py or colab.ipyn.
1. A **FAVA** dataset is written to BigQuery.
1. Connect the [Looker Studio Dashboard](https://lookerstudio.google.com/c/u/0/reporting/e31cdc17-8377-42f5-a9ba-cee27202fcc4/) and check scores.
1. Update the prompts to improve scores, or use the AI generated answers in your system.

## Install And Run

BQFlow is used for authentication and writing the results to BigQuery.

```
git clone https://github.com/google/bqflow
python3 -m pip install -r bqflow/requirements.txt
export PYTHONPATH=$PYTHONPATH:$(pwd)/bqflow

python bqflow/auth.py -h
python bqflow/auth.py -c client.json -u user.json
```

The FAVA script uses the same requirements as ABCD Detector.

```
git clone -branch paul_changes https://github.com/google-marketing-solutions/abcds-detector
python3 -m pip install -r abcds-detector/requirements.txt

python main.py google_pixel.json -u user.json -p gcp-project-id -v
```
