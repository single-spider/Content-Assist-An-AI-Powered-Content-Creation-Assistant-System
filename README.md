# Content-Assist-An-AI-Powered-Content-Creation-Assistant-System


A versatile desktop application designed to streamline your writing process with the power of generative AI. Built with Python and CustomTkinter, this tool provides a structured environment for writers, developers, and content creators to organize their work, generate new ideas, and refine existing text.

![AI Content Assistant Screenshot](https://raw.githubusercontent.com/single-spider/Content-Assist-An-AI-Powered-Content-Creation-Assistant-System/main/images/demo.png)
*(It's highly recommended to replace the link above with an actual screenshot or GIF of your application in action!)*

---

## ✨ Core Features

*   **🗂️ Project-Based Organization**:
    *   Structure your work into **Folders** and **Pages**.
    *   Save and load entire projects, keeping all your content in a single, portable `.json` file.
    *   Automatic, timestamped backups are created on startup to prevent data loss.

*   **🤖 Powerful AI Integration**:
    *   Connects to major AI providers: **Google AI (Gemini)** and **OpenRouter**.
    *   Securely manage multiple API keys for different providers or projects.
    *   Dynamically fetch and select from a list of available AI models.
    *   Create and customize **AI Functions** (system prompts) tailored to your specific needs (e.g., "Summarize", "Generate Dialogue", "Fix Grammar").
    *   Run AI functions on an entire page or just a selected block of text.
    *   Use the **References** feature to provide the AI with extra context from other pages.

*   **✍️ Rich Text Editing**:
    *   A clean, focused writing workspace.
    *   Basic formatting tools: **Bold**, *Italic*, and <u>Underline</u>.
    *   Live word count for the page and current selection.

*   **🎨 Modern & Customizable UI**:
    *   Built with the modern **CustomTkinter** framework.
    *   Supports System, Light, and Dark appearance modes.
    *   Intuitive layout with a navigator sidebar, function bar, and status bar.
    *   Search functionality to quickly find content across all your pages.

---

## 🚀 Getting Started

Follow these steps to get the AI Content Assistant running on your local machine.

### 1. Prerequisites

*   Python 3.8 or newer.
*   An API key from [Google AI Studio](https://makersuite.google.com/app/apikey) or [OpenRouter.ai](https://openrouter.ai/keys).

### 2. Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/single-spider/Content-Assist-An-AI-Powered-Content-Creation-Assistant-System.git
    cd Content-Assist-An-AI-Powered-Content-Creation-Assistant-System
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required dependencies:**
    Create a file named `requirements.txt` in the project root with the following content:
    ```
    customtkinter
    google-generativeai
    requests
    Pillow
    ```
    Then, install the packages:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up the `icons` folder:**
    The application requires an `icons` folder in the same directory as the script.
    *   Create a folder named `icons`.
    *   Place the necessary `.png` icon files inside it. The required icons are listed in the script and include:
        `add.png`, `bold.png`, `clear.png`, `delete.png`, `folder.png`, `italic.png`, `load.png`, `page.png`, `refresh.png`, `save.png`, `settings.png`, `underline.png`.
    *(You can find free icons from sources like Flaticon, Iconfinder, or use your own).*

### 3. Running the Application

Once the installation is complete, run the main script:
```bash
python Content_Assist_V2.py
```

---

## ⚙️ Configuration

The first time you run the application, you'll need to configure your API key.

1.  Launch the application and click the **Settings** button in the bottom-left sidebar.
2.  Go to the **API Keys** tab.
    *   Click "Add New API Key".
    *   Enter a memorable name (e.g., "My Google Key") and the API key value.
    *   The new key will be automatically selected as the active key.
3.  Go to the **AI Model** tab.
    *   Select your AI Provider (Google AI or OpenRouter).
    *   Click **"Refresh List"**. The application will fetch all compatible models for your key.
    *   Select a model from the list (e.g., `gemini-1.5-flash-latest`).
4.  Close the Settings window. You are now ready to use the AI features!

---

## 📖 How to Use

*   **Folders & Pages**: Use the `+ Folder` and `+ Page` buttons to create your content structure. Click on a folder or page in the navigator to select it.
*   **Writing**: Click on a page to load its content into the main workspace and start writing. Your work is saved automatically as you type.
*   **AI Functions**:
    *   Select a folder to see its associated AI functions at the top of the workspace.
    *   To run a function, simply click its button. It will use the entire page content as input.
    *   To run a function on a specific part of your text, **highlight the text** before clicking the function button.
*   **Managing Functions**: Click the "Manage" button next to the AI functions to open a dialog where you can create, edit, or delete the system prompts for the current folder.
*   **References**: In the sidebar navigator, click the "📌" button next to a page to add it to the "References" list. Any page in this list will be included as context in all future AI calls, which is great for character sheets, style guides, or plot summaries.

---

## 📁 Project Structure

```
.
├── Content_Assist_V2.py        # The main application script
├── requirements.txt            # Project dependencies
├── icons/                      # Folder for UI icons (you must create this)
│   ├── add.png
│   ├── delete.png
│   └── ... (and all other icons)
├── backups/                    # Automatic backups are stored here
└── ai_assistant_data_v2_1.json # Default data file for your projects and settings
```

---

## 🤝 Contributing

Contributions are welcome! If you have suggestions for improvements or want to fix a bug, please feel free to:

1.  Fork the Project.
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the Branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

---

## 📄 License

This project is open-source. Consider adding a license file (e.g., [MIT License](https://opensource.org/licenses/MIT)) to clarify usage rights.

---

## 🙏 Acknowledgments

*   [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the beautiful modern UI framework.
*   [Google's Generative AI](https://ai.google/discover/generativeai/) for the powerful language models.
*   [OpenRouter](https://openrouter.ai/) for providing unified access to a wide range of AI models.
