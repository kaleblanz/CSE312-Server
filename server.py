import json
import socketserver

from util.database import drawingBoard_collection
from util.request import Request
from util.router import Router
from util.hello_path import hello_path
from util.websockets import *

#import all functions from path_functions
from path_functions import *

#parse mutlimeida function
from util.multipart import parse_multipart

user_list = []

class MyTCPHandler(socketserver.BaseRequestHandler):

    def __init__(self, request, client_address, server):
        self.router = Router()

        #example route
        #self.router.add_route("GET", "/hello", hello_path, True)
        # TODO: Add your routes here

        #render the home page which is index.html at path: "/"
        #$ is for re, makes it so string only matches with the slash
        self.router.add_route("GET","/$", render_index_html)

        self.router.add_route("GET","/chat",render_index_html )

        #render any images
        # dot means - amything can replace the dot besides an empty string
        self.router.add_route("GET","/public/imgs/.",render_images)

        #render js
        self.router.add_route("GET", "/public/js/.", render_js)

        #add create message route
        self.router.add_route("POST","/api/chats", create_message_route)

        # add GET message route
        self.router.add_route("GET", "/api/chats", get_message_route)

        # add PATCH message route
        # the period is for the id that is to be expected
        self.router.add_route("PATCH", f"/api/chats/.", update_message_route)

        # add DELETE message route
        #period makes it so we can get the id
        self.router.add_route("DELETE",f"/api/chats/." ,delete_message_route)


        #HW 2 ROUTES:
        #render all html routes for hw2:
        #render the html register page
        self.router.add_route("GET", "/register", render_index_html)
        # render the html login page
        self.router.add_route("GET", "/login", render_index_html)
        # render html settings page
        self.router.add_route("GET","/settings", render_index_html)
        #render search-users html
        self.router.add_route("GET","/search-users",render_index_html)

        #add the route for Registration
        self.router.add_route("POST", "/register", post_registration_route)

        #add the route for login
        self.router.add_route("POST", "/login", post_login_route)

        #add the route for logout
        self.router.add_route("GET", "/logout", get_logout_route)

        #add route for @me that display username
        self.router.add_route("GET", "/api/users/@me", return_profile_route)

        #add route for filter and search users
        self.router.add_route("GET" , "/api/users/search" , filer_search_users_route)

        #add route to update profile
        self.router.add_route("POST", "/api/users/settings", update_profile_route)

        #HW2 AO 2FA TOTP
        self.router.add_route("POST","/api/totp/enable", totp_2fa_route)

        #HW2 AO OAuth 2.0 GitHub Sign In
        #route is to request the users GitHub identity
        self.router.add_route("GET","/authgithub", request_user_github_identity_route, True)

        #route is to handle when user is redirected back to our web app
        self.router.add_route("GET","/authcallback", code_for_access_code_github_route)


        #HW 3 HTML Routes
        #render change avatar page
        self.router.add_route("GET","/change-avatar", render_index_html)
        # handle file uploads from user for avatar
        self.router.add_route("POST", "/api/users/avatar", avatar_upload_route)



        #render page that displays all videos
        self.router.add_route("GET", "/videotube", render_index_html)

        #render upload video form
        self.router.add_route("GET", "/videotube/upload", render_index_html)

        #rendering to display a single video using the id, the '.' allows any id
        self.router.add_route("GET", "/videotube/videos/.", render_index_html)

        #upload videos
        self.router.add_route("POST","/api/videos", upload_video_route)

        #retrieve all videos
        self.router.add_route("GET","/api/videos", get_all_videos_route, True)

        #retreive a single video
        self.router.add_route("GET", "/api/videos/.", get_one_video_route)

        #render videos
        #self.router.add_route("GET", "/public/video/.", render_video)
        self.router.add_route("GET", "/public/videos/.", render_video)

        #HW 3 AO1
        #render html to change thumbnails
        self.router.add_route("GET","/videotube/set-thumbnail", render_index_html)

        #route to change thumbnail
        self.router.add_route("PUT","/api/thumbnails/.", change_thumbnail_route)



        #HW 4
        #echo page
        self.router.add_route("GET", "/test-websocket", render_index_html)
        #drawing board page
        self.router.add_route("GET", "/drawing-board", render_index_html)
        #video call page
        self.router.add_route("GET", "/video-call", render_index_html)
        #video call room page via an id
        self.router.add_route("GET", "/video-call/.", render_index_html)

        #route to upgrade to websocket
        #self.router.add_route("GET", "/websocket", upgrade_websocket_route)


        super().__init__(request, client_address, server)

    def handle(self):
        received_data = self.request.recv(2048)

        #print(self.client_address)
        #print("--- received data ---")
        #print(received_data)
        #print("--- end of data ---\n\n")
        request = Request(received_data)

        #true when user requests a WebSocket
        if request.path == "/websocket":
            auth_token = request.cookies['auth_token']

            hash_auth = hashlib.sha256(auth_token.encode()).hexdigest()
            user = user_collection.find_one({"auth_token" : hash_auth})
            user_list.append({"username": user['username'], "tcp_handler": self})
            print(f"self in hande:{self.client_address}")
            #response to accept websocket
            response = handshake_ws(request)

            # send 101 switching protocols to start http
            self.request.sendall(response.to_data())

            #broadcast this message to all WS users because a new handshake has occurred
            broadcast_active_user_list()

            # send the init_strokes to active user:
            all_strokes = drawingBoard_collection.find({})
            strokes = []
            for stroke in all_strokes:
                stroke.pop("_id")
                strokes.append(stroke)
            dict_all_strokes = {"messageType": "init_strokes", "strokes": strokes}
            print("dict_all_strokes:", dict_all_strokes)
            json_dict_all_strokes = json.dumps(dict_all_strokes)
            self.request.sendall(generate_ws_frame(json_dict_all_strokes.encode()))


            print("received_data from ws path:",received_data)
            while True:
                received_data = self.request.recv(2048)

                opcode_mask = 0b00001111
                opcode = received_data[0] & opcode_mask

                #frame = parse_ws_frame(received_data)
                #opcode is to close the connection
                if opcode == 8:
                    #remove the name from active_user_list
                    name = user['username']

                    #send the closing frame to the client
                    byte0 = 0b10001000 #1 fin bit and 1000 for close connection
                    byte1 = 0b00000000
                    combine_b0_b1 = byte0.to_bytes(1,'little') + byte1.to_bytes(1,'little')
                    self.request.sendall(generate_ws_frame(combine_b0_b1))

                    # delete the name from user_list
                    user_list.remove({"username": name, "tcp_handler": self})
                    # broadcast our new userlist after the removal
                    broadcast_active_user_list()

                    #break the while true
                    return


                #add a buffer
                #read the payload_length and make sure you've read that many bytes
                byte1 = received_data[1]
                payload_length_mask = 0b01111111
                payload_length = byte1 & payload_length_mask
                print(f"inside buffering, payload_length:{payload_length}")




                #buffering for payload<126 (probably don't need this)
                if payload_length < 126:
                    total_receive_bytes = received_data
                    while len(total_receive_bytes) < payload_length + 6:
                        total_receive_bytes += self.request.recv(2048)
                    print("total_receive_bytes:", total_receive_bytes)
                    frame = parse_ws_frame(total_receive_bytes)
                    payload = json.loads(frame.payload.decode())
                    print(f"payload:{payload}")
                    #self.request.sendall(generate_ws_frame(json_result.encode()))
                    #means user is drawing on the drawing board
                    if payload['messageType'] == 'drawing':
                        #update our db storing all drawings
                        draw_dict = {"startX" : payload['startX'], "startY": payload['startY'] ,
                         "endX": payload['endX'] , "endY":  payload['endY'] ,  "color": payload['color'] }
                        drawingBoard_collection.insert_one(draw_dict)

                        #broadcast this drawing to every active user with WS connection
                        broadcast_drawing_content(payload)

                    if payload['messageType'] == 'echo_client':
                        response_dict = {"messageType": "echo_server", "text": payload['text']}
                        json_decode = json.dumps(response_dict).encode()
                        self.request.sendall(generate_ws_frame(json_decode))

                #buffering for payload size between >=126 and <65536
                if payload_length == 126:
                    extended_payload_length = (received_data[2]<<8) + received_data[3]
                    print(f"inside buffering, extended_payload_length:{extended_payload_length}")
                    total_receive_bytes = received_data
                    while len(total_receive_bytes) < extended_payload_length + 8:
                        total_receive_bytes += self.request.recv(2048)
                    print("total_receive_bytes:",total_receive_bytes)

                    frame = parse_ws_frame(total_receive_bytes)
                    payload = json.loads(frame.payload.decode())
                    print(f"payload:{payload}")
                    # self.request.sendall(generate_ws_frame(json_result.encode()))
                    # means user is drawing on the drawing board
                    if payload['messageType'] == 'drawing':
                        # update our db storing all drawings
                        draw_dict = {"startX": payload['startX'], "startY": payload['startY'],
                                     "endX": payload['endX'], "endY": payload['endY'], "color": payload['color']}
                        drawingBoard_collection.insert_one(draw_dict)

                        # broadcast this drawing to every active user with WS connection
                        broadcast_drawing_content(payload)

                    if payload['messageType'] == 'echo_client':
                        response_dict = {"messageType": "echo_server", "text": payload['text']}
                        json_decode = json.dumps(response_dict).encode()
                        self.request.sendall(generate_ws_frame(json_decode))



                #buffering for payload size >=65536
                if payload_length == 127:
                    extended_payload_length = (received_data[2]<<56) + (received_data[3]<<48) + (received_data[4]<<40) + (received_data[5]<<32) + (received_data[6]<<24) + (received_data[7]<<16) + (received_data[8]<<8) + received_data[9]
                    print(f"inside buffering, extended_payload_length:{extended_payload_length}")
                    total_receive_bytes = received_data
                    while len(total_receive_bytes) < extended_payload_length + 14:
                        total_receive_bytes += self.request.recv(2048)
                    print("total_receive_bytes:", total_receive_bytes)

                    frame = parse_ws_frame(total_receive_bytes)
                    payload = json.loads(frame.payload.decode())
                    print(f"payload:{payload}")
                    # self.request.sendall(generate_ws_frame(json_result.encode()))
                    # means user is drawing on the drawing board
                    if payload['messageType'] == 'drawing':
                        # update our db storing all drawings
                        draw_dict = {"startX": payload['startX'], "startY": payload['startY'],
                                     "endX": payload['endX'], "endY": payload['endY'], "color": payload['color']}
                        drawingBoard_collection.insert_one(draw_dict)

                        # broadcast this drawing to every active user with WS connection
                        broadcast_drawing_content(payload)

                    if payload['messageType'] == 'echo_client':
                        response_dict = {"messageType": "echo_server", "text": payload['text']}
                        json_decode = json.dumps(response_dict).encode()
                        self.request.sendall(generate_ws_frame(json_decode))


                print("buffer recv data:",received_data)
                print_pretty_frame(received_data)



        else:
            """
            create a buffer:
            * read the content length of the request and buffer until you read the whole body
            """
            all_bytes = received_data
            if "Content-Length" in request.headers:
                accumulated_body = len(request.body)

                total_size = int(request.headers["Content-Length"])
                #print(f"total_size:{total_size}         type:{type(total_size)}")
                #print(f"accumbody:{accumulated_body}         type:{type(accumulated_body)}")
                while accumulated_body < total_size:
                    new_data = self.request.recv(2048)
                    all_bytes+=new_data
                    if not new_data:
                        break
                    #print(f"new_data:{new_data}")
                    #new_request = Request(new_data)
                    accumulated_body += len(new_data)
                    request.body += new_data
                #print(f"request that was buffered body:{len(request.body)}")
                #print(f"allbytes:{all_bytes}")
                self.router.route_request(request,self)
            else:
                self.router.route_request(request, self)



