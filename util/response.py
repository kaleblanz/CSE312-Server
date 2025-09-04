import json

'''
Response Class:
* helps you construct a response to sent to the client
* i will constuct end responses at every endpoint that i have (this makes my life/code a lot easier) 
'''
'''
before i send, i have to remove the ';' in the cookies string AND RSTRIP (and maybe even a \r\n)
and add another \r\n to the headers string
'''
class Response:
    def __init__(self):
        #create instace variables that will be used in different methods

        #defualt values for status code and message if set_status() is never called
        self.var_status_code = 200
        self.var_status_msg = "OK"

        #REMEMBER TO ADD NO SNIFF
        self.var_headers = "\r\n"

        self.var_cookies = ""

        self.var_body = b""

        self.var_content_type = "text/plain; charset=utf-8"

    def set_status(self, code, text):
        #code -> int
        #text -> string
        self.var_status_code = code
        self.var_status_msg = text
        return self

    def headers(self, headers):
        #headers -> dict:{str=str}
        #iterate through each k-v and form a string and add it to header variable
        for header in headers:
            header_value = headers[header]
            self.var_headers += header + ": " + header_value + "\r\n"
            #print(f"each header line: {self.var_headers}")
        return self

    def cookies(self, cookies):
        #cookies -> dict {str -> str}
        #Cookie: name=value; name2=value2; name3=value3
        value_string = ": "

        #true when first time adding
        if self.var_cookies == "":
            for cookie in cookies:
                value = cookies[cookie]
                value_string+= cookie + "=" + value + "; "
            self.var_cookies = "Cookie" + value_string
            print("value string: ",value_string)
        #true when 2nd time or more adding
        else:
            value_string = ""
            for cookie in cookies:
                value = cookies[cookie]
                value_string+= cookie + "=" + value + "; "
            self.var_cookies += value_string

        return self

    def bytes(self, data):
        #data -> bytes
        #append the already bytes of body to the request.var_body
        self.var_body += data
        return self

    def text(self, data):
        #data -> string
        data_bytes = data.encode()
        self.var_body+= data_bytes
        return self

    def json(self, data):
        #data -> {} OR []
        #change content type
        self.var_content_type = "application/json"
        #turn the data input to a json string then decode to bytes
        self.var_body = json.dumps().encode()
        return self

    def to_data(self):
        return b''


def test1():
    res = Response()
    res.text("hello")
    expected = b'HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: 5\r\n\r\nhello'
    actual = res.to_data()

    assert expected == actual

def test_headers_method():
    dic = {"Content-Type":"text/plain; charset=utf-8", "Cookie":"id=123; theme=dark"}
    response = Response()
    response.headers(dic)
    header_line = response.var_headers
    print(f"header_line inside test: {header_line}")
    dic2 = {"Host":"localhost:8080"}
    response.headers(dic2)
    assert response.var_headers == "\r\nContent-Type: text/plain; charset=utf-8\r\nCookie: id=123; theme=dark\r\nHost: localhost:8080\r\n"

def test_cookies_method():
    dic = {"id":"123","theme":"dark"} 
    response = Response()
    response.cookies(dic)
    cookie_line = response.var_cookies
    print(f"cookie line: {cookie_line}")

    dic2 = {"x":"y","a":"b"}
    response.cookies(dic2)
    print(f"the self.cooke:{response.var_cookies}")
    assert response.var_cookies.rstrip() == "Cookie: id=123; theme=dark; x=y; a=b;"
                                  #"Cookie: id=123; theme=dark; x=y; a=b;"

if __name__ == '__main__':
    #test1()
    test_headers_method()
    test_cookies_method()

