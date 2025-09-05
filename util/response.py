import json

'''
Response Class:
* helps you construct a response to sent to the client
* i will constuct end responses at every endpoint that i have (this makes my life/code a lot easier) 
'''
class Response:
    def __init__(self):
        #create instace variables that will be used in different methods

        #defualt values for status code and message if set_status() is never called
        self.var_status_code = 200
        self.var_status_msg = "OK"

        #REMEMBER TO ADD NO SNIFF
        self.var_headers = ""

        self.var_cookies = ""

        self.var_body = b""

        self.var_content_type = "text/plain; charset=utf-8"

        self.var_content_length = 0

    def set_status(self, code, text):
        #code -> int
        #text -> string
        self.var_status_code = code
        self.var_status_msg = text
        return self

    def headers(self, headers):
        #headers -> dict:{str=str}
        #iterate through each k-v and form a string and add it to header variable
        if self.var_headers == "":
            self.var_headers += "\r\n"
        
        for header in headers:
            header_value = headers[header]
            #if len(self.var_headers) == 2:
            #self.var_headers += header + ": " + header_value + "\r\n\r\n"
            #else:
            #self.var_headers.replace("\r\n\r\n","\r\n")
            self.var_headers += header + ": " + header_value + "\r\n\r\n"
            #print(f"each header line: {self.var_headers}")
        
        #replace all the double with single \r\n
        self.var_headers = self.var_headers.replace("\r\n\r\n","\r\n")
        #add it to the end of the string
        self.var_headers += "\r\n"
        return self

    def cookies(self, cookies):
        #cookies -> dict {str -> str}
        #Cookie: name=value; name2=value2; name3=value3
        if self.var_cookies == "":
            self.var_cookies += '\r\n'

        for cookie in cookies:
            value = cookie + "=" + cookies[cookie]
            self.var_cookies += "Set-Cookie: " + value + '\r\n\r\n'

        self.var_cookies = self.var_cookies.replace('\r\n\r\n','\r\n')
        self.var_cookies += '\r\n'
        return self

    def bytes(self, data):
        #data -> bytes
        #append the already bytes of body to the request.var_body
        self.var_body += data
        return self

    def text(self, data):
        #data -> string
        data_bytes = data.encode()
        self.var_body += data_bytes
        return self

    def json(self, data):
        #data -> {} OR []
        #change content type
        self.var_content_type = "application/json"
        #turn the data input to a json string then decode to bytes
        self.var_body = json.dumps(data).encode()
        return self

    def to_data(self):
        #returns the entire response in bytes (PROPER HTTP PROTOCOL)
        response = b''
        status_line = "HTTP/1.1 " + str(self.var_status_code) + " " + self.var_status_msg

        #encode the status line into bytes and at to response
        response += status_line.encode()

        #the case for when a content type was never given
        if "Content-Type" not in self.var_headers:
            if self.var_content_type != "":
                self.var_headers += f"\r\nContent-Type: {self.var_content_type}\r\n"
            else:
                self.var_headers += "\r\nContent-Type: text/plain; charset=utf-8\r\n"

        #set the content length
        #assume we dont have to check if the content_length is wrong from user input
        self.var_content_length = len(self.var_body)
        if "Content-Length" not in self.var_headers:
            self.var_headers += f"\r\nContent-Length: {self.var_content_length}\r\n"

        #add our no sniff
        if "X-Content-Type-Options" not in self.var_headers:
            self.var_headers += "\r\nX-Content-Type-Options: nosniff\r\n"
        '''
        if i have to string.replace('\r\n\r\n','\r\n')
        += '\r\n'
        to confirm the structure is correct
        '''
        header_cookie_line = self.var_headers+self.var_cookies
        #print("header_cookie_line before replace:", header_cookie_line.encode() )
        header_cookie_line = header_cookie_line.replace("\r\n\r\n\r\n\r\n","\r\n")
        header_cookie_line = header_cookie_line.replace("\r\n\r\n\r\n","\r\n")
        header_cookie_line = header_cookie_line.replace("\r\n\r\n","\r\n")
        #print("header_cookie_line after replace:", header_cookie_line.encode() )
        header_cookie_line += "\r\n"
        header_cookie_line_encoded = header_cookie_line.encode()
        response += header_cookie_line_encoded



        response += self.var_body

    

        return response




