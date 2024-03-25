# aguefort

:game_die: A chatbot for asking about D&amp;D tips powered by Dropout's Adventuring Academy knowledge and LLMs.

## Prerequisites

- AWS Account
- Docker
- Poetry

## Downloading Adventuring Academy Data

1. Clone `dropout-dl` repo: `git clone https://github.com/mosswg/dropout-dl.git`
2. Build Docker image: `cd dropout-dl && docker build -t dropout-dl:latest .`
3. Remove the `dropout-dl` repo, it's no longer needed: `cd .. && rm -rf dropout-dl`
4. Clone `aguefort` repo: `git clone https://github.com/rey-allan/aguefort.git`
5. Install all dependencies and create virtual environment: `poetry install && poetry shell`
6. Create `login` file at the root of the repo with your Dropout email and password, one per line
   ```
   email@example.com
   123456789
   ```
7. Run the script: `python3 scripts/download_captions.py`
8. Go grab a coffee while the script runs, it will take some time
9. Captions will be saved to `data/captions` in the format `season-episode_number.vtt`

## Generating the Knowledge Base

> **Note:** Make sure to download the Adventuring Academy data before (see above)!

1. Run the script: `python3 scripts/generate_kb.py`
2. Go to sleep while the script runs, it will take a long time
3. Knowledge base will be saved to `data/adventuring_academy_kb`

## Running the App

> **Note:** Make sure to generate the knowledge base before (see above)!

1. Request access to Claude family of models via Bedrock in your AWS Account
   - Make sure to specify your use of these models will be for personal projects _only_
   - Access should be granted in a few minutes
2. Create an IAM user in your AWS Account with the `AmazonBedrockFullAccess` policy attached to it, and note down your **access** and **secret** keys
3. Create an `.env` file inside `app/` folder with the following keys:
   ```
   AWS_ACCESS_KEY_ID=<YOUR_ACCESS_KEY>
   AWS_SECRET_ACCESS_KEY=<YOUR_SECRET_KEY>
   AWS_REGION=<REGION_WITH_BEDROCK_ACCESS>
   ```
4. Run the app: `python3 app/app.py`
5. Open the app in your favorite browser, the default URL should look like this: `http://127.0.0.1:7860`
6. Enjoy!
