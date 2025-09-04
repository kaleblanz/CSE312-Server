class Request:

    def __init__(self, request: bytes):
        # TODO: parse the bytes of the request and populate the following instance variables

        #splits the bytes at the point b"\r\n\r\n", body is [1] and the rest is [0]
        request_bytes_split = request.split(b"\r\n\r\n")
        #print(request_bytes_split)

        #turn the bytes into a literal string (its everything but the body)
        request_headers_reqLine = request_bytes_split[0].decode()
        #print(request_headers_reqLine)

        #split at the new line, [0] is the Request Line, 1..n indexes are each header
        request_headers_reqLine = request_headers_reqLine.split('\r\n')
        #print(f"request line and the headers: {request_headers_reqLine}")

        #request line
        request_line = request_headers_reqLine[0]
        #print(f"request line: {request_line}")

        #all the request headers, deletes the request line 
        request_headers_reqLine.pop(0)
        request_headers = request_headers_reqLine
        print(f"request headers: {request_headers}")

        #split the 2 spaces in request line
        method,path,http_v = request_line.split(' ')
        print(f"method: {(method)}    path: {(path)}    http: {(http_v)}")


        self.body = request_bytes_split[1]
        self.method = method.rstrip().lstrip()
        self.path = path.rstrip().lstrip()
        self.http_version = http_v.rstrip().lstrip()
        self.headers = {}
        self.cookies = {}

#need to test for Content-Type: text/html; charset=utf-8

def test1():
    request = Request(b'GET / HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
    assert request.method == "GET"
    assert request.path == "/"
    assert request.http_version == "HTTP/1.1"

    assert "Host" in request.headers
    assert request.headers["Host"] == "localhost:8080"  # note: The leading space in the header value must be removed

    assert "Connection" in request.headers
    assert request.headers["Connection"] == "keep-alive"

    assert len(request.headers) == 2
    assert len(request.cookies) == 0
    assert request.body == b""  # There is no body for this request.
    # When parsing POST requests, the body must be in bytes, not str

    # This is the start of a simple way (ie. no external libraries) to test your code.
    # It's recommended that you complete this test and add others, including at least one
    # test using a POST request. Also, ensure that the types of all values are correct

def test2():
    request = Request(b'POST /api/chats HTTP/1.1\r\nHost: localhost:8080\r\nContent-Type: application/json\r\nContent-Length: 18\r\nCookie: id=123; theme=dark\r\nOrigin: http://localhost:8080\r\n\r\n{"content":"asdf"}')
    assert request.method == "POST"
    assert request.path == "/api/chats"
    assert request.http_version == "HTTP/1.1"

    assert "Host" in request.headers
    assert request.headers["Host"] == "localhost:8080"

    assert "Content-Type" in request.headers
    assert request.headers["Content-Type"] == "application/json"

    assert "Content-Length" in request.headers
    assert request.headers["Content-Length"] == 18

    assert "id" in request.headers
    assert "id" in request.cookies
    assert request.headers["id"] == 123
    assert request.cookies["id"] == 123

    assert "theme" in request.headers
    assert "theme" in request.cookies
    assert request.headers["theme"] == "dark"
    assert request.cookies["theme"] == "dark"

    assert "Origin" in request.headers
    assert request.headers["Origin"] == "http://localhost:8080"

    assert len(request.headers) == 6
    assert len(request.cookies) == 2

    assert request.body == b"{'content':'asdf'}"

    '''
    POST Request Test:
          POST /api/chats HTTP/1.1\r\nHost: localhost:8080\r\nContent-Type: application/json\r\nContent-Length: 18
self.method^ self.path^  http^      self.headers^                 self.headers^              self.headers^
    \r\nCookie: id=123; theme=dark\r\nOrigin: http://localhost:8080\r\n\r\n{"content":"asdf"}
    self.headers^ANDself.cookies         self.headers^                       self.body^

    cookies: {"id"=123, "theme"="dark"}
    headers: {"Host"="localhost:8080", "Content-Type"="application/json", 
    "Content-Length": 18, "id"=123, "theme"="dark"}
    '''


if __name__ == '__main__':
    #test1()
    test2()
