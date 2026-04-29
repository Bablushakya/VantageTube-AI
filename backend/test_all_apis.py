#!/usr/bin/env python3
"""
VantageTube AI - Comprehensive API Testing Script
Tests all endpoints and generates a detailed report
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000/api"
HEALTH_URL = "http://localhost:8000/health"

# Test data
TEST_USER = {
    "email": f"test_{datetime.now().timestamp()}@example.com",
    "password": "TestPassword123!",
    "confirm_password": "TestPassword123!",
    "first_name": "Test",
    "last_name": "User",
    "display_name": "Test User"
}

# Results tracking
results = {
    "timestamp": datetime.now().isoformat(),
    "base_url": BASE_URL,
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "modules": {}
}

# Global state
access_token = None
user_id = None


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_test(name: str, method: str, endpoint: str):
    """Print test info"""
    print(f"[TEST] {method:6} {endpoint:40} - {name}")


def print_result(status: bool, message: str = ""):
    """Print test result"""
    status_text = "✅ PASS" if status else "❌ FAIL"
    print(f"       {status_text} {message}\n")


def test_endpoint(
    name: str,
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    expected_status: int = 200,
    module: str = "general"
) -> tuple[bool, Any]:
    """Test a single endpoint"""
    global results
    
    results["total_tests"] += 1
    
    print_test(name, method, endpoint)
    
    url = f"{BASE_URL}{endpoint}"
    
    # Add auth header if token exists
    if headers is None:
        headers = {}
    if access_token and "Authorization" not in headers:
        headers["Authorization"] = f"Bearer {access_token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        success = response.status_code == expected_status
        
        if success:
            results["passed"] += 1
            message = f"Status {response.status_code}"
            print_result(True, message)
            
            # Track in module
            if module not in results["modules"]:
                results["modules"][module] = {"passed": 0, "failed": 0, "tests": []}
            results["modules"][module]["passed"] += 1
            results["modules"][module]["tests"].append({
                "name": name,
                "status": "passed",
                "status_code": response.status_code
            })
            
            return True, response.json() if response.text else {}
        else:
            results["failed"] += 1
            message = f"Expected {expected_status}, got {response.status_code}"
            print_result(False, message)
            
            # Track in module
            if module not in results["modules"]:
                results["modules"][module] = {"passed": 0, "failed": 0, "tests": []}
            results["modules"][module]["failed"] += 1
            results["modules"][module]["tests"].append({
                "name": name,
                "status": "failed",
                "status_code": response.status_code,
                "error": response.text[:200]
            })
            
            return False, response.json() if response.text else {}
    
    except requests.exceptions.ConnectionError:
        results["failed"] += 1
        print_result(False, "Connection refused - Backend not running?")
        
        if module not in results["modules"]:
            results["modules"][module] = {"passed": 0, "failed": 0, "tests": []}
        results["modules"][module]["failed"] += 1
        results["modules"][module]["tests"].append({
            "name": name,
            "status": "failed",
            "error": "Connection refused"
        })
        
        return False, None
    
    except Exception as e:
        results["failed"] += 1
        print_result(False, f"Exception: {str(e)}")
        
        if module not in results["modules"]:
            results["modules"][module] = {"passed": 0, "failed": 0, "tests": []}
        results["modules"][module]["failed"] += 1
        results["modules"][module]["tests"].append({
            "name": name,
            "status": "failed",
            "error": str(e)
        })
        
        return False, None


def test_health():
    """Test health endpoint"""
    print_header("HEALTH CHECK")
    
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running!")
            print(f"   Response: {response.json()}\n")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}\n")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend at", HEALTH_URL)
        print("   Make sure the backend is running:\n")
        print("   cd vantagetube-ai/backend")
        print("   python -m uvicorn app.main:app --reload\n")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        return False


def test_authentication():
    """Test authentication endpoints"""
    global access_token, user_id
    
    print_header("AUTHENTICATION TESTS")
    
    # Register
    success, data = test_endpoint(
        "Register User",
        "POST",
        "/auth/register",
        data=TEST_USER,
        expected_status=201,
        module="authentication"
    )
    
    if success and data:
        access_token = data.get("access_token")
        user_id = data.get("user", {}).get("id")
        print(f"   User ID: {user_id}")
        print(f"   Token: {access_token[:50]}...\n")
    else:
        print("   ⚠️  Registration failed - skipping remaining auth tests\n")
        return
    
    # Login
    test_endpoint(
        "Login User",
        "POST",
        "/auth/login",
        data={"email": TEST_USER["email"], "password": TEST_USER["password"]},
        expected_status=200,
        module="authentication"
    )
    
    # Get current user
    test_endpoint(
        "Get Current User",
        "GET",
        "/auth/me",
        expected_status=200,
        module="authentication"
    )
    
    # Check auth
    test_endpoint(
        "Check Auth Status",
        "GET",
        "/auth/check",
        expected_status=200,
        module="authentication"
    )
    
    # Refresh token
    test_endpoint(
        "Refresh Token",
        "POST",
        "/auth/refresh",
        expected_status=200,
        module="authentication"
    )


def test_users():
    """Test user endpoints"""
    print_header("USER MANAGEMENT TESTS")
    
    if not access_token:
        print("⚠️  Skipping - No access token\n")
        return
    
    # Get profile
    test_endpoint(
        "Get User Profile",
        "GET",
        "/users/me",
        expected_status=200,
        module="users"
    )
    
    # Update profile
    test_endpoint(
        "Update User Profile",
        "PUT",
        "/users/me",
        data={
            "first_name": "Updated",
            "last_name": "Name",
            "niche": "tech",
            "bio": "I create tech content"
        },
        expected_status=200,
        module="users"
    )
    
    # Get settings
    test_endpoint(
        "Get User Settings",
        "GET",
        "/users/settings",
        expected_status=200,
        module="users"
    )
    
    # Update settings
    test_endpoint(
        "Update User Settings",
        "PUT",
        "/users/settings",
        data={
            "theme": "dark",
            "email_notifications": True,
            "weekly_seo_report": True
        },
        expected_status=200,
        module="users"
    )


def test_content_generation():
    """Test content generation endpoints"""
    print_header("CONTENT GENERATION TESTS")
    
    if not access_token:
        print("⚠️  Skipping - No access token\n")
        return
    
    # Generate titles
    test_endpoint(
        "Generate Titles",
        "POST",
        "/content/generate/titles",
        data={
            "topic": "How to learn Python programming",
            "keywords": ["python", "programming", "tutorial"],
            "tone": "educational",
            "count": 3
        },
        expected_status=200,
        module="content"
    )
    
    # Generate description
    test_endpoint(
        "Generate Description",
        "POST",
        "/content/generate/description",
        data={
            "topic": "How to learn Python programming",
            "title": "Python for Beginners",
            "tone": "educational"
        },
        expected_status=200,
        module="content"
    )
    
    # Generate tags
    test_endpoint(
        "Generate Tags",
        "POST",
        "/content/generate/tags",
        data={
            "topic": "How to learn Python programming",
            "count": 10
        },
        expected_status=200,
        module="content"
    )
    
    # Generate thumbnail text
    test_endpoint(
        "Generate Thumbnail Text",
        "POST",
        "/content/generate/thumbnail-text",
        data={
            "topic": "How to learn Python programming",
            "count": 3
        },
        expected_status=200,
        module="content"
    )
    
    # Get content history
    test_endpoint(
        "Get Content History",
        "GET",
        "/content/history",
        expected_status=200,
        module="content"
    )
    
    # Get content stats
    test_endpoint(
        "Get Content Stats",
        "GET",
        "/content/stats",
        expected_status=200,
        module="content"
    )


def test_seo_analysis():
    """Test SEO analysis endpoints"""
    print_header("SEO ANALYSIS TESTS")
    
    if not access_token:
        print("⚠️  Skipping - No access token\n")
        return
    
    # Analyze video
    test_endpoint(
        "Analyze Video SEO",
        "POST",
        "/seo/analyze",
        data={"video_id": "test-video-123"},
        expected_status=200,
        module="seo"
    )
    
    # Get dashboard stats
    test_endpoint(
        "Get SEO Dashboard Stats",
        "GET",
        "/seo/dashboard/stats",
        expected_status=200,
        module="seo"
    )


def test_trending():
    """Test trending endpoints"""
    print_header("TRENDING TOPICS TESTS")
    
    if not access_token:
        print("⚠️  Skipping - No access token\n")
        return
    
    # Get categories
    test_endpoint(
        "Get YouTube Categories",
        "GET",
        "/trending/categories",
        expected_status=200,
        module="trending"
    )
    
    # Get regions
    test_endpoint(
        "Get Supported Regions",
        "GET",
        "/trending/regions",
        expected_status=200,
        module="trending"
    )
    
    # Get trending stats
    test_endpoint(
        "Get Trending Stats",
        "GET",
        "/trending/stats?region=US",
        expected_status=200,
        module="trending"
    )
    
    # Get trending dashboard
    test_endpoint(
        "Get Trending Dashboard",
        "GET",
        "/trending/dashboard?region=US",
        expected_status=200,
        module="trending"
    )
    
    # Fetch trending (may fail if YouTube API not configured)
    test_endpoint(
        "Fetch Trending Videos",
        "POST",
        "/trending/fetch",
        data={"region": "US", "max_results": 10},
        expected_status=200,
        module="trending"
    )


def test_youtube():
    """Test YouTube endpoints"""
    print_header("YOUTUBE INTEGRATION TESTS")
    
    if not access_token:
        print("⚠️  Skipping - No access token\n")
        return
    
    # Get channels
    test_endpoint(
        "Get YouTube Channels",
        "GET",
        "/youtube/channels",
        expected_status=200,
        module="youtube"
    )


def print_summary():
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    total = results["total_tests"]
    passed = results["passed"]
    failed = results["failed"]
    
    if total == 0:
        print("❌ No tests were run\n")
        return
    
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"Total Tests:  {total}")
    print(f"Passed:       {passed} ✅")
    print(f"Failed:       {failed} ❌")
    print(f"Success Rate: {percentage:.1f}%\n")
    
    print("Module Breakdown:")
    print("-" * 60)
    
    for module, data in results["modules"].items():
        module_total = data["passed"] + data["failed"]
        module_percentage = (data["passed"] / module_total * 100) if module_total > 0 else 0
        status = "✅" if data["failed"] == 0 else "⚠️"
        print(f"{status} {module:20} {data['passed']:3}/{module_total:3} ({module_percentage:5.1f}%)")
    
    print("-" * 60 + "\n")
    
    # Save results to file
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("📊 Detailed results saved to: test_results.json\n")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  VantageTube AI - API Testing Suite")
    print("="*60)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Base URL: {BASE_URL}\n")
    
    # Check health
    if not test_health():
        print("\n❌ Backend is not running. Cannot proceed with tests.\n")
        sys.exit(1)
    
    # Run test suites
    test_authentication()
    test_users()
    test_content_generation()
    test_seo_analysis()
    test_trending()
    test_youtube()
    
    # Print summary
    print_summary()
    
    print("="*60)
    print(f"  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
