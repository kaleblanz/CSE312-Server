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


            print("received_data from ws path:",received_data)
            while True:
                received_data = self.request.recv(2048)

                frame = parse_ws_frame(received_data)
                #opcode is to close the connection
                if frame.opcode == 8:
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


                #send the init_strokes to active user:
                all_strokes = drawingBoard_collection.find({})
                strokes = []
                for stroke in all_strokes:
                    stroke.pop("_id")
                    strokes.append(stroke)
                dict_all_strokes = {"messageType":"init_strokes", "strokes" : strokes}
                print("dict_all_strokes:",dict_all_strokes)
                json_dict_all_strokes = json.dumps(dict_all_strokes)
                #self.request.sendall(generate_ws_frame(json_dict_all_strokes.encode()))
                #self.request.sendall(generate_ws_frame(b'meow'))

                json_result = json.dumps(dict_all_strokes)
                #self.request.sendall(generate_ws_frame(json_result.encode()))

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
                        #self.request.sendall(generate_ws_frame(json.dumps({'messageType': 'init_strokes', 'strokes': [{'startX': 377, 'startY': 395, 'endX': 377, 'endY': 395, 'color': '#000000'}, {'startX': 95, 'startY': 191, 'endX': 95, 'endY': 191, 'color': '#000000'}, {'startX': 95, 'startY': 191, 'endX': 95, 'endY': 191, 'color': '#000000'}, {'startX': 95, 'startY': 191, 'endX': 95, 'endY': 191, 'color': '#000000'}, {'startX': 95, 'startY': 191, 'endX': 97, 'endY': 191, 'color': '#000000'}, {'startX': 97, 'startY': 191, 'endX': 98, 'endY': 191, 'color': '#000000'}, {'startX': 98, 'startY': 191, 'endX': 100, 'endY': 191, 'color': '#000000'}, {'startX': 100, 'startY': 191, 'endX': 103, 'endY': 191, 'color': '#000000'}, {'startX': 103, 'startY': 191, 'endX': 111, 'endY': 191, 'color': '#000000'}, {'startX': 111, 'startY': 191, 'endX': 117, 'endY': 191, 'color': '#000000'}, {'startX': 117, 'startY': 191, 'endX': 121, 'endY': 191, 'color': '#000000'}, {'startX': 121, 'startY': 191, 'endX': 127, 'endY': 191, 'color': '#000000'}, {'startX': 127, 'startY': 191, 'endX': 132, 'endY': 191, 'color': '#000000'}, {'startX': 132, 'startY': 191, 'endX': 133, 'endY': 191, 'color': '#000000'}, {'startX': 133, 'startY': 191, 'endX': 137, 'endY': 191, 'color': '#000000'}, {'startX': 137, 'startY': 191, 'endX': 139, 'endY': 191, 'color': '#000000'}, {'startX': 139, 'startY': 191, 'endX': 140, 'endY': 191, 'color': '#000000'}, {'startX': 140, 'startY': 191, 'endX': 143, 'endY': 191, 'color': '#000000'}, {'startX': 143, 'startY': 191, 'endX': 146, 'endY': 191, 'color': '#000000'}, {'startX': 146, 'startY': 191, 'endX': 146, 'endY': 191, 'color': '#000000'}, {'startX': 146, 'startY': 191, 'endX': 148, 'endY': 191, 'color': '#000000'}, {'startX': 148, 'startY': 191, 'endX': 149, 'endY': 191, 'color': '#000000'}, {'startX': 149, 'startY': 191, 'endX': 149, 'endY': 191, 'color': '#000000'}, {'startX': 149, 'startY': 191, 'endX': 150, 'endY': 191, 'color': '#000000'}, {'startX': 150, 'startY': 191, 'endX': 151, 'endY': 191, 'color': '#000000'}, {'startX': 151, 'startY': 191, 'endX': 151, 'endY': 191, 'color': '#000000'}, {'startX': 151, 'startY': 191, 'endX': 152, 'endY': 191, 'color': '#000000'}, {'startX': 152, 'startY': 191, 'endX': 152, 'endY': 191, 'color': '#000000'}, {'startX': 152, 'startY': 191, 'endX': 152, 'endY': 191, 'color': '#000000'}, {'startX': 152, 'startY': 191, 'endX': 153, 'endY': 191, 'color': '#000000'}, {'startX': 153, 'startY': 191, 'endX': 153, 'endY': 191, 'color': '#000000'}, {'startX': 153, 'startY': 191, 'endX': 153, 'endY': 191, 'color': '#000000'}, {'startX': 33, 'startY': 134, 'endX': 33, 'endY': 134, 'color': '#ff9e9e'}, {'startX': 33, 'startY': 134, 'endX': 33, 'endY': 134, 'color': '#ff9e9e'}, {'startX': 33, 'startY': 134, 'endX': 21, 'endY': 60, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 60, 'endX': 21, 'endY': 60, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 60, 'endX': 21, 'endY': 60, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 60, 'endX': 21, 'endY': 60, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 60, 'endX': 21, 'endY': 61, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 61, 'endX': 21, 'endY': 61, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 61, 'endX': 21, 'endY': 62, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 62, 'endX': 21, 'endY': 62, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 62, 'endX': 21, 'endY': 63, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 63, 'endX': 21, 'endY': 64, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 64, 'endX': 21, 'endY': 64, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 64, 'endX': 21, 'endY': 65, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 65, 'endX': 21, 'endY': 67, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 67, 'endX': 21, 'endY': 67, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 67, 'endX': 21, 'endY': 69, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 69, 'endX': 21, 'endY': 71, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 71, 'endX': 21, 'endY': 72, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 72, 'endX': 21, 'endY': 74, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 74, 'endX': 21, 'endY': 77, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 77, 'endX': 21, 'endY': 78, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 78, 'endX': 21, 'endY': 80, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 80, 'endX': 21, 'endY': 82, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 82, 'endX': 21, 'endY': 83, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 83, 'endX': 21, 'endY': 85, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 85, 'endX': 21, 'endY': 88, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 88, 'endX': 21, 'endY': 89, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 89, 'endX': 21, 'endY': 91, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 91, 'endX': 21, 'endY': 93, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 93, 'endX': 21, 'endY': 94, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 94, 'endX': 21, 'endY': 96, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 96, 'endX': 21, 'endY': 99, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 99, 'endX': 21, 'endY': 100, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 100, 'endX': 21, 'endY': 102, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 102, 'endX': 21, 'endY': 104, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 104, 'endX': 21, 'endY': 105, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 105, 'endX': 21, 'endY': 106, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 106, 'endX': 20, 'endY': 109, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 109, 'endX': 20, 'endY': 111, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 111, 'endX': 20, 'endY': 113, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 113, 'endX': 20, 'endY': 116, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 116, 'endX': 20, 'endY': 118, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 118, 'endX': 20, 'endY': 120, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 120, 'endX': 20, 'endY': 123, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 123, 'endX': 20, 'endY': 125, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 125, 'endX': 20, 'endY': 127, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 127, 'endX': 20, 'endY': 130, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 130, 'endX': 20, 'endY': 132, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 132, 'endX': 20, 'endY': 134, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 134, 'endX': 20, 'endY': 135, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 135, 'endX': 20, 'endY': 136, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 136, 'endX': 20, 'endY': 138, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 138, 'endX': 20, 'endY': 139, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 139, 'endX': 20, 'endY': 139, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 139, 'endX': 20, 'endY': 140, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 140, 'endX': 20, 'endY': 141, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 141, 'endX': 20, 'endY': 141, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 141, 'endX': 20, 'endY': 142, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 142, 'endX': 20, 'endY': 143, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 143, 'endX': 20, 'endY': 143, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 143, 'endX': 20, 'endY': 144, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 144, 'endX': 20, 'endY': 145, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 145, 'endX': 20, 'endY': 146, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 146, 'endX': 20, 'endY': 147, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 147, 'endX': 20, 'endY': 148, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 148, 'endX': 20, 'endY': 149, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 149, 'endX': 20, 'endY': 150, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 150, 'endX': 20, 'endY': 151, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 151, 'endX': 20, 'endY': 152, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 152, 'endX': 20, 'endY': 153, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 153, 'endX': 20, 'endY': 154, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 154, 'endX': 20, 'endY': 154, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 154, 'endX': 20, 'endY': 155, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 155, 'endX': 20, 'endY': 156, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 156, 'endX': 20, 'endY': 156, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 156, 'endX': 20, 'endY': 157, 'color': '#ff9e9e'}, {'startX': 20, 'startY': 157, 'endX': 21, 'endY': 158, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 158, 'endX': 21, 'endY': 158, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 158, 'endX': 21, 'endY': 158, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 158, 'endX': 21, 'endY': 159, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 159, 'endX': 21, 'endY': 159, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 159, 'endX': 21, 'endY': 160, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 160, 'endX': 21, 'endY': 160, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 160, 'endX': 21, 'endY': 160, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 160, 'endX': 21, 'endY': 161, 'color': '#ff9e9e'}, {'startX': 21, 'startY': 161, 'endX': 22, 'endY': 161, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 161, 'endX': 22, 'endY': 161, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 161, 'endX': 22, 'endY': 161, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 161, 'endX': 22, 'endY': 162, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 162, 'endX': 22, 'endY': 162, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 162, 'endX': 22, 'endY': 162, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 162, 'endX': 22, 'endY': 163, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 163, 'endX': 22, 'endY': 164, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 164, 'endX': 22, 'endY': 165, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 165, 'endX': 22, 'endY': 166, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 166, 'endX': 22, 'endY': 167, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 167, 'endX': 22, 'endY': 167, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 167, 'endX': 22, 'endY': 169, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 169, 'endX': 22, 'endY': 169, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 169, 'endX': 22, 'endY': 170, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 170, 'endX': 22, 'endY': 171, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 171, 'endX': 22, 'endY': 172, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 172, 'endX': 22, 'endY': 172, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 172, 'endX': 22, 'endY': 173, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 173, 'endX': 22, 'endY': 174, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 174, 'endX': 22, 'endY': 174, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 174, 'endX': 22, 'endY': 175, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 175, 'endX': 22, 'endY': 175, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 175, 'endX': 22, 'endY': 176, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 176, 'endX': 22, 'endY': 176, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 176, 'endX': 22, 'endY': 176, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 176, 'endX': 22, 'endY': 177, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 177, 'endX': 22, 'endY': 177, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 177, 'endX': 22, 'endY': 177, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 177, 'endX': 22, 'endY': 177, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 177, 'endX': 22, 'endY': 178, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 178, 'endX': 22, 'endY': 178, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 178, 'endX': 22, 'endY': 178, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 178, 'endX': 22, 'endY': 178, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 178, 'endX': 22, 'endY': 179, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 179, 'endX': 22, 'endY': 179, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 179, 'endX': 22, 'endY': 179, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 179, 'endX': 22, 'endY': 179, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 179, 'endX': 22, 'endY': 179, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 179, 'endX': 22, 'endY': 180, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 180, 'endX': 22, 'endY': 180, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 180, 'endX': 22, 'endY': 180, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 180, 'endX': 22, 'endY': 181, 'color': '#ff9e9e'}, {'startX': 22, 'startY': 181, 'endX': 36, 'endY': 165, 'color': '#ff9e9e'}, {'startX': 36, 'startY': 165, 'endX': 36, 'endY': 165, 'color': '#ff9e9e'}, {'startX': 36, 'startY': 165, 'endX': 25, 'endY': 252, 'color': '#ff9e9e'}, {'startX': 25, 'startY': 252, 'endX': 50, 'endY': 169, 'color': '#ff9e9e'}, {'startX': 50, 'startY': 169, 'endX': 43, 'endY': 118, 'color': '#ff9e9e'}, {'startX': 43, 'startY': 118, 'endX': 39, 'endY': 153, 'color': '#ff9e9e'}, {'startX': 39, 'startY': 153, 'endX': 33, 'endY': 132, 'color': '#ff9e9e'}, {'startX': 33, 'startY': 132, 'endX': 33, 'endY': 132, 'color': '#ff9e9e'}, {'startX': 29, 'startY': 205, 'endX': 29, 'endY': 205, 'color': '#000000'}, {'startX': 294, 'startY': 213, 'endX': 294, 'endY': 213, 'color': '#000000'}, {'startX': 46, 'startY': 159, 'endX': 46, 'endY': 159, 'color': '#000000'}, {'startX': 31, 'startY': 114, 'endX': 31, 'endY': 114, 'color': '#FF0000'}, {'startX': 41, 'startY': 151, 'endX': 41, 'endY': 151, 'color': '#FF0000'}, {'startX': 28, 'startY': 121, 'endX': 28, 'endY': 121, 'color': '#000000'}, {'startX': 28, 'startY': 121, 'endX': 28, 'endY': 121, 'color': '#000000'}, {'startX': 28, 'startY': 121, 'endX': 28, 'endY': 121, 'color': '#000000'}, {'startX': 28, 'startY': 121, 'endX': 28, 'endY': 123, 'color': '#000000'}, {'startX': 28, 'startY': 123, 'endX': 28, 'endY': 126, 'color': '#000000'}, {'startX': 28, 'startY': 126, 'endX': 28, 'endY': 129, 'color': '#000000'}, {'startX': 28, 'startY': 129, 'endX': 28, 'endY': 133, 'color': '#000000'}, {'startX': 28, 'startY': 133, 'endX': 28, 'endY': 137, 'color': '#000000'}, {'startX': 28, 'startY': 137, 'endX': 28, 'endY': 139, 'color': '#000000'}, {'startX': 28, 'startY': 139, 'endX': 28, 'endY': 145, 'color': '#000000'}, {'startX': 28, 'startY': 145, 'endX': 28, 'endY': 151, 'color': '#000000'}, {'startX': 28, 'startY': 151, 'endX': 28, 'endY': 154, 'color': '#000000'}, {'startX': 28, 'startY': 154, 'endX': 28, 'endY': 159, 'color': '#000000'}, {'startX': 28, 'startY': 159, 'endX': 28, 'endY': 165, 'color': '#000000'}, {'startX': 28, 'startY': 165, 'endX': 28, 'endY': 167, 'color': '#000000'}, {'startX': 28, 'startY': 167, 'endX': 28, 'endY': 171, 'color': '#000000'}, {'startX': 28, 'startY': 171, 'endX': 28, 'endY': 175, 'color': '#000000'}, {'startX': 28, 'startY': 175, 'endX': 28, 'endY': 176, 'color': '#000000'}, {'startX': 28, 'startY': 176, 'endX': 28, 'endY': 178, 'color': '#000000'}, {'startX': 28, 'startY': 178, 'endX': 28, 'endY': 180, 'color': '#000000'}, {'startX': 28, 'startY': 180, 'endX': 28, 'endY': 182, 'color': '#000000'}, {'startX': 28, 'startY': 182, 'endX': 28, 'endY': 183, 'color': '#000000'}, {'startX': 28, 'startY': 185, 'endX': 28, 'endY': 186, 'color': '#000000'}, {'startX': 28, 'startY': 186, 'endX': 28, 'endY': 187, 'color': '#000000'}, {'startX': 28, 'startY': 187, 'endX': 28, 'endY': 188, 'color': '#000000'}, {'startX': 28, 'startY': 188, 'endX': 28, 'endY': 189, 'color': '#000000'}, {'startX': 28, 'startY': 189, 'endX': 28, 'endY': 190, 'color': '#000000'}, {'startX': 28, 'startY': 190, 'endX': 28, 'endY': 191, 'color': '#000000'}, {'startX': 28, 'startY': 191, 'endX': 28, 'endY': 193, 'color': '#000000'}, {'startX': 28, 'startY': 193, 'endX': 28, 'endY': 195, 'color': '#000000'}, {'startX': 28, 'startY': 195, 'endX': 28, 'endY': 196, 'color': '#000000'}, {'startX': 28, 'startY': 196, 'endX': 28, 'endY': 197, 'color': '#000000'}, {'startX': 28, 'startY': 197, 'endX': 28, 'endY': 199, 'color': '#000000'}, {'startX': 28, 'startY': 199, 'endX': 28, 'endY': 200, 'color': '#000000'}, {'startX': 28, 'startY': 200, 'endX': 28, 'endY': 202, 'color': '#000000'}, {'startX': 28, 'startY': 202, 'endX': 28, 'endY': 204, 'color': '#000000'}, {'startX': 28, 'startY': 204, 'endX': 28, 'endY': 205, 'color': '#000000'}, {'startX': 28, 'startY': 205, 'endX': 28, 'endY': 206, 'color': '#000000'}, {'startX': 28, 'startY': 206, 'endX': 28, 'endY': 208, 'color': '#000000'}, {'startX': 28, 'startY': 208, 'endX': 28, 'endY': 209, 'color': '#000000'}, {'startX': 28, 'startY': 209, 'endX': 28, 'endY': 210, 'color': '#000000'}, {'startX': 28, 'startY': 210, 'endX': 28, 'endY': 211, 'color': '#000000'}, {'startX': 28, 'startY': 211, 'endX': 28, 'endY': 212, 'color': '#000000'}, {'startX': 28, 'startY': 212, 'endX': 28, 'endY': 213, 'color': '#000000'}, {'startX': 28, 'startY': 213, 'endX': 28, 'endY': 215, 'color': '#000000'}, {'startX': 28, 'startY': 215, 'endX': 28, 'endY': 215, 'color': '#000000'}, {'startX': 28, 'startY': 215, 'endX': 28, 'endY': 217, 'color': '#000000'}, {'startX': 28, 'startY': 217, 'endX': 28, 'endY': 218, 'color': '#000000'}, {'startX': 28, 'startY': 218, 'endX': 28, 'endY': 219, 'color': '#000000'}, {'startX': 28, 'startY': 219, 'endX': 28, 'endY': 221, 'color': '#000000'}, {'startX': 28, 'startY': 222, 'endX': 28, 'endY': 224, 'color': '#000000'}, {'startX': 28, 'startY': 224, 'endX': 28, 'endY': 225, 'color': '#000000'}, {'startX': 28, 'startY': 225, 'endX': 28, 'endY': 227, 'color': '#000000'}, {'startX': 28, 'startY': 227, 'endX': 28, 'endY': 228, 'color': '#000000'}, {'startX': 28, 'startY': 228, 'endX': 28, 'endY': 229, 'color': '#000000'}, {'startX': 28, 'startY': 229, 'endX': 28, 'endY': 231, 'color': '#000000'}, {'startX': 28, 'startY': 231, 'endX': 28, 'endY': 232, 'color': '#000000'}, {'startX': 28, 'startY': 232, 'endX': 28, 'endY': 233, 'color': '#000000'}, {'startX': 28, 'startY': 233, 'endX': 28, 'endY': 234, 'color': '#000000'}, {'startX': 28, 'startY': 234, 'endX': 28, 'endY': 235, 'color': '#000000'}, {'startX': 28, 'startY': 235, 'endX': 28, 'endY': 236, 'color': '#000000'}, {'startX': 28, 'startY': 236, 'endX': 28, 'endY': 237, 'color': '#000000'}, {'startX': 28, 'startY': 237, 'endX': 28, 'endY': 238, 'color': '#000000'}, {'startX': 28, 'startY': 238, 'endX': 28, 'endY': 239, 'color': '#000000'}, {'startX': 28, 'startY': 239, 'endX': 28, 'endY': 240, 'color': '#000000'}, {'startX': 28, 'startY': 240, 'endX': 29, 'endY': 240, 'color': '#000000'}, {'startX': 29, 'startY': 240, 'endX': 29, 'endY': 241, 'color': '#000000'}, {'startX': 29, 'startY': 241, 'endX': 29, 'endY': 242, 'color': '#000000'}, {'startX': 29, 'startY': 242, 'endX': 29, 'endY': 242, 'color': '#000000'}, {'startX': 29, 'startY': 242, 'endX': 29, 'endY': 243, 'color': '#000000'}, {'startX': 29, 'startY': 243, 'endX': 29, 'endY': 243, 'color': '#000000'}, {'startX': 29, 'startY': 243, 'endX': 29, 'endY': 244, 'color': '#000000'}, {'startX': 29, 'startY': 244, 'endX': 29, 'endY': 244, 'color': '#000000'}, {'startX': 29, 'startY': 244, 'endX': 29, 'endY': 245, 'color': '#000000'}, {'startX': 29, 'startY': 245, 'endX': 29, 'endY': 245, 'color': '#000000'}, {'startX': 29, 'startY': 245, 'endX': 29, 'endY': 246, 'color': '#000000'}, {'startX': 29, 'startY': 246, 'endX': 29, 'endY': 246, 'color': '#000000'}, {'startX': 29, 'startY': 246, 'endX': 29, 'endY': 247, 'color': '#000000'}, {'startX': 29, 'startY': 247, 'endX': 29, 'endY': 247, 'color': '#000000'}, {'startX': 29, 'startY': 247, 'endX': 29, 'endY': 248, 'color': '#000000'}, {'startX': 29, 'startY': 248, 'endX': 30, 'endY': 249, 'color': '#000000'}, {'startX': 30, 'startY': 249, 'endX': 30, 'endY': 249, 'color': '#000000'}, {'startX': 30, 'startY': 249, 'endX': 30, 'endY': 249, 'color': '#000000'}, {'startX': 30, 'startY': 249, 'endX': 30, 'endY': 250, 'color': '#000000'}, {'startX': 30, 'startY': 250, 'endX': 30, 'endY': 250, 'color': '#000000'}, {'startX': 30, 'startY': 250, 'endX': 30, 'endY': 250, 'color': '#000000'}, {'startX': 58, 'startY': 162, 'endX': 58, 'endY': 162, 'color': '#000000'}, {'startX': 58, 'startY': 162, 'endX': 58, 'endY': 162, 'color': '#000000'}, {'startX': 58, 'startY': 162, 'endX': 58, 'endY': 162, 'color': '#000000'}, {'startX': 58, 'startY': 162, 'endX': 58, 'endY': 162, 'color': '#000000'}, {'startX': 58, 'startY': 162, 'endX': 57, 'endY': 162, 'color': '#000000'}, {'startX': 57, 'startY': 162, 'endX': 57, 'endY': 162, 'color': '#000000'}, {'startX': 56, 'startY': 163, 'endX': 55, 'endY': 164, 'color': '#000000'}, {'startX': 55, 'startY': 164, 'endX': 54, 'endY': 165, 'color': '#000000'}, {'startX': 54, 'startY': 165, 'endX': 52, 'endY': 166, 'color': '#000000'}, {'startX': 52, 'startY': 166, 'endX': 50, 'endY': 168, 'color': '#000000'}, {'startX': 50, 'startY': 168, 'endX': 47, 'endY': 170, 'color': '#000000'}, {'startX': 47, 'startY': 170, 'endX': 46, 'endY': 172, 'color': '#000000'}, {'startX': 46, 'startY': 172, 'endX': 42, 'endY': 174, 'color': '#000000'}, {'startX': 42, 'startY': 174, 'endX': 39, 'endY': 177, 'color': '#000000'}, {'startX': 39, 'startY': 177, 'endX': 38, 'endY': 179, 'color': '#000000'}, {'startX': 38, 'startY': 179, 'endX': 34, 'endY': 182, 'color': '#000000'}, {'startX': 34, 'startY': 182, 'endX': 32, 'endY': 185, 'color': '#000000'}, {'startX': 32, 'startY': 185, 'endX': 31, 'endY': 186, 'color': '#000000'}, {'startX': 31, 'startY': 186, 'endX': 29, 'endY': 188, 'color': '#000000'}, {'startX': 29, 'startY': 188, 'endX': 27, 'endY': 190, 'color': '#000000'}, {'startX': 27, 'startY': 190, 'endX': 26, 'endY': 190, 'color': '#000000'}, {'startX': 26, 'startY': 190, 'endX': 24, 'endY': 192, 'color': '#000000'}, {'startX': 24, 'startY': 192, 'endX': 23, 'endY': 193, 'color': '#000000'}, {'startX': 23, 'startY': 193, 'endX': 23, 'endY': 194, 'color': '#000000'}, {'startX': 23, 'startY': 194, 'endX': 21, 'endY': 195, 'color': '#000000'}, {'startX': 21, 'startY': 195, 'endX': 21, 'endY': 196, 'color': '#000000'}, {'startX': 21, 'startY': 196, 'endX': 20, 'endY': 197, 'color': '#000000'}, {'startX': 20, 'startY': 197, 'endX': 19, 'endY': 198, 'color': '#000000'}, {'startX': 19, 'startY': 198, 'endX': 19, 'endY': 198, 'color': '#000000'}, {'startX': 19, 'startY': 198, 'endX': 19, 'endY': 199, 'color': '#000000'}, {'startX': 19, 'startY': 199, 'endX': 18, 'endY': 199, 'color': '#000000'}, {'startX': 18, 'startY': 199, 'endX': 18, 'endY': 199, 'color': '#000000'}, {'startX': 18, 'startY': 199, 'endX': 18, 'endY': 200, 'color': '#000000'}, {'startX': 18, 'startY': 200, 'endX': 17, 'endY': 200, 'color': '#000000'}, {'startX': 17, 'startY': 200, 'endX': 17, 'endY': 200, 'color': '#000000'}, {'startX': 17, 'startY': 200, 'endX': 17, 'endY': 200, 'color': '#000000'}, {'startX': 17, 'startY': 200, 'endX': 16, 'endY': 201, 'color': '#000000'}, {'startX': 16, 'startY': 201, 'endX': 16, 'endY': 201, 'color': '#000000'}, {'startX': 18, 'startY': 236, 'endX': 18, 'endY': 236, 'color': '#000000'}, {'startX': 18, 'startY': 236, 'endX': 33, 'endY': 300, 'color': '#000000'}, {'startX': 33, 'startY': 300, 'endX': 22, 'endY': 166, 'color': '#000000'}, {'startX': 86, 'startY': 219, 'endX': 86, 'endY': 219, 'color': '#000000'}, {'startX': 16, 'startY': 154, 'endX': 16, 'endY': 154, 'color': '#000000'}, {'startX': 27, 'startY': 149, 'endX': 27, 'endY': 149, 'color': '#000000'}, {'startX': 27, 'startY': 149, 'endX': 27, 'endY': 149, 'color': '#000000'}, {'startX': 36, 'startY': 134, 'endX': 36, 'endY': 134, 'color': '#000000'}, {'startX': 36, 'startY': 134, 'endX': 36, 'endY': 135, 'color': '#000000'}, {'startX': 36, 'startY': 135, 'endX': 36, 'endY': 136, 'color': '#000000'}, {'startX': 36, 'startY': 136, 'endX': 36, 'endY': 137, 'color': '#000000'}, {'startX': 36, 'startY': 137, 'endX': 36, 'endY': 139, 'color': '#000000'}, {'startX': 36, 'startY': 139, 'endX': 36, 'endY': 144, 'color': '#000000'}, {'startX': 36, 'startY': 149, 'endX': 36, 'endY': 153, 'color': '#000000'}, {'startX': 36, 'startY': 153, 'endX': 36, 'endY': 160, 'color': '#000000'}, {'startX': 36, 'startY': 160, 'endX': 36, 'endY': 169, 'color': '#000000'}, {'startX': 36, 'startY': 169, 'endX': 36, 'endY': 175, 'color': '#000000'}, {'startX': 36, 'startY': 175, 'endX': 36, 'endY': 187, 'color': '#000000'}, {'startX': 36, 'startY': 187, 'endX': 36, 'endY': 202, 'color': '#000000'}, {'startX': 36, 'startY': 210, 'endX': 36, 'endY': 221, 'color': '#000000'}, {'startX': 36, 'startY': 221, 'endX': 36, 'endY': 234, 'color': '#000000'}, {'startX': 36, 'startY': 234, 'endX': 36, 'endY': 238, 'color': '#000000'}, {'startX': 36, 'startY': 238, 'endX': 36, 'endY': 243, 'color': '#000000'}, {'startX': 36, 'startY': 243, 'endX': 36, 'endY': 249, 'color': '#000000'}, {'startX': 36, 'startY': 249, 'endX': 36, 'endY': 252, 'color': '#000000'}, {'startX': 36, 'startY': 252, 'endX': 36, 'endY': 254, 'color': '#000000'}, {'startX': 36, 'startY': 254, 'endX': 36, 'endY': 257, 'color': '#000000'}, {'startX': 36, 'startY': 257, 'endX': 36, 'endY': 257, 'color': '#000000'}, {'startX': 99, 'startY': 247, 'endX': 99, 'endY': 247, 'color': '#000000'}, {'startX': 47, 'startY': 198, 'endX': 47, 'endY': 198, 'color': '#000000'}, {'startX': 44, 'startY': 219, 'endX': 44, 'endY': 219, 'color': '#000000'}, {'startX': 79, 'startY': 254, 'endX': 79, 'endY': 254, 'color': '#000000'}]}).encode()))

                    if payload['messageType'] == 'echo_client':
                        pass
                    #self.request.sendall(generate_ws_frame(b'meow'))

                #buffering for payload size between >=126 and <65536
                if payload_length == 126:
                    extended_payload_length = (received_data[2]<<8) + received_data[3]
                    print(f"inside buffering, extended_payload_length:{extended_payload_length}")
                    total_receive_bytes = received_data
                    while len(total_receive_bytes) < extended_payload_length + 8:
                        total_receive_bytes += self.request.recv(2048)
                    print("total_receive_bytes:",total_receive_bytes)

                #buffering for payload size >=65536
                if payload_length == 127:
                    extended_payload_length = (received_data[2]<<56) + (received_data[3]<<48) + (received_data[4]<<40) + (received_data[5]<<32) + (received_data[6]<<24) + (received_data[7]<<16) + (received_data[8]<<8) + received_data[9]
                    print(f"inside buffering, extended_payload_length:{extended_payload_length}")
                    total_receive_bytes = received_data
                    while len(total_receive_bytes) < extended_payload_length + 14:
                        total_receive_bytes += self.request.recv(2048)
                    print("total_receive_bytes:", total_receive_bytes)


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