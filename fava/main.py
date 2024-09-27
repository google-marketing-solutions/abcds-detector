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

import time
import json
import argparse

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig, Part, HarmCategory, HarmBlockThreshold
from google.api_core.exceptions import InternalServerError, ResourceExhausted

from bqflow.util.configuration import Configuration
from bqflow.util.auth import get_credentials
from bqflow.util.bigquery_api import BigQuery

RETRIES = 3
DATASET = 'FAVA'
MODEL = 'gemini-1.5-pro'
CONFIG = GenerationConfig(
  temperature=None,
  top_p=None,
  top_k=None,
  candidate_count=1,
  max_output_tokens=8192,
  seed=5
)

'''
This script is used to bulk analyze videos based on user specified features.
It combines a list of videos with a list of feature prompts to produce a CSV.

git clone https://github.com/google/bqflow
python3 -m pip install -r bqflow/requirements.txt
python3 -m pip install vertexai

export PYTHONPATH=$PYTHONPATH:$(pwd)/bqflow

python main.py prompt.json -u user.json -p gtech-kenjora -v

The prompt.json file has the following format:

{
  "prompt": "You are a creative expert who analyzes and labels video ads to answer specific questions about the content in the video and how it adheres to a set of features.  Only base your answers strictly on what information is available in the video attached. Do not make up any information that is not part of the video.",
  "videos":[
    "gs://bucket/video_1.mp4",
    "gs://bucket/video_2.mp4"
  ],
  "features": [
    { "feature": "Creative Style",
      "prompt": "What is the primary creative style that the ad is shot in?",
      "option": {
        "Animated": "The ad primarily uses animation or computer-generated imagery.",
        "Live Action": "The ad primarily features real people and settings."
      }
      "test":{
        "gs://bucket/video_1.mp4":"Live Action",
      }
    },
  ]
}

Use 'option' for a single answer, and 'options' for multiple possible responses.
The script will produce output as well as a CSV file with the results.
'''

def safely_generate_content(model, video, prompt):
  '''Makes a request to Gemini to get a prediction based on the provided prompt

  Args:
    model: a vertex model object
    video: a Parts object with the video
    prompt: a string with the prompt for model

  Returns:
    response.text: a string with the generated response
  '''
  for retry in range(RETRIES, 0, -1):
    try:
      response = model.generate_content(
        [video, prompt],
        safety_settings={
          HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
          HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
          HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
          HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        },
        generation_config=CONFIG,
        stream=False
      )
      return response.text.replace('"', '').replace('.', '').replace('\n', ' ').replace('*', '').strip()

    except InternalServerError as ex:
      if retry > 0:
        print(f'THROTTLE ERROR RETRY {retry}...')
        time.sleep(30)
      else:
        raise

    except ResourceExhausted as ex:
      if retry > 0:
        print(f'THROTTLE ERROR RETRY {retry}...')
        time.sleep(30)
      else:
        raise

    except AttributeError as ex:
      error_message = str(ex)
      if retry > 0 and 'Content has no parts' in error_message:
        print(f'ATTRIBUTE ERROR RETRY {retry}:', error_message)
        print(f'Error: {ex} Gemini might be blocking the response due to safety issues.\n')
        time.sleep(10)
      else:
        raise

    except Exception as ex:
      error_message = str(ex)
      if (retry > 0 and (
        '429 Quota exceeded' in error_message
        or '503 The service is currently unavailable' in error_message
        or '403' in error_message
      )):
        print(f'GENERAL EXCEPTION RETRY {retry}:', type(ex), str(ex))
        time.sleep(10)
      else:
        raise

  return ""

