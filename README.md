# NAS-Server

A lightweight, self-hosted Network Attached Storage (NAS) full-stack web application built with **Flask** to store, manage, and access your files from your own hardware.

## Key Features

- **File & Directory Management:** Navigate folders, create directories, upload multiple files with live progress/upload speedometers, and download files individually or as dynamically generated `.zip` archives.

- **Native C++ Thumbnail Generator:** Asynchronously offloads video thumbnail generation to a multi-threaded C++ background worker process to generate thumbnails.

- **Built-in Media Viewing:** Modal-based image viewer and video streaming interface directly inside the web browser.

- **Security & Access Control:**
  * User authentication with Bcrypt password hashing and Flask-Login session management.
  * CSRF protection across form submissions and asynchronous fetch endpoints.
  * Thread-safe (`filelock`) IP rate-limiting and temporary lockout mechanisms against brute-force login attempts.
  * Strict path validation to prevent directory traversal attacks.

## Prerequisites

- **FFmpeg** should be installed and added to your system `PATH` (windows/linux) for the video generation C++ worker to work.

- A **free threaded Python3** installation is recommended, the code would work without free threaded python installation also but a Python3 installation is mandatory.

## Getting Started

1. **Clone the Repository**

   ```bash
   git clone https://github.com/Shaurya-Labs/NAS-Server.git
   cd NAS-Server
   ```

2. **Set up Virtual Environment & Install Dependencies**

   - Windows:
     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     pip install -r requirements.txt
     ```
   - Linux:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     pip3 install -r requirements.txt
     ```

3. **Setup C++ files**

   - **Windows:**
     - **Download pre-compiled binary:** Download directly from the [Releases](https://github.com/Shaurya-Labs/NAS-Server/releases) page and move it inside the `cpp_utils` folder.
     - **Compile from source:**
       ```bash
       # The output file name SHOULD match the C++ file name
       g++ ./cpp_utils/thumbnail_generator.cpp -o ./cpp_utils/thumbnail_generator.exe -std=c++23
       ```

   - **Linux:**
     ```bash
     # The output file name SHOULD match the C++ file name
     g++ ./cpp_utils/thumbnail_generator.cpp -o ./cpp_utils/thumbnail_generator -std=c++23
     ```

4. **Edit the configuration files**

   Create a `config/` directory in the project's root and create a `config.json` file inside it. Your config.json file should look like this:

   ```json
   {
       "SECRET_KEY": "",
       "ROOT_PATH": "C:/NAS_Files"
   }
   ```

   - **SECRET_KEY:** This would be used to configure the `Flask.secret_key`.
   - **ROOT_PATH:** This is the path pointing to the `NAS_Files` folder, where all the files would be stored by the NAS.

5. **Initialize Database and Create a new user login**

   ```bash
   flask db upgrade
   ```

> [!NOTE]
> **Change the default username and password** by editing the `username` and `password` variables in `create_new_user.py` file, the default username is "default" and the default password is "default"

   - Windows:
     ```bash
     python create_new_user.py
     ```

   - Linux:
     ```bash
     python3 create_new_user.py
     ```

6. **Run the backend server**

   - Windows:
     ```bash
     python run.py
     ```

   - Linux:
     ```bash
     python3 run.py
     ```

   > You can access the website locally by typing the address `localhost:8000` in any web browser.

## Tech Stack

- **Backend:** Python 3 (Flask, Flask-SQLAlchemy, Flask-Login, Flask-Migrate, Flask-Bcrypt, Flask-WTF, FileLock, Pillow)

- **Native Worker:** C++ (GCC/MSVC) utilizing standard C++ file streams, processes, and threading

- **Video Engine:** FFmpeg (invoked via native worker)

- **Frontend:** Vanilla JavaScript (Fetch API, Web Workers), CSS3, HTML5 (Jinja2 templates)

- **Database:** SQLite (managed via SQLAlchemy ORM)
