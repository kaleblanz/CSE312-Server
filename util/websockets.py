import base64
import hashlib

from charset_normalizer import from_bytes

from util.FRAME_OBJ import FRAME_OBJ
from util.response import Response


#takes WS Key and returns accept string
def compute_accept(ws_key):
    #appends guid to ws_key
    guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    accept_str = ws_key + guid

    #compute sha-1
    hash_accept = hashlib.sha1(accept_str.encode()).digest()


    #base64 encode of the hash
    base64_of_hash_accept = base64.encodebytes(hash_accept).decode()

    #strip the trailing \n
    return base64_of_hash_accept.strip()


#takes bytes that represents ws frame
def parse_ws_frame(frame_bytes):
    frame_obj = FRAME_OBJ()

    #get the fin bit
    byte0 = frame_bytes[0]
    fin_bit_mask = 0b10000000
    fin_bit = byte0 & fin_bit_mask
    fin_bit_shift = fin_bit >> 7
    frame_obj.fin_bit = fin_bit_shift

    #get the opcode
    opcode_mask = 0b00001111
    opcode = byte0 & opcode_mask
    frame_obj.opcode = opcode

    #get the payload_length
    byte1 = frame_bytes[1]
    payload_length_mask = 0b01111111
    payload_length = byte1 & payload_length_mask
    frame_obj.payload_length = payload_length

    #length is 7 bits
    if frame_obj.payload_length < 126:
        print("length is 7 bits")
        combine_mask_bytes = (frame_bytes[2]<<24) + (frame_bytes[3]<<16) + (frame_bytes[4]<<8) + frame_bytes[5]
        combine_mask_bytes_list = [frame_bytes[2], frame_bytes[3], frame_bytes[4], frame_bytes[5]]
        print("byte2:", frame_bytes[2])
        print("byte3:", frame_bytes[3])
        print("byte4:", frame_bytes[4])
        print("byte5:", frame_bytes[5])
        print(f"combine_mask_bytes:{combine_mask_bytes}")
        print(f"combine_mask_bytes_list:{combine_mask_bytes_list}")

        byte_str = b''
        #accumulator for out byte_str
        for i in range(0,frame_obj.payload_length):
            #6+i because we start at the 6th byte
            # the byte of payload data
            payload_byte = frame_bytes[6+i]
            # mask byte from from our mask 4 bytes
            mask_byte = combine_mask_bytes_list[i%4]
            # XOR payload byte and mask byte
            byte_after_masking = payload_byte ^ mask_byte
            # convert out resultant masked integer to its byte representation
            byte_str += byte_after_masking.to_bytes(1,"big")
                                    #1 is for byte length -> 1 byte
        frame_obj.payload = byte_str
        print("byte_str:",byte_str)



    #length is 16 bits
    elif frame_obj.payload_length == 126:
        print("length is 16 bits")
        #bytes 2 and 3 contain our payload
        #left shift byte 2 8 bits because byte2 is the MSByte
        payload_length = (frame_bytes[2]<<8) + frame_bytes[3]
        frame_obj.payload_length = payload_length
        print("payload_length:",frame_obj.payload_length)

        #mask are bytes 4,5,6,7
        mask_list = [frame_bytes[4], frame_bytes[5], frame_bytes[6], frame_bytes[7]]

        payload = b''
        for i in range(0, frame_obj.payload_length):
            #8th byte in frame is the first byte of payload_data
            payload_byte = frame_bytes[8+i]
            # correct mask byte to mask for the correct payload byte
            mask_byte = mask_list[i%4]
            # XOR the payload_byte and mask_byte
            masked_payload = payload_byte ^ mask_byte
            #turn our masked integer to its byte equivalent
            payload += masked_payload.to_bytes(1,'little')

            if i > 2030:
                print(f"i:{i}       payload:{payload}")

        frame_obj.payload = payload
        print(f"payload:{frame_obj.payload}")





    #length is 64 bits
    else:
        print("length is 64 bits")




    return frame_obj






#take request and return response accepting upgrade to webSocket
def handshake_ws(request):
    ws_key = request.headers['Sec-WebSocket-Key']
    accept_key = compute_accept(ws_key)

    response = Response()
    response.set_status(101, "Switching Protocols")
    response.headers({"Connection": "Upgrade", "Upgrade": "websocket",
                      "Sec-Websocket-Accept": accept_key})
    return response

def byte_to_binary_string(byte_):
    # convert my byte to binary -> then to string -> remove the 0b
    as_binary = str(bin(byte_))[2:]

    for _ in range(len(as_binary), 8):
        as_binary = '0' + as_binary
    return as_binary

def print_pretty_frame(data):
    print("-------WebSocket Frame:")
    new_line_counter = 0
    for i in data:
        # end in print is now assigned a space inbetween each print
        print(byte_to_binary_string(i), end=' ')
        new_line_counter = new_line_counter + 1
        if new_line_counter == 4:
            print()
            new_line_counter = 0
    print("\n---------- END OF FRAME ----------")

def test_hash():
    key = "VE85jtsmKiz6n22B+lIRRg=="
    accept = compute_accept(key)
    print("accept:",accept)
    assert accept == 'qvR8fSJ12PVkGZev/rAMuJSSfJU='

