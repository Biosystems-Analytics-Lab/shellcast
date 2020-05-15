# shellcast
ShellCast web app repository

## Running locally
### Setup virtual environment
1. Make sure that you have Python 3 installed on your machine.
2. Create a virtual environment with `python3 -m venv venv`.
3. Activate the virtual environment with `source venv/bin/activate` if on a Linux or Mac machine.  If on a Windows machine, use `venv\Scripts\activate.bat`.  Now "python" will refer to the virtual environment's copy of Python 3. You can deactivate the virtual environment with `deactivate` (Linux/Mac/Windows).
4. Install the app and testing dependencies with `pip install -r requirements.txt` and then `pip install -r requirements-test.txt`.

### Run Python app locally
1. With the virtual environment activated, you can run the Python app with `python main.py`.
2. Now you can navigate to [http://localhost:8080](http//:localhost:8080) in your browser to see the web app.

### Run tests
1. With the virtual environment activated, you can run the tests with `python -m pytest`.
2. You should see the test output in the console.
