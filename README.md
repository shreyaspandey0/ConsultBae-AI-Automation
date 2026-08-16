# ConsultBae AI Automation

Welcome to the **ConsultBae AI Automation** repository. This project handles various AI-driven automation workflows, custom agentic integrations, and helper scripts for ConsultBae operations.

## Repository Structure

The repository is organized as follows:

```text
ConsultBae-AI-Automation/
├── app/          # Web/frontend application files (e.g., custom UI dashboards or portals)
├── data/         # Data assets, local databases, mock files, or temporary run outputs
├── docs/         # Documentation, workflow designs, and system architectures
├── n8n/          # n8n workflows, custom nodes, and JSON exports
├── scripts/      # Standalone scripts (Python, JS, etc.) for utility and background jobs
├── src/          # Core backend logic, shared libraries, and API clients
├── tests/        # Unit, integration, and end-to-end test suites
└── README.md     # Project overview and documentation
```

## Getting Started

### Prerequisites

*   [Node.js](https://nodejs.org/) (v18+ recommended)
*   [Python](https://www.python.org/) (3.10+ recommended)
*   [n8n](https://n8n.io/) (for workflow execution)

### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-organization/ConsultBae-AI-Automation.git
    cd ConsultBae-AI-Automation
    ```
2.  **Environment Variables:**
    Copy the sample environment file (once available) and update it with the necessary API keys:
    ```bash
    cp .env.example .env
    ```

## Development and Workflows

*   **Custom Apps:** Located in [app/](file:///c:/Users/Shreyash%20Pandey/Desktop/ConsultBae-AI-Automation/app).
*   **n8n Workflows:** Save n8n JSON exports in [n8n/](file:///c:/Users/Shreyash%20Pandey/Desktop/ConsultBae-AI-Automation/n8n).
*   **Helper Scripts:** Add operational scripts to [scripts/](file:///c:/Users/Shreyash%20Pandey/Desktop/ConsultBae-AI-Automation/scripts).

## Stuck Log

### 1. Audio metadata and database schema mismatch

I initially faced an issue where the audio submission endpoint was using database column names that did not match the existing SQLite schema. The API returned a database error during submission.

I inspected the SQLite schema and compared it with the INSERT query. I also used AI assistance to understand the error and identify the mismatch. I rejected the idea of changing the database blindly because it could affect the existing data model. Instead, I aligned the API query and schema carefully and verified the result by submitting an actual audio file.

### 2. NumPy value could not be serialized by FastAPI

While returning the calculated audio loudness, FastAPI raised an error related to a NumPy float value that could not be serialized correctly.

I searched the error and asked AI about FastAPI JSON serialization of NumPy types. I considered changing the entire response structure but rejected that because the problem was specifically the NumPy value. I converted the calculated value to a native Python float before returning/storing it and tested the endpoint again.

### 3. Audio file caused UTF-8 decoding error

While testing the audio submissions listing, I encountered a UnicodeDecodeError because binary audio data was being treated as text.

I traced the error to the response handling rather than the audio-processing logic. I used debugging output and AI assistance to identify that the audio file itself should be served as binary data instead of being decoded as UTF-8. I corrected the audio-serving logic and verified the playback endpoint with an actual MP3 file.