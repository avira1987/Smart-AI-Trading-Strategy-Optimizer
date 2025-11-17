"""
Proxy Server ساده برای اجرا روی کلاینت محلی
این فایل باید روی کلاینت محلی (با IP ایران) اجرا شود
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import json

class ProxyHandler(BaseHTTPRequestHandler):
    """Handler برای درخواست‌های proxy"""
    
    def do_GET(self):
        """دریافت درخواست GET"""
        try:
            # دریافت URL از query parameter
            url = self.path.lstrip('/')
            if not url.startswith('http'):
                # اگر URL کامل نیست، از header استفاده کن
                url = self.headers.get('X-Target-URL', 'https://nerkh.io' + self.path)
            
            print(f"[PROXY] Forwarding request to: {url}")
            
            # ساخت درخواست
            req = urllib.request.Request(url)
            
            # کپی کردن headers (به جز host)
            for header, value in self.headers.items():
                if header.lower() not in ['host', 'connection']:
                    req.add_header(header, value)
            
            # ارسال درخواست
            with urllib.request.urlopen(req, timeout=10) as response:
                # خواندن پاسخ
                data = response.read()
                
                # ارسال پاسخ
                self.send_response(response.status)
                
                # کپی کردن headers پاسخ
                for header, value in response.headers.items():
                    if header.lower() not in ['connection', 'transfer-encoding']:
                        self.send_header(header, value)
                
                self.end_headers()
                self.wfile.write(data)
                
                print(f"[PROXY] Response: {response.status}")
                
        except Exception as e:
            print(f"[PROXY ERROR] {e}")
            self.send_error(500, str(e))
    
    def do_POST(self):
        """دریافت درخواست POST"""
        try:
            url = self.path.lstrip('/')
            if not url.startswith('http'):
                url = self.headers.get('X-Target-URL', 'https://nerkh.io' + self.path)
            
            # خواندن body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            print(f"[PROXY] POST to: {url}")
            
            req = urllib.request.Request(url, data=body)
            
            for header, value in self.headers.items():
                if header.lower() not in ['host', 'connection', 'content-length']:
                    req.add_header(header, value)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read()
                
                self.send_response(response.status)
                for header, value in response.headers.items():
                    if header.lower() not in ['connection', 'transfer-encoding']:
                        self.send_header(header, value)
                self.end_headers()
                self.wfile.write(data)
                
        except Exception as e:
            print(f"[PROXY ERROR] {e}")
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        """غیرفعال کردن log پیش‌فرض"""
        pass


def run_proxy_server(port=8080):
    """اجرای proxy server"""
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, ProxyHandler)
    print(f"[PROXY SERVER] Running on port {port}")
    print(f"[PROXY SERVER] Access from VPS: http://YOUR_CLIENT_IP:{port}")
    print("[PROXY SERVER] Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[PROXY SERVER] Stopping...")
        httpd.shutdown()


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_proxy_server(port)

