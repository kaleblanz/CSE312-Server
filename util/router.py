#from response import Response 
from util.response import Response


import re

class Router:
    '''
    Router Class:
    *allows your server to route requests
    *given a certain method and path will call a certain function (action)
    '''
    def __init__(self):
        #fill in with instance variables to help other methods
        self.route = {}

    def add_route(self, method, path, action, exact_path=False):
        '''
        http method (method) -> string
        path of req (path) -> string
        function that handles request matching the given method and path (action) -> function
        if the path must match exactly or begin with provided path, default=false (exact_path) -> boolean
        no return
        '''
        #key of this dictionary will be a method + " " + route
        #and value is a list of [method,action,exact path]
        route_var = method + " " + path #+ " HTTP/1.1"
        self.route[route_var] = [action,exact_path]
        

    def route_request(self, request, handler):
        print(f"self.route:{self.route}")
        '''
        * takes a request object and a TCPHandler object (returns nothing)
        
        *method will check the method and path of the request object
        *determine which added path should be used, and call the function associated with that path (args: request obj, TCPHandler obj)
        '''
        request_method = request.method
        request_path = request.path
        request_method_path = request_method + " " + request_path

        func_called_bool = False

        '''
        maybe 1 if
        
        with the request line, see if it matches(exact or 'start substring' ) with any of the keys in the dict
        possible inputs:
        /public/image/image.webp
        /public/image/image.png
        '''
        
        for request_line in self.route:
             if re.match(request_line,request_method_path) is not None:
                  bool_path = self.route[request_line][1]
                  if bool_path == False: #(string has to be a substring)
                       func = self.route[request_line][0]
                       func(request,handler)
                       func_called_bool = True
                       print(f"the route from input request object:{request_method_path}      the request in self.route:{request_line}")
                       break
                  else:#when bool_path = true (strings have to be exact)
                      if request_line == request_method_path:
                          func = self.route[request_line][0]
                          func(request, handler)
                          func_called_bool = True
                          print(f"the route from input request object:{request_method_path}      the request in self.route:{request_line}")
                          break

        if func_called_bool == False:
            print("404 will be called!!!!!")
            #call 404
            response = Response()
            response.set_status(404,"Not Found")
            response.text("your path can not be found :(")
            response.to_data()


'''
from util.request import Request 
def test1():
    #404 error!
    router = Router()
    request = Request(b'GET /public/image HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
    router.add_route("GET","/public/image/dinosaour.png", action_function, False)
    print(router.route)
    router.route_request(request,None)
        

def test2():
    #404 should be called
    router = Router()
    request = Request(b'GET /public/image HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
    router.add_route("GET","chat.html",action_function,False)
    print(f"router.route:{router.route}")
    router.route_request(request, None)

def test3():
    #404 should be called
    router = Router()
    request = Request(b'GET /public/image HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
    router.add_route("GET","chat.html",action_function,False)
    router.add_route("GET","dog.html",action_function,False)
    router.add_route("GET","image.html",action_function,False)
    print(f"router.route:{router.route}")
    router.route_request(request, None)

def test4():
    #404 should be called
    router = Router()
    request = Request(b'GET /public/dog.html HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
    router.add_route("GET","chat.html",action_function,False)
    router.add_route("GET","dog.html",action_function,False)
    router.add_route("GET","image.html",action_function,False)
    print(f"router.route:{router.route}")
    router.route_request(request, None)

def test5():
    #the route from input request object:GET /public/image/eagle.jpg      the request in self.route:GET /public/image/
    router = Router()
    request = Request(b'GET /public/image/eagle.jpg HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
    router.add_route("GET","chat.html",action_function,False)
    router.add_route("GET","dog.html",action_function,False)
    router.add_route("GET","/public/image/",action_function,False)
    print(f"router.route:{router.route}")
    router.route_request(request, None)

def test6():
    #404 error
    router = Router()
    request = Request(b'GET /public/image/eagle.jpg HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
    router.add_route("GET","chat.html",action_function,False)
    router.add_route("GET","dog.html",action_function,False)
    router.add_route("GET","/public/image/",action_function,True)
    print(f"router.route:{router.route}")
    router.route_request(request, None)

def test7():
    #404 error
    router = Router()
    request = Request(b'GET /public/image/ HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
    router.add_route("GET","chat.html",action_function,False)
    router.add_route("GET","dog.html",action_function,False)
    router.add_route("POST","/public/image/",action_function,False)
    print(f"router.route:{router.route}")
    router.route_request(request, None)
    
def test8():
    #the route from input request object:GET /public/image/      the request in self.route:GET /public/image/
    router = Router()
    request = Request(b'GET /public/image/ HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
    router.add_route("GET","chat.html",action_function,False)
    router.add_route("GET","dog.html",action_function,False)
    router.add_route("GET","/public/image/",action_function,False)
    router.add_route("GET","/public/",action_function,False)
    print(f"router.route:{router.route}")
    router.route_request(request, None)

def test9():
    #print router.route: /
    router = Router()
    request = Request(b'GET /public/image/ HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
    router.add_route("GET","/",action_function,False)
    print(f"router.route:{router.route}")
    router.route_request(request, None)

def test10():
    #print 404 error
    router = Router()
    request = Request(b'GET /public/image/ HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
    router.add_route("GET","/",action_function,True)
    print(f"router.route:{router.route}")
    router.route_request(request, None)

def test11():
    #print 404 error
    router = Router()
    request = Request(b'GET /public/image/ HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
    router.add_route("GET", "/image/", action_function, False)
    print(f"router.route:{router.route}")
    router.route_request(request, None)

def test12():
    #print 404 error
    router = Router()
    request = Request(b'GET /public/image/ HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
    router.add_route("GET", "/image/", action_function, True)
    print(f"router.route:{router.route}")
    router.route_request(request, None)

def test13():
    #print 404
    router = Router()
    request = Request(b'POST / HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
    router.add_route("GET", "/", action_function, False)
    print(f"router.route:{router.route}")
    router.route_request(request, None)


def test14():
    #print path of /
    router = Router()
    request = Request(b'POST / HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
    router.add_route("POST", "/", action_function, True)
    print(f"router.route:{router.route}")
    router.route_request(request, None)



def action_function(request, handler):
    pass
     
    
if __name__ == '__main__':
    #test1()
    #test2()
    #test3()
    #test4()
    #test5()
    #test6()
    #test7()
    #test8()
    #test9()
    #test10()
    #test11()
    #test12()
    #test13()
    test14()
'''
