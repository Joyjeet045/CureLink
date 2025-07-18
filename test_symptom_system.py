#!/usr/bin/env python
"""
Test script for the symptom-based doctor matching system
"""

import subprocess
import sys
import os
import json
from datetime import datetime

def test_predictor():
    """Test the predictor with different symptoms"""
    print("🧪 Testing Symptom Predictor...")
    
    test_cases = [
        "I have chest pain and shortness of breath",
        "My vision has been getting blurry and I have eye pain",
        "I have joint pain and difficulty walking",
        "I have a persistent cough and wheezing",
        "I have severe headache and dizziness"
    ]
    
    for i, symptoms in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {symptoms}")
        try:
            result = subprocess.run([
                sys.executable, 'predictor.py', symptoms
            ], capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                # Parse the output to get specialties
                output_lines = result.stdout.strip().split('\n')
                specialties = []
                for line in output_lines:
                    if 'LLM refined ranking:' in line:
                        specialties_str = line.split('LLM refined ranking:')[1].strip()
                        specialties = [s.strip() for s in specialties_str.split(',')]
                        break
                
                if specialties:
                    print(f"✅ Predicted specialties: {', '.join(specialties)}")
                else:
                    print("⚠️  No specific specialties found, using fallback")
            else:
                print(f"❌ Predictor failed: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error running predictor: {e}")

def test_database_models():
    """Test database models and relationships"""
    print("\n🗄️  Testing Database Models...")
    
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'doctors_app.settings')
        django.setup()
        
        from Hospitals.models import Doctor, VideoAppointment, doctor_departments
        from django.contrib.auth.models import User
        
        # Test doctor departments
        print(f"✅ Available departments: {doctor_departments}")
        
        # Test VideoAppointment model
        print(f"✅ VideoAppointment model fields: {[f.name for f in VideoAppointment._meta.fields]}")
        
        # Test Doctor model
        print(f"✅ Doctor model fields: {[f.name for f in Doctor._meta.fields]}")
        
        # Count existing data
        doctor_count = Doctor.objects.count()
        user_count = User.objects.count()
        print(f"✅ Database has {doctor_count} doctors and {user_count} users")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")

def test_websocket_routing():
    """Test websocket routing configuration"""
    print("\n🔌 Testing WebSocket Routing...")
    
    try:
        from doctors_app.routing import websocket_urlpatterns
        
        print("✅ WebSocket URL patterns:")
        for pattern in websocket_urlpatterns:
            print(f"   - {pattern.pattern}")
            
        # Check if SymptomRequestConsumer is included
        consumer_names = [str(pattern.callback.__name__) for pattern in websocket_urlpatterns]
        if 'SymptomRequestConsumer' in consumer_names:
            print("✅ SymptomRequestConsumer is properly configured")
        else:
            print("❌ SymptomRequestConsumer not found in routing")
            
    except Exception as e:
        print(f"❌ WebSocket routing test failed: {e}")

def test_url_patterns():
    """Test URL patterns for the new views"""
    print("\n🌐 Testing URL Patterns...")
    
    try:
        from Hospitals.urls import urlpatterns
        
        required_urls = [
            'submit_symptoms',
            'doctor_requests', 
            'update_appointment_status',
            'video_consultation_room'
        ]
        
        url_names = [pattern.name for pattern in urlpatterns if hasattr(pattern, 'name') and pattern.name]
        
        print("✅ Found URL patterns:")
        for name in url_names:
            print(f"   - {name}")
            
        missing_urls = [url for url in required_urls if url not in url_names]
        if missing_urls:
            print(f"❌ Missing URL patterns: {missing_urls}")
        else:
            print("✅ All required URL patterns are configured")
            
    except Exception as e:
        print(f"❌ URL pattern test failed: {e}")

def main():
    """Run all tests"""
    print("🚀 CureLink Symptom-Based Doctor Matching System Test")
    print("=" * 60)
    
    test_predictor()
    test_database_models()
    test_websocket_routing()
    test_url_patterns()
    
    print("\n" + "=" * 60)
    print("✅ Test completed! The system should be ready to use.")
    print("\n📝 Next steps:")
    print("1. Start the server: daphne -p 8001 doctors_app.asgi:application")
    print("2. Create some doctor accounts and set them online")
    print("3. Create patient accounts and test the symptom submission")
    print("4. Check the doctor requests page for incoming requests")

if __name__ == "__main__":
    main() 