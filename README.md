## ABCDs Detector

This notebook generates 12 ABCDs signals for the provided videos in a given Google Cloud Storage Bucket. For each video it sends an API call to the [Video Intelligence API](https://cloud.google.com/video-intelligence?hl=en), only if not proccessed before, and produces 12 ABCDs signals for each video and stores them in an output file in json format on Google Cloud Storage. This file can be easily loaded into BigQuery for further processing.

**Requirements:**

* Google Cloud Project with enabled APIs:
    * [Video Intelligence API](https://cloud.google.com/video-intelligence?hl=en)
    * Vertex AI
* Project Billing enabled
* Python libraries:
    * `google-cloud-videointelligence`
    * `google-cloud-aiplatform`

**Features:**

Detection of the following 12 ABCD signals:

* Attract: Face Early
* Attract: Pace Quick
* Attract: Dynamic Start
* Brand: Logo Big
* Brand: Logo Early
* Brand: Product Early
* Brand: Name Early
* Connect: Face Close
* Connect: Overall Pacing
* Direct: Audio Early
* Direct: Call to Action (speech)
* Direct: Call to Action (text on screen)

You can see more on the ABCD methodology [here](https://www.thinkwithgoogle.com/intl/en-emea/future-of-marketing/creativity/youtube-video-ad-best-practices/)

## Where to start?

1. Navigate to [colab.research.google.com](http://colab.research.google.com)
2. In the dialog, open a Notebook from GitHub
3. Enter the url from this page

**How to use:**

1. Create 2 Google Cloud Storage Buckets (one for input, one for output, if not existing) and add your videos in the input one.
3. Install the required Python libraries.
4. Run all the installation steps in the notebook.
5. Specify all the parameters as desired in the "parameters" cell, making sure the buckets name matched with the one created in step one.
6. Run the remaining of the cells in the notebook.
7. Check the output file in Google Cloud Storage: "final_abcd_report.json".
8. (Optional) Load the json file into BigQuery for further analysis.

**Customization:**

* Change the default parameters used for the ABCDs detection.
* Modify the ABCDs signals detection logic to fit yours.
* Add or remove ABCDs signals.
* Specify your own logic for calculating ABCDs score per video.

**Note:**

* This notebook is a starting point and can be further customized to fit your specific needs.

**Additional Resources:**

* Google Video Intelligence API: [https://cloud.google.com/video-intelligence](https://cloud.google.com/video-intelligence?hl=en)
* Vertex AI: [https://cloud.google.com/vertex-ai](https://cloud.google.com/vertex-ai)
* ABCDs: [youtube-video-ad-best-practices](https://www.thinkwithgoogle.com/intl/en-emea/future-of-marketing/creativity/youtube-video-ad-best-practices/)
