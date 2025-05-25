#!/usr/bin/env python3
"""
Currency Recognition API Backend Test Suite
Tests all API endpoints including dual AI integration
"""

import requests
import sys
import json
import io
import base64
from datetime import datetime
from PIL import Image
import os

class CurrencyAPITester:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_username = f"test_user_{datetime.now().strftime('%H%M%S')}"
        self.test_password = "TestPass123!"

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        if details and success:
            print(f"   Details: {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Default headers
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        # Override with custom headers
        if headers:
            test_headers.update(headers)
        
        # Remove Content-Type for file uploads
        if files:
            test_headers.pop('Content-Type', None)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=test_headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}

            if success:
                self.log_test(name, True, f"Status: {response.status_code}")
                return True, response_data
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}. Response: {response_data}")
                return False, response_data

        except requests.exceptions.RequestException as e:
            self.log_test(name, False, f"Request error: {str(e)}")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Unexpected error: {str(e)}")
            return False, {}

    def create_test_image(self):
        """Create a simple test image for currency analysis"""
        # Create a simple test image with text
        img = Image.new('RGB', (400, 200), color='lightgreen')
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return img_byte_arr

    def test_health_check(self):
        """Test health check endpoint"""
        return self.run_test(
            "Health Check",
            "GET",
            "/api/health",
            200
        )

    def test_register(self):
        """Test user registration"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "/api/register",
            200,
            data={
                "username": self.test_username,
                "password": self.test_password
            }
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Registered user: {self.test_username}")
            return True
        return False

    def test_login(self):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "/api/login",
            200,
            data={
                "username": self.test_username,
                "password": self.test_password
            }
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Logged in user: {self.test_username}")
            return True
        return False

    def test_duplicate_registration(self):
        """Test duplicate user registration (should fail)"""
        return self.run_test(
            "Duplicate Registration (should fail)",
            "POST",
            "/api/register",
            400,
            data={
                "username": self.test_username,
                "password": self.test_password
            }
        )

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        return self.run_test(
            "Invalid Login (should fail)",
            "POST",
            "/api/login",
            401,
            data={
                "username": "nonexistent_user",
                "password": "wrong_password"
            }
        )

    def test_currency_analysis(self):
        """Test currency image analysis with dual AI"""
        if not self.token:
            self.log_test("Currency Analysis", False, "No authentication token")
            return False

        # Create test image
        test_image = self.create_test_image()
        
        files = {
            'file': ('test_currency.png', test_image, 'image/png')
        }
        
        success, response = self.run_test(
            "Currency Analysis (Dual AI)",
            "POST",
            "/api/analyze-currency",
            200,
            files=files
        )
        
        if success:
            # Check if response has expected structure
            required_fields = ['analysis_id', 'openai_result', 'gemini_result', 'combined_analysis']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                self.log_test("Currency Analysis Structure", False, f"Missing fields: {missing_fields}")
                return False
            else:
                self.log_test("Currency Analysis Structure", True, "All required fields present")
                
                # Store analysis ID for later tests
                self.analysis_id = response.get('analysis_id')
                
                # Check AI results
                openai_result = response.get('openai_result', {})
                gemini_result = response.get('gemini_result', {})
                
                print(f"   OpenAI Provider: {openai_result.get('provider', 'Unknown')}")
                print(f"   Gemini Provider: {gemini_result.get('provider', 'Unknown')}")
                
                if openai_result.get('error'):
                    print(f"   OpenAI Error: {openai_result['error']}")
                if gemini_result.get('error'):
                    print(f"   Gemini Error: {gemini_result['error']}")
                
                return True
        
        return False

    def test_get_analyses(self):
        """Test getting user's analysis history"""
        if not self.token:
            self.log_test("Get Analyses", False, "No authentication token")
            return False

        success, response = self.run_test(
            "Get Analysis History",
            "GET",
            "/api/analysis",
            200
        )
        
        if success and 'analyses' in response:
            analyses_count = len(response['analyses'])
            self.log_test("Analysis History Structure", True, f"Found {analyses_count} analyses")
            return True
        
        return False

    def test_get_specific_analysis(self):
        """Test getting a specific analysis by ID"""
        if not self.token:
            self.log_test("Get Specific Analysis", False, "No authentication token")
            return False
        
        if not hasattr(self, 'analysis_id') or not self.analysis_id:
            self.log_test("Get Specific Analysis", False, "No analysis ID available")
            return False

        return self.run_test(
            "Get Specific Analysis",
            "GET",
            f"/api/analysis/{self.analysis_id}",
            200
        )

    def test_unauthorized_access(self):
        """Test accessing protected endpoints without token"""
        # Temporarily remove token
        original_token = self.token
        self.token = None
        
        success, _ = self.run_test(
            "Unauthorized Access (should fail)",
            "GET",
            "/api/analysis",
            401
        )
        
        # Restore token
        self.token = original_token
        return success

    def test_invalid_file_upload(self):
        """Test uploading non-image file"""
        if not self.token:
            self.log_test("Invalid File Upload", False, "No authentication token")
            return False

        # Create a text file instead of image
        text_content = io.BytesIO(b"This is not an image file")
        
        files = {
            'file': ('test.txt', text_content, 'text/plain')
        }
        
        return self.run_test(
            "Invalid File Upload (should fail)",
            "POST",
            "/api/analyze-currency",
            400,
            files=files
        )

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Currency Recognition API Test Suite")
        print(f"📍 Testing endpoint: {self.base_url}")
        print("=" * 60)

        # Test sequence
        tests = [
            ("Basic API Health", self.test_health_check),
            ("User Registration", self.test_register),
            ("Duplicate Registration", self.test_duplicate_registration),
            ("User Login", self.test_login),
            ("Invalid Login", self.test_invalid_login),
            ("Unauthorized Access", self.test_unauthorized_access),
            ("Currency Analysis", self.test_currency_analysis),
            ("Get Analysis History", self.test_get_analyses),
            ("Get Specific Analysis", self.test_get_specific_analysis),
            ("Invalid File Upload", self.test_invalid_file_upload),
        ]

        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.log_test(test_name, False, f"Test execution error: {str(e)}")

        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED!")
            return 0
        else:
            print("⚠️  SOME TESTS FAILED")
            return 1

def main():
    # Get backend URL from environment or use default
    backend_url = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
    
    print(f"Currency Recognition API Tester")
    print(f"Backend URL: {backend_url}")
    
    # Check if we can reach the backend
    try:
        response = requests.get(f"{backend_url}/api/health", timeout=10)
        print(f"✅ Backend is reachable (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Cannot reach backend: {e}")
        print("Make sure the backend is running and accessible")
        return 1

    # Run tests
    tester = CurrencyAPITester(backend_url)
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())