# GEMINI.md - Project Manual

This document provides a comprehensive overview of the "Podcastfy" project, its architecture, and instructions for building, running, and developing it.

## 1. Project Overview

This is a Python-based podcast generation system that transforms various content sources (text files, URLs, PDFs, YouTube videos) into a natural, multi-speaker conversational podcast.

The system's core is a highly configurable, three-step workflow:
1.  **Generate Script:** A script is generated from the source material using the `podcastfy` library and a Gemini Large Language Model (LLM).
2.  **Embed Tags:** A second LLM pass intelligently embeds Text-to-Speech (TTS) emotion and SSML tags (e.g., `[happy]`, `[PAUSE=1s]`) into the script. This step is designed to make the final audio sound more expressive and natural.
3.  **Generate Audio:** The final audio file is generated from the tagged script using the Gemini Multi-Speaker TTS API.

A key feature is the six-level English proficiency setting (A1 to C2) defined in `podcast_config.yaml`. This setting dynamically adjusts the vocabulary, complexity, conversational style, and even the TTS tagging strategy for the generated podcast.

### Key Technologies
*   **Language:** Python
*   **Core Libraries:** `podcastfy`, `google-generativeai`, `python-dotenv`, `pyyaml`
*   **APIs:** Google Gemini (for script generation, tag embedding, and TTS)
*   **Configuration:** The entire workflow is driven by a central `podcast_config.yaml` file.

## 2. Building and Running

### 2.1. Initial Setup

1.  **Run the setup script:** This script will check for dependencies (`ffmpeg`), create a Python virtual environment, and install all required packages.
    ```bash
    bash setup.sh
    ```
2.  **Activate the virtual environment:**
    ```bash
    source venv/bin/activate
    ```
3.  **Set API Key:** Create a `.env` file in the root directory and add your Gemini API key.
    ```
    GEMINI_API_KEY=YOUR_API_KEY
    ```

### 2.2. Configuration

All settings are managed in `podcast_config.yaml`. To generate a podcast, you typically need to configure:
1.  `basic.english_level`: Set the desired proficiency level (e.g., "A1", "B2", "C1").
2.  `basic.podcast_length`: Set the target length (e.g., "short", "medium", "long").
3.  `input.sources`: Provide a list of content sources (URLs, file paths, etc.).

### 2.3. Running the Workflow

The main entry point is `podcast_workflow.py`, which offers several execution modes.

*   **Development Mode (Recommended for testing):**
    Runs the three steps (script, tags, audio) sequentially, pausing for user confirmation before each step. This allows for inspection and debugging.
    ```bash
    python podcast_workflow.py --mode dev
    ```

*   **Production Mode:**
    Runs all three steps automatically without pausing.
    ```bash
    python podcast_workflow.py --mode prod
    ```

*   **Custom Mode (For specific tasks):**
    Allows for running specific steps. For example, to regenerate audio from an existing script:
    ```bash
    python podcast_workflow.py --mode custom --steps audio --script-dir ./output/scripts/script_20250821_...
    ```

### 2.4. Testing

*   To test the connection to the Gemini API:
    ```bash
    python test_api.py
    ```
*   To test various TTS generation modes:
    ```bash
    bash test_all_modes.sh
    ```

## 3. Development Conventions

*   **Modular Architecture:** The project is divided into single-responsibility scripts:
    *   `generate_script.py`: Script creation.
    *   `embed_tags.py`: Intelligent TTS tag insertion.
    *   `generate_audio.py`: TTS audio generation.
    *   `podcast_workflow.py`: Main controller that orchestrates the process.

*   **Configuration-Driven:** Logic is heavily driven by `podcast_config.yaml`. This allows for easy modification of the output without changing Python code. The YAML file is extensively documented.

*   **Organized Outputs:** All generated assets (scripts, tagged scripts, audio) are saved into uniquely timestamped directories within the `output/` folder. Each run's metadata is saved as a `metadata.json` file in the corresponding output directory.

*   **Virtual Environment:** Development relies on a Python virtual environment managed by `venv`, as established in the `setup.sh` script.

*   **Documentation:** The project contains detailed documentation in both English (`README.md`) and Chinese (`LLM標籤嵌入系統實施計劃.md`), explaining the architecture, usage, and design principles.
