# Notifications

## Email

### Gmail API

#### Create access credentials

[Create access credentials](https://developers.google.com/workspace/guides/create-credentials#desktop-app)

To send notifications to users, the server requires impersonating a user. Physically interacting with authentication processes is not possible in this case. Therefore, automatic authentication should be implemented.

In order to do this, two options are available: "OAuth client ID credentials" and "Service account credentials". For the "Service account credentials," domain-wide configurations are required, which require administrative privileges to setup. For this reason, ShellCast uses "OAuth client ID credentials". Email notifications are sent from the ShellCast Analysis server that does not have a web server setup, so follow the "Desktop app" instructions on the "Create access credentials" link.

#### Generating Email Secret Key
*Currently, email notifications are being sent from the analysis server as a temporary measure to prevent redundant updates on the NC, SC, and FL websites, optimizing time efficiency. However, the email notification functionality should ultimately be implemented on the web server.*

**Option 1: Run the script**
```bash
cd analysis/shellcast-analysis
python src/generate_secret_key.py
```
**Option 2: One-liner**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
