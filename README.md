# aguefort

:game_die: A chatbot for asking about D&amp;D tips powered by Dropout's Adventuring Academy knowledge and LLMs.

## Prerequisites

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