def test_frame_parse_1_7bit():
    frame_bytes = b'\x81\xac\x8eaY\x93\xf5C4\xf6\xfd\x128\xf4\xeb5 \xe3\xebCc\xb1\xed\t8\xe7\xc3\x04*\xe0\xef\x06<\xb1\xa2C4\xf6\xfd\x128\xf4\xebCc\xb1\xe6\x08{\xee'
    frame = parse_ws_frame(frame_bytes)
    expected_payload = b'{"messageType":"chatMessage","message":"hi"}'

    expected_payload_length = 44
    expected_fin_bit = 1
    expected_opcode = 1
    assert expected_fin_bit == frame.fin_bit
    assert expected_opcode == frame.opcode
    assert expected_payload_length == frame.payload_length
    assert expected_payload == frame.payload

def test_frame_parse_2_7bit():
    frame_bytes = b"\x81\xb8\xb3YS9\xc8{>\\\xc0*2^\xd6\r*I\xd6{i\x1b\xd6:;V\xec:?P\xd67'\x1b\x9f{'\\\xcb-q\x03\x918>\x19\xday<W\x93-;\\\x93>!P\xd7fqD"
    frame = parse_ws_frame(frame_bytes)
    expected_payload = b'{"messageType":"echo_client","text":"am i on the grid?"}'

    expected_payload_length = 56
    expected_fin_bit = 1
    expected_opcode = 1
    assert expected_fin_bit == frame.fin_bit
    assert expected_opcode == frame.opcode
    assert expected_payload_length == frame.payload_length
    assert expected_payload == frame.payload

def test_frame_parse_1_16bit():
    frame_bytes =  b"\x81\xfe\x01.\xd9t\xd1S\xa2V\xbc6\xaa\x07\xb04\xbc \xa8#\xbcV\xebq\xbc\x17\xb9<\x86\x17\xbd:\xbc\x1a\xa5q\xf5V\xa56\xa1\x00\xf3i\xfb\x00\xa8#\xb0\x1a\xb6s\xad\x1b\xf1!\xbc\x15\xb2;\xf9\x00\xb96\xf9E\xe7s\xbb\x1d\xa5s\xa9\x15\xa8?\xb6\x15\xb5s\xb5\x11\xbf4\xad\x1c\xfds\xa9\x15\xa8?\xb6\x15\xb5\x0c\xb5\x11\xbf4\xad\x1c\xf1$\xb0\x00\xb9s\xbb\x11\xf1b\xebB\xf12\xb7\x10\xf1'\xb1\x11\xf11\xb5\x15\xb9 \xaa\x1c\xb99\xf9\x10\xa22\xb1\x1e\xba7\xaa\x15\xba9\xf7T\xb9;\xb3\x10\xb7 \xb1\x1e\xb55\xaa\x15\xbb;\xb2\x18\xb77\xaa\x15\xbd9\xb2\x1c\xa27\xbf\x15\xb39\xac\x01\xe9`\xebL\xe9a\xea@\xe6j\xe1C\xe8g\xebG\xb99\xbc\x1c\xbb8\xbc\x1c\xba$\xb1\x06\xb4;\xb3\x1f\xb78\xb1\x1e\xb05\xf7T\xe9`\xe1A\xe2g\xeeL\xe2d\xeb@\xe9d\xe0G\xe3g\xe1M\xe6`\xedF\xe4k\xe0C\xe2g\xecM\xe9d\xedG\xe4k\xeeM\xe5`\xeaL\xe6j\xedF\xe4`\xe1M\xe6g\xebA\xe8k\xeeG\xe4`\xe0L\xe6f\xe0C\xe9c\xedG\xe8k\xeeG\xe4j\xeaL\xe6f\xebM\xe9a\xeaC\xe5f\xfb\t"

    frame = parse_ws_frame(frame_bytes)
    expected_payload = b'{"messageType":"echo_client","text":"typing to reach the 16 bit payload length, payload_length with be 126 and the blahsshhj dsahjkdsakj. hhjdfshjdfsajhklfdsaljkhsdfabjuu8328823479879423hjehjkehkwhrehjkfkhjaf. 838534783724879324897342589734598743587943387942538974259873539875978043987359387529823745"}'

    expected_payload_length = 302
    expected_fin_bit = 1
    expected_opcode = 1
    assert expected_fin_bit == frame.fin_bit
    assert expected_opcode == frame.opcode
    assert expected_payload_length == frame.payload_length
    assert expected_payload == frame.payload, f"expected_payload:\n{expected_payload}\nactual:{frame.payload}"


def test_frame_parse_2_16bit():
    frame_bytes = b'\x81\xfe\x1fj\xc24\xd8a\xb9\x16\xb5\x04\xb1G\xb9\x06\xa7`\xa1\x11\xa7\x16\xe2C\xa7W\xb0\x0e\x9dW\xb4\x08\xa7Z\xacC\xee\x16\xac\x04\xba@\xfa[\xe0U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00\xa3U\xb9\x00'

    expected_payload = b'{"messageType":"echo_client","text":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaabbb"}'

    expected_payload_length = len(b'{"messageType":"echo_client","text":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaabbb"}')

    print("actual_length:", expected_payload_length)
    frame = parse_ws_frame(frame_bytes)

    expected_fin_bit = 1
    expected_opcode = 1
    assert expected_fin_bit == frame.fin_bit
    assert expected_opcode == frame.opcode
    assert expected_payload_length == frame.payload_length
    assert expected_payload == frame.payload, f"expected_payload:\n{expected_payload}\nactual:{frame.payload}"

if __name__ == "__main__":
    #test_hash()
    #test_frame_parse_1_7bit()
    #test_frame_parse_2_7bit()
    #test_frame_parse_1_16bit()
    test_frame_parse_2_16bit()




