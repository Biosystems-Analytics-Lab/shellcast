#!/usr/bin/env python3
"""
Test runner script for ShellCast unsubscribe system tests.
This script runs all tests from the src/tests directory.
"""

import os
import subprocess
import sys


def run_test(test_file):
    """Run a single test file."""
    print(f"\n{'=' * 60}")
    print(f"🧪 Running: {test_file}")
    print(f"{'=' * 60}")

    try:
        # Determine the working directory for this test
        if test_file in [
            "src/tests/test_email_content.py",
            "src/tests/test_unsubscribe.py",
        ]:
            # These tests need to run from the src directory
            working_dir = "src"
            test_path = "tests/" + os.path.basename(test_file)
        else:
            # Other tests can run from the root directory
            working_dir = "."
            test_path = test_file

        # Run the test file
        result = subprocess.run(
            [sys.executable, test_path], capture_output=True, text=True, cwd=working_dir
        )

        if result.returncode == 0:
            print("✅ Test passed!")
            print(result.stdout)
        else:
            print("❌ Test failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 ShellCast Unsubscribe System Test Suite")
    print("=" * 60)

    # Get the tests directory
    tests_dir = "src/tests"

    if not os.path.exists(tests_dir):
        print(f"❌ Tests directory not found: {tests_dir}")
        return

    # Find all test files
    test_files = []
    for file in os.listdir(tests_dir):
        if file.startswith("test_") and file.endswith(".py"):
            test_files.append(os.path.join(tests_dir, file))

    if not test_files:
        print("❌ No test files found")
        return

    print(f"Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"  - {test_file}")

    # Run tests
    passed = 0
    failed = 0

    for test_file in test_files:
        if run_test(test_file):
            passed += 1
        else:
            failed += 1

    # Summary
    print(f"\n{'=' * 60}")
    print("🎯 Test Summary")
    print(f"{'=' * 60}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")

    if failed == 0:
        print("\n🎉 All tests passed! Your unsubscribe system is ready.")
        print("\nNext steps:")
        print("1. Send a test notification email")
        print("2. Click the unsubscribe link in the email")
        print("3. Verify the unsubscribe process works")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the errors above.")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
