from request import Request 
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
        '''
        * takes a request object and a TCPHandler object (returns nothing)
        
        *method will check the method and path of the request object
        *determine which added path should be used, and call the function associated with that path (args: request obj, TCPHandler obj)
        '''
        request_method = request.method
        request_path = request.path
        request_method_path = request_method + " " + request_path

        '''
        with the request line, see if it matches(exact or 'start substring' ) with any of the keys in the dict
        possible inputs:
        /public/image/image.webp
        /public/image/image.png
        
        '''
        '''
        #this should deal for the multiple image type case
        if re.match("/public/image/",request_method_path) != None:
            if request_method_path in self.route:
                  func = self.route[request_method_path][0]
                  func(request,handler)
            else:
                exact_bool = self.route[request_method_path][1]
                if exact_bool == True and request_method_path not in self.route:
                     pass
                    #return 404
                func = self.route["/public/image/"]
                func(request,handler)[0]
        
        #if the request line is a route in the set of keys in the objects dicitionary
        elif (request_method_path in self.route):
            func = self.route[request_method_path][0]
            func(request,handler)
        
        #if both of those fail, send a response with a 404
        else:
            pass
        '''


def test1():
        router = Router()
        request = Request(b'GET / HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
        router.add_route("GET","/public/image", None, False)
        print(router.route)
        router.route_request(request,None)


    
if __name__ == '__main__':
        test1()
    
