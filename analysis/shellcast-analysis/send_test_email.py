#!/usr/bin/env python3
"""
Simple script to send a test email with unsubscribe footer.
This runs the test_send_email.py script from the src/tests directory.
"""

import subprocess
import sys
import os

def main():
    """Send a test email."""
    print("📧 ShellCast Test Email Sender")
    print("=" * 50)
    
    # Path to the test script
    test_script = "src/tests/test_send_email.py"
    
    if not os.path.exists(test_script):
        print(f"❌ Test script not found: {test_script}")
        return False
    
    print("Sending test email with unsubscribe footer...")
    print("This will send an email to: mshukun@ncsu.edu")
    print("Unsubscribe link: http://127.0.0.1:3361/unsubscribe?email=mshukun@ncsu.edu")
    print()
    
    try:
        # Run the test script
        result = subprocess.run([sys.executable, test_script], 
                              capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n🎉 Test email sent successfully!")
            print("\nNext steps:")
            print("1. Check your email at mshukun@ncsu.edu")
            print("2. Click the unsubscribe link in the email")
            print("3. Test the unsubscribe process on your local server")
            return True
        else:
            print(f"\n❌ Test email failed with exit code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
