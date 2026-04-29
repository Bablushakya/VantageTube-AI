"""
Test script to verify Supabase connection and environment setup
Run this before starting the server to ensure everything is configured correctly
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_environment():
    """Test if environment variables are loaded"""
    print("🔍 Testing Environment Variables...")
    try:
        from app.core.config import settings
        
        print(f"✅ SUPABASE_URL: {settings.SUPABASE_URL[:30]}...")
        print(f"✅ SUPABASE_KEY: {settings.SUPABASE_KEY[:20]}...")
        print(f"✅ SECRET_KEY: {settings.SECRET_KEY[:20]}...")
        print(f"✅ APP_NAME: {settings.APP_NAME}")
        print(f"✅ DEBUG: {settings.DEBUG}")
        print(f"✅ ENVIRONMENT: {settings.ENVIRONMENT}")
        return True
    except Exception as e:
        print(f"❌ Environment Error: {e}")
        return False


def test_supabase_connection():
    """Test Supabase connection"""
    print("\n🔍 Testing Supabase Connection...")
    try:
        from app.core.supabase import get_supabase
        
        supabase = get_supabase()
        
        # Try to query the users table (should work even if empty)
        response = supabase.table("users").select("*").limit(1).execute()
        
        print(f"✅ Supabase Connected Successfully!")
        print(f"✅ Database accessible")
        return True
    except Exception as e:
        print(f"❌ Supabase Connection Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check if database_schema.sql was executed in Supabase SQL Editor")
        print("   2. Verify SUPABASE_URL and SUPABASE_KEY in .env file")
        print("   3. Check if 'users' table exists in Supabase Table Editor")
        return False


def test_jwt():
    """Test JWT token generation"""
    print("\n🔍 Testing JWT Token Generation...")
    try:
        from app.core.security import create_access_token, decode_access_token
        
        # Create test token
        test_data = {"sub": "test-user-id", "email": "test@example.com"}
        token = create_access_token(test_data)
        
        print(f"✅ Token Generated: {token[:30]}...")
        
        # Decode token
        decoded = decode_access_token(token)
        
        if decoded and decoded.get("sub") == "test-user-id":
            print(f"✅ Token Decoded Successfully")
            print(f"✅ User ID: {decoded.get('sub')}")
            print(f"✅ Email: {decoded.get('email')}")
            return True
        else:
            print(f"❌ Token Decode Failed")
            return False
    except Exception as e:
        print(f"❌ JWT Error: {e}")
        return False


def test_password_hashing():
    """Test password hashing"""
    print("\n🔍 Testing Password Hashing...")
    try:
        from app.core.security import get_password_hash, verify_password
        
        test_password = "testpassword123"
        hashed = get_password_hash(test_password)
        
        print(f"✅ Password Hashed: {hashed[:30]}...")
        
        # Verify password
        if verify_password(test_password, hashed):
            print(f"✅ Password Verification Works")
            return True
        else:
            print(f"❌ Password Verification Failed")
            return False
    except Exception as e:
        print(f"❌ Password Hashing Error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 VantageTube AI - Backend Connection Test")
    print("=" * 60)
    
    results = []
    
    # Test 1: Environment
    results.append(("Environment Variables", test_environment()))
    
    # Test 2: Supabase
    results.append(("Supabase Connection", test_supabase_connection()))
    
    # Test 3: JWT
    results.append(("JWT Tokens", test_jwt()))
    
    # Test 4: Password Hashing
    results.append(("Password Hashing", test_password_hashing()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All Tests Passed! Backend is ready to start!")
        print("\n🚀 Start the server with:")
        print("   uvicorn app.main:app --reload")
        print("\n📚 API Documentation:")
        print("   http://localhost:8000/docs")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\n💡 Common Solutions:")
        print("   1. Run database_schema.sql in Supabase SQL Editor")
        print("   2. Check .env file has correct Supabase credentials")
        print("   3. Ensure all dependencies are installed: pip install -r requirements.txt")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