def main(prompts:dict, project:str, service:str, client:str, user:str, verbose:bool):
  '''Loops through videos and prompts and builds tag list.

  Args:
    prompts: a structure of videos and prompts
    project: the id of the Google Cloud Project
    service: a path to credentials
    client: a path to credentials
    user: a path to credentials
    verbose: to print output or not
  '''


  config = Configuration(
    project=project,
    service=service,
    client=client,
    user=user,
    verbose=verbose
  )

  # authenticate
  vertexai.init(
    project=config.project,
    location='us-central1',
    credentials=get_credentials(config, 'user')
  )

  with open(prompts, 'r') as file:
    features = json.load(file)

  rows = [('VIDEO', 'FEATURE', 'ANSWER', 'TRUTH', 'CORRECT')]
  for video_uri in features['videos']:
    print('\nVIDEO:', video_uri)

    video = Part.from_uri(uri=video_uri, mime_type="video/mp4")

    for feature in features['features']:

      model = GenerativeModel(MODEL)
      #model.generate_content([video, features['prompt']])

      # skip turned off
      if not 'feature' in feature: continue

      print('\nFEATURE:', feature['feature'])

      prompt = features['prompt']

      # single choice
      if 'option' in feature:
        prompt += f"\nPlease check the video for the following:"
        for option_name, option_details in feature['option'].items():
          prompt += f"\nRespond with feature '{option_name}' when the video has: {option_details}"
        prompt += f"\n\nRespond ONLY with one of the following labels: {', '.join(feature['option'].keys())}"
  
      # multiple choice
      elif 'options' in feature:
        prompt += f"\nFormat the response as a comma separated list. Please evaluate the video for each criteria and include all that apply:"
        for option_name, option_details in feature['options'].items():
          prompt += f"\nInclude '{option_name}' in the response list when the video has: {option_details}"
        prompt += f"\n\nRespond ONLY with labels from this list: {', '.join(feature['options'].keys())}"
  
      # execute prompt
      if verbose:
        print('PROMPT:', prompt)
  
      response = safely_generate_content(model, video, prompt)

      if 'option' in feature:
        truth = feature['test'].get(video_uri, '')
        correct = 1 if truth.lower() == response.lower() else 0
      elif 'options' in feature:
        truth = feature['test'].get(video_uri, [])
        correct = 1 if len(set(truth) & set(map(lambda r: r.strip(), response.split(',')))) > 0 else 0
        truth = ', '.join(truth) # just so the CSV stores comma values

      # show results
      if verbose:
        print('RESPONSE:', response)
        print('TRUTH:', truth)
        print('CORRECT:', int(correct * 100), '%')

      rows.append((
        prompts.replace('.json', ''),
        video_uri, feature['feature'],
        response,
        truth,
        correct
      ))

  BigQuery(config, 'user').datasets_create(
    project_id=config.project,
    dataset_id=DATASET,
    expiration_days=45
  )

  BigQuery(config, 'user').rows_to_table(
    project_id=config.project,
    dataset_id=DATASET,
    table_id='AI_' + prompts.rsplit('/', 1)[-1].replace('.json', '').title(),
    rows=rows,
    source_format='CSV',
    schema=[
      { "name": "Advertiser", "type": "STRING" },
      { "name": "Video_File", "type": "STRING" },
      { "name": "Feature", "type": "STRING" },
      { "name": "Value", "type": "STRING" },
      { "name": "Truth", "type": "STRING" },
      { "name": "Correct", "type": "FLOAT" }
    ],
    disposition='WRITE_TRUNCATE',
    header=True,
    wait=True
  )

if __name__ == '__main__':

  # load command line parameters
  parser = argparse.ArgumentParser()

  parser.add_argument('prompts', help='Prompt file to use, must be json.', default=None)
  parser.add_argument('--project', '-p', help='Cloud ID of Google Cloud Project.', default=None)
  parser.add_argument('--service', '-s', help='Path to SERVICE credentials json file.', default=None)
  parser.add_argument('--client', '-c', help='Path to CLIENT credentials json file.', default=None)
  parser.add_argument('--user', '-u', help='Path to USER credentials json file.', default=None)
  parser.add_argument('--verbose', '-v', help='Print all the steps as they happen.', action='store_true')
 
  main(**vars(parser.parse_args()))