def main():
    host = "0.0.0.0"
    port = 8080
    socketserver.ThreadingTCPServer.allow_reuse_address = True

    server = socketserver.ThreadingTCPServer((host, port), MyTCPHandler)

    print("Listening on port " + str(port))
    server.serve_forever()


def broadcast_active_user_list():
    # user_list = [{"tcp_handler" : tcp, "username":"username"}, ...]
    for user in user_list:
        tcp_handler = user['tcp_handler']
        user = user['username']
        all_usernames = []
        for username in user_list:
            all_usernames.append({"username": username['username']})
        result = {"messageType": "active_users_list", "users": all_usernames}
        json_result = json.dumps(result)
        tcp_handler.request.sendall(generate_ws_frame(json_result.encode()))

def broadcast_drawing_content(payload):
    for user in user_list:
        tcp_handler = user['tcp_handler']

        json_result = json.dumps(payload)
        tcp_handler.request.sendall(generate_ws_frame(json_result.encode()))


def remove_user_from_user_list(name):
    new_user_list = []
    for user in user_list:
        username = user['username']
        if username != name:
            new_user_list.append(user)
    return new_user_list




if __name__ == "__main__":
    main()


"""
inside handle:
have our router send this to your function handling webSocket connections
    inside this we'll do the handshake
send the handshake over the socket then enter the infinite loop

while true:
    rec_data = recv(2048)
    print(rec_data)
"""

#going to have to track all of our websocket connections
    #keep track of every open connection
#LO -> need buffer, but don't need to worry about reading too much
"""
# WS handshake is complete
# can't let the method to end

while true:
    listen for msg over tcp connection, call recv and when we buffer multimedia
        except now what we expect to recv are frames not http
    if we see an opcode of 8 (b1000) -> 
        BREAK, method end, tcp connection close, clean up DS tracking open web socket connections
        
"""

"""
buffering:
    same as hw 3
    when you get a frame, check payload length, make sure you've read that many bytes
    (make sure you don't count the bytes of the headers)
    if you haven't read that many bytes, you're in a buffering state
        keep reading from the socket until you've read that many bytes
        
    
"""