def testMultipleToData():
    #TEXT/PLAIN is all caps just to make sure it uses the all caps one and not the lower case for the specific test case
    response = Response()
    response.bytes(b"this is my text")
    response.headers({"Content-Type": "TEXT/PLAIN; charset=utf-8"})
    response.cookies({"id":"123", "theme":"dark"})
    expected = b'HTTP/1.1 200 OK\r\nContent-Type: TEXT/PLAIN; charset=utf-8\r\nContent-Length: 15\r\nX-Content-Type-Options: nosniff\r\nSet-Cookie: id=123\r\nSet-Cookie: theme=dark\r\n\r\nthis is my text'
              #b'HTTP/1.1 200 OK\r\nContent-Type: TEXT/PLAIN; charset=utf-8\r\nContent-Length: 15\r\nX-Content-Type-Options: nosniff\r\nSet-Cookie: id=123\r\nSet-Cookie: theme=dark\r\n\r\nthis is my text    
    actual = response.to_data()
    #print("1st print:",actual)
    assert actual == expected
    
    
    response.headers({"Host": "localhost:8080"})
    response.cookies({"x":"y"})
    response.set_status(202, "OKAY")
    response.bytes(b" from me")
    expected = b'HTTP/1.1 202 OKAY\r\nContent-Type: TEXT/PLAIN; charset=utf-8\r\nContent-Length: 15\r\nX-Content-Type-Options: nosniff\r\nHost: localhost:8080\r\nSet-Cookie: id=123\r\nSet-Cookie: theme=dark\r\nSet-Cookie: x=y\r\n\r\nthis is my text from me'
              #b'HTTP/1.1 202 OKAY\r\nContent-Type: TEXT/PLAIN; charset=utf-8\r\nContent-Length: 15\r\nX-Content-Type-Options: nosniff\r\nHost: localhost:8080\r\nSet-Cookie: id=123\r\nSet-Cookie: theme=dark\r\nSet-Cookie: x=y\r\n\r\nthis is my text from me'
    actual = response.to_data()
    #print("2nd print:",actual)
    assert expected == actual


    
    
def testJSON():
    response = Response()
    response.text("hellooooo")
    lis = [1,2,3,4]
    response.json(lis)
    response.set_status(404, "NOOO")
    response.cookies({"p":"opp","b":"sds"})

    expected = b'HTTP/1.1 404 NOOO\r\nContent-Type: application/json\r\nContent-Length: 12\r\nX-Content-Type-Options: nosniff\r\nSet-Cookie: p=opp\r\nSet-Cookie: b=sds\r\n\r\n[1, 2, 3, 4]'
              #b'HTTP/1.1 404 NOOO\r\nContent-Type: application/json\r\nContent-Length: 12\r\nX-Content-Type-Options: nosniff\r\nSet-Cookie: p=opp\r\nSet-Cookie: b=sds\r\n\r\n[1, 2, 3, 4]'
    actual = response.to_data()
    #print("actual:",actual)
    assert expected == actual





def test1():
    res = Response()
    res.text("hello")
    expected = b'HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: 5\r\nX-Content-Type-Options: nosniff\r\n\r\nhello'
              #b'HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: 5\r\n\r\nhello'
    actual = res.to_data()
    #print(f"actual: {actual}")
    assert expected == actual

def test_headers_method():
    dic = {"Content-Type":"text/plain; charset=utf-8", "Cookie":"id=123; theme=dark"}
    response = Response()
    response.headers(dic)
    header_line = response.var_headers
    #rint(f"header_line inside test: {header_line}")
    dic2 = {"Host":"localhost:8080"}
    response.headers(dic2)
    #print("response.var_headers:",response.var_headers)
    assert response.var_headers == "\r\nContent-Type: text/plain; charset=utf-8\r\nCookie: id=123; theme=dark\r\nHost: localhost:8080\r\n\r\n"
                                 #b'\r\nContent-Type: text/plain; charset=utf-8\r\nCookie: id=123; theme=dark\r\nHost: localhost:8080\r\n\r\n'
        



def test_cookies_method():
    dic = {"id":"123","theme":"dark"} 
    response = Response()
    response.cookies(dic)
    cookie_line = response.var_cookies
    #print(f"cookie line: {cookie_line}")
    assert response.var_cookies == "\r\nSet-Cookie: id=123\r\nSet-Cookie: theme=dark\r\n\r\n"

    dic2 = {"x":"y","a":"b"}
    response.cookies(dic2)
    #print(f"the self.cooke:{response.var_cookies}")
    assert response.var_cookies == "\r\nSet-Cookie: id=123\r\nSet-Cookie: theme=dark\r\nSet-Cookie: x=y\r\nSet-Cookie: a=b\r\n\r\n"
    #print("test cookies method passed")
    




def test_headers_method2():
    response = Response()
    dic = {"id":"123", "theme":"dark"}
    dic2 = {"x":"y", "a":"b"}

    response.headers(dic)
    #print("WITH 1 DIC response.var_headers:",response.var_headers)
    assert response.var_headers == "\r\nid: 123\r\ntheme: dark\r\n\r\n"


    response.headers(dic2)
    #print("WITH 2 DIC response.var_headers:",response.var_headers)
    assert response.var_headers == "\r\nid: 123\r\ntheme: dark\r\nx: y\r\na: b\r\n\r\n"



if __name__ == '__main__':
    test1()
    test_headers_method()
    test_cookies_method()
    testMultipleToData()
    test_headers_method2()
    testJSON()

