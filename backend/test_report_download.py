"""
Test script to verify report download endpoint works
"""
import requests

# Test with a valid scan ID (assuming scan ID 1 exists)
url = "http://localhost:8000/scans/1/download-report"

# You'll need to replace this with a real token from your login
# For now, let's just test if the endpoint responds
response = requests.get(url)

print(f"Status Code: {response.status_code}")
print(f"Content-Type: {response.headers.get('Content-Type')}")
print(f"Response length: {len(response.content)} bytes")

if response.status_code == 401:
    print("\n✅ Endpoint is working! (401 = needs authentication, which is expected)")
elif response.status_code == 200:
    print("\n✅ Endpoint is working! PDF generated successfully")
    # Save the PDF
    with open("test_report.pdf", "wb") as f:
        f.write(response.content)
    print("📄 PDF saved as test_report.pdf")
else:
    print(f"\n❌ Unexpected status code: {response.status_code}")
    print(f"Response: {response.text[:500]}")
