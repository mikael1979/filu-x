#!/usr/bin/env python3
"""
Simple HTTP server for Filu-X protocol testing
Run: python3 http_server.py [--port 8000] [--dir ./data/public/http]
"""

import http.server
import socketserver
import argparse
import json
import os
from pathlib import Path

class FiluXHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that serves Filu-X public directories"""
    
    def end_headers(self):
        # Add CORS headers for cross-origin requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, HEAD')
        super().end_headers()
    
    def do_GET(self):
        # Log requests for debugging
        print(f"📥 GET {self.path}")
        
        # Serve the file
        super().do_GET()
        
        # Log response status
        if self.path.endswith('.json'):
            print(f"📤 Sent JSON file")
    
    def log_message(self, format, *args):
        # Suppress default logging to avoid clutter
        pass

def main():
    parser = argparse.ArgumentParser(description='Filu-X HTTP Protocol Test Server')
    parser.add_argument('--port', '-p', type=int, default=8000, help='Port to listen on')
    parser.add_argument('--dir', '-d', type=str, default='./data/public/http', help='Directory to serve')
    parser.add_argument('--bind', '-b', type=str, default='127.0.0.1', help='Address to bind to')
    
    args = parser.parse_args()
    
    # Convert to absolute path and resolve
    serve_dir = Path(args.dir).resolve()
    
    # Ensure directory exists
    serve_dir.mkdir(parents=True, exist_ok=True)
    
    # Change to serve directory
    os.chdir(serve_dir)
    
    print(f"🌐 Filu-X HTTP Test Server")
    print(f"📁 Serving directory: {serve_dir}")
    print(f"🔗 URL: http://{args.bind}:{args.port}/")
    print(f"📝 Example: filu-x resolve http://{args.bind}:{args.port}/profile.json")
    print(f"🛑 Press Ctrl+C to stop")
    
    handler = FiluXHTTPRequestHandler
    with socketserver.TCPServer((args.bind, args.port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

if __name__ == '__main__':
    main()
