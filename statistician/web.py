from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from cassandra.cluster import Cluster

class Web_server(BaseHTTPRequestHandler):

    cluster = Cluster()
    session = cluster.connect('sports_matcher')

    def do_GET(self):
        results = self.session.execute("SELECT * FROM started_matches")
        response = ""
        for r in results:
            response += "<br>"+r.time.isoformat()

        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(response)
        return

try:
    server = HTTPServer(('', 1444), Web_server)
    print('started stuff')
    server.serve_forever()
except KeyboardInterrupt:
    server.socket.close()
