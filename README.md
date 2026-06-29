# ReconVault

ReconVault is a clean, terminal-aesthetic desktop application for Linux designed for security researchers, bug bounty hunters, and CTF players. It provides a centralized platform to organize all recon findings per target, including subdomains, IPs, ports, endpoints, notes, and vulnerabilities, eliminating the need for scattered spreadsheets or text files.

## Installation and Run Instructions

1.  **Prerequisites:** Ensure you have Python 3.10+ installed on your Linux system.

2.  **Install PyQt6:** Open your terminal and install the required GUI library:
    ```bash
    pip install PyQt6
    ```

3.  **Download ReconVault:** Download the `reconvault.py` file and `requirements.txt` from the provided archive.

4.  **Run the Application:** Navigate to the directory where you saved `reconvault.py` in your terminal and execute:
    ```bash
    python3 reconvault.py
    ```

    The application will automatically create a `.reconvault` directory and `reconvault.db` database in your home directory (`~/.reconvault/reconvault.db`) on its first run.

## Feature Overview

*   **Target Management:** Create, list, search, filter, and delete targets. Each target includes name, domain, platform, and dates.
*   **Target Workspace:** Dedicated tabs for each target to organize:
    *   **Subdomains:** Table for subdomains, IPs, status, tech stack, and notes. Supports inline editing and import from text files.
    *   **Ports & Services:** Table for IPs, ports, protocols, services, versions, and notes. Supports inline editing and import from Nmap output.
    *   **Endpoints:** Table for URLs, methods, parameters, status codes, and notes. Supports inline editing.
    *   **Vulnerabilities:** Table for title, severity (with colored badges), status, CVE/CWE, and description. Supports inline editing.
    *   **Notes:** A large plain text editor for freeform notes with auto-save functionality.
*   **Dashboard:** Home screen displaying total targets, total vulnerabilities by severity, and recent activity.
*   **Export:** Export any target's full data as a Markdown report.
*   **Global Search:** Search across all targets and all tabs simultaneously.

## Screenshots

*(Screenshots will be added here)*

## License

This project is licensed under the MIT License - see the LICENSE file for details.